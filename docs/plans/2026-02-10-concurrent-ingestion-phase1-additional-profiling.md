# Concurrent Ingestion Phase 1: Additional Profiling Tasks

**Date:** 2026-02-10  
**Status:** Proposed  
**Related:** [Phase 1 TDD Plan](2026-02-10-concurrent-ingestion-phase1-tdd-plan.md)

## Executive Summary

Phase 1 profiling revealed that **file mode ingestion is CPU-bound** (no asyncio speedup) and **API mode is I/O-bound** (69 items/s). However, we have not profiled the output side or full pipeline, which may be the true bottleneck. This plan outlines additional profiling tasks needed before Phase 2 design.

## Current Profiling Results

### File Mode (10K items)
- **Sequential**: 2,797 items/s, 0 MB memory
- **Concurrent (asyncio, 5-20 workers)**: 0.9-1.0x speedup
- **Conclusion**: CPU-bound (JSON parsing), limited by Python GIL

### API Mode (5K items)  
- **Sequential**: 69 items/s (72.3 seconds total)
- **Concurrent**: Not implemented (requires aiohttp)
- **Conclusion**: I/O-bound, would benefit from concurrent requests

## Critical Gap: Output Performance Unknown

Current profiling measured **ingestion only**. We don't know:
- How fast is OutputModule writing to disk?
- Is JSON serialization slower than parsing?
- Does filesystem metadata (mkdir) cause bottlenecks?
- What's the end-to-end pipeline throughput?

**Risk**: If output is slower than ingestion, concurrent ingestion won't improve overall performance.

---

## Proposed Additional Tasks

### Task 1: Output Module Profiler (CRITICAL)

**Priority:** HIGH  
**Estimated Effort:** 2-4 hours  
**Dependencies:** None

#### Objective
Measure OutputModule write performance to identify if it's a bottleneck.

#### Implementation
Create `scripts/profiling/profile_output.py`:

```python
async def benchmark_output_writes(
    output_dir: Path,
    item_count: int,
    output_mode: str  # "individual" | "collection"
) -> BenchmarkResult:
    """Measure JSON serialization + disk write performance."""
```

#### Test Scenarios
1. Individual file writes (one file per item)
2. Collection writes (all items in one file)
3. With/without fsync (durability vs speed)
4. Different filesystems (SSD vs HDD)

#### Success Criteria
- Measure write throughput (items/s)
- Identify disk I/O wait time
- Compare to ingestion speed (2,797 items/s)

#### Expected Outcomes
- **Best case**: Output faster than ingestion → ingestion is bottleneck
- **Worst case**: Output at 100 items/s with fsync → **output is bottleneck**

---

### Task 2: Full Pipeline Profiler (HIGH PRIORITY)

**Priority:** HIGH  
**Estimated Effort:** 4-6 hours  
**Dependencies:** Output profiler

#### Objective
Measure end-to-end performance: IngestModule → TransformModule → OutputModule.

#### Implementation
Create `scripts/profiling/profile_pipeline.py`:

```python
async def benchmark_full_pipeline(
    input_dir: Path,
    output_dir: Path,
    config_path: Path,
    concurrency: int
) -> BenchmarkResult:
    """Run complete pipeline with all modules."""
```

#### Test Scenarios
1. Sequential pipeline (baseline)
2. Concurrent ingestion, sequential output
3. Concurrent ingestion, batched output
4. Include transform operations (field mapping, validation)
5. Measure checkpoint overhead

#### Success Criteria
- End-to-end throughput (items/s)
- Breakdown by module (ingest %, transform %, output %)
- Memory usage across full pipeline
- Identify true bottleneck

---

### Task 3: Multiprocessing File Profiler (MEDIUM PRIORITY)

**Priority:** MEDIUM  
**Estimated Effort:** 2-3 hours  
**Dependencies:** None

#### Objective
Test if multiprocessing bypasses GIL to achieve true parallelism for CPU-bound JSON parsing.

#### Implementation
Add to `scripts/profiling/profile_file_io.py`:

```python
async def benchmark_multiprocess_files(
    directory: Path,
    workers: int
) -> BenchmarkResult:
    """Use ProcessPoolExecutor for true parallelism."""
```

#### Test Scenarios
- 5, 10, 20 worker processes
- Compare to asyncio results (1.0x)

#### Success Criteria
- Achieve 3-5x speedup with multiprocessing
- Validate GIL bypass hypothesis

#### Expected Outcomes
- **If speedup achieved**: Multiprocessing is viable for Phase 2
- **If no speedup**: Bottleneck is elsewhere (disk I/O, not CPU)

---

### Task 4: Concurrent API Profiler (LOWER PRIORITY)

**Priority:** LOW (Defer to Phase 2)  
**Estimated Effort:** 6-8 hours  
**Dependencies:** aiohttp dependency

#### Objective
Measure concurrent API request performance with true async HTTP.

#### Implementation
- Add `poetry add aiohttp`
- Implement `benchmark_concurrent_api_aiohttp()` in `profile_api_requests.py`
- Handle pagination, rate limiting, authentication

#### Rationale for Deferral
- API mode is I/O-bound (confirmed)
- Concurrent implementation should be part of Phase 2 production code
- Can test concurrency during Phase 2 implementation

---

## Recommended Execution Order

1. ✅ **Output Module Profiler** - Answers "Is output the bottleneck?"
2. ✅ **Full Pipeline Profiler** - Answers "What's the true end-to-end bottleneck?"
3. ⚠️ **Multiprocessing File Profiler** - Validates approach (only if output isn't bottleneck)
4. ⏸️ **Concurrent API Profiler** - Defer to Phase 2

## Critical Questions to Answer

Before designing Phase 2 concurrent architecture:

> **Q1:** Is the bottleneck in ingestion, transformation, or output?

> **Q2:** Can multiprocessing achieve real speedup for file mode?

> **Q3:** What's the optimal worker count for different modes?

> **Q4:** Does output performance change with different output formats (individual vs collection)?

## Estimated Total Effort

- **Minimum viable** (Tasks 1-2): 6-10 hours
- **Complete profiling** (Tasks 1-3): 8-13 hours
- **Full suite** (Tasks 1-4): 14-21 hours

## Files to Create/Modify

### New Files
- `scripts/profiling/profile_output.py`
- `scripts/profiling/profile_pipeline.py`
- `tests/scripts/test_profile_output.py`
- `tests/scripts/test_profile_pipeline.py`

### Modified Files
- `scripts/profiling/profile_file_io.py` (add multiprocessing)
- `scripts/profiling/benchmark_ingest.py` (add CLI commands)
- `scripts/profiling/README.md` (document new profilers)

## Success Metrics

At completion, we should be able to answer:
- ✅ End-to-end pipeline throughput
- ✅ Bottleneck identification (ingestion vs output)
- ✅ Multiprocessing viability for file mode
- ✅ Optimal concurrency levels per mode
- ✅ Memory usage across full pipeline

## Next Steps

1. Review and approve this plan
2. Update Phase 1 PRD with additional tasks
3. Implement in priority order (Output → Pipeline → Multiprocessing)
4. Use findings to inform Phase 2 concurrent architecture design

## References

- [Phase 1 Implementation Plan](2026-02-10-concurrent-ingestion-phase1-tdd-plan.md)
- [Phase 1 Profiling Results](../../results/)
- [Profiling Scripts README](../../scripts/profiling/README.md)
