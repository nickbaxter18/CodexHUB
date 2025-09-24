"""Loader utilities for governance rules that influence arbitration decisions."""

# === Imports / Dependencies ===
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Optional


# === Types, Interfaces, Contracts, Schema ===
class GovernanceRules:
    """Immutable view over governance priorities per metric and agent."""

    def __init__(self, priorities: Optional[Mapping[str, Mapping[str, float]]] = None) -> None:
        self._priorities: Dict[str, Dict[str, float]] = {}
        if priorities:
            for metric, agents in priorities.items():
                self._priorities[metric] = {
                    str(agent): float(weight) for agent, weight in agents.items()
                }

    def get_priority(self, metric: Optional[str], agent: Optional[str]) -> float:
        """Return governance priority for ``agent`` on ``metric`` (defaults to ``1.0``)."""

        if not metric or not agent:
            return 1.0
        return self._priorities.get(metric, {}).get(agent, 1.0)

    def as_dict(self) -> Dict[str, Dict[str, float]]:
        """Expose priorities for debugging and audits."""

        return {metric: dict(agents) for metric, agents in self._priorities.items()}


def load_governance_rules(path: Optional[Path] = None) -> GovernanceRules:
    """Load governance rules from ``path`` or default location if available."""

    search_paths = []
    if path is not None:
        search_paths.append(Path(path))
    search_paths.append(Path("config/governance_rules.json"))
    for candidate in search_paths:
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                return GovernanceRules(data.get("priorities", {}))
            except (OSError, ValueError, TypeError, AttributeError):
                break
    return GovernanceRules()


# === Error & Edge Case Handling ===
# Invalid or missing rule files fall back to empty governance data, effectively using neutral priorities.


# === Performance / Resource Considerations ===
# Rule files are loaded eagerly once per process invocation; the resulting structure is a small nested dict.


# === Exports / Public API ===
__all__ = ["GovernanceRules", "load_governance_rules"]
