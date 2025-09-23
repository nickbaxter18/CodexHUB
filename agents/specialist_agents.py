"""
SECTION: Header & Purpose
    - Provides concrete specialist agents (Architect, Frontend, Backend, QA, CI/CD, Knowledge)
      that extend the shared ``Agent`` contract.
    - Introduces ``SpecialistAgent`` dispatch utilities that normalise task payloads, coordinate
      macro expansion, and surface governance-aware capability metadata.
    - Implements a lightweight knowledge retrieval pipeline so the Knowledge agent can answer
      repository style and governance queries from NDJSON knowledge sources.

SECTION: Imports / Dependencies
    - Depends on Python standard library modules (dataclasses, json, pathlib, re, typing).
    - Integrates with the existing macro engine/runtime and QA subsystems to ensure outputs are
      validated against configured QA budgets and that macro expansions remain type-safe.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Sequence,
    Tuple,
)

from macro_system.engine import MacroEngine
from macro_system.types import Macro
from qa.qa_engine import QAEngine
from qa.qa_event_bus import QAEventBus

from .agent_base import Agent


# === Types & Interfaces ===
@dataclass(frozen=True)
class AgentTask:
    """Normalised representation of a specialist agent task request."""

    action: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    tests_executed: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None


TaskHandler = Callable[[AgentTask], Dict[str, Any]]


@dataclass(frozen=True)
class KnowledgeDocument:
    """Immutable knowledge entry surfaced by the ``KnowledgeAgent``."""

    identifier: str
    title: str
    content: str
    tags: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], *, fallback_id: str) -> "KnowledgeDocument":
        """Build a document from a mapping, ensuring required fields are present."""

        identifier = str(payload.get("id", fallback_id))
        title = str(payload.get("title") or payload.get("name") or identifier)
        raw_content = payload.get("content") or payload.get("body") or payload.get("text")
        if raw_content is None:
            raise ValueError("Knowledge entries must include content/text fields")
        content = str(raw_content)
        raw_tags = payload.get("tags") or payload.get("topics") or []
        if isinstance(raw_tags, (list, tuple, set)):
            tags = tuple(str(tag) for tag in raw_tags)
        elif raw_tags:
            tags = (str(raw_tags),)
        else:
            tags = tuple()
        return cls(identifier=identifier, title=title, content=content, tags=tags)


class SpecialistAgent(Agent):
    """Base class for concrete specialist agents with macro-aware task dispatch."""

    def __init__(
        self,
        name: str,
        qa_engine: QAEngine,
        event_bus: QAEventBus,
        *,
        macro_engine: Optional[MacroEngine] = None,
        domain_macro_filter: Optional[Callable[[Macro], bool]] = None,
    ) -> None:
        super().__init__(name, qa_engine, event_bus)
        self._handlers: MutableMapping[str, TaskHandler] = {}
        self._macro_engine = macro_engine
        self._domain_macros: Tuple[str, ...] = ()
        if macro_engine is not None and domain_macro_filter is not None:
            domain_macros: List[str] = []
            for macro_name in macro_engine.available_macros():
                description = macro_engine.describe(macro_name)
                if domain_macro_filter(description):
                    domain_macros.append(macro_name)
            self._domain_macros = tuple(sorted(domain_macros))
        if macro_engine is not None:
            self.register_handler("expand_macros", self._handle_expand_macros)

    # === Registration & Introspection ===
    def register_handler(self, action: str, handler: TaskHandler) -> None:
        """Register ``handler`` for ``action``; overwriting requires explicit deregistration."""

        if not action:
            raise ValueError("Action name must be a non-empty string")
        if action in self._handlers:
            raise ValueError(f"Handler already registered for action '{action}'")
        self._handlers[action] = handler

    def available_actions(self) -> List[str]:
        """Return the sorted list of actions supported by the specialist agent."""

        return sorted(self._handlers)

    def describe_capabilities(self) -> Dict[str, Any]:
        """Expose agent actions, default macros, and required QA tests for observability."""

        return {
            "agent": self.name,
            "actions": self.available_actions(),
            "default_macros": list(self._domain_macros),
            "required_tests": self.required_tests(),
        }

    # === Task Execution ===
    def perform_task(
        self, task: AgentTask | Mapping[str, Any], *, correlation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Normalise ``task`` and dispatch to the appropriate handler."""

        normalised = self._normalise_task(task)
        if correlation_id is not None and normalised.correlation_id is None:
            normalised = AgentTask(
                action=normalised.action,
                payload=dict(normalised.payload),
                tests_executed=tuple(normalised.tests_executed),
                metadata=dict(normalised.metadata),
                correlation_id=correlation_id,
            )
        handler = self._handlers.get(normalised.action)
        if handler is None:
            raise ValueError(f"Agent '{self.name}' does not support action '{normalised.action}'")
        result = handler(normalised)
        if not isinstance(result, dict):
            raise TypeError("Handler must return a dictionary of metrics and outputs")
        result.setdefault("agent", self.name)
        result.setdefault("action", normalised.action)
        result.setdefault("inputs", dict(normalised.payload))
        if normalised.metadata and "metadata" not in result:
            result["metadata"] = dict(normalised.metadata)
        if normalised.tests_executed and "tests_executed" not in result:
            result["tests_executed"] = list(normalised.tests_executed)
        metrics = result.setdefault("metrics", {})
        if not isinstance(metrics, dict):
            raise TypeError("Handler metrics entry must be a dictionary")
        metrics.setdefault("actions_executed", 1)
        if normalised.correlation_id:
            result.setdefault("correlation_id", normalised.correlation_id)
        return result

    # === Macro Utilities ===
    def expand_macros(self, macros: Sequence[str]) -> Dict[str, str]:
        """Expand the provided macro names using the configured macro engine."""

        if self._macro_engine is None:
            raise RuntimeError(f"Agent '{self.name}' cannot expand macros without a macro engine")
        expansions: Dict[str, str] = {}
        for macro_name in macros:
            if not isinstance(macro_name, str) or not macro_name.startswith("::"):
                raise ValueError("Macro names must be strings prefixed with '::'")
            expansions[macro_name] = self._macro_engine.expand(macro_name)
        return expansions

    def default_macros(self) -> Tuple[str, ...]:
        """Return macros associated with the agent's domain scope."""

        return self._domain_macros

    # === Internal Helpers ===
    @staticmethod
    def _normalise_task(task: AgentTask | Mapping[str, Any]) -> AgentTask:
        if isinstance(task, AgentTask):
            return task
        if not isinstance(task, Mapping):
            raise TypeError("Task must be an AgentTask or mapping")
        action = task.get("action")
        if not isinstance(action, str) or not action.strip():
            raise ValueError("Task action must be a non-empty string")
        payload = task.get("payload", {})
        if isinstance(payload, Mapping):
            payload_dict = dict(payload)
        elif payload is None:
            payload_dict = {}
        else:
            raise TypeError("Task payload must be a mapping when provided")
        tests_value = task.get("tests_executed", ())
        if tests_value in (None, "", []):
            tests_tuple: Tuple[str, ...] = tuple()
        elif isinstance(tests_value, Sequence) and not isinstance(tests_value, (str, bytes)):
            tests_tuple = tuple(str(item) for item in tests_value)
        else:
            raise TypeError("tests_executed must be an iterable of strings when provided")
        metadata_value = task.get("metadata", {})
        if isinstance(metadata_value, Mapping):
            metadata_dict = dict(metadata_value)
        elif metadata_value in (None, ""):
            metadata_dict = {}
        else:
            raise TypeError("Task metadata must be a mapping when provided")
        correlation_id = task.get("correlation_id")
        if correlation_id is not None:
            correlation_id = str(correlation_id)
        return AgentTask(
            action=action,
            payload=payload_dict,
            tests_executed=tests_tuple,
            metadata=metadata_dict,
            correlation_id=correlation_id,
        )

    def _handle_expand_macros(self, task: AgentTask) -> Dict[str, Any]:
        macros = self._resolve_macro_names(task, default_to_domain=True)
        expansions = self.expand_macros(macros)
        return {
            "metrics": {
                "macros_requested": len(macros),
                "macros_resolved": len(expansions),
            },
            "outputs": {"macros": expansions},
        }

    def _resolve_macro_names(
        self,
        task: AgentTask,
        *,
        default_to_domain: bool,
        allow_empty: bool = False,
        limit: Optional[int] = None,
    ) -> List[str]:
        payload_macros = task.payload.get("macros")
        macros: List[str]
        if payload_macros is None:
            macros = list(self._domain_macros) if default_to_domain else []
        elif isinstance(payload_macros, Sequence) and not isinstance(payload_macros, (str, bytes)):
            macros = [str(name) for name in payload_macros]
        else:
            raise TypeError("Payload macros must be provided as a sequence of strings")
        if limit is not None and limit > 0:
            macros = macros[:limit]
        if not macros and not allow_empty:
            raise ValueError("No macros available for expansion")
        return macros

    @staticmethod
    def _normalise_limit(value: Any) -> Optional[int]:
        """Convert an optional payload limit into a positive integer if provided."""

        if value is None:
            return None
        if isinstance(value, bool):
            raise ValueError("Boolean values are not valid limits")
        try:
            limit = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError("Limit must be coercible to an integer") from exc
        return limit if limit > 0 else None


