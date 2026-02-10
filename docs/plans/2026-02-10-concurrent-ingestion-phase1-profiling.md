# Concurrent Ingestion - Phase 1: Profiling & Design

**Date**: 2026-02-10  
**Status**: Draft  
**Version**: 1.0

---

## 1. Executive Summary

The `IngestModule` currently processes items sequentially, which creates performance bottlenecks when handling large collections. Testing with 80K+ items revealed unacceptable processing times. This document outlines **Phase 1** of a two-phase approach to implement concurrent request handling:

- **Phase 1** (This Document): Profile and benchmark to identify bottlenecks and inform design
- **Phase 2** (Future): Implement worker pool-based concurrent ingestion

### Goals for Phase 1
1. Create profiling/benchmarking scripts to measure current performance
2. Identify specific bottlenecks (I/O, parsing, network, etc.)
3. Design a balanced worker pool architecture informed by profiling data
4. Document findings and recommendations for Phase 2 implementation

---

## 2. Problem Statement

### Current State
- **IngestModule** processes items one-at-a-time sequentially
- Both API and file modes are affected
- Real-world testing: 80K+ item collection takes excessively long
- No concurrency capabilities in current implementation

### Pain Points
1. **API Mode**: Sequential HTTP requests to STAC APIs waste idle time waiting for responses
2. **File Mode**: Sequential file reads underutilize disk I/O capacity
3. **Scalability**: Performance degrades linearly with collection size
4. **User Experience**: Long-running pipelines without optimization options

### Gap from Specification
The v1.0.0 spec describes advanced concurrency features (worker pools, request splitting, time-chunking) that were never implemented. Current code is a minimal viable implementation.

---

## 3. Background Context

### Architecture Constraints
- **Streaming Model**: Modules connected as async generators, items flow one-at-a-time
- **Order Independence**: Downstream modules (Transform, Update, Output) don't depend on item order
- **Error Handling**: Non-critical failures collected via `FailureCollector`, don't crash pipeline
- **Checkpointing**: Existing `CheckpointManager` tracks completed items for resume capability

### Key Insights from Design Discussion
1. **Both modes need concurrency**: API and file modes both suffer from sequential processing
2. **Order doesn't matter**: Output can handle items arriving out-of-order
3. **Keep it simple**: Prefer maintainability over maximum performance
4. **Checkpoint-based retry**: 429 rate limit errors can bubble up as failures, rely on checkpoints for retry

---

## 4. Phase 1 Objectives

### Primary Goal
**Create data-driven insights** to inform the concurrent ingestion implementation by measuring:
- Where time is actually spent (I/O vs parsing vs network)
- How concurrency affects performance at different levels
- Memory usage patterns with concurrent operations
- Practical concurrency limits for different scenarios

### Success Criteria
✅ Profiling script that measures file I/O, parsing, and API performance  
✅ Benchmark results showing sequential vs concurrent performance  
✅ Identification of primary bottleneck (I/O, CPU, network)  
✅ Recommended concurrency levels for each mode  
✅ Design document for Phase 2 worker pool implementation  

### Non-Goals (Phase 2)
❌ Implementing actual concurrent ingestion (Phase 2)  
❌ Time-chunking or request splitting (future optimization)  
❌ Automatic retry/backoff for rate limits (handled by checkpointing)  

---

## 5. Profiling Strategy

### 5.1 File Mode Benchmarks

**Test Scenarios:**
1. **Many Small Files** (simulates typical workflow)
   - 10K JSON files, ~5KB each
   - Measure: sequential read, concurrent read (5/10/20 workers)
   - Metrics: total time, throughput (items/sec), memory usage

2. **Few Large Files** (Parquet use case)
   - 5 Parquet files, ~100MB each
   - Measure: sequential vs concurrent loading
   - Metrics: parse time, memory overhead

3. **Items Directory** (collection workflow)
   - Real collection with 1K items
   - Test: `_load_items_from_directory` performance
   - Compare: sequential vs concurrent with error handling

**What We're Measuring:**
- Is it I/O bound (disk read speed)?
- Is it CPU bound (JSON parsing)?
- Does concurrency help, and at what level?
- Memory overhead of concurrent operations

### 5.2 API Mode Benchmarks

**Test Scenarios:**
1. **Small Collection** (baseline)
   - 100 items, single page
   - Measure: pystac-client (current) vs aiohttp (proposed)
   - Metrics: request latency, total time

2. **Large Collection** (stress test)
   - 10K items, multiple pages
   - Measure: sequential vs concurrent (5/10/20 workers)
   - Metrics: throughput, memory, rate limit encounters

3. **Pagination Performance**
   - Test: `/search` endpoint pagination efficiency
   - Compare: sequential page fetching vs concurrent page fetching
   - Handle: `next` link traversal patterns

**What We're Measuring:**
- Network latency impact
- Optimal concurrent request count
- pystac-client overhead vs direct HTTP
- Memory usage with buffered items

### 5.3 Mixed Workload

**Realistic Pipeline:**
- Ingest (file or API) → Transform → Output
- Measure: end-to-end time with concurrent ingest
- Compare: current sequential vs proposed concurrent
- Verify: downstream modules handle out-of-order items correctly

---

## 6. Profiling Script Design

### Script Structure
```
scripts/
  profiling/
    benchmark_ingest.py          # Main benchmarking script
    profile_file_io.py           # File mode profiling
    profile_api_requests.py      # API mode profiling
    test_data_generator.py       # Generate test collections
    results/
      benchmark_results.json     # Output data
      benchmark_report.md        # Human-readable summary
```

