# API Reference

All endpoints are prefixed with `/api`. The Stage 1 implementation includes high-level routes that return
mocked yet realistic payloads. Each controller file contains detailed docstrings describing the intent of the
routes and response models.

Key endpoints:

- `GET /api/assets` — List available assets and metadata.
- `POST /api/pricing/suggestions` — Generate pricing recommendations for a requested asset.
- `POST /api/maintenance/schedule` — Produce a maintenance plan for an asset.
- `POST /api/screening/evaluate` — Score tenant applications for risk and fairness indicators.
- `POST /api/payments/plan` — Produce a payment plan with rent-splitting details.
- `POST /api/esg/report` — Compile sustainability indicators and recommendations.
- `POST /api/community/events` — Create a community event.
- `GET /api/scheduling/agenda` — Fetch the current smart scheduling plan.
- `POST /api/alerts` — Submit a new alert for delivery.
- `POST /api/energy/trade` — Register an energy trading action.