class ArchitectAgent(SpecialistAgent):
    """Architect specialist agent orchestrating macro-driven architectural plans."""

    def __init__(
        self,
        qa_engine: QAEngine,
        event_bus: QAEventBus,
        *,
        macro_engine: Optional[MacroEngine] = None,
    ) -> None:
        super().__init__(
            "Architect",
            qa_engine,
            event_bus,
            macro_engine=macro_engine,
            domain_macro_filter=lambda macro: (macro.owner_agent or "").lower()
            == "architect agent".lower(),
        )
        self.register_handler("generate_blueprint", self._generate_blueprint)

    def _generate_blueprint(self, task: AgentTask) -> Dict[str, Any]:
        limit = self._normalise_limit(task.payload.get("limit"))
        macros = self._resolve_macro_names(task, default_to_domain=True, limit=limit)
        expansions = self.expand_macros(macros)
        plan_outline = "\n\n".join(expansions.values())
        return {
            "metrics": {
                "architecture_macros": len(macros),
                "outline_characters": len(plan_outline),
            },
            "outputs": {
                "macro_order": macros,
                "blueprint": plan_outline,
            },
        }


class FrontendAgent(SpecialistAgent):
    """Frontend specialist agent delivering UI scaffolds and component guidance."""

    def __init__(
        self,
        qa_engine: QAEngine,
        event_bus: QAEventBus,
        *,
        macro_engine: Optional[MacroEngine] = None,
    ) -> None:
        super().__init__(
            "Frontend",
            qa_engine,
            event_bus,
            macro_engine=macro_engine,
            domain_macro_filter=lambda macro: (macro.owner_agent or "").lower()
            == "frontend agent".lower(),
        )
        self.register_handler("scaffold_interface", self._scaffold_interface)

    def _scaffold_interface(self, task: AgentTask) -> Dict[str, Any]:
        limit = self._normalise_limit(task.payload.get("limit"))
        macros = self._resolve_macro_names(task, default_to_domain=True, limit=limit)
        expansions = self.expand_macros(macros)
        components = {
            name: expansion
            for name, expansion in expansions.items()
            if name.startswith("::frontendgen")
        }
        return {
            "metrics": {
                "frontend_macros": len(macros),
                "component_sections": len(components),
            },
            "outputs": {
                "components": components,
                "supporting_guidance": expansions,
            },
        }


