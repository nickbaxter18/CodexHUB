# Operator Interface Specification

## Objective

Provide transparent and controllable interactions for human operators to supervise agent workflows, approve deliverables and intervene when necessary.

## Components

- **OperatorInterface (`src/operator/interface.ts`)** – CLI/automation entry point for commands and notifications.
- **OperatorHooks (`src/operator/hooks.ts`)** – Binds operator actions to meta-agent decisions.
- **OperatorUI (`src/operator/ui.ts`)** – Placeholder for future UI integration; Stage 1 defines interfaces and state contracts.

## Capabilities

- Enqueue new macro tasks with priority and policy overrides.
- Approve, refine, expand or rollback deliverables.
- Adjust fairness weights, risk tolerances and concurrency limits.
- Receive notifications from integrations (Slack, email) and respond interactively.

## Safety Mechanisms

- Role-based access control ensures only authorised users may issue destructive commands.
- Command validation prevents injection or malformed instructions.
- All interactions are recorded in the memory log for auditing and compliance.
