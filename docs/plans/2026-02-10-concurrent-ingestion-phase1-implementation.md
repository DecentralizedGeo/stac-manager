# Implementation Plan: Concurrent Ingestion Phase 1 - Profiling

**Date**: 2026-02-10  
**Related Document**: [Phase 1 PRD](./2026-02-10-concurrent-ingestion-phase1-profiling.md)  
**Status**: Draft

---

## Goal

Create comprehensive profiling and benchmarking scripts to measure IngestModule performance bottlenecks and inform the design of concurrent request handling. This is a **measurement-first** approach to ensure implementation decisions are data-driven.

---

## Proposed Changes

### New Scripts Directory

Create `scripts/profiling/` with the following structure:

```
scripts/
  profiling/
    __init__.py                      # Package marker
    benchmark_ingest.py              # Main CLI for running benchmarks
    profile_file_io.py               # File mode profiling utilities
    profile_api_requests.py          # API mode profiling utilities
    test_data_generator.py           # Generate test STAC collections
    utils.py                         # Shared utilities (timing, memory tracking)
    results/                         # Output directory (gitignored)
      .gitkeep                       # Ensures directory exists
    README.md                        # Usage documentation
```

---

## File Details

### 1. `scripts/profiling/utils.py`

**Purpose**: Shared utilities for timing, memory tracking, and result formatting

**Key Functions**:
```python
@contextmanager
def measure_time(label: str) -> Iterator[dict]:
    """Context manager to measure execution time"""
    # Uses time.perf_counter() for precision
    # Returns dict with label, duration_seconds

@contextmanager  
def measure_memory(label: str) -> Iterator[dict]:
    """Context manager to track memory usage"""
    # Uses tracemalloc to measure peak memory
    # Returns dict with label, peak_memory_mb

class BenchmarkResult:
    """Structured benchmark result"""
    scenario: str
    strategy: str  # "sequential" or "concurrent"
    concurrency: int  # 1 for sequential
    duration_seconds: float
    throughput_items_per_sec: float
    peak_memory_mb: float
    items_processed: int
    
def save_results(results: list[BenchmarkResult], output_path: Path):
    """Save results as JSON and Markdown report"""

def compare_results(baseline: BenchmarkResult, concurrent: BenchmarkResult):
    """Calculate speedup, memory overhead"""
```

**Tests**: Unit tests in `tests/scripts/test_profiling_utils.py`
- Test timing accuracy (compare to known sleep duration)
- Test memory tracking (allocate known size)
- Test result serialization (JSON round-trip)

---

### 2. `scripts/profiling/test_data_generator.py`

**Purpose**: Generate synthetic STAC collections for benchmarking

**Key Functions**:
```python
def generate_stac_item(item_id: str, collection_id: str = "test-collection") -> dict:
    """Generate a minimal valid STAC item"""
    # Simple geometry, 5 assets, ~5KB JSON size
    
def generate_item_files(
    output_dir: Path, 
    count: int,
    collection_id: str = "test-collection"
) -> Path:
    """Generate N individual JSON files in a directory"""
    # Output: {output_dir}/{item_id}.json
    # Returns path to directory
    
def generate_feature_collection(
    output_path: Path,
    count: int,
    collection_id: str = "test-collection"  
) -> Path:
    """Generate a FeatureCollection JSON file"""
    # Output: single JSON with "features" array
    # Returns path to file
    
def generate_parquet_file(
    output_path: Path,
    count: int,
    collection_id: str = "test-collection"
) -> Path:
    """Generate a Parquet file with STAC items"""
    # Uses stac_geoparquet or pyarrow
    # Returns path to file
```

**Tests**: Integration tests in `tests/scripts/test_data_generator.py`
- Generate small dataset (10 items), verify structure
- Validate generated items with stac-validator
- Check file sizes are reasonable

---

### 3. `scripts/profiling/profile_file_io.py`

**Purpose**: Benchmark file mode ingestion performance

**Key Functions**:
```python
async def benchmark_sequential_files(directory: Path, max_items: int = None) -> BenchmarkResult:
    """Measure current IngestModule performance (baseline)"""
    # Uses existing IngestModule with mode="file"
    # Tracks time and memory
    
async def benchmark_concurrent_files(
    directory: Path, 
    concurrency: int,
    max_items: int = None
) -> BenchmarkResult:
    """Measure concurrent file reading"""
    # Simulates proposed concurrent implementation
    # Uses asyncio.gather with semaphore
    # Returns metrics for comparison
    
async def benchmark_parquet_loading(parquet_path: Path) -> BenchmarkResult:
    """Measure Parquet file loading performance"""
    # Current approach (load entire table)
    # Future: chunked reading if beneficial
```

