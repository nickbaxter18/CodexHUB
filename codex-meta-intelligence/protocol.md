# Protocol Specification

## Harmony Protocol

The Harmony Protocol mediates conflicting proposals from agents. Proposals include change descriptions, priority, confidence score and citations. `resolveConflict` evaluates proposals using deterministic tiebreakers (priority, confidence, recency) and merges non-conflicting segments. When no safe resolution exists, it escalates to operators.

## Execution Pipeline

The pipeline enforces the Draft → Audit → Refinement → Elevation → Delivery → Deploy sequence. Each stage declares entry conditions, exit checks and rollback behaviour. Pipeline orchestration resides in `src/protocol/execution.ts`.

## Styling Cognition

Styling checks ensure outputs comply with U-DIG IT design laws: contrast, typography hierarchy, motion grammar, fairness and emotional resonance. The Stage 1 implementation evaluates basic numeric rules and produces warnings for violations.

## Open Protocol Bridges

- **MCP (Model Context Protocol)** – Tool registry describing callable functions and JSON schemas.
- **ACP (Agent Communication Protocol)** – Structured envelopes with signature verification and version negotiation.
- **A2A (Agent-to-Agent Discovery)** – Registry for capability advertisement and health status.
- **ANP (Agent Network Protocol)** – Identity, authentication and authorisation for cross-organisation interaction.
- **AG-UI** – API surface for UI integrations including dashboards and operator consoles.

Stage 1 provides type definitions and validation utilities. Implementations evolve in later stages but remain spec-compliant from inception.
