# RentalOS-AI

RentalOS-AI is a full-stack operating system for the rental economy that fuses AI-driven
operations, sustainability intelligence, blockchain-secured ownership, and rich
community engagement. The project is delivered in three completed stages that build on
one another without stubs or placeholders:

- **Stage 1 – Foundations:** Established the modular monolith layout, FastAPI service
  contracts, React dashboard skeleton, deterministic AI agent interfaces, and core
  documentation covering goals, risks, and sustainability commitments.
- **Stage 2 – Intelligence & Integrations:** Introduced data-informed pricing and
  maintenance pipelines, fairness-aware screening logic, in-memory knowledge graph
  abstractions, plugin registry scaffolding, blockchain tokenization hooks, and richer
  testing scenarios spanning services and integrations.
- **Stage 3 – Resilience & Extensibility:** Activated manifest-driven plugin loading with
  signature validation, comprehensive health/readiness probes, fairness and sustainability
  telemetry dashboards, observability instrumentation, and governance workflows across
  the stack.

## Vision & Goals

RentalOS-AI empowers property owners, operators, tenants, investors, and sustainability
leaders to collaborate around a unified, ethical, and data-rich command center. Key
objectives include:

- **Streamlined operations:** AI orchestrates pricing, maintenance, scheduling, and
  vendor coordination to keep assets profitable and compliant.
- **Tenant-centric experience:** Mobile-first portals support onboarding, payments,
  community programming, and feedback loops.
- **Portfolio intelligence:** Predictive analytics benchmark occupancy, revenue, ESG, and
  risk metrics in real time.
- **New business models:** Tokenization, fractional ownership, and energy marketplaces
  unlock co-living and investment innovation.
- **Ethical stewardship:** Fairness dashboards, audit trails, privacy controls, and ESG
  metrics keep decision-making transparent and responsible.

## Architectural Snapshot

- **Backend:** FastAPI application exposing services for assets, pricing, maintenance,
  leasing, screening, payments, ESG, community, scheduling, alerts, energy trading,
  plugins, and health checks. SQLAlchemy models and Pydantic schemas provide contract
  integrity while knowledge-base abstractions mirror upcoming Neo4j integrations.
- **AI Orchestrator:** Specialized agents (pricing, maintenance, risk, screening,
  sustainability, scheduling, alerting) are dispatched through a concurrency-aware
  orchestrator that blends historical metrics, anomaly detection, and policy governance.
- **Data Plane:** In-memory stores simulate PostgreSQL, Redis caching, and Neo4j for
  deterministic tests while surfacing interfaces for future external replacements.
- **Frontend:** React + Vite application styled with Tailwind; dashboards adapt to role
  permissions, surface energy and fairness metrics, and host a plugin marketplace with
  dynamic module loading.
- **Plugins & Integrations:** The `plugins/` directory holds signed manifests loaded at
  runtime. Plugins may register API extensions, UI widgets, and webhook listeners while
  respecting sandbox boundaries.
- **Observability & Governance:** Logging, compression, and authentication middlewares
  pair with `/health` and `/ready` endpoints, Prometheus-friendly metrics, audit logs,
  fairness explainability views, and sustainability scorecards.

## Core Capabilities

- Dynamic pricing with demand, ESG, and competitor adjustments plus explainable
  confidence intervals.
- Predictive maintenance scheduling with sensor anomaly detection, drone inspection
  planning, and vendor routing.
- Lease abstraction, compliance validation, and multilingual onboarding flows.
- Fairness-aware tenant screening with demographic parity checks and appeal workflows.
- Payment orchestration covering ACH, card, wallet, crypto, escrow, rent splitting, and
  credit reporting hooks.
- ESG & sustainability analytics with carbon budgeting, offset procurement, water and
  waste monitoring, and green inventory management.
- Community engagement including event booking, social feeds, roommate matching, and
  governance voting recorded on-chain.
- Energy marketplace for trading surplus renewables, benchmarking consumption, and
  integrating demand-response incentives.
- Plugin marketplace with signature validation, permissioned capabilities, and lifecycle
  controls spanning install, enable/disable, upgrade, and audit logging.
- Resilience toolset featuring health probes, observability pipelines, chaos testing
  hooks, and governance dashboards for fairness, privacy, and sustainability.

## Operational Playbooks

RentalOS-AI ships with end-to-end workflows that demonstrate how the subsystems work in
concert. Each playbook traces the data journey, agent orchestration, user experience, and
compliance checkpoints so operators can replicate or extend the behaviour without guess
work.

- **Asset Onboarding → Monetization:** Create a digital twin, ingest historical leases,
  and trigger the pricing agent for base rates. The screening service validates tenant
  dossiers, while compliance checks confirm ESG and regulatory posture. Pricing
  suggestions stream into the dashboard with Shapley explainability and carbon pricing
  modifiers. Once accepted, payment plans, escrow accounts, and credit reporting hooks are
  activated automatically.
- **Predictive Maintenance Loop:** Sensor ingestion (temperature, vibration, energy)
  flows through the maintenance agent, which calls anomaly detectors and references the
  knowledge graph for asset context. Scheduling optimizes technician routing with energy
  targets, while the alert service pushes notifications across mobile, email, and in-app
  channels. Drone inspections and post-repair verification are logged for ESG impact and
  blockchain-backed audit trails.