**Tests**: Integration tests in `tests/scripts/test_profile_file_io.py`
- Run benchmarks with small dataset (100 items)
- Verify results structure is complete
- Check concurrent version doesn't crash

---

### 4. `scripts/profiling/profile_api_requests.py`

**Purpose**: Benchmark API mode ingestion performance

**Key Functions**:
```python
async def benchmark_sequential_api(
    catalog_url: str,
    collection_id: str,
    max_items: int = 100
) -> BenchmarkResult:
    """Measure current IngestModule API performance (baseline)"""
    # Uses pystac-client (current implementation)
    
async def benchmark_concurrent_api_aiohttp(
    catalog_url: str,
    collection_id: str,
    concurrency: int,
    max_items: int = 100
) -> BenchmarkResult:
    """Measure concurrent API requests with aiohttp"""
    # Direct async HTTP to /search endpoint
    # Simulates worker pool approach
    # Handles pagination with concurrent requests
    
async def benchmark_concurrent_api_pystac(
    catalog_url: str,
    collection_id: str,
    concurrency: int,
    max_items: int = 100
) -> BenchmarkResult:
    """Measure pystac-client in ThreadPoolExecutor"""
    # Alternative: wrap pystac-client in threads
    # Compare to aiohttp approach
```

**Tests**: Integration tests in `tests/scripts/test_profile_api_requests.py`
- Mock STAC API server for controlled testing
- Verify request counting (ensure concurrency respected)
- Test pagination handling

**Note**: These tests use mock APIs to avoid hitting real services. Real benchmarks are run manually.

---

### 5. `scripts/profiling/benchmark_ingest.py`

**Purpose**: Main CLI script to run all benchmarks

**Usage**:
```bash
# File mode benchmarks
python scripts/profiling/benchmark_ingest.py file \
  --test-size 10000 \
  --concurrency 1,5,10,20 \
  --output results/file_benchmark.json

# API mode benchmarks  
python scripts/profiling/benchmark_ingest.py api \
  --catalog-url https://earth-search.aws.element84.com/v1 \
  --collection-id sentinel-2-l2a \
  --max-items 1000 \
  --concurrency 1,5,10,20 \
  --output results/api_benchmark.json

# Full benchmark suite
python scripts/profiling/benchmark_ingest.py all \
  --test-size 10000 \
  --output results/
```

**Implementation**:
- Uses `click` for CLI (consistent with project patterns)
- Calls profiling functions from other modules
- Generates both JSON data and Markdown reports
- Progress display with estimated time remaining

**Tests**: CLI tests in `tests/scripts/test_benchmark_cli.py`
- Test argument parsing
- Mock profiling functions, verify they're called correctly
- Test output file creation

---

### 6. `scripts/profiling/README.md`

**Purpose**: Documentation for using profiling scripts

**Contents**:
- Overview of profiling strategy
- How to run benchmarks
- How to interpret results
- Example output and analysis
- Tips for test data generation

---

## Verification Plan

### Automated Tests

**Test Files to Create**:
1. `tests/scripts/test_profiling_utils.py`
   - Command: `pytest tests/scripts/test_profiling_utils.py -v`
   - Coverage: Timing, memory tracking, result serialization

2. `tests/scripts/test_data_generator.py`
   - Command: `pytest tests/scripts/test_data_generator.py -v`
   - Coverage: STAC item generation, file creation, validation

3. `tests/scripts/test_profile_file_io.py`
   - Command: `pytest tests/scripts/test_profile_file_io.py -v`
   - Coverage: File benchmark functions with small datasets

4. `tests/scripts/test_profile_api_requests.py`
   - Command: `pytest tests/scripts/test_profile_api_requests.py -v`
   - Coverage: API benchmark functions with mock server

5. `tests/scripts/test_benchmark_cli.py`
   - Command: `pytest tests/scripts/test_benchmark_cli.py -v`
   - Coverage: CLI argument parsing and execution

**Run All Tests**:
```bash
pytest tests/scripts/ -v
```

### Manual Testing

