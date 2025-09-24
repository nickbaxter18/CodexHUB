# API Reference

All endpoints are prefixed with `/api` unless otherwise noted. Stage 3 completed the
full contract surface described below; every route returns structured JSON with
consistent metadata, correlation IDs, and error envelopes (HTTP 4xx/5xx include
`code`, `message`, and `context`).

## Assets

- `GET /api/assets` – List assets, IoT devices, occupancy, ESG scores, and current
  pricing recommendations.
- `POST /api/assets` – Create an asset with baseline ESG, compliance, and ownership data.
- `GET /api/assets/{asset_id}` – Retrieve full digital twin, including sensor snapshots,
  maintenance backlog, and risk posture.

## Pricing

- `POST /api/pricing/suggestions` – Request a pricing recommendation; payload includes
  `assetId`, `startDate`, and `duration`. Response returns `suggestedPrice`, `components`,
  and `confidence` values aligned with explainability dashboards.
- **Sample Request:**
  ```json
  {
    "assetId": 42,
    "startDate": "2024-07-01",
    "duration": 30,
    "channels": ["direct", "midterm"],
    "esgIncentives": true
  }
  ```
- **Sample Response:**
  ```json
  {
    "assetId": 42,
    "suggestedPrice": 189.5,
    "currency": "USD",
    "confidence": 0.92,
    "components": {
      "base": 165,
      "demandLift": 12,
      "esgCredit": -4.5,
      "eventImpact": 17
    },
    "explanations": [
      { "feature": "occupancy_trend", "weight": 0.37 },
      { "feature": "carbon_intensity", "weight": -0.09 }
    ]
  }
  ```
- `GET /api/pricing/history/{asset_id}` – Access four-week pricing history used in trend
  charts.
- `POST /api/pricing/rules` – Update revenue optimization rules with immediate feedback
  for marketplace integrations.

## Maintenance

- `POST /api/maintenance/schedule` – Generate or refresh maintenance plans. Payload
  accepts prioritized systems, anomaly overrides, and drone availability.
- **Sample Response Snippet:**
  ```json
  {
    "assetId": 42,
    "tasks": [
      {
        "id": "mnt-8841",
        "system": "HVAC",
        "recommendedDate": "2024-06-18",
        "severity": "high",
        "esgImpact": { "carbon": -18.4, "water": 0 },
        "requiresDrone": true,
        "linkedAlerts": ["alert-201"]
      }
    ]
  }
  ```
- `GET /api/maintenance/history/{asset_id}` – Summaries of completed and upcoming tasks
  plus estimated downtime avoided.
- `POST /api/maintenance/inspection` – Schedule drone inspections with geofencing and
  compliance metadata.

## Lease & Screening

- `POST /api/lease/abstract` – Upload and parse leases; returns extracted clauses,
  obligations, renewal notices, and compliance gaps.
- `POST /api/lease/validate` – Run legal checks based on jurisdiction, rent control, and
  ESG commitments.
- `POST /api/screening/evaluate` – Score tenant applications with fairness metrics,
  reason codes, and recommended actions.
- **Error Envelope Example (HTTP 422):**
  ```json
  {
    "code": "SCREENING_VALIDATION_ERROR",
    "message": "Income verification document missing",
    "context": { "required": ["incomeDocument"] }
  }
  ```
- `GET /api/screening/audit/{application_id}` – Retrieve audit trail, consent records, and
  fairness dashboards for a specific screening decision.

## Payments

- `POST /api/payments/plan` – Create payment plans with rent splits, due dates, and
  currency conversions.
- **Idempotency:** Include `Idempotency-Key` header to safely retry requests. Keys are
  stored for 48 hours.
- `POST /api/payments/collect` – Initiate a payment across supported rails; response
  includes escrow status, settlement ETA, and compliance checks.
- `GET /api/payments/history/{lease_id}` – Transaction ledger with anomaly and fraud
  indicators.

## ESG & Sustainability

- `POST /api/esg/report` – Submit sensor and operational metrics; response returns carbon,
  water, waste, and social impact KPIs with improvement suggestions.
- **Partial Response Example:**
  ```json
  {
    "assetId": 42,
    "period": "2024-Q2",
    "carbon": { "totalKg": 1280, "intensity": 9.4, "targetDelta": -1.2 },
    "water": { "totalLiters": 32000, "intensity": 0.8 },
    "waste": { "recycledKg": 140, "landfillKg": 60 },
    "recommendations": [
      "Shift HVAC runtime to off-peak hours",
      "Enroll in local solar community program"
    ]
  }
  ```
- `GET /api/esg/portfolio` – Aggregated ESG dashboard, carbon budgets, and offset status
  per asset and portfolio.
- `POST /api/esg/offsets` – Purchase or allocate offsets; response tracks registry IDs and
  retirement certificates.

## Community & Scheduling

- `POST /api/community/events` – Create events, set capacity, pricing, accessibility
  accommodations, and sustainability ratings.
- `POST /api/community/events/{event_id}/join` – RSVP with waitlist and roommate-matching
  logic.
- `GET /api/community/feed` – Retrieve moderated social feed with reputation context.
- `GET /api/scheduling/agenda` – Generate consolidated schedule for maintenance, move-ins,
  inspections, and community events.
- `POST /api/scheduling/commit` – Confirm assignments and push notifications to vendors
  and residents.

## Alerts & Energy

- `POST /api/alerts` – Submit alert events; response provides deduplication status and
  predicted severity.
- `GET /api/alerts/stream` – Server-sent events/WebSocket endpoint for real-time alert
  updates.
- `POST /api/energy/trade` – Register renewable energy trades or demand-response actions
  with price, volume, and carbon data.
- `GET /api/energy/ledger` – Access historical trades, offsets consumed, and marketplace
  analytics.

## Plugins

- `GET /api/plugins` – List installed plugins with permissions, signatures, and health
  status.
- `POST /api/plugins/install` – Register a plugin manifest; requires administrator role
  and signature validation.
- `POST /api/plugins/{plugin_id}/enable` – Enable plugin after sandbox verification.
- `POST /api/plugins/{plugin_id}/disable` – Disable plugin gracefully with cleanup report.
- `POST /api/plugins/{plugin_id}/reload` – Hot-reload plugin code and metadata.
- **Security Note:** Plugins must provide detached Ed25519 signatures and a minimum
  permission scope. Installation attempts without signatures return HTTP 403 with audit log
  references.

## Health & Observability

- `GET /health` – Liveness probe covering runtime, dependency heartbeat, plugin registry,
  blockchain connector, and cursor integration status.
- `GET /ready` – Readiness probe checking database migrations, cache warmup, model
  availability, and webhook subscriptions.
- `GET /api/metrics` – Prometheus-compatible metrics feed (response times, energy usage,
  fairness deltas, queue depths).
- **Rate Limiting:** Health probes are exempt from tenant-level rate limiting, whereas all
  `/api/*` endpoints default to 120 requests/minute per token with exponential backoff on
  throttling responses.

## Governance & Compliance

- `GET /api/fairness/dashboard` – Model explainability payload used by frontend fairness
  boards (Shapley values, demographic parity, equalized odds).
- `POST /api/privacy/requests` – Submit data access/deletion/export requests with audit
  receipts.
- `GET /api/audit/logs` – Retrieve immutable decision logs with blockchain anchoring
  proofs.

All endpoints are documented through FastAPI's OpenAPI schema accessible via
`/docs` and `/redoc`. Integration tests (`src/backend/tests/integration`) exercise each
workflow end-to-end to guarantee parity between documentation and implementation.
