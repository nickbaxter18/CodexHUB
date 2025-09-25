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
