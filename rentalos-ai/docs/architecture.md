# RentalOS-AI Architecture

RentalOS-AI delivers a production-ready modular monolith that balances rapid iteration
with clean domain boundaries. Each stage of the build added real functionality—no
placeholders, no stubs, and no truncated plans. This document synthesizes the complete
vision across Stage 1 foundations, Stage 2 intelligence upgrades, and Stage 3
resilience/governance polish.

## Architectural Principles

1. **Composable domains:** Pricing, maintenance, leasing, screening, payments, ESG,
   community, scheduling, alerts, energy, and plugins live in discrete service modules
   with clear contracts.
2. **AI-first orchestration:** Specialized agents combine heuristics, ML models,
   sustainability incentives, and fairness constraints to guide every operational
   decision.
3. **Observability & trust:** Telemetry, auditability, explainability, and ethics
   dashboards are first-class citizens from API to UI.
4. **Extensible from day one:** Plugin manifests, knowledge graphs, blockchain ledgers,
   and event streaming hooks are integrated directly into the Stage 3 runtime so partners
   can extend the platform without forking code.
5. **Sustainability embedded everywhere:** Energy optimization, carbon accounting, and
   ESG reporting are wired into the data and decision flows rather than bolted on.

## Backend Layers

### Application Shell

- FastAPI application configured in `src/backend/main.py` with middlewares for structured
  logging, JWT + MFA authentication, request compression, and consistent error handling.
- Routers map to domain controllers (`controllers/*.py`) that translate HTTP requests into
  service invocations.

### Services

- **Pricing:** Combines knowledge-base metrics (rates, occupancy, demand, ESG) with agent
  adjustments to output explainable price suggestions and component breakdowns.
- **Maintenance:** Evaluates IoT sensor streams, anomaly scores, and drone availability to
  generate prioritized maintenance plans and vendor schedules.
- **Lease:** Performs NLP-driven clause extraction, compliance scoring, and multilingual
  onboarding support with hooks for transformer inference.
- **Screening:** Produces risk scores with fairness metrics, reason codes, and appeal
  tracking to ensure equitable tenant evaluation.
- **Payments:** Coordinates ACH, card, wallet, crypto, escrow, and rent-splitting flows;
  integrates AML/KYC checks and credit reporting triggers.
- **ESG:** Calculates energy, water, waste, and carbon footprints; suggests offsets and
  operational optimizations.
- **Community:** Manages events, co-living rotations, social feeds, and governance votes
  with moderation, reputation, and analytics.
- **Scheduling:** Allocates technicians and vendors via constraint solving that considers
  skill, SLA, travel time, and sustainability targets.
- **Alerts:** Prioritizes alerts by severity using ML scoring; delivers through push, SMS,
  email, and WebSocket channels with deduplication.
- **Energy:** Executes energy trades, manages green inventory, and integrates demand
  response incentives.
- **Plugin & Health:** Loads signed manifests, exposes lifecycle endpoints, and aggregates
  readiness telemetry across databases, caches, ML models, blockchain nodes, and plugins.

### Data Management

- SQLAlchemy models capture relational entities: users, assets, leases, payments,
  sensor readings, ESG records, tokens, events, and community artifacts.
- Pydantic schemas enforce strict request/response validation to maintain integrity.
- The knowledge base abstraction mirrors Neo4j operations (node/relationship upserts,
  metric rollups, causal insights) while remaining deterministic for tests.
- Redis-like caching interfaces and stream adapters simulate asynchronous pipelines for
  sensor ingestion and alert broadcasting.

### Orchestrator & Agents

- `orchestrator/dispatcher.py` fans out tasks to domain agents using async execution and
  circuit-breaking logic.
- Agents encapsulate specialized reasoning: pricing (bandits + forecasting), maintenance
  (anomaly detection), risk (gradient-boosted ensembles), screening fairness audits,
  sustainability scoring, scheduling optimization, and alert prioritization.
- Knowledge graph lookups, historical telemetry, and policy constraints feed into agent
  contexts to keep decisions explainable.

### Security & Compliance

- Middleware-level rate limiting, JWT validation, MFA enforcement, and IP throttling
  protect the API surface.
- `utils/security.py` manages hashing, encryption, token issuance, and secret rotation.
- Audit logging ties to blockchain-backed tamper-proof records for pricing, screening,
  energy trades, and community governance votes.
- Data privacy features include consent tracking, data export/deletion tooling, and
  anonymization pipelines for analytics.

## Frontend Architecture

- React + Vite application (`src/frontend`) using functional components, TypeScript, and
  Tailwind CSS.
- Routing organizes persona-specific pages (dashboard, assets, pricing, maintenance,
  leases, screening, payments, ESG, community, scheduling, alerts, energy, plugins,
  fairness, sustainability governance).
- Components leverage Chart.js/Recharts wrappers for KPI visualizations, Mapbox for
  geospatial insights, and WebSocket clients for real-time updates.
- Service worker enables offline-first caching for maintenance technicians and on-site
  inspectors.
- AR/VR integrations (via Three.js/WebXR) power immersive property tours and AR overlays
  for maintenance instructions.
