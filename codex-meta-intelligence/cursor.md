# Cursor Integration Blueprint

## Objectives

- Synchronise Cursor IDE configuration with Codex Meta-Intelligence agent workflows.
- Enforce consistent rule merging between `.cursorrules` and AGENTS.md files.
- Provide API bridges for file indexing, context sharing and compliance enforcement.

## Integration Points

- `src/cursor/adaptor.ts` communicates with Cursor APIs, harmonising rules and delivering context packets.
- `src/cursor/sync.ts` manages bidirectional sync between local changes and cloud state, handling merge conflicts via the Harmony Protocol.

## Operational Modes

- **Agent Mode** – Executes macros and QA flows triggered from Cursor.
- **Ask Mode** – Delegates to knowledge retrieval and summarisation pathways.
- **Manual Mode** – Supports targeted file edits with guardrails and compliance checks.

## Security & Privacy

All outbound data is scrubbed using governance policies. Sensitive files may be redacted or replaced with summaries before leaving the execution environment. API credentials are loaded via environment variables and validated through enforcement utilities.

## Roadmap

Stage 2 adds full API support and cursor automation, while Stage 3 integrates UI feedback loops and plugin synchronisation.

## Runtime Integration Utilities

Stage 1 now includes a Cursor integration runtime (`src/cursor/index.ts`) that satisfies the enforcement workflow described in the blueprint:

- `startCursorAutoInvocation(paths)` wires file watchers for every monitored workspace path using glob patterns from `CURSOR_FILE_PATTERNS`. Duplicate events are throttled using the monitor interval to keep downstream cost predictable.
- `requireCursorAgent(agentType)` returns a higher-order wrapper that asserts Cursor auto-invocation is active before allowing domain handlers to run, ensuring every code path is executed with an explicit agent role.
- `validateCursorCompliance()` and `enforceCursorIntegration()` orchestrate environment validation. They verify API credentials, knowledge ingestion, brain blocks activation, mobile goal management and agent selection before returning a compliance score.

Supporting modules located under `src/knowledge` and `src/mobile` provide the contextual data required by Cursor:

- `auto-loader.ts` ingests NDJSON files listed in `KNOWLEDGE_NDJSON_PATHS`, normalises metadata and refreshes entries on a configurable interval.
- `brain-blocks-integration.ts` exposes semantic queries, derived sections and tag taxonomies for the loaded knowledge blocks.
- `mobile-app.ts` offers an in-memory goal manager so operators can create, approve and complete tasks from mobile channels.

These utilities are idempotent, safe to start multiple times and automatically awaken dormant subsystems when compliance checks demand them. Agents can therefore execute Cursor-enforced workflows without bespoke bootstrapping scripts.
