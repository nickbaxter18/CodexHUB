"""Load NDJSON-based knowledge corpora for the Knowledge agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, List, Sequence

from agents.specialist_agents import KnowledgeDocument

if TYPE_CHECKING:  # pragma: no cover - import for typing only
    from agents.specialist_agents import KnowledgeAgent


class KnowledgeCorpusLoader:
    """Load KnowledgeDocument entries from NDJSON files or directories."""

    def __init__(self, paths: Sequence[Path | str]) -> None:
        if not paths:
            raise ValueError("At least one path must be provided for knowledge loading")
        self._paths: List[Path] = [Path(path) for path in paths]

    def load(self) -> List[KnowledgeDocument]:
        """Return all valid documents discovered across configured paths."""

        documents: List[KnowledgeDocument] = []
        for path in self._paths:
            if path.is_dir():
                for file_path in sorted(path.glob("*.ndjson")):
                    documents.extend(self._load_file(file_path))
            elif path.is_file() and path.suffix.lower() == ".ndjson":
                documents.extend(self._load_file(path))
        return documents

    def load_into_agent(self, agent: "KnowledgeAgent") -> int:
        """Populate ``agent`` with corpus documents, returning count ingested."""

        documents = self.load()
        if documents:
            agent.ingest_documents(documents)
        return len(documents)

    @staticmethod
    def _load_file(path: Path) -> List[KnowledgeDocument]:
        documents: List[KnowledgeDocument] = []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:  # pragma: no cover - surfaced during IO failures
            return documents
        for index, line in enumerate(lines, start=1):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            try:
                document = KnowledgeDocument.from_mapping(
                    payload, fallback_id=f"{path.name}:{index}"
                )
            except ValueError:
                continue
            documents.append(document)
        return documents


def discover_default_knowledge_paths(root: Path | None = None) -> List[Path]:
    """Return NDJSON files within the repository suitable for knowledge bootstrapping."""

    base = root or Path(__file__).resolve().parents[1]
    candidates: List[Path] = []
    for pattern in ("*.ndjson",):
        candidates.extend(sorted(base.glob(pattern)))
    knowledge_dir = base / "knowledge_sources"
    if knowledge_dir.exists():
        candidates.extend(sorted(knowledge_dir.glob("*.ndjson")))
    return [path for path in candidates if path.is_file()]


def bootstrap_repository_knowledge(agent: "KnowledgeAgent", *, root: Path | None = None) -> int:
    """Load repository NDJSON corpora into ``agent`` and return ingested count."""

    paths = discover_default_knowledge_paths(root)
    if not paths:
        return 0
    loader = KnowledgeCorpusLoader(paths)
    return loader.load_into_agent(agent)
