# Knowledge System Specification

## Purpose

The knowledge subsystem maintains durable knowledge blocks, enabling agents to retrieve historical insights, code snippets and design references. Stage 1 relies on an in-memory store with deterministic indexing and validation.

## Data Structures

- **KnowledgeBlock** – Contains `id`, `content`, `metadata` (author, timestamp, tags, citations, source), `reliabilityScore` and optional `links` to related blocks.
- **KnowledgeQuery** – Structured query comprising `keywords`, `tags`, optional embedding vector, `limit` and `sort` preferences.
- **KnowledgeResponse** – List of matched blocks with confidence scores and traceability metadata.

JSON Schemas in `src/knowledge/scaffolds.ts` enforce the structure of blocks and NDJSON ingestion pipelines.

## Operations

- `storeBlock(block)` – Validates schema compliance, ensures ID uniqueness and appends to the store.
- `fetchBlock(id)` – Returns block by identifier.
- `searchBlocks(query)` – Performs keyword/tag filtering with scoring heuristics and returns ranked results.

## Persistence Strategy

Stage 1 stores blocks in-memory with optional JSON export. Stage 2 integrates vector and graph databases. Stage 3 adds freshness monitoring and automatic updates.

## Governance

- All writes are logged to the memory subsystem for auditing.
- Blocks track provenance and licensing to satisfy compliance checks.
- Schema validation prevents injection and ensures consistent metadata.

## Integration Points

- Context Fabric uses the knowledge service for context ingestion.
- Macros reference knowledge metadata when generating deliverables.
- Operators can import NDJSON scaffolds through CLI interfaces.
