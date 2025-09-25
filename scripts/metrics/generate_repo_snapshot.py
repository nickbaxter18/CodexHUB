#!/usr/bin/env python3
"""Generate a repository snapshot with directory inventory and knowledge graph data."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

ROOT = Path(__file__).resolve().parents[2]
RESULTS_DIR = ROOT / "results" / "metrics"
DEFAULT_GRAPH_PATH = RESULTS_DIR / "repo-graph.json"
DEFAULT_MERMAID_PATH = RESULTS_DIR / "repo-graph.mmd"
DEFAULT_SUMMARY_PATH = RESULTS_DIR / "repo-graph-summary.md"
SKIP_DIR_NAMES = {
    ".context-bundle",
    ".git",
    ".husky",
    ".pnpm",
    "node_modules",
    "results",
    "dist",
    "build",
    "__pycache__",
    ".ruff_cache",
    ".mypy_cache",
}
GOVERNANCE_FILES = {"AGENT.md": "agent", "AGENTS.md": "agents"}
QUALITY_CONFIG_NAMES = {
    ".pre-commit-config.yaml": "pre_commit",
    "pyproject.toml": "python_tooling",
    "package.json": "node_package",
    "pnpm-workspace.yaml": "pnpm_workspace",
    "turbo.json": "turbo_pipeline",
    "eslint.config.mjs": "eslint",
    "ruff.toml": "ruff",
    "cspell.json": "spellcheck",
    "requirements.txt": "python_requirements",
    "requirements-dev.txt": "python_requirements",
}


@dataclass
class Node:
    identifier: str
    label: str
    node_type: str
    path: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "id": self.identifier,
            "label": self.label,
            "type": self.node_type,
            "path": self.path,
        }


@dataclass
class Edge:
    source: str
    target: str
    relation: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "source": self.source,
            "target": self.target,
            "relation": self.relation,
        }


def load_json(path: Path) -> Optional[dict]:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def decode_workspace_patterns(path: Path) -> List[str]:
    raw = path.read_text(encoding="utf-8")
    patterns = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("-"):
            patterns.append(stripped.lstrip("- ").strip("'\""))
    return patterns


def resolve_workspace_members(patterns: Sequence[str]) -> Dict[str, Path]:
    members: Dict[str, Path] = {}
    for pattern in patterns:
        for path in ROOT.glob(pattern):
            if path.is_dir():
                if path.name == "__pycache__":
                    continue
                key = path.name
                if key in members:
                    key = f"{path.parent.name}/{path.name}"
                members[key] = path
    return members


def collect_package_info(path: Path) -> Optional[dict]:
    package_json = path / "package.json"
    if not package_json.exists():
        return None
    data = load_json(package_json)
    if not data:
        return None
    return {
        "name": data.get("name", path.name),
        "dependencies": sorted((data.get("dependencies") or {}).keys()),
        "devDependencies": sorted((data.get("devDependencies") or {}).keys()),
        "scripts": sorted((data.get("scripts") or {}).keys()),
    }


def infer_node_type(path: Path) -> str:
    parts = path.relative_to(ROOT).parts
    if parts[0] == "apps":
        return "app"
    if parts[0] in {"packages", "libs"}:
        return "library"
    if parts[0] in {"src", "scripts"}:
        return "core"
    if parts[0] in {
        "backend",
        "qa_engine",
        "meta_agent",
        "macro_system",
        "codex-meta-intelligence",
        "agents",
    }:
        return "service"
    return "misc"


def build_node_identifier(path: Path) -> str:
    return "/".join(path.relative_to(ROOT).parts)


def collect_python_packages() -> Dict[str, Path]:
    config_path = ROOT / "pyproject.toml"
    if not config_path.exists():
        return {}
    config = config_path.read_text(encoding="utf-8")
    pattern = re.compile(r"^src\s*=\s*\[(.*?)\]", re.MULTILINE | re.DOTALL)
    match = pattern.search(config)
    packages: Dict[str, Path] = {}
    if match:
        entries = match.group(1).splitlines()
        for entry in entries:
            cleaned = entry.strip()
            cleaned = cleaned.strip(",")
            cleaned = cleaned.strip()
            cleaned = cleaned.strip('"')
            if not cleaned:
                continue
            packages[cleaned] = ROOT / cleaned
    extras = {
        "meta_agent": ROOT / "meta_agent",
        "macro_system": ROOT / "macro_system",
        "qa_engine": ROOT / "qa_engine",
    }
    for name, path in extras.items():
        packages.setdefault(name, path)
    return {name: path for name, path in packages.items() if path.exists()}


def iter_repository_files() -> Iterable[Tuple[Path, Sequence[str]]]:
    for root, dirs, files in os.walk(ROOT):
        root_path = Path(root)
        if root_path == ROOT:
            relative_parts: Sequence[str] = ()
        else:
            relative_parts = root_path.relative_to(ROOT).parts
        if any(part in SKIP_DIR_NAMES for part in relative_parts):
            dirs[:] = []
            continue
        dirs[:] = [name for name in dirs if name not in SKIP_DIR_NAMES]
        yield root_path, files


def collect_governance_artifacts() -> List[Dict[str, str]]:
    artifacts: List[Dict[str, str]] = []
    for directory, files in iter_repository_files():
        relevant = set(files) & set(GOVERNANCE_FILES.keys())
        if not relevant:
            continue
        for filename in sorted(relevant):
            path = directory / filename
            relative_path = path.relative_to(ROOT)
            artifacts.append(
                {
                    "path": str(relative_path),
                    "scope": str(relative_path.parent) or ".",
                    "kind": GOVERNANCE_FILES[filename],
                }
            )
    return sorted(artifacts, key=lambda item: item["path"])


def collect_quality_configs() -> List[Dict[str, str]]:
    configs: List[Dict[str, str]] = []
    for directory, files in iter_repository_files():
        for filename in files:
            config_type = QUALITY_CONFIG_NAMES.get(filename)
            if not config_type:
                continue
            path = (directory / filename).relative_to(ROOT)
            configs.append(
                {
                    "path": str(path),
                    "type": config_type,
                }
            )
    deduped: Dict[str, Dict[str, str]] = {}
    for config in configs:
        deduped[config["path"]] = config
    return sorted(deduped.values(), key=lambda item: item["path"])


def scan_python_imports(
    package_name: str, path: Path, module_map: Dict[str, str]
) -> Dict[str, int]:
    import_counts: Dict[str, int] = defaultdict(int)
    if not path.exists():
        return import_counts
    for file_path in path.rglob("*.py"):
        try:
            source = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in re.finditer(r"^(?:from|import)\s+([\w\.]+)", source, re.MULTILINE):
            module = match.group(1)
            top_level = module.split(".")[0]
            target = module_map.get(top_level)
            if target and target != package_name:
                import_counts[target] += 1
    return import_counts


def compose_mermaid(nodes: Iterable[Node], edges: Iterable[Edge]) -> str:
    lines = ["graph TD"]
    for node in nodes:
        safe_label = node.label.replace("`", '"')
        lines.append(f"  {node.identifier.replace('/', '_')}[{safe_label}]")
    for edge in edges:
        lines.append(
            "  "
            + edge.source.replace("/", "_")
            + " -->|"
            + edge.relation.replace("|", "/")
            + "| "
            + edge.target.replace("/", "_")
        )
    return "\n".join(lines)


def build_graph() -> dict:
    workspace_patterns = decode_workspace_patterns(ROOT / "pnpm-workspace.yaml")
    workspace_members = resolve_workspace_members(workspace_patterns)

    python_packages = collect_python_packages()
    module_map = {}
    for name in python_packages:
        module_map[name.split("/")[-1]] = name
    module_map.update(
        {
            "src": "src",
            "packages": "packages/automation",
            "qa_engine": "qa_engine",
            "meta_agent": "meta_agent",
            "macro_system": "macro_system",
        }
    )

    nodes: Dict[str, Node] = {}
    edges: List[Edge] = []

    for _key, path in workspace_members.items():
        identifier = build_node_identifier(path)
        node_type = infer_node_type(path)
        package_info = collect_package_info(path)
        label = package_info["name"] if package_info else path.name
        nodes[identifier] = Node(
            identifier=identifier,
            label=label,
            node_type=node_type,
            path=str(path.relative_to(ROOT)),
        )
        if package_info:
            for dep in package_info["dependencies"] + package_info["devDependencies"]:
                for _other_key, other_path in workspace_members.items():
                    other_info = collect_package_info(other_path)
                    if other_info and other_info["name"] == dep:
                        edges.append(
                            Edge(
                                source=identifier,
                                target=build_node_identifier(other_path),
                                relation="depends_on",
                            )
                        )

    for package, path in python_packages.items():
        identifier = build_node_identifier(path)
        if identifier not in nodes:
            nodes[identifier] = Node(
                identifier=identifier,
                label=package,
                node_type="python",
                path=str(path.relative_to(ROOT)),
            )

    for package, path in python_packages.items():
        identifier = build_node_identifier(path)
        import_counts = scan_python_imports(package, path, module_map)
        for target_name, count in import_counts.items():
            target_path = python_packages.get(target_name)
            if not target_path:
                continue
            target_identifier = build_node_identifier(target_path)
            relation = "imports"
            if count > 5:
                relation = f"imports({count})"
            edges.append(Edge(source=identifier, target=target_identifier, relation=relation))

    nodes_list = sorted(nodes.values(), key=lambda item: item.identifier)
    edges_list = edges

    mermaid = compose_mermaid(nodes_list, edges_list)
    governance_artifacts = collect_governance_artifacts()
    quality_configs = collect_quality_configs()

    return {
        "generatedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
        "nodes": [node.to_dict() for node in nodes_list],
        "edges": [edge.to_dict() for edge in edges_list],
        "mermaid": mermaid,
        "workspaceMembers": sorted(
            {key: str(path.relative_to(ROOT)) for key, path in workspace_members.items()}.items(),
        ),
        "pythonPackages": sorted(
            {key: str(path.relative_to(ROOT)) for key, path in python_packages.items()}.items()
        ),
        "governanceArtifacts": governance_artifacts,
        "qualityConfigs": quality_configs,
    }


def summarise_graph(graph: dict) -> str:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    node_types = Counter(node.get("type", "unknown") for node in nodes)
    dependency_edges = [edge for edge in edges if edge.get("relation") == "depends_on"]
    import_edges = [edge for edge in edges if edge.get("relation", "").startswith("imports")]

    top_dependencies = Counter(edge["target"] for edge in dependency_edges)
    top_imports = Counter(edge["target"] for edge in import_edges)

    def format_table(counter: Counter[str]) -> str:
        if not counter:
            return "_None captured in latest snapshot._"
        lines = ["| Target | References |", "| --- | ---: |"]
        for identifier, count in counter.most_common(10):
            lines.append(f"| `{identifier}` | {count} |")
        return "\n".join(lines)

    lines = [
        "# Workspace Knowledge Graph Summary",
        "",
        f"Generated on **{graph.get('generatedAt', 'unknown')}**.",
        "",
        "## Node Composition",
        "",
        "| Type | Count |",
        "| --- | ---: |",
    ]

    for node_type, count in sorted(node_types.items(), key=lambda item: item[0]):
        lines.append(f"| {node_type} | {count} |")

    lines.extend(
        [
            "",
            f"Total edges tracked: **{len(edges)}**",
            "",
            "## Top Workspace Package Dependencies",
            "",
            format_table(top_dependencies),
            "",
            "## Top Python Package Imports",
            "",
            format_table(top_imports),
            "",
            "## Workspace Members",
            "",
        ]
    )

    workspace_members = graph.get("workspaceMembers", [])
    if workspace_members:
        lines.append("| Key | Path |")
        lines.append("| --- | --- |")
        for key, path in workspace_members:
            lines.append(f"| `{key}` | `{path}` |")
    else:
        lines.append("_No pnpm workspace members detected._")

    python_packages = graph.get("pythonPackages", [])
    lines.extend(
        [
            "",
            "## Python Packages",
            "",
        ]
    )
    if python_packages:
        lines.append("| Package | Path |")
        lines.append("| --- | --- |")
        for package, path in python_packages:
            lines.append(f"| `{package}` | `{path}` |")
    else:
        lines.append("_No Python packages detected._")

    governance_artifacts = graph.get("governanceArtifacts", [])
    lines.extend(
        [
            "",
            "## Governance Artifacts",
            "",
        ]
    )
    if governance_artifacts:
        lines.append("| Kind | Scope | Path |")
        lines.append("| --- | --- | --- |")
        for artifact in governance_artifacts:
            kind = artifact.get("kind", "unknown")
            scope = artifact.get("scope", ".")
            path = artifact.get("path", "")
            lines.append(f"| {kind} | `{scope}` | `{path}` |")
    else:
        lines.append("_No governance artifacts detected._")

    quality_configs = graph.get("qualityConfigs", [])
    lines.extend(
        [
            "",
            "## Quality Configuration Files",
            "",
        ]
    )
    if quality_configs:
        lines.append("| Type | Path |")
        lines.append("| --- | --- |")
        for config in quality_configs:
            lines.append(f"| {config.get('type', 'unknown')} | `{config.get('path', '')}` |")
    else:
        lines.append("_No quality configuration files detected._")

    lines.append("")

    return "\n".join(lines)


def write_outputs(graph: dict, graph_path: Path, mermaid_path: Path, summary_path: Path) -> None:
    graph_path.parent.mkdir(parents=True, exist_ok=True)
    with graph_path.open("w", encoding="utf-8") as handle:
        json.dump(graph, handle, indent=2)
    mermaid_path.parent.mkdir(parents=True, exist_ok=True)
    mermaid_path.write_text(graph["mermaid"] + "\n", encoding="utf-8")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(summarise_graph(graph), encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--graph-path", type=Path, default=DEFAULT_GRAPH_PATH)
    parser.add_argument("--mermaid-path", type=Path, default=DEFAULT_MERMAID_PATH)
    parser.add_argument("--summary-path", type=Path, default=DEFAULT_SUMMARY_PATH)
    args = parser.parse_args(argv)

    graph = build_graph()
    write_outputs(graph, args.graph_path, args.mermaid_path, args.summary_path)
    print(f"Graph written to {args.graph_path}")
    print(f"Mermaid snapshot written to {args.mermaid_path}")
    print(f"Summary written to {args.summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
