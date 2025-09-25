# Macro Orchestration Blueprint

## Purpose

Macros coordinate multiple agents to satisfy complex objectives. They decompose prompts into sequenced or parallel agent invocations, enforce the Execution Pipeline and apply Harmony Protocol decisions when outputs conflict.

## Definitions

- **MacroDefinition** – Declares name, description, ordered stages, fallback macro, quality gates and telemetry labels.
- **MacroContext** – Aggregates operator intent, AGENTS.md guidance, selected knowledge packets and run metadata.
- **MacroResult** – Aggregated collection of agent results, execution timeline, QA summary and derived artefacts.

TypeScript types and runtime schemas are located in `src/macro/types.ts`. Macros are authored declaratively in `src/macro/scripts.ts` with composable helper functions such as `sequence`, `parallel`, and `retryableStage`.

## Execution Model

1. The meta-agent invokes `runMacro` with a macro name and context.
2. `MacroOrchestrator` loads the macro definition, validates it against schema contracts and resolves required agents.
3. Each stage is executed via the Execution Pipeline. Draft outputs cascade into QA, Refinement, Elevation, Delivery and Deploy phases.
4. Failures trigger fallback macros or retries with exponential backoff, as defined by macro metadata.
5. Final results are persisted via the memory subsystem and forwarded to operators.

## Error Handling

- Invalid macros throw descriptive `MacroConfigurationError` exceptions.
- Stage timeouts produce partial results but keep telemetry consistent.
- Harmony Protocol decisions are logged to the memory subsystem for auditing.

## Performance Considerations

- Macros can spawn parallel branches when tasks are independent. Worker limits are derived from meta-agent scheduling policies.
- Macro execution is fully asynchronous and supports streaming updates via EventEmitter events.

## Extensibility

- Additional macros can be defined by appending to `src/macro/scripts.ts`.
- Custom pipeline stages may be implemented by extending `ExecutionStage` in `src/protocol/execution.ts`.
- Variant comparisons are stored in markdown footnotes for operator review.
