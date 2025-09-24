# RentalOS-AI Architecture

RentalOS-AI follows a modular monolith architecture that keeps backend services, orchestration logic,
frontend presentation, and shared documentation in a single repository. Stage 1 establishes the key
packages, data models, and request flows that later stages will expand with advanced AI and integrations.

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
Future stages will integrate PostgreSQL, Redis caching, and a Neo4j knowledge graph. For Stage 1 we provide
in-memory mock data for deterministic tests.

## Observability & Security

Middlewares add structured logging, request compression, and simplified authentication hooks. Security utilities
handle hashing and token creation, and validators provide fairness and sanitation helpers.

## Extensibility

The orchestrator coordinates specialized agents that encapsulate AI-driven logic. Stage 1 supplies lightweight
agents with deterministic responses, enabling tests and demonstrating how asynchronous orchestration will work in
later stages.