class BackendAgent(SpecialistAgent):
    """Backend specialist agent focused on API, data, and performance workflows."""

    def __init__(
        self,
        qa_engine: QAEngine,
        event_bus: QAEventBus,
        *,
        macro_engine: Optional[MacroEngine] = None,
    ) -> None:
        super().__init__(
            "Backend",
            qa_engine,
            event_bus,
            macro_engine=macro_engine,
            domain_macro_filter=lambda macro: (macro.owner_agent or "").lower()
            == "backend agent".lower(),
        )
        self.register_handler("design_services", self._design_services)

    def _design_services(self, task: AgentTask) -> Dict[str, Any]:
        limit = self._normalise_limit(task.payload.get("limit"))
        macros = self._resolve_macro_names(task, default_to_domain=True, limit=limit)
        expansions = self.expand_macros(macros)
        api_macros = [name for name in macros if "api" in name]
        return {
            "metrics": {
                "backend_macros": len(macros),
                "api_related_macros": len(api_macros),
            },
            "outputs": {
                "macro_order": macros,
                "service_guidance": expansions,
            },
        }


class QAAgent(SpecialistAgent):
    """Quality assurance agent aggregating regression, accessibility, and performance audits."""

    def __init__(
        self,
        qa_engine: QAEngine,
        event_bus: QAEventBus,
        *,
        macro_engine: Optional[MacroEngine] = None,
    ) -> None:
        super().__init__(
            "QA",
            qa_engine,
            event_bus,
            macro_engine=macro_engine,
            domain_macro_filter=lambda macro: (macro.owner_agent or "").lower()
            == "qa agent".lower(),
        )
        self.register_handler("assemble_suite", self._assemble_suite)

    def _assemble_suite(self, task: AgentTask) -> Dict[str, Any]:
        limit = self._normalise_limit(task.payload.get("limit"))
        macros = self._resolve_macro_names(task, default_to_domain=True, limit=limit)
        expansions = self.expand_macros(macros)
        required_tests = self.required_tests()
        metrics = {
            "qa_macros": len(macros),
            "required_tests": len(required_tests),
        }
        outputs = {
            "qa_playbook": expansions,
            "test_gaps": [test for test in required_tests if test not in task.tests_executed],
        }
        if task.tests_executed:
            metrics["tests_provided"] = len(task.tests_executed)
        return {"metrics": metrics, "outputs": outputs}


