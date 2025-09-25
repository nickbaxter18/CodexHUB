# CodexHUB Agent Architecture Overview

The CodexHUB workspace hosts several autonomous and semi-autonomous agent systems. This document centralises the high-level
orientation material for every agent-facing capability so that contributors can locate the authoritative specifications without
hunting through individual subprojects.

## Project Map

| Project                   | Purpose                                                                             | Detailed Specification                                               |
| ------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `codex-meta-intelligence` | Multi-agent operating system that implements the Codex Meta-Intelligence blueprint. | [codex-meta-intelligence/agent.md](codex-meta-intelligence/agent.md) |
| `agents/`                 | Legacy Python agents that power notebook-based experiments.                         | [agents/README.md](agents/README.md)                                 |
| `macro_system/`           | Macro orchestration prototypes that predate the Meta-Intelligence stack.            | [macro_system/README.md](macro_system/README.md)                     |
| `cursor/`                 | Cursor IDE integration utilities and launch scripts.                                | [cursor/README.md](cursor/README.md)                                 |

The Codex Meta-Intelligence project is the canonical implementation moving forward. All new agent work should be developed
there unless an explicit exception is recorded in `ROADMAP.md`.

## Governance Principles

1. **Single Source of Truth** – Each project maintains its own `agent.md`/`AGENTS.md` pair. This root document simply points to
   them and records the ownership model.
2. **Context Engineering Compliance** – Before an agent runs, it must merge AGENT/AGENTS guidance from the repository root, the
   project root and the target directory. The TypeScript implementation lives in `codex-meta-intelligence/src/agent/reader.ts`.
3. **Cursor Enforcement** – Cursor integration scripts under `scripts/` must be invoked before automated coding tasks. Refer to
   `scripts/auto_setup_cursor.py` for the end-to-end bootstrap pipeline.
4. **Testing & Quality Gates** – Every agent workflow must execute the commands declared in the applicable `AGENTS.md` file.
   For the Meta-Intelligence stack this includes `pnpm lint`, `pnpm test`, `pnpm typecheck` and `pnpm build` as part of Stage 1.
5. **Telemetry** – Agents publish execution traces through `codex-meta-intelligence/src/analytics/{metrics,tracing}.ts` so that
   operator dashboards and automated monitors receive consistent signals.

## When to Update This File

Update this document whenever a new agent-focused project is added to the repository, when a project is deprecated, or when
ownership changes. Include cross-references to the authoritative specs so that downstream agents (and human operators) can
locate rule changes quickly.
