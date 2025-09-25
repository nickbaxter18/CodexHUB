# Memory System Specification

## Objectives

Memory services capture episodic records, caches and operational logs to enable observability, retrospectives and foresight analytics.

## Components

- **Memory API (`src/memory/index.ts`)** – Stores and retrieves structured `MemoryRecord` objects.
- **Logger (`src/memory/logs.ts`)** – Writes append-only logs with rotation, compression and encryption hooks.
- **Cache (`src/memory/cache.ts`)** – Implements in-memory LRU cache with TTL enforcement for working memory scenarios.

## Data Structures

- `MemoryRecord`: contains `id`, `agentId`, `timestamp`, `dataType`, `payload`, `tags` and optional `sensitivity` metadata.
- `LogEntry`: summarises pipeline actions with references to tasks and macros.
- `CacheEntry`: stores short-lived computation results with expiry metadata.

## Guarantees

- All operations emit events consumed by analytics modules.
- Encryption utilities ensure sensitive payloads remain protected.
- Retrieval queries support filtering by date range, agent or tag.

## Stage 1 Implementation

The current implementation uses in-memory structures and Node file streams with rotation thresholds. Future stages will swap in durable storage without changing the public API.