### Key Features
1. **Parameterized Tests**: Configurable collection sizes, concurrency levels
2. **Time Profiling**: Use `time.perf_counter()` for precision
3. **Memory Profiling**: Track memory usage with `tracemalloc`
4. **Result Export**: JSON format for analysis, Markdown for readability
5. **Comparison Mode**: Side-by-side sequential vs concurrent results

### Example Output
```markdown
## File Mode Benchmark Results

### Scenario: 10K Small JSON Files

| Strategy    | Concurrency | Time (s) | Throughput (items/s) | Memory (MB) |
|-------------|-------------|----------|----------------------|-------------|
| Sequential  | 1           | 45.2     | 221                  | 120         |
| Concurrent  | 5           | 12.3     | 813                  | 180         |
| Concurrent  | 10          | 8.7      | 1,149                | 250         |
| Concurrent  | 20          | 9.1      | 1,099                | 410         |

**Findings:** Optimal concurrency at 10 workers (3.6x speedup). Diminishing returns beyond 10.
```

---

## 7. Design Options (Phase 2 Preview)

Based on our brainstorming discussion, three approaches were considered:

### Option 1: Semaphore-Based Concurrency
- Simple `asyncio.Semaphore` to limit concurrent operations
- Direct async I/O for files, aiohttp for API
- **Pro**: Simplest, small code change
- **Con**: Less optimal for very large collections

### Option 2: Worker Pool with Queue ⭐ **Recommended**
- Task queue with N worker coroutines
- Coordinator yields results as they arrive
- **Pro**: Balanced complexity/performance, matches spec vision
- **Con**: More complex than Option 1

### Option 3: Time-Chunking + Workers
- Split API queries by time range (RequestSplitter)
- Distribute chunks to workers
- **Pro**: Maximum performance for huge collections
- **Con**: Most complex, only benefits API mode

**Decision**: Profiling results will inform which option to pursue. Initial bias toward **Option 2** for balance.

---

## 8. Configuration Schema (Proposed)

Extend `IngestConfig` with concurrency settings:

```python
class IngestConfig(BaseModel):
    # ... existing fields ...
    
    # NEW: Concurrency settings
    concurrency: int = Field(
        default=1,  # Sequential by default (backward compatible)
        ge=1,
        le=50,
        description="Max concurrent workers for fetching items"
    )
    
    worker_strategy: Literal["semaphore", "queue"] = Field(
        default="semaphore",
        description="Concurrency implementation strategy"
    )
```

**Design Notes:**
- `concurrency=1` maintains current behavior (no breaking change)
- Users opt-in by setting `concurrency > 1`
- `worker_strategy` allows future experimentation

---

## 9. Implementation Impact

### Files Modified (Phase 2)
- `src/stac_manager/modules/ingest.py`: Add concurrent fetch methods
- `src/stac_manager/modules/config.py`: Extend `IngestConfig`
- `tests/unit/modules/test_ingest.py`: Add concurrency tests

### Dependencies Added
- `aiohttp`: Async HTTP client for API mode (replaces pystac-client in workers)
- `aiofiles` (optional): Async file I/O if profiling shows benefit

### Backward Compatibility
✅ No breaking changes  
✅ Default `concurrency=1` preserves existing behavior  
✅ Existing configs work without modification  

---

## 10. Testing Strategy (Phase 2 Preview)

### Unit Tests
- Test concurrent file loading with mock files
- Test concurrent API requests with mock server
- Verify items yielded correctly (order-independent)
- Test concurrency limits respected

### Integration Tests
- End-to-end pipeline with concurrent ingest
- Verify checkpoint integration works
- Test failure handling with concurrent operations

### Performance Tests
- Regression test: ensure no slowdown with `concurrency=1`
- Benchmark: measure speedup with `concurrency > 1`

---

## 11. Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Profiling shows no I/O bottleneck | High | CPU-bound tasks won't benefit from concurrency; consider alternative optimizations |
| Memory usage spikes with concurrency | Medium | Implement queue size limits, backpressure mechanisms |
| Rate limits encountered in testing | Low | Use test APIs with known limits, document findings |
| Concurrency adds bugs | Medium | Comprehensive testing, incremental rollout |

---

## 12. Deliverables (Phase 1)

1. **Profiling Scripts**: `scripts/profiling/` directory with benchmarking tools
2. **Benchmark Results**: Data and analysis showing bottlenecks
3. **Design Document**: Detailed Phase 2 implementation plan
4. **Recommendation**: Specific concurrency approach based on data

---

## 13. Timeline

**Phase 1** (Estimated 1-2 weeks):
- Week 1: Create profiling scripts, run benchmarks
- Week 2: Analyze results, write Phase 2 design doc

**Phase 2** (TBD based on Phase 1 findings):
- Implementation of chosen concurrency approach
- Testing and validation
- Documentation updates

---

## 14. Success Metrics

Phase 1 is successful when:
- ✅ We have concrete data on where time is spent
- ✅ We know the optimal concurrency level for each mode
- ✅ We have a clear recommendation for implementation approach
- ✅ Design document is approved and ready for implementation

---

## Appendix A: Related Documentation

- [IngestModule Spec](../spec/stac-manager-v1.0.0/modules/ingest.md)
- [Async & Parallel Analysis](../spec/stac-manager-v1.0.0/appendix/async-parallel-analysis.md)
- [Project Memory - Procedural](../../.github/memory/procedural.md)
