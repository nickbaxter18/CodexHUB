# Context Fabric Specification

## Purpose

The context engine ingests, normalises, indexes, retrieves, composes, evaluates and persists contextual information for agents. Stage 1 provides a deterministic in-memory vector store and rule-based summarisation.

## Layers

- **Fabric (`src/context/fabric.ts`)** – Manages storage of context packets, embeddings and summaries. Supports ingest, normalise, index and persist operations.
- **Orchestrator (`src/context/orchestrator.ts`)** – Handles retrieve, compose and evaluate flows, applying relevance scoring and quality gates.
- **Governance (`src/context/governance.ts`)** – Enforces security policies, consent records and compliance checks for context usage.

## Data Structures

- `ContextPacket`: contains `id`, `source`, `content`, `summary`, `embedding`, `metadata` and `createdAt` timestamp.
- `ContextRequest`: describes retrieval needs (roles, keywords, embedding, limit, filters).
- `ContextResponse`: returns selected packets with scoring explanations.

## Lifecycle

1. **Ingest**: Raw inputs validated and enriched with metadata.
2. **Normalise**: Text cleaned, truncated and summarised.
3. **Index**: Embeddings generated (simple hashing in Stage 1) and stored in vector index.
4. **Retrieve**: Query uses cosine-like similarity with fallback keyword search.
5. **Compose**: Selected packets merged with deduplication and length budgeting.
6. **Evaluate**: Governance policies verify sensitivity, freshness and fairness.
7. **Persist**: Packets stored and optionally exported for long-term archives.

## Security

Governance layer enforces RBAC, data minimisation and redaction of sensitive fields. Policy violations trigger exceptions and operator alerts.
