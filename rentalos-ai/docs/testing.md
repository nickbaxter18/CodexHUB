# Testing Strategy

Stage 1 focuses on deterministic unit tests for every backend service plus integration tests for select API
routes. Frontend tests verify that components render expected labels and that page layouts stitch components
together. The testing harness uses `pytest` for Python modules and `vitest` with React Testing Library for
TypeScript code.

Future stages will extend this foundation with performance, fairness, and resilience testing.
