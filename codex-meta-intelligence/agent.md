# Agent Specifications

## Overview

The agent subsystem provides specialised autonomous workers that execute domain-specific tasks inside the Codex Meta-Intelligence platform. All agents inherit from a shared base class defined in `src/agent/index.ts`. Agents operate on top of the Execution Pipeline and respect the Harmony Protocol for conflict resolution.

## Roles

- **FrontendAgent** – Crafts user interfaces and design artefacts. Consumes UI-related tasks and validates styling via the styling cognition utilities.
- **BackendAgent** – Implements APIs, services and infrastructure automation. Enforces security and dependency hygiene policies.
- **KnowledgeAgent** – Manages ingestion and retrieval of knowledge blocks. Synchronises the knowledge store with context fabric components.
- **QAAAgent** – Executes aesthetic, technical and narrative quality checks before deliverables progress to operators.
- **RefinementAgent** – Applies iterative improvements to outputs. Integrates with styling cognition rules and QA feedback.

## Contracts

- **AgentConfig**: Unique identifier, role, concurrency limits, default timeout and accessible tool identifiers.
- **AgentMessage**: Task envelope containing `taskId`, `macroId`, `payload`, `context`, merged `guidelines`, and metadata (timestamps, priority, origin).
- **AgentResult**: Execution response containing status, optional error, produced artefacts, context updates, QA findings and metrics.

Schemas for the contracts are exported from `src/agent/types.ts` and validated using Ajv. All interactions rely on JSON serialisable structures and explicit version fields to remain forward compatible.

## Lifecycle

1. The meta-agent schedules a task and posts an `AgentMessage` to the message bus.
2. The receiving agent merges AGENTS.md guidance via `AgentGuidelineReader` and configures its runtime environment.
3. The agent resolves context from the Context Fabric, executes domain logic and records telemetry.
4. Results are emitted as `AgentResult` objects. Failures trigger retries or operator escalation according to protocol rules.

## Error Handling & Resilience

- Agents use typed error classes defined in `src/shared/types.ts`.
- Timeouts, invalid payloads and context fetch errors are reported with actionable diagnostics.
- Each agent exposes a heartbeat to the monitoring subsystem to enable liveness tracking.

## Performance Considerations

- Concurrency is constrained via semaphores to prevent resource exhaustion.
- Long-running tasks periodically emit progress updates so the meta-agent can make pre-emptive scheduling decisions.
- Outputs are streamed via async generators when large artefacts must be returned.

## Public API

Agents expose a `handleMessage` method that validates messages, invokes `execute`, and returns structured results. Utility methods support dry-run execution, environment bootstrapping and compliance verification with AGENTS.md and Cursor rules.
