"""Trust score engine with append-only durability and Bayesian-style updates."""

# === Imports / Dependencies ===
from __future__ import annotations

import contextlib
import json
import os
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Mapping, Optional


# === Types, Interfaces, Contracts, Schema ===
@dataclass(frozen=True)
class _JournalEntry:
    """Structured representation of a trust score mutation."""

    agent: str
    score: float
    event: str
    timestamp: str


class TrustEngine:
    """Maintain agent trust scores backed by durable journaled storage."""

    def __init__(
        self,
        storage_path: Path,
        flush_interval: int = 10,
        *,
        thresholds: Optional[Mapping[str, float]] = None,
        default_scores: Optional[Mapping[str, float]] = None,
    ) -> None:
        self.storage_path = storage_path
        self.journal_path = storage_path.with_suffix(f"{storage_path.suffix}.journal")
        self.trust_scores: Dict[str, float] = {}
        self._flush_interval = max(1, flush_interval)
        self._pending_writes = 0
        self._lock = threading.RLock()
        self._ensure_storage_dir()
        thresholds = thresholds or {}
        self._minimum = float(thresholds.get("minimum", 0.1))
        self._maximum = float(thresholds.get("maximum", 1.5))
        self._success_multiplier = float(thresholds.get("success_multiplier", 1.05))
        self._failure_multiplier = float(thresholds.get("failure_multiplier", 0.9))
        self._defaults: Dict[str, float] = {
            str(agent): float(score) for agent, score in (default_scores or {}).items()
        }
        self.load()
        self._apply_defaults()

    def _ensure_storage_dir(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> None:
        """Load trust snapshot and replay journal to reconstruct state."""

        with self._lock:
            self.trust_scores = self._load_snapshot()
            for entry in self._read_journal():
                self.trust_scores[entry.agent] = entry.score

    def _apply_defaults(self) -> None:
        for agent, score in self._defaults.items():
            self.trust_scores.setdefault(agent, score)

    def ensure_agent(self, agent: str) -> None:
        """Ensure ``agent`` has a trust score entry using defaults when needed."""

        with self._lock:
            if agent not in self.trust_scores:
                self.trust_scores[agent] = self._defaults.get(agent, 1.0)

    def _load_snapshot(self) -> Dict[str, float]:
        try:
            raw_text = self.storage_path.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            return {}
        try:
            data = json.loads(raw_text)
        except (ValueError, TypeError):
            return {}
        if not isinstance(data, dict):
            return {}
        snapshot: Dict[str, float] = {}
        for agent, score in data.items():
            try:
                snapshot[str(agent)] = float(score)
            except (TypeError, ValueError):
                continue
        return snapshot

    def _read_journal(self) -> Iterable[_JournalEntry]:
        try:
            lines = self.journal_path.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            return []
        except OSError:
            return []
        entries = []
        for line in lines:
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                agent = str(payload["agent"])
                score = float(payload["score"])
                event = str(payload.get("event", "update"))
                timestamp = str(payload.get("timestamp", ""))
            except (ValueError, TypeError, KeyError):
                continue
            entries.append(
                _JournalEntry(agent=agent, score=score, event=event, timestamp=timestamp)
            )
        return entries

    def save(self) -> None:
        """Persist the current state to a compact snapshot and truncate the journal."""

        self.flush()

    def flush(self) -> None:
        """Explicitly persist a snapshot and clear the journal."""

        with self._lock:
            serialized = json.dumps(self.trust_scores, sort_keys=True)
            temp_path = self.storage_path.with_suffix(f"{self.storage_path.suffix}.tmp")
            try:
                temp_path.write_text(serialized, encoding="utf-8")
                os.replace(temp_path, self.storage_path)
                if self.journal_path.exists():
                    self.journal_path.unlink()
                self._pending_writes = 0
            except OSError:
                # If persistence fails we keep the journal for replay and remove temp file if present.
                with contextlib.suppress(FileNotFoundError, OSError):
                    temp_path.unlink()

    def record_failure(self, agent: str) -> None:
        """Demote trust for ``agent`` in response to a failure event."""

        self._record(agent, multiplier=self._failure_multiplier, event="failure")

    def record_success(self, agent: str) -> None:
        """Promote trust for ``agent`` when a success event is observed."""

        self._record(agent, multiplier=self._success_multiplier, event="success")

    def _record(self, agent: Optional[str], multiplier: float, event: str) -> None:
        if not agent:
            return
        with self._lock:
            score = self.trust_scores.get(agent, 1.0)
            new_score = max(min(score * multiplier, self._maximum), self._minimum)
            self.trust_scores[agent] = new_score
            self._append_journal(agent, new_score, event)
            self._pending_writes += 1
            if self._pending_writes >= self._flush_interval:
                self._pending_writes = 0
                self.flush()

    def _append_journal(self, agent: str, score: float, event: str) -> None:
        entry = {
            "agent": agent,
            "score": score,
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        try:
            with self.journal_path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(entry, sort_keys=True))
                handle.write("\n")
        except OSError:
            # Journaling failure leaves state in-memory; snapshot on next flush will recover.
            pass

    def get_trust_scores(self) -> Dict[str, float]:
        """Return a copy of current trust scores for arbitration."""

        with self._lock:
            return dict(self.trust_scores)


# === Error & Edge Case Handling ===
# Missing or corrupt snapshots or journal entries revert gracefully to empty defaults. Journal write
# failures leave state in memory until the next successful flush, preserving durability through replay.


# === Performance / Resource Considerations ===
# Journaling performs append-only writes and batches snapshot compaction every ``flush_interval`` events.
# Thread locks guard concurrent updates while keeping read access lightweight.


# === Exports / Public API ===
__all__ = ["TrustEngine"]