class CICDAgent(SpecialistAgent):
    """CI/CD specialist agent orchestrating pipeline operations and recovery flows."""

    def __init__(
        self,
        qa_engine: QAEngine,
        event_bus: QAEventBus,
        *,
        macro_engine: Optional[MacroEngine] = None,
    ) -> None:
        super().__init__(
            "CICD",
            qa_engine,
            event_bus,
            macro_engine=macro_engine,
            domain_macro_filter=self._is_cicd_macro if macro_engine is not None else None,
        )
        self.register_handler("orchestrate_pipeline", self._orchestrate_pipeline)

    @staticmethod
    def _is_cicd_macro(macro: Macro) -> bool:
        name = macro.name.lower()
        tags = {tag.lower() for tag in macro.tags}
        return "cicd" in name or "ci" in tags or "cd" in tags or "deployment" in tags

    def _orchestrate_pipeline(self, task: AgentTask) -> Dict[str, Any]:
        macros = self._resolve_macro_names(
            task, default_to_domain=True, limit=task.payload.get("limit")
        )
        expansions = self.expand_macros(macros)
        recovery_macros = [name for name in macros if "rollback" in name or "notify" in name]
        return {
            "metrics": {
                "pipeline_macros": len(macros),
                "recovery_steps": len(recovery_macros),
            },
            "outputs": {
                "pipeline_sequence": macros,
                "playbook": expansions,
            },
        }