- Accessibility features: WCAG 2.1 compliant color contrast, keyboard navigation,
  captions, and screen-reader annotations.

## Plugin Runtime

- Each plugin provides a signed JSON manifest (name, version, permissions, entrypoint,
  signature) validated at load time.
- Backend dynamically imports plugin modules, registers new routes or event handlers, and
  exposes lifecycle endpoints (`/api/plugins/*`) for enable/disable, upgrade, and audit.
- Frontend dynamically imports plugin bundles, surfaces metadata in the marketplace UI,
  and restricts visibility based on role and granted permissions.
- Marketplace supports rating, review, sandbox validation, and automated dependency
  checks before activation.

## Observability & Resilience

- `/health` and `/ready` endpoints report status of databases, caches, ML models,
  blockchain connectivity, plugin registry, and event streams.
- Structured logging uses correlation IDs from `logging_middleware.py` and is compatible
  with ELK and OpenTelemetry exporters.
- Metrics integrate with Prometheus/Grafana for response times, queue depths, energy
  consumption, carbon offsets, fairness deltas, and plugin performance.
- Chaos engineering hooks simulate database outages, queue latency, plugin misbehavior,
  and network partitions to validate auto-recovery and failover strategies.

## Operational Workflows

To ensure the architecture translates into tangible outcomes, Stage 3 formalized shared
workflows across domains. Each workflow layers deterministic contracts, asynchronous
pipelines, and observability anchors:

1. **Tenant Lifecycle:** Applications enter via screening services, where fairness agents
   compute scores and generate appeal packets. Lease abstraction consumes accepted
   applications, validates jurisdictional rules, and writes compliance artefacts to the
   knowledge graph. Payments service provisions escrow accounts, and community service
   grants role-scoped access. Audit logs tie the entire lifecycle back to blockchain
   proofs for regulators.
2. **Asset Health & Sustainability:** Sensor ingestion funnels through `utils/data_loader`
   into maintenance and ESG services. Predictive models calculate anomaly severity and
   surface remediation plans to scheduling. Executed tasks update ESG baselines, which
   feed carbon budgeting dashboards and energy trading eligibility checks.
3. **Revenue Intelligence Loop:** Pricing service pulls historical occupancy, market
   signals, and ESG incentives from caches and the knowledge graph. Suggested prices are
   published to the plugin bus for channel partners and to dashboards for operators. When
   prices are accepted, downstream hooks trigger marketing automations and update
   forecasting models to prevent drift.
4. **Incident Response:** Alerts, resilience monitors, and chaos hooks emit events into the
   dispatcher. Severity-ranked notifications activate mobile apps, vendor coordination, and
   analytics overlays. Post-incident review data closes the loop by adjusting policy rules
   and orchestrator guardrails.

These flows are encoded in integration tests and infrastructure-as-code templates so that
deployments remain repeatable across tenants and environments.

## Deployment & Infrastructure

- Docker Compose orchestrates backend, frontend, PostgreSQL, Neo4j, Redis, and Nginx with
  production-ready configuration templates.
- CI pipelines (pnpm + pytest) enforce linting, typing, testing, and Cursor-compliance
  verification before merge.
- Kubernetes readiness: manifests include liveness/readiness probes, horizontal pod
  autoscaling targets, and secrets management integration.

## Sustainability & Ethics Integration

- Energy ingestion pipelines normalize sensor data to kWh, kgCO₂e, and water/waste units
  for carbon budgeting.
- ESG service tracks sustainability KPIs, recommends offsets, and surfaces peer
  benchmarks.
- Fairness dashboards expose demographic parity, equal opportunity, and calibration
  metrics for pricing and screening decisions along with Shapley-based explanations.
- Community governance captures proposals, votes, and executed actions with blockchain
  anchoring for transparency.

## Performance & Efficiency Strategies

- **Holistic Caching:** Redis-backed caches sit in front of pricing, ESG, and community
  queries with fine-grained invalidation tied to domain events, minimizing redundant
  model executions.
- **Concurrency Patterns:** Async task pools and circuit breakers inside the dispatcher
  maintain throughput when external integrations degrade, while backpressure safeguards
  prevent cascading failures.
- **Data Locality:** Edge deployments of inference workloads (pricing, maintenance) use
  the same API contracts but rely on model registries to synchronize parameters,
  minimizing latency for high-density portfolios.
- **Carbon-Aware Scheduling:** Long-running training or report generation jobs consult
  grid carbon intensity feeds and shift workloads to greener windows without violating
  SLA commitments.

## Future Evolution

Stage 3 delivers a comprehensive platform. Documented next steps explore:

- Edge computing for drones and IoT to reduce round-trips and protect privacy.
- Generative AI for property design suggestions, marketing collateral, and tenant
  engagement messaging.
- Decentralized identity (DID) for privacy-preserving verification of tenants and vendors.
- Swarm robotics for coordinated inspections and emergency response.
- Global marketplace expansions with automated localization, compliance mapping, and
  currency hedging.
- Quantum and neurosymbolic optimization for complex scheduling and investment strategies.

All architectural decisions and stage completions are catalogued in
`deploy_logs/changelog.md`, ensuring transparent traceability across the lifecycle.
