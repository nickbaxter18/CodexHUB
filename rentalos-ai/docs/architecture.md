# RentalOS-AI Architecture

RentalOS-AI follows a modular monolith architecture that keeps backend services, orchestration logic,
frontend presentation, and shared documentation in a single repository. Stage 1 establishes the key
packages, data models, and request flows that later stages will expand with advanced AI and integrations.
Stage 2 layers data feedback loops onto those foundations: market snapshots flow into the pricing
service via the knowledge base, sensor rollups highlight anomalies for maintenance, and a plugin
registry models the extension marketplace that external partners will eventually use.

## Backend Overview

The FastAPI backend exposes REST endpoints for pricing, maintenance, leasing, screening, payments,
ESG reporting, community features, scheduling, alerts, and energy trading. Each module includes services
encapsulating domain logic and controllers that map HTTP routes to service calls.

## Frontend Overview

The React + Vite frontend provides dashboards and workflows for the major personas: property managers,
owners, tenants, community coordinators, and sustainability officers. Stage 1 supplies functional views for
core modules and sets up Tailwind-powered design primitives.

## Data Management

SQLAlchemy models describe relational entities while Pydantic schemas ensure strict validation of API payloads.
The Stage 2 knowledge base upgrade retains an in-memory implementation but now tracks per-entity metric
series, providing weighted averages, rolling confidence calculations, and snapshots for tests.
Future stages will integrate PostgreSQL, Redis caching, and a Neo4j knowledge graph. For now we provide
in-memory mock data that mimic those interfaces for deterministic tests.

## Observability & Security

Middlewares add structured logging, request compression, and simplified authentication hooks. Security utilities
handle hashing and token creation, and validators provide fairness and sanitation helpers.

## Extensibility

The orchestrator coordinates specialized agents that encapsulate AI-driven logic. Stage 2 preserves the
deterministic agent responses but feeds them with richer pre-processing: pricing adjustments blend
weighted historical rates, demand indexes, and sustainability modifiers before delegating to the agent
layer, while maintenance agents receive severity hints derived from anomaly scores. The API service now
hosts a plugin registry so third parties can register, enable, and disable integrations without altering
core code paths.
