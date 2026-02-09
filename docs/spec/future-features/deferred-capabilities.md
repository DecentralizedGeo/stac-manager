# Deferred Capabilities (Future Features)

## Overview
This document tracks features and capabilities identified during V1 planning that have been explicitly deferred to V2 or later to maintain scope.

---

## 1. Async Authentication Injection
**Status**: Deferred (V1 targets open data only)

### Requirement
The ability to inject authentication headers (OAuth2, bearer tokens) into the optimized `aiohttp` pipelines used by the `IngestModule`.

### Technical Gap
`pystac-client` handles auth negotiation well in synchronous mode, but our V1 architecture bypasses it for performance using `aiohttp`. A standardized `AuthMiddleware` or `AuthProtocol` is needed that can sign requests for both clients.

---

## 2. Distributed Rate Limiting
**Status**: Deferred (V1 is single-process)

### Requirement
Coordinate rate limits across multiple running instances of STAC Manager (e.g., in a Kubernetes cluster) to avoid aggregate bans from upstream APIs.

### Technical Concept
- Shared state using Redis or Memcached.
- Token Bucket algorithm implemented with atomic counters in the shared store.

---

## 3. High-Performance Validation
**Status**: Deferred (V1 uses `pystac.Item.validate()`)

### Requirement
Extremely fast (sub-millisecond) validation for pipelines processing >1000 items/second.

### Performance Issue
`pystac` validation loads the full JSON schema into `jsonschema`, which can be slow (10-100ms per item).

### Proposed Solution
- Use `fastjsonschema` or `orjson` based validation.
- Pre-compile schemas at module initialization.
- Benchmark "Schema-less" validation that checks only struct existence.
