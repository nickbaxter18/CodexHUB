# Codex Meta-Intelligence Platform

Codex Meta-Intelligence is a multi-agent operating system for software development. Stage 1 establishes the scaffolding for agents, macros, context fabric, knowledge management and compliance with OpenAI and Cursor integration guidelines.

## Features (Stage 1)

- Microservice-inspired architecture with dedicated directories for each subsystem.
- Build orchestrator that executes linting, tests and type checks based on `stage.json`.
- Agent framework with context-aware execution, AGENTS.md parsing and message bus hooks.
- Knowledge, memory, protocol and context services providing deterministic behaviour and documentation.
- QA, CI/CD, foresight, security, analytics and integration modules prepared for Stage 2 enhancements.

## Getting Started

```bash
cd codex-meta-intelligence
pnpm install --ignore-workspace-root-check
pnpm build
```

## Development Workflow

1. Modify or extend modules under `src/`.
2. Update relevant specification markdown files when behaviour changes.
3. Run quality gates:
   - `pnpm lint`
   - `pnpm test`
   - `pnpm typecheck`
4. Execute `./build.sh` to run stage tasks and optionally promote to the next stage.

## Testing

Jest tests reside in `tests/`. Stage 1 focuses on unit tests covering the agent framework, memory cache and pipeline orchestrator. Integration tests will be introduced in Stage 2.

## Contributing

Follow AGENTS.md guidelines for coding standards, logging conventions and pull request preparation. Document any new dependencies or configuration updates in this README.
