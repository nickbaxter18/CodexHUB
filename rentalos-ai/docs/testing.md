# Testing Strategy

Stage 1 focuses on deterministic unit tests for every backend service plus integration tests for select API
routes. Frontend tests verify that components render expected labels and that page layouts stitch components
together. The testing harness uses `pytest` for Python modules and `vitest` with React Testing Library for
TypeScript code.

Stage 2 introduces data-driven verifications:

- Pricing tests feed market snapshots into the knowledge base and assert that recommendations include
  market adjustments with elevated confidence scores.
- Maintenance tests establish sensor baselines, trigger anomalies, and ensure follow-up tasks surface in
  generated schedules.
- API tests simulate plugin registration, lifecycle toggles, and metadata summaries for marketplace-ready
  integrations.

Future stages will extend this foundation with performance, fairness, and resilience testing.