class KnowledgeAgent(SpecialistAgent):
    """Knowledge integration agent providing NDJSON-backed governance answers."""

    def __init__(
        self,
        qa_engine: QAEngine,
        event_bus: QAEventBus,
        *,
        macro_engine: Optional[MacroEngine] = None,
        documents: Optional[Iterable[KnowledgeDocument]] = None,
    ) -> None:
        super().__init__(
            "Knowledge",
            qa_engine,
            event_bus,
            macro_engine=macro_engine,
            domain_macro_filter=None,
        )
        self._documents: List[KnowledgeDocument] = list(documents or [])
        self.register_handler("query", self._query)

    def ingest_documents(self, documents: Iterable[KnowledgeDocument]) -> None:
        """Add additional knowledge documents to the in-memory corpus."""

        for document in documents:
            self._documents.append(document)

    def load_ndjson(self, path: Path | str) -> int:
        """Load NDJSON knowledge entries from ``path`` into the agent corpus."""

        entries_added = 0
        resolved_path = Path(path)
        try:
            lines = resolved_path.read_text(encoding="utf-8").splitlines()
        except OSError as exc:  # pragma: no cover - surface file IO issues
            raise RuntimeError(f"Failed to load knowledge file: {resolved_path}") from exc
        for index, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
                document = KnowledgeDocument.from_mapping(
                    payload, fallback_id=f"{resolved_path.name}:{index}"
                )
            except (json.JSONDecodeError, ValueError):
                continue
            self._documents.append(document)
            entries_added += 1
        return entries_added

    def documents(self) -> List[KnowledgeDocument]:
        """Return a copy of the knowledge corpus for inspection/testing."""

        return list(self._documents)

    def _query(self, task: AgentTask) -> Dict[str, Any]:
        payload = task.payload
        query = payload.get("query")
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Knowledge queries must include a non-empty 'query' string")
        limit = payload.get("limit")
        limit_int = int(limit) if isinstance(limit, int) and limit > 0 else 5
        results = self._search_documents(query, limit=limit_int)
        metrics = {
            "knowledge_documents": len(self._documents),
            "results_returned": len(results),
        }
        if not results:
            metrics["misses"] = 1
        return {"metrics": metrics, "outputs": {"answers": results}}

    def _search_documents(self, query: str, *, limit: int) -> List[Dict[str, Any]]:
        tokens = [token for token in re.findall(r"[a-z0-9]+", query.lower()) if token]
        if not tokens:
            return []
        scored: List[Tuple[float, KnowledgeDocument, str]] = []
        for document in self._documents:
            score = self._score_document(document, tokens)
            if score <= 0:
                continue
            snippet = self._build_snippet(document.content, tokens)
            scored.append((score, document, snippet))
        scored.sort(key=lambda entry: entry[0], reverse=True)
        answers: List[Dict[str, Any]] = []
        for score, document, snippet in scored[:limit]:
            answers.append(
                {
                    "id": document.identifier,
                    "title": document.title,
                    "tags": list(document.tags),
                    "score": score,
                    "snippet": snippet,
                }
            )
        return answers

    @staticmethod
    def _score_document(document: KnowledgeDocument, tokens: Sequence[str]) -> float:
        haystack_title = document.title.lower()
        haystack_content = document.content.lower()
        score = 0.0
        for token in tokens:
            score += haystack_title.count(token) * 2.0
            score += haystack_content.count(token)
        if document.tags:
            tag_text = " ".join(tag.lower() for tag in document.tags)
            for token in tokens:
                score += 0.5 if token in tag_text else 0.0
        return score

    @staticmethod
    def _build_snippet(content: str, tokens: Sequence[str], *, radius: int = 120) -> str:
        lowered = content.lower()
        for token in tokens:
            index = lowered.find(token)
            if index >= 0:
                start = max(index - radius, 0)
                end = min(index + radius, len(content))
                snippet = content[start:end].strip()
                return snippet
        return content[: radius * 2].strip()


# === Exports / Public API ===
__all__ = [
    "AgentTask",
    "ArchitectAgent",
    "BackendAgent",
    "CICDAgent",
    "FrontendAgent",
    "KnowledgeAgent",
    "KnowledgeDocument",
    "QAAgent",
    "SpecialistAgent",
]
