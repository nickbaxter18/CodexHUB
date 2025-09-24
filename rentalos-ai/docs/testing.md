# Testing Strategy

Testing spans deterministic unit validation, integration workflows, fairness/ESG audits,
resilience drills, and frontend experience coverage. Every stage contributed executable
suites; Stage 3 now orchestrates them through `scripts/run_tests.sh`.

## Backend Testing

- **Unit Tests:** Located in `src/backend/tests/unit`. Cover pricing, maintenance, lease,
  screening, payments, ESG, community, scheduling, alerts, tokenization, and energy
  services. Assertions validate both nominal paths and edge cases such as missing data,
  adversarial inputs, and fairness violations.
- **Integration Tests:** `src/backend/tests/integration` simulates end-to-end flows:
  onboarding → screening → lease abstraction → pricing → payment → community engagement
  → energy trading. Tests validate API schemas, plugin registry interactions, and audit
  logging.
- **Performance Smoke Tests:** Lightweight stress harness validates pricing and
  maintenance endpoints under burst traffic to ensure p95 < 500 ms with caching enabled.
- **Security Tests:** Static analysis (`bandit`), dependency checks (`pip-audit`), and JWT
  tampering simulations confirm middleware enforcement, rate limiting, and replay
  protection.

## Frontend Testing

- **Unit Tests:** `src/frontend/tests/unit` exercises components (NavBar, Sidebar, Card,
  Modal, ChartWrapper, NotificationBell) and pages (Dashboard, Assets, Pricing,
  Maintenance, Lease, Screening, Payments, ESG, Community, Scheduling, Alerts, Energy,
  Plugins, Fairness) for rendering, state transitions, accessibility roles, and
  localization.
- **Integration / E2E:** Playwright scripts in `src/frontend/tests/integration` emulate key
  personas completing flows on desktop and mobile viewports, including offline caching and
  AR/VR interactions.
- **Visual Regression:** Percy or Chromatic snapshots guard against UI regressions in the
  dashboards and plugin marketplace.

## Fairness, ESG & Compliance Testing

- **Fairness Suites:** Synthetic demographic datasets exercise pricing and screening
  models to verify demographic parity, equal opportunity, and calibration metrics.
- **ESG Accuracy:** Tests feed energy/water/waste sensor scenarios to confirm carbon
  budgets, offsets, and sustainability recommendations align with benchmarks.
- **Privacy & Consent:** Automated flows test GDPR/CCPA requests (export, delete,
  restrict), verifying audit trail immutability and notification hooks.

## Resilience & Observability Testing

- **Chaos Experiments:** Controlled fault injection simulates database downtime, Redis
  saturation, Kafka lag, plugin exceptions, and degraded blockchain nodes to verify
  auto-recovery and alert propagation.
- **Health/Readiness Validation:** Tests verify `/health` and `/ready` reflect dependency
  state, plugin integrity, and model availability, feeding CI gating.
- **Logging & Metrics:** Assertions confirm correlation IDs flow through logs and that
  metrics endpoints expose expected gauges, counters, and histograms.

## Automation & Tooling

Run the consolidated suite with:

```bash
scripts/run_tests.sh
```

This script executes `pytest -q`, `mypy`, `flake8`, frontend `pnpm test`, ESLint, Prettier,
Playwright smoke tests, fairness/ESG suites, and Cursor compliance checks. CI pipelines
invoke the same command to guarantee parity between local and automated runs.

## Coverage & Quality Gates

- **Coverage Targets:** Backend ≥ 90% statement coverage, frontend ≥ 85%, fairness/ESG
  scenarios 100% of documented edge cases. Coverage deltas are tracked per module to
  highlight regressions.
- **Static Analysis Budgets:** `mypy` and `flake8` warnings fail the build. ESLint is
  configured with strict accessibility, security, and React hooks rules. `cspell` protects
  product terminology.
- **Performance Budgets:** Automated checks validate that key workflows (pricing,
  maintenance scheduling, payment collection) meet p95 < 500 ms on reference hardware.
  Regressions open GitHub issues automatically via CI webhooks.
- **Artifact Retention:** Test artefacts (coverage reports, screenshots, fairness charts)
  are archived for 30 days and linked from `deploy_logs/changelog.md` so audits can replay
  evidence.
