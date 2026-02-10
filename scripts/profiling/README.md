# STAC Manager Profiling Scripts

Benchmarking tools to measure IngestModule performance and inform concurrent request handling design.

## Purpose

These scripts help identify bottlenecks in STAC item ingestion:
- **File Mode**: Is it I/O-bound (disk read) or CPU-bound (JSON parsing)?
- **API Mode**: How much speedup can we get from concurrent HTTP requests?
- **Optimal Concurrency**: What's the best worker count for each mode?

## Installation

No additional dependencies needed beyond STAC Manager's core requirements.

For API benchmarking (future), add:
```bash
poetry add aiohttp
```

## Usage

### File Mode Benchmark

Generate test data and measure file loading performance:

```bash
# Quick test (1K items)
python scripts/profiling/benchmark_ingest.py file \
  --test-size 1000 \
  --concurrency 1,5,10 \
  --output results/quick_test.json

# Full benchmark (10K items, more concurrency levels)
python scripts/profiling/benchmark_ingest.py file \
  --test-size 10000 \
  --concurrency 1,5,10,20,50 \
  --output results/file_10k.json
```

**Output:**
- `results/file_10k.json`: Structured benchmark data
- `results/file_10k_report.md`: Human-readable Markdown report

### API Mode Benchmark

Test against a real STAC API:

```bash
python scripts/profiling/benchmark_ingest.py api \
  --catalog-url https://earth-search.aws.element84.com/v1 \
  --collection-id sentinel-2-l2a \
  --max-items 500 \
  --concurrency 1,5,10 \
  --output results/api_earth_search.json
```

**Note:** Concurrent API benchmarking requires `aiohttp` (not yet implemented).

## Interpreting Results

### Example Report

```markdown
## 10K JSON Files

| Strategy   | Concurrency | Time (s) | Throughput (items/s) | Memory (MB) | Speedup |
|------------|-------------|----------|----------------------|-------------|---------|
| sequential | 1           | 45.2     | 221                  | 120         | baseline|
| concurrent | 5           | 12.3     | 813                  | 180         | 3.7x    |
| concurrent | 10          | 8.7      | 1,149                | 250         | 5.2x    |
| concurrent | 20          | 9.1      | 1,099                | 410         | 5.0x    |

**Best Performance**: 10 workers with 5.2x speedup
```

### What to Look For

✅ **Significant Speedup (3-5x)**: I/O-bound, concurrency helps a lot
- Implement worker pool with recommended concurrency level

⚠️ **Modest Speedup (1.5-2x)**: Mixed I/O and CPU
- Concurrency helps but not dramatically

❌ **No Speedup (<1.2x)**: CPU-bound (unlikely for file I/O)
- Consider other optimizations (streaming parsers, Parquet)

📈 **Diminishing Returns**: Speedup plateaus beyond certain concurrency
- Use that level as the default (e.g., 10 workers)

## Test Data Cleanup

Benchmark data is stored in `scripts/profiling/test_data/` (gitignored).

To clean up:
```bash
rm -rf scripts/profiling/test_data/
rm -rf scripts/profiling/results/*.json
```

## Architecture

```
scripts/profiling/
├── benchmark_ingest.py          # Main CLI
├── profile_file_io.py           # File mode benchmarks
├── profile_api_requests.py      # API mode benchmarks
├── test_data_generator.py       # Generate test STAC items
├── utils.py                     # Timing, memory, reporting
├── results/                     # Output directory (gitignored)
└── test_data/                   # Generated test items (gitignored)
```

## Next Steps

After benchmarking:
1. Review results to identify bottlenecks
2. Determine optimal concurrency levels
3. Design Phase 2 concurrent IngestModule implementation
4. Use findings to inform worker pool architecture

## References

- [Phase 1 PRD](../../docs/plans/2026-02-10-concurrent-ingestion-phase1-profiling.md)
- [Implementation Plan](../../docs/plans/2026-02-10-concurrent-ingestion-phase1-tdd-plan.md)