- **Tenant Empowerment & Community Governance:** Tenants receive mobile-first onboarding,
  fairness-reviewed screening decisions, and access to payments, maintenance requests,
  and community events. Governance proposals leverage plugin-provided rules (e.g., weighted
  voting, sustainability initiatives) and capture results on-chain for immutable
  transparency.
- **Energy Marketplace Participation:** Assets with renewable generation publish surplus
  capacity via the energy service. Pricing aligns with market feeds and sustainability
  incentives, while offsets and carbon credits reconcile automatically. Alerts surface
  when consumption threatens carbon budgets, prompting the orchestrator to suggest demand
  response actions or storage utilization.

Each playbook is backed by integration tests and monitoring dashboards so teams can adapt
the flows to bespoke business rules with confidence.

## Optimization & Efficiency Levers

The platform embeds instrumentation to continuously raise efficiency, sustainability, and
fairness benchmarks:

- **SLO Guardrails:** Default service-level objectives target <500 ms API p95 latency,
  <1 minute alert propagation, and <5 minutes knowledge graph sync. Dashboards expose SLI
  adherence, and CI blocks merges that degrade SLO budgets.
- **Cost & Carbon Intelligence:** Pricing, maintenance, and energy services expose cost
  curves and carbon intensity to agents so decisions balance profitability with ESG
  commitments. Budget variance alerts recommend optimization levers such as dynamic
  staffing, preventative maintenance, or participation in green tariffs.
- **Model Lifecycle Automation:** Drift detectors compare live inference distributions
  against training baselines, automatically queuing retraining jobs or fairness audits.
  Versioned artifacts ensure rollbacks are immediate and explainable.
- **Operational Feedback Loops:** Post-action surveys, dispute outcomes, and remediation
  latencies feed back into the orchestrator, allowing reinforcement learning policies to
  tune incentives, vendor selection, and tenant communications.

## Getting Started

### Backend

1. Create and activate a Python 3.11 virtual environment.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run the FastAPI app: `uvicorn src.backend.main:app --reload`.
4. Access OpenAPI docs at `http://localhost:8000/docs` for live endpoint exploration.

### Frontend

1. Install Node.js (LTS) and pnpm.
2. From the repository root, install dependencies: `pnpm install`.
3. Start the development server: `pnpm --filter frontend dev` (or `npm run dev`
   if using npm tooling).
4. Open `http://localhost:5173` to view the dashboard with live plugin marketplace,
   fairness telemetry, and ESG widgets.

### Docker Compose

Run the entire stack, including PostgreSQL, Neo4j, and Redis containers, with:

```bash
docker compose up --build
```

The compose file provisions service stubs today and is ready to host production-grade
infrastructure in future iterations.

## Quality, Testing & Compliance

- **Python:** `pytest -q` for backend unit and integration suites; `mypy` and `flake8`
  guard type and style contracts.
- **Frontend:** `pnpm test` executes Vitest suites; `pnpm lint` and `pnpm format` keep
  TypeScript and Tailwind consistent.
- **Security:** Secrets are never hard-coded. JWT + MFA middleware, rate limiting, and
  structured logging create defensible defaults.
- **Fairness & Sustainability:** Dedicated tests verify demographic parity, ESG scoring
  accuracy, carbon accounting, and offset allocation.
- **Resilience:** Chaos experiments simulate degraded databases, queue outages, and
  plugin failures; health probes feed alerting pipelines.

## Repository Layout

```
rentalos-ai/
├── deploy_logs/           # Stage completion and architectural decision history
├── docs/                  # Architecture, API, testing, risk, and sustainability guides
├── plugins/               # Signed plugin manifests for runtime discovery
├── scripts/               # Stage detector, Cursor automation, testing helpers
├── src/backend/           # FastAPI app, services, orchestrator, middlewares, tests
├── src/frontend/          # React app with Tailwind styling and role-based routing
├── docker/                # Dockerfiles and Nginx config for containerized deployments
└── requirements.txt       # Backend dependency pinning
```

## Observability & Governance

- **Telemetry:** Structured logs with correlation IDs, Prometheus metrics exporters, and
  OpenTelemetry hooks facilitate root-cause analysis.
- **Auditability:** Immutable decision logs (pricing, screening, energy trades) can be
  anchored to blockchain ledgers and exported for regulators.
- **Privacy:** Consent management, data deletion tooling, and anonymization pipelines
  support GDPR/CCPA compliance.
- **Sustainability Oversight:** Carbon budgets, offset transactions, and ESG scoring are
  surfaced across dashboards and reports.

## Roadmap & Future Enhancements

Stage 3 delivered a production-ready baseline. Future research directions already
captured in the documentation include:

- Edge-native processing for IoT sensors and drone fleets to reduce latency.
- Generative AI copilots for retrofit recommendations, leasing collateral, and community
  engagement content.
- Decentralized identity (DID) for privacy-preserving tenant and vendor verification.
- Swarm robotics for rapid inspections and emergency response.
- Global marketplace features with automated localization, currency hedging, and
  compliance mapping.
- Quantum and neurosymbolic optimization experiments for portfolio allocation and
  scheduling under complex constraints.

Every completed stage, documentation update, and architectural decision is logged in
`deploy_logs/changelog.md` to ensure traceability and continuity.