**Step 1: Generate Test Data**
```bash
# Create test collection with 10K items
python scripts/profiling/test_data_generator.py \
  --output test_data/items_10k \
  --count 10000 \
  --format directory
```

**Step 2: Run File Mode Benchmark**
```bash
# Benchmark file mode with different concurrency levels
python scripts/profiling/benchmark_ingest.py file \
  --directory test_data/items_10k \
  --concurrency 1,5,10,20 \
  --output results/file_benchmark.json
```

**Expected Output**:
- `results/file_benchmark.json` (structured data)
- `results/file_benchmark_report.md` (human-readable)
- Console shows progress and summary

**Step 3: Run API Mode Benchmark**
```bash
# Benchmark API mode (uses public Earth Search API)
python scripts/profiling/benchmark_ingest.py api \
  --catalog-url https://earth-search.aws.element84.com/v1 \
  --collection-id sentinel-2-l2a \
  --max-items 500 \
  --concurrency 1,5,10 \
  --output results/api_benchmark.json
```

**Expected Output**:
- Comparison of sequential vs concurrent API requests
- Shows throughput improvement
- Identifies optimal concurrency level

**Step 4: Review Results**
```bash
# View Markdown report
cat results/file_benchmark_report.md
cat results/api_benchmark_report.md
```

**What to Look For**:
- ✅ Speedup with concurrency (2-5x for I/O bound)
- ✅ Diminishing returns beyond certain concurrency level
- ✅ Memory usage remains reasonable
- ✅ Identification of bottleneck (I/O vs CPU)

---

## Dependencies

**New Dependencies** (add to `pyproject.toml`):
```toml
[tool.poetry.dependencies]
# Existing dependencies remain...
aiohttp = "^3.9.0"  # For concurrent API requests
aiofiles = { version = "^23.0.0", optional = true }  # For async file I/O (if beneficial)

[tool.poetry.group.dev.dependencies]
# For profiling/benchmarking
requests-mock = "^1.11.0"  # Mock HTTP in tests (already exists)
```

**No Breaking Changes**: All new dependencies are for scripts/testing only, not core library

---

## Implementation Steps

### Phase 1: Foundation
1. Create `scripts/profiling/` directory structure
2. Implement `utils.py` (timing, memory tracking)
3. Write tests for `utils.py`
4. Verify: `pytest tests/scripts/test_profiling_utils.py -v`

### Phase 2: Test Data Generation  
5. Implement `test_data_generator.py`
6. Write tests for data generator
7. Verify: `pytest tests/scripts/test_data_generator.py -v`
8. Manual test: Generate 1K items, validate with stac-validator

### Phase 3: File Mode Profiling
9. Implement `profile_file_io.py`
10. Write benchmark tests
11. Verify: `pytest tests/scripts/test_profile_file_io.py -v`
12. Manual benchmark: Run with 10K items

### Phase 4: API Mode Profiling
13. Implement `profile_api_requests.py`
14. Create mock API server for tests
15. Write benchmark tests
16. Verify: `pytest tests/scripts/test_profile_api_requests.py -v`
17. Manual benchmark: Run against Earth Search API

### Phase 5: CLI Integration
18. Implement `benchmark_ingest.py` CLI
19. Write CLI tests
20. Verify: `pytest tests/scripts/test_benchmark_cli.py -v`
21. Manual test: Run full benchmark suite

### Phase 6: Documentation
22. Write `scripts/profiling/README.md`
23. Document findings in results/
24. Update main project docs if needed

---

## Success Criteria

✅ All automated tests pass  
✅ Benchmarks can run successfully with test data  
✅ Results clearly show bottlenecks (I/O vs CPU vs network)  
✅ Recommended concurrency levels for each mode  
✅ Data informs Phase 2 design decisions  

---

## Next Steps (Phase 2)

After completing Phase 1 profiling:
1. Review benchmark results
2. Write Phase 2 implementation plan (concurrent IngestModule)
3. Choose specific worker pool approach based on data
4. Implement concurrent fetching with TDD
5. Verify performance improvements match predictions

---

## References

- [Phase 1 PRD](./2026-02-10-concurrent-ingestion-phase1-profiling.md)
- [IngestModule Current Implementation](../../src/stac_manager/modules/ingest.py)
- [IngestModule Tests](../../tests/unit/modules/test_ingest.py)
- [IngestModule Spec](../spec/stac-manager-v1.0.0/modules/ingest.md)
