# Meta-Agent Specification

## Mission

The meta-agent serves as the executive control plane for Codex Meta-Intelligence. It schedules tasks, selects macros, enforces policies and orchestrates agent execution to maintain reliability, fairness and compliance.

## Core Components

- **Scheduler (`src/metaagent/scheduler.ts`)** – Implements priority queues, fairness constraints and time-slicing for concurrent tasks.
- **State Manager (`src/metaagent/state.ts`)** – Persists task metadata, agent registry information, telemetry snapshots and audit trails.
- **Monitor (`src/metaagent/monitor.ts`)** – Collects metrics, health status and anomaly signals for escalation to operators.
- **Orchestrator (`src/metaagent/index.ts`)** – Public entry point combining scheduler, macros and monitoring.

## Task Lifecycle

1. Operator or automation enqueues a `MetaTask` describing goals, requested macro and optional constraints.
2. Scheduler prioritises tasks using weighted fairness; risk and foresight data adjust ordering.
3. Macro orchestrator executes tasks; intermediate events are streamed to observers.
4. On completion, results are recorded, context updates are persisted, and operators receive notifications via integration connectors.

## Policy Enforcement

Meta-agent validates AGENTS.md rules, Cursor compliance, security policies and fairness constraints before dispatching work. Policy failures trigger operator alerts and mark tasks as blocked.

## Fault Tolerance

- Heartbeat monitoring restarts stalled tasks with exponential backoff.
- Dead-letter queues store failed macro runs for later inspection.
- Distributed locks prevent duplicate scheduling across cluster deployments.

## Extensibility

- Additional scheduling strategies can plug into `SchedulerStrategy` interface.
- Observers subscribe to `MetaAgentEvents` for real-time dashboards, Slack notifications or plugin actions.

## Public API

- `enqueueTask(metaTask: MetaTask): string` – adds a task and returns the generated identifier.
- `cancelTask(taskId: string): boolean` – cancels running or queued tasks when safe.
- `getState(): MetaStateSnapshot` – returns immutable view of scheduler queues, running tasks and metrics.
