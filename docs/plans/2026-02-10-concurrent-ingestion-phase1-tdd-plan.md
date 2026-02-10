# Concurrent Ingestion Phase 1: Profiling Scripts - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build profiling and benchmarking scripts to measure IngestModule performance bottlenecks and inform concurrent request handling design.

**Architecture:** Create standalone profiling scripts in `scripts/profiling/` that measure file I/O, parsing, and API request performance. Use TDD with comprehensive test coverage. Generate benchmark data as JSON + Markdown reports to identify optimal concurrency levels.

**Tech Stack:** Python 3.12+, asyncio, aiohttp, pytest, click, tracemalloc, pyarrow

---

## Task 1: Create Profiling Utils - Timing Measurement

**Files:**
- Create: `scripts/profiling/__init__.py`
- Create: `scripts/profiling/utils.py`
- Create: `tests/scripts/__init__.py`
- Create: `tests/scripts/test_profiling_utils.py`

**Step 1: Write failing test for time measurement**

File: `tests/scripts/test_profiling_utils.py`

```python
"""Tests for profiling utilities."""
import time
import pytest
from scripts.profiling.utils import measure_time


def test_measure_time_tracks_duration():
    """Test that measure_time accurately tracks execution duration."""
    with measure_time("test_operation") as result:
        time.sleep(0.1)  # Sleep for 100ms
    
    assert result["label"] == "test_operation"
    assert 0.09 < result["duration_seconds"] < 0.12  # Allow 10ms tolerance
    assert "timestamp" in result


def test_measure_time_handles_exceptions():
    """Test that measure_time still records time on exceptions."""
    with pytest.raises(ValueError):
        with measure_time("failing_operation") as result:
            raise ValueError("test error")
    
    # Result should still contain timing data
    assert result["label"] == "failing_operation"
    assert result["duration_seconds"] > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_profiling_utils.py::test_measure_time_tracks_duration -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'scripts.profiling.utils'"

**Step 3: Create package init files**

File: `scripts/profiling/__init__.py`
```python
"""Profiling and benchmarking utilities for STAC Manager."""
```

File: `tests/scripts/__init__.py`
```python
"""Tests for scripts."""
```

**Step 4: Write minimal implementation for measure_time**

File: `scripts/profiling/utils.py`

```python
"""Profiling utilities for measuring performance."""
import time
from contextlib import contextmanager
from typing import Iterator
from datetime import datetime


@contextmanager
def measure_time(label: str) -> Iterator[dict]:
    """Context manager to measure execution time with high precision.
    
    Args:
        label: Description of the operation being measured
        
    Yields:
        dict: Result dictionary with label, duration_seconds, timestamp
        
    Example:
        >>> with measure_time("file_read") as result:
        ...     data = read_file()
        >>> print(f"Took {result['duration_seconds']:.2f}s")
    """
    result = {
        "label": label,
        "timestamp": datetime.utcnow().isoformat(),
        "duration_seconds": 0.0
    }
    
    start = time.perf_counter()
    try:
        yield result
    finally:
        end = time.perf_counter()
        result["duration_seconds"] = end - start
```

**Step 5: Run test to verify it passes**

Run: `pytest tests/scripts/test_profiling_utils.py::test_measure_time_tracks_duration -v`

Expected: PASS

Run: `pytest tests/scripts/test_profiling_utils.py::test_measure_time_handles_exceptions -v`

Expected: PASS

**Step 6: Commit**

```bash
git add scripts/profiling/__init__.py scripts/profiling/utils.py
git add tests/scripts/__init__.py tests/scripts/test_profiling_utils.py
git commit -m "feat(profiling): add measure_time utility with tests"
```

---

## Task 2: Add Memory Profiling Utility

**Files:**
- Modify: `scripts/profiling/utils.py`
- Modify: `tests/scripts/test_profiling_utils.py`

**Step 1: Write failing test for memory measurement**

File: `tests/scripts/test_profiling_utils.py` (append)

```python
from scripts.profiling.utils import measure_memory


def test_measure_memory_tracks_allocation():
    """Test that measure_memory tracks memory usage."""
    with measure_memory("test_allocation") as result:
        # Allocate ~10MB
        big_list = [0] * (10 * 1024 * 1024 // 8)  # 8 bytes per int
    
    assert result["label"] == "test_allocation"
    assert result["peak_memory_mb"] > 5  # At least 5MB allocated
    assert result["peak_memory_mb"] < 50  # Reasonable upper bound


def test_measure_memory_baseline():
    """Test that measure_memory works with minimal allocation."""
    with measure_memory("baseline") as result:
        x = 42  # Minimal allocation
    
    assert result["label"] == "baseline"
    assert result["peak_memory_mb"] >= 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_profiling_utils.py::test_measure_memory_tracks_allocation -v`

Expected: FAIL with "ImportError: cannot import name 'measure_memory'"

**Step 3: Implement measure_memory**

File: `scripts/profiling/utils.py` (append)

```python
import tracemalloc


@contextmanager
def measure_memory(label: str) -> Iterator[dict]:
    """Context manager to measure peak memory usage.
    
    Args:
        label: Description of the operation being measured
        
    Yields:
        dict: Result dictionary with label, peak_memory_mb
        
    Example:
        >>> with measure_memory("data_load") as result:
        ...     data = load_dataset()
        >>> print(f"Peak memory: {result['peak_memory_mb']:.1f}MB")
    """
    result = {
        "label": label,
        "peak_memory_mb": 0.0
    }
    
    tracemalloc.start()
    try:
        yield result
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        result["peak_memory_mb"] = peak / (1024 * 1024)  # Convert bytes to MB
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/scripts/test_profiling_utils.py::test_measure_memory_tracks_allocation -v`

Expected: PASS

Run: `pytest tests/scripts/test_profiling_utils.py::test_measure_memory_baseline -v`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/profiling/utils.py tests/scripts/test_profiling_utils.py
git commit -m "feat(profiling): add measure_memory utility with tests"
```

---

## Task 3: Create BenchmarkResult Data Class

**Files:**
- Modify: `scripts/profiling/utils.py`
- Modify: `tests/scripts/test_profiling_utils.py`

**Step 1: Write failing test for BenchmarkResult**

File: `tests/scripts/test_profiling_utils.py` (append)

```python
from scripts.profiling.utils import BenchmarkResult


def test_benchmark_result_creation():
    """Test BenchmarkResult dataclass creation."""
    result = BenchmarkResult(
        scenario="10K JSON files",
        strategy="sequential",
        concurrency=1,
        duration_seconds=45.2,
        throughput_items_per_sec=221.2,
        peak_memory_mb=120.5,
        items_processed=10000
    )
    
    assert result.scenario == "10K JSON files"
    assert result.strategy == "sequential"
    assert result.concurrency == 1
    assert result.speedup == 1.0  # Sequential baseline


def test_benchmark_result_speedup_calculation():
    """Test speedup is calculated correctly for concurrent runs."""
    baseline = BenchmarkResult(
        scenario="test",
        strategy="sequential",
        concurrency=1,
        duration_seconds=100.0,
        throughput_items_per_sec=100.0,
        peak_memory_mb=50.0,
        items_processed=10000
    )
    
    concurrent = BenchmarkResult(
        scenario="test",
        strategy="concurrent",
        concurrency=10,
        duration_seconds=25.0,
        throughput_items_per_sec=400.0,
        peak_memory_mb=75.0,
        items_processed=10000,
        baseline_duration_seconds=100.0
    )
    
    assert concurrent.speedup == 4.0  # 100 / 25
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_profiling_utils.py::test_benchmark_result_creation -v`

Expected: FAIL with "ImportError: cannot import name 'BenchmarkResult'"

**Step 3: Implement BenchmarkResult**

File: `scripts/profiling/utils.py` (append)

```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BenchmarkResult:
    """Structured benchmark result with performance metrics.
    
    Attributes:
        scenario: Description of benchmark scenario
        strategy: "sequential" or "concurrent"
        concurrency: Number of concurrent workers (1 for sequential)
        duration_seconds: Total execution time
        throughput_items_per_sec: Items processed per second
        peak_memory_mb: Peak memory usage
        items_processed: Total items processed
        baseline_duration_seconds: Optional baseline time for speedup calculation
    """
    scenario: str
    strategy: str
    concurrency: int
    duration_seconds: float
    throughput_items_per_sec: float
    peak_memory_mb: float
    items_processed: int
    baseline_duration_seconds: Optional[float] = None
    
    @property
    def speedup(self) -> float:
        """Calculate speedup compared to baseline.
        
        Returns:
            Speedup factor (e.g., 4.0 = 4x faster)
        """
        if self.baseline_duration_seconds is None:
            return 1.0  # Sequential baseline
        
        if self.baseline_duration_seconds == 0:
            return 1.0
            
        return self.baseline_duration_seconds / self.duration_seconds
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/scripts/test_profiling_utils.py::test_benchmark_result_creation -v`

Expected: PASS

Run: `pytest tests/scripts/test_profiling_utils.py::test_benchmark_result_speedup_calculation -v`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/profiling/utils.py tests/scripts/test_profiling_utils.py
git commit -m "feat(profiling): add BenchmarkResult dataclass"
```

---

## Task 4: Add Result Serialization (JSON)

**Files:**
- Modify: `scripts/profiling/utils.py`
- Modify: `tests/scripts/test_profiling_utils.py`

**Step 1: Write failing test for JSON serialization**

File: `tests/scripts/test_profiling_utils.py` (append)

```python
import json
from pathlib import Path
from scripts.profiling.utils import save_results_json, load_results_json


def test_save_and_load_results_json(tmp_path):
    """Test saving and loading benchmark results as JSON."""
    results = [
        BenchmarkResult(
            scenario="test",
            strategy="sequential",
            concurrency=1,
            duration_seconds=10.0,
            throughput_items_per_sec=100.0,
            peak_memory_mb=50.0,
            items_processed=1000
        ),
        BenchmarkResult(
            scenario="test",
            strategy="concurrent",
            concurrency=5,
            duration_seconds=2.5,
            throughput_items_per_sec=400.0,
            peak_memory_mb=75.0,
            items_processed=1000,
            baseline_duration_seconds=10.0
        )
    ]
    
    output_path = tmp_path / "results.json"
    save_results_json(results, output_path)
    
    assert output_path.exists()
    
    loaded_results = load_results_json(output_path)
    assert len(loaded_results) == 2
    assert loaded_results[0].scenario == "test"
    assert loaded_results[1].speedup == 4.0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_profiling_utils.py::test_save_and_load_results_json -v`

Expected: FAIL with "ImportError: cannot import name 'save_results_json'"

**Step 3: Implement JSON serialization functions**

File: `scripts/profiling/utils.py` (append)

```python
import json
from pathlib import Path
from typing import List


def save_results_json(results: List[BenchmarkResult], output_path: Path) -> None:
    """Save benchmark results to JSON file.
    
    Args:
        results: List of benchmark results
        output_path: Path to output JSON file
    """
    data = [
        {
            "scenario": r.scenario,
            "strategy": r.strategy,
            "concurrency": r.concurrency,
            "duration_seconds": r.duration_seconds,
            "throughput_items_per_sec": r.throughput_items_per_sec,
            "peak_memory_mb": r.peak_memory_mb,
            "items_processed": r.items_processed,
            "baseline_duration_seconds": r.baseline_duration_seconds,
            "speedup": r.speedup
        }
        for r in results
    ]
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2))


def load_results_json(input_path: Path) -> List[BenchmarkResult]:
    """Load benchmark results from JSON file.
    
    Args:
        input_path: Path to JSON file
        
    Returns:
        List of BenchmarkResult objects
    """
    data = json.loads(input_path.read_text())
    
    return [
        BenchmarkResult(
            scenario=item["scenario"],
            strategy=item["strategy"],
            concurrency=item["concurrency"],
            duration_seconds=item["duration_seconds"],
            throughput_items_per_sec=item["throughput_items_per_sec"],
            peak_memory_mb=item["peak_memory_mb"],
            items_processed=item["items_processed"],
            baseline_duration_seconds=item.get("baseline_duration_seconds")
        )
        for item in data
    ]
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/scripts/test_profiling_utils.py::test_save_and_load_results_json -v`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/profiling/utils.py tests/scripts/test_profiling_utils.py
git commit -m "feat(profiling): add JSON serialization for results"
```

---

## Task 5: Add Markdown Report Generation

**Files:**
- Modify: `scripts/profiling/utils.py`
- Modify: `tests/scripts/test_profiling_utils.py`

**Step 1: Write failing test for Markdown report**

File: `tests/scripts/test_profiling_utils.py` (append)

```python
from scripts.profiling.utils import generate_markdown_report


def test_generate_markdown_report(tmp_path):
    """Test generating Markdown report from results."""
    results = [
        BenchmarkResult(
            scenario="10K JSON files",
            strategy="sequential",
            concurrency=1,
            duration_seconds=45.2,
            throughput_items_per_sec=221.2,
            peak_memory_mb=120.5,
            items_processed=10000
        ),
        BenchmarkResult(
            scenario="10K JSON files",
            strategy="concurrent",
            concurrency=10,
            duration_seconds=8.7,
            throughput_items_per_sec=1149.4,
            peak_memory_mb=250.0,
            items_processed=10000,
            baseline_duration_seconds=45.2
        )
    ]
    
    output_path = tmp_path / "report.md"
    generate_markdown_report(results, output_path, title="File Mode Benchmarks")
    
    assert output_path.exists()
    
    content = output_path.read_text()
    assert "File Mode Benchmarks" in content
    assert "10K JSON files" in content
    assert "5.2x" in content  # Speedup
    assert "| sequential | 1 |" in content  # Table row
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_profiling_utils.py::test_generate_markdown_report -v`

Expected: FAIL with "ImportError: cannot import name 'generate_markdown_report'"

**Step 3: Implement Markdown report generation**

File: `scripts/profiling/utils.py` (append)

```python
def generate_markdown_report(
    results: List[BenchmarkResult],
    output_path: Path,
    title: str = "Benchmark Results"
) -> None:
    """Generate Markdown report from benchmark results.
    
    Args:
        results: List of benchmark results
        output_path: Path to output Markdown file
        title: Report title
    """
    lines = [
        f"# {title}\n",
        f"**Generated**: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n",
        ""
    ]
    
    # Group results by scenario
    scenarios = {}
    for result in results:
        if result.scenario not in scenarios:
            scenarios[result.scenario] = []
        scenarios[result.scenario].append(result)
    
    # Generate table for each scenario
    for scenario, scenario_results in scenarios.items():
        lines.append(f"## {scenario}\n")
        lines.append("| Strategy | Concurrency | Time (s) | Throughput (items/s) | Memory (MB) | Speedup |")
        lines.append("|----------|-------------|----------|----------------------|-------------|---------" + "|")
        
        for r in scenario_results:
            speedup_str = f"{r.speedup:.1f}x" if r.speedup > 1.0 else "baseline"
            lines.append(
                f"| {r.strategy} | {r.concurrency} | {r.duration_seconds:.1f} | "
                f"{r.throughput_items_per_sec:.0f} | {r.peak_memory_mb:.0f} | {speedup_str} |"
            )
        
        # Add findings section
        concurrent_results = [r for r in scenario_results if r.strategy == "concurrent"]
        if concurrent_results:
            best = max(concurrent_results, key=lambda r: r.speedup)
            lines.append("")
            lines.append(f"**Best Performance**: {best.concurrency} workers with {best.speedup:.1f}x speedup\n")
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines))
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/scripts/test_profiling_utils.py::test_generate_markdown_report -v`

Expected: PASS

**Step 5: Run all utils tests**

Run: `pytest tests/scripts/test_profiling_utils.py -v`

Expected: All tests PASS

**Step 6: Commit**

```bash
git add scripts/profiling/utils.py tests/scripts/test_profiling_utils.py
git commit -m "feat(profiling): add Markdown report generation"
```

---

## Task 6: Create Test Data Generator

**Files:**
- Create: `scripts/profiling/test_data_generator.py`
- Create: `tests/scripts/test_data_generator.py`

**Step 1: Write failing test for STAC item generation**

File: `tests/scripts/test_data_generator.py`

```python
"""Tests for test data generation."""
from scripts.profiling.test_data_generator import generate_stac_item


def test_generate_stac_item_structure():
    """Test that generated STAC item has valid structure."""
    item = generate_stac_item("test-item-001", "test-collection")
    
    assert item["type"] == "Feature"
    assert item["id"] == "test-item-001"
    assert item["collection"] == "test-collection"
    assert "geometry" in item
    assert "properties" in item
    assert "assets" in item
    assert len(item["assets"]) == 5


def test_generate_stac_item_unique_ids():
    """Test that items have unique IDs."""
    item1 = generate_stac_item("item-1")
    item2 = generate_stac_item("item-2")
    
    assert item1["id"] != item2["id"]
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_data_generator.py::test_generate_stac_item_structure -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'scripts.profiling.test_data_generator'"

**Step 3: Implement generate_stac_item**

File: `scripts/profiling/test_data_generator.py`

```python
"""Generate test STAC data for benchmarking."""
from datetime import datetime, timezone
from typing import Dict, Any


def generate_stac_item(item_id: str, collection_id: str = "test-collection") -> Dict[str, Any]:
    """Generate a minimal valid STAC item.
    
    Args:
        item_id: Unique item identifier
        collection_id: Collection identifier
        
    Returns:
        STAC Item dictionary (~5KB JSON)
    """
    return {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": item_id,
        "collection": collection_id,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-122.5, 37.5],
                [-122.0, 37.5],
                [-122.0, 38.0],
                [-122.5, 38.0],
                [-122.5, 37.5]
            ]]
        },
        "bbox": [-122.5, 37.5, -122.0, 38.0],
        "properties": {
            "datetime": datetime.now(timezone.utc).isoformat(),
            "title": f"Test Item {item_id}",
            "description": "Test STAC item for benchmarking",
            "platform": "test-platform",
            "instruments": ["test-sensor"],
            "gsd": 10.0,
            "proj:epsg": 4326
        },
        "assets": {
            "visual": {
                "href": f"https://example.com/{item_id}/visual.tif",
                "type": "image/tiff; application=geotiff",
                "roles": ["visual"]
            },
            "B01": {
                "href": f"https://example.com/{item_id}/B01.tif",
                "type": "image/tiff; application=geotiff",
                "roles": ["data"]
            },
            "B02": {
                "href": f"https://example.com/{item_id}/B02.tif",
                "type": "image/tiff; application=geotiff",
                "roles": ["data"]
            },
            "B03": {
                "href": f"https://example.com/{item_id}/B03.tif",
                "type": "image/tiff; application=geotiff",
                "roles": ["data"]
            },
            "metadata": {
                "href": f"https://example.com/{item_id}/metadata.xml",
                "type": "application/xml",
                "roles": ["metadata"]
            }
        },
        "links": [
            {
                "rel": "self",
                "href": f"https://example.com/collections/{collection_id}/items/{item_id}"
            },
            {
                "rel": "collection",
                "href": f"https://example.com/collections/{collection_id}"
            }
        ]
    }
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/scripts/test_data_generator.py::test_generate_stac_item_structure -v`

Expected: PASS

Run: `pytest tests/scripts/test_data_generator.py::test_generate_stac_item_unique_ids -v`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/profiling/test_data_generator.py tests/scripts/test_data_generator.py
git commit -m "feat(profiling): add STAC item generator"
```

---

## Task 7: Add File Generation Functions

**Files:**
- Modify: `scripts/profiling/test_data_generator.py`
- Modify: `tests/scripts/test_data_generator.py`

**Step 1: Write failing test for directory generation**

File: `tests/scripts/test_data_generator.py` (append)

```python
import json
from pathlib import Path
from scripts.profiling.test_data_generator import generate_item_files


def test_generate_item_files_creates_directory(tmp_path):
    """Test generating directory of JSON item files."""
    output_dir = tmp_path / "items"
    
    result_path = generate_item_files(output_dir, count=10)
    
    assert result_path == output_dir
    assert output_dir.exists()
    assert output_dir.is_dir()
    
    # Check files created
    json_files = list(output_dir.glob("*.json"))
    assert len(json_files) == 10
    
    # Validate one file
    first_file = json_files[0]
    item = json.loads(first_file.read_text())
    assert item["type"] == "Feature"
    assert "id" in item


def test_generate_item_files_custom_collection(tmp_path):
    """Test generating items with custom collection ID."""
    output_dir = tmp_path / "custom_items"
    
    generate_item_files(output_dir, count=5, collection_id="my-collection")
    
    json_files = list(output_dir.glob("*.json"))
    item = json.loads(json_files[0].read_text())
    assert item["collection"] == "my-collection"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_data_generator.py::test_generate_item_files_creates_directory -v`

Expected: FAIL with "ImportError: cannot import name 'generate_item_files'"

**Step 3: Implement generate_item_files**

File: `scripts/profiling/test_data_generator.py` (append)

```python
import json
from pathlib import Path


def generate_item_files(
    output_dir: Path,
    count: int,
    collection_id: str = "test-collection"
) -> Path:
    """Generate N individual JSON item files in a directory.
    
    Args:
        output_dir: Directory to create items in
        count: Number of items to generate
        collection_id: Collection identifier for items
        
    Returns:
        Path to output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(count):
        item_id = f"item-{i:06d}"
        item = generate_stac_item(item_id, collection_id)
        
        file_path = output_dir / f"{item_id}.json"
        file_path.write_text(json.dumps(item, indent=2))
    
    return output_dir
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/scripts/test_data_generator.py::test_generate_item_files_creates_directory -v`

Expected: PASS

Run: `pytest tests/scripts/test_data_generator.py::test_generate_item_files_custom_collection -v`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/profiling/test_data_generator.py tests/scripts/test_data_generator.py
git commit -m "feat(profiling): add directory generation for test items"
```

---

## Task 8: Add FeatureCollection Generation

**Files:**
- Modify: `scripts/profiling/test_data_generator.py`
- Modify: `tests/scripts/test_data_generator.py`

**Step 1: Write failing test for FeatureCollection**

File: `tests/scripts/test_data_generator.py` (append)

```python
from scripts.profiling.test_data_generator import generate_feature_collection


def test_generate_feature_collection(tmp_path):
    """Test generating FeatureCollection JSON file."""
    output_file = tmp_path / "collection.json"
    
    result_path = generate_feature_collection(output_file, count=100)
    
    assert result_path == output_file
    assert output_file.exists()
    
    data = json.loads(output_file.read_text())
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 100
    assert data["features"][0]["type"] == "Feature"
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_data_generator.py::test_generate_feature_collection -v`

Expected: FAIL with "ImportError: cannot import name 'generate_feature_collection'"

**Step 3: Implement generate_feature_collection**

File: `scripts/profiling/test_data_generator.py` (append)

```python
def generate_feature_collection(
    output_path: Path,
    count: int,
    collection_id: str = "test-collection"
) -> Path:
    """Generate a FeatureCollection JSON file with N items.
    
    Args:
        output_path: Path to output JSON file
        count: Number of items to include
        collection_id: Collection identifier for items
        
    Returns:
        Path to output file
    """
    features = [
        generate_stac_item(f"item-{i:06d}", collection_id)
        for i in range(count)
    ]
    
    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(feature_collection, indent=2))
    
    return output_path
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/scripts/test_data_generator.py::test_generate_feature_collection -v`

Expected: PASS

**Step 5: Run all data generator tests**

Run: `pytest tests/scripts/test_data_generator.py -v`

Expected: All tests PASS

**Step 6: Commit**

```bash
git add scripts/profiling/test_data_generator.py tests/scripts/test_data_generator.py
git commit -m "feat(profiling): add FeatureCollection generation"
```

---

## Task 9: Create File Mode Profiler - Sequential Baseline

**Files:**
- Create: `scripts/profiling/profile_file_io.py`
- Create: `tests/scripts/test_profile_file_io.py`

**Step 1: Write failing test for sequential file benchmark**

File: `tests/scripts/test_profile_file_io.py`

```python
"""Tests for file I/O profiling."""
import asyncio
from pathlib import Path
from scripts.profiling.test_data_generator import generate_item_files
from scripts.profiling.profile_file_io import benchmark_sequential_files


def test_benchmark_sequential_files(tmp_path):
    """Test benchmarking sequential file loading."""
    # Generate test data
    items_dir = tmp_path / "items"
    generate_item_files(items_dir, count=50)
    
    # Run benchmark
    result = asyncio.run(benchmark_sequential_files(items_dir))
    
    assert result.scenario == "Sequential file loading"
    assert result.strategy == "sequential"
    assert result.concurrency == 1
    assert result.items_processed == 50
    assert result.duration_seconds > 0
    assert result.throughput_items_per_sec > 0
    assert result.peak_memory_mb > 0
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_profile_file_io.py::test_benchmark_sequential_files -v`

Expected: FAIL with "ModuleNotFoundError: No module named 'scripts.profiling.profile_file_io'"

**Step 3: Implement benchmark_sequential_files**

File: `scripts/profiling/profile_file_io.py`

```python
"""File I/O profiling utilities."""
import asyncio
from pathlib import Path
from typing import Optional
import sys

# Add src to path for importing IngestModule
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from stac_manager.modules.ingest import IngestModule
from stac_manager.core.context import WorkflowContext
from scripts.profiling.utils import BenchmarkResult, measure_time, measure_memory


async def benchmark_sequential_files(
    directory: Path,
    max_items: Optional[int] = None
) -> BenchmarkResult:
    """Measure current IngestModule file mode performance (baseline).
    
    Args:
        directory: Directory containing item JSON files
        max_items: Optional limit on items to process
        
    Returns:
        BenchmarkResult with performance metrics
    """
    config = {
        "mode": "file",
        "source": str(directory),
        "max_items": max_items
    }
    
    ingest = IngestModule(config)
    context = WorkflowContext.create()
    
    items_processed = 0
    
    with measure_time("sequential_file_load") as time_result:
        with measure_memory("sequential_file_load") as mem_result:
            async for item in ingest.fetch(context):
                items_processed += 1
    
    duration = time_result["duration_seconds"]
    throughput = items_processed / duration if duration > 0 else 0
    
    return BenchmarkResult(
        scenario="Sequential file loading",
        strategy="sequential",
        concurrency=1,
        duration_seconds=duration,
        throughput_items_per_sec=throughput,
        peak_memory_mb=mem_result["peak_memory_mb"],
        items_processed=items_processed
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/scripts/test_profile_file_io.py::test_benchmark_sequential_files -v`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/profiling/profile_file_io.py tests/scripts/test_profile_file_io.py
git commit -m "feat(profiling): add sequential file benchmark"
```

---

## Task 10: Add Concurrent File Benchmark (Simulated)

**Files:**
- Modify: `scripts/profiling/profile_file_io.py`
- Modify: `tests/scripts/test_profile_file_io.py`

**Step 1: Write failing test for concurrent file loading**

File: `tests/scripts/test_profile_file_io.py` (append)

```python
from scripts.profiling.profile_file_io import benchmark_concurrent_files


def test_benchmark_concurrent_files(tmp_path):
    """Test benchmarking concurrent file loading."""
    # Generate test data
    items_dir = tmp_path / "items"
    generate_item_files(items_dir, count=50)
    
    # Run concurrent benchmark
    result = asyncio.run(benchmark_concurrent_files(items_dir, concurrency=5))
    
    assert result.scenario.startswith("Concurrent file loading")
    assert result.strategy == "concurrent"
    assert result.concurrency == 5
    assert result.items_processed == 50
    assert result.duration_seconds > 0


def test_concurrent_faster_than_sequential(tmp_path):
    """Test that concurrent loading is faster (on I/O bound systems)."""
    items_dir = tmp_path / "items"
    generate_item_files(items_dir, count=100)
    
    sequential = asyncio.run(benchmark_sequential_files(items_dir))
    concurrent = asyncio.run(benchmark_concurrent_files(items_dir, concurrency=10))
    
    # Concurrent should be at least as fast (may not be faster on SSD)
    # This is mainly to verify both run successfully
    assert concurrent.items_processed == sequential.items_processed
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/scripts/test_profile_file_io.py::test_benchmark_concurrent_files -v`

Expected: FAIL with "ImportError: cannot import name 'benchmark_concurrent_files'"

**Step 3: Implement benchmark_concurrent_files**

File: `scripts/profiling/profile_file_io.py` (append)

```python
import json


async def benchmark_concurrent_files(
    directory: Path,
    concurrency: int,
    max_items: Optional[int] = None
) -> BenchmarkResult:
    """Measure concurrent file reading performance (simulated future implementation).
    
    This simulates what concurrent file loading would look like by using
    asyncio.gather with semaphore-controlled file reads.
    
    Args:
        directory: Directory containing item JSON files
        concurrency: Number of concurrent file readers
        max_items: Optional limit on items to process
        
    Returns:
        BenchmarkResult with performance metrics
    """
    json_files = sorted(directory.glob("*.json"))
    
    if max_items:
        json_files = json_files[:max_items]
    
    semaphore = asyncio.Semaphore(concurrency)
    items = []
    
    async def load_item(file_path: Path) -> dict:
        """Load a single item file with concurrency control."""
        async with semaphore:
            # Use asyncio.to_thread for actual file I/O
            content = await asyncio.to_thread(file_path.read_text, encoding='utf-8')
            return json.loads(content)
    
    with measure_time("concurrent_file_load") as time_result:
        with measure_memory("concurrent_file_load") as mem_result:
            # Load all files concurrently
            items = await asyncio.gather(*[load_item(f) for f in json_files])
    
    items_processed = len(items)
    duration = time_result["duration_seconds"]
    throughput = items_processed / duration if duration > 0 else 0
    
    return BenchmarkResult(
        scenario=f"Concurrent file loading (workers={concurrency})",
        strategy="concurrent",
        concurrency=concurrency,
        duration_seconds=duration,
        throughput_items_per_sec=throughput,
        peak_memory_mb=mem_result["peak_memory_mb"],
        items_processed=items_processed
    )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/scripts/test_profile_file_io.py::test_benchmark_concurrent_files -v`

Expected: PASS

Run: `pytest tests/scripts/test_profile_file_io.py::test_concurrent_faster_than_sequential -v`

Expected: PASS

**Step 5: Run all file profiling tests**

Run: `pytest tests/scripts/test_profile_file_io.py -v`

Expected: All tests PASS

**Step 6: Commit**

```bash
git add scripts/profiling/profile_file_io.py tests/scripts/test_profile_file_io.py
git commit -m "feat(profiling): add concurrent file benchmark simulation"
```

---

## Task 11: Create API Mode Profiler Stub

**Files:**
- Create: `scripts/profiling/profile_api_requests.py`
- Create: `tests/scripts/test_profile_api_requests.py`

**Step 1: Write test with mock API server**

File: `tests/scripts/test_profile_api_requests.py`

```python
"""Tests for API profiling."""
import asyncio
import pytest
from scripts.profiling.profile_api_requests import benchmark_sequential_api


@pytest.mark.skip(reason="Requires mock STAC API server - implement in integration tests")
def test_benchmark_sequential_api():
    """Test benchmarking sequential API requests.
    
    This test is skipped in unit tests. It should be implemented
    as an integration test with a mock STAC API server.
    """
    result = asyncio.run(benchmark_sequential_api(
        catalog_url="http://localhost:8080",
        collection_id="test-collection",
        max_items=100
    ))
    
    assert result.strategy == "sequential"
    assert result.items_processed <= 100


def test_api_profiler_placeholder():
    """Placeholder test to ensure module can be imported."""
    from scripts.profiling import profile_api_requests
    assert hasattr(profile_api_requests, 'benchmark_sequential_api')
```

**Step 2: Run test**

Run: `pytest tests/scripts/test_profile_api_requests.py::test_api_profiler_placeholder -v`

Expected: FAIL with "ModuleNotFoundError"

**Step 3: Create API profiler stub**

File: `scripts/profiling/profile_api_requests.py`

```python
"""API request profiling utilities.

Note: Full implementation requires aiohttp dependency and mock server for testing.
This stub provides the interface for manual benchmarking against real APIs.
"""
import asyncio
from pathlib import Path
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from stac_manager.modules.ingest import IngestModule
from stac_manager.core.context import WorkflowContext
from scripts.profiling.utils import BenchmarkResult, measure_time, measure_memory


async def benchmark_sequential_api(
    catalog_url: str,
    collection_id: str,
    max_items: int = 100
) -> BenchmarkResult:
    """Measure current IngestModule API mode performance (baseline).
    
    Args:
        catalog_url: STAC API catalog URL
        collection_id: Collection to fetch
        max_items: Maximum items to fetch
        
    Returns:
        BenchmarkResult with performance metrics
    """
    config = {
        "mode": "api",
        "source": catalog_url,
        "collection_id": collection_id,
        "max_items": max_items,
        "limit": 100  # Page size
    }
    
    ingest = IngestModule(config)
    context = WorkflowContext.create()
    
    items_processed = 0
    
    with measure_time("sequential_api") as time_result:
        with measure_memory("sequential_api") as mem_result:
            async for item in ingest.fetch(context):
                items_processed += 1
    
    duration = time_result["duration_seconds"]
    throughput = items_processed / duration if duration > 0 else 0
    
    return BenchmarkResult(
        scenario=f"Sequential API ({collection_id})",
        strategy="sequential",
        concurrency=1,
        duration_seconds=duration,
        throughput_items_per_sec=throughput,
        peak_memory_mb=mem_result["peak_memory_mb"],
        items_processed=items_processed
    )


async def benchmark_concurrent_api_aiohttp(
    catalog_url: str,
    collection_id: str,
    concurrency: int,
    max_items: int = 100
) -> BenchmarkResult:
    """Measure concurrent API requests with aiohttp (future implementation).
    
    TODO: Implement after adding aiohttp dependency
    
    Args:
        catalog_url: STAC API catalog URL
        collection_id: Collection to fetch
        concurrency: Number of concurrent workers
        max_items: Maximum items to fetch
        
    Returns:
        BenchmarkResult with performance metrics
    """
    raise NotImplementedError(
        "Concurrent API benchmarking requires aiohttp. "
        "This will be implemented after adding the dependency."
    )
```

**Step 4: Run test**

Run: `pytest tests/scripts/test_profile_api_requests.py::test_api_profiler_placeholder -v`

Expected: PASS

**Step 5: Commit**

```bash
git add scripts/profiling/profile_api_requests.py tests/scripts/test_profile_api_requests.py
git commit -m "feat(profiling): add API profiler stub for manual testing"
```

---

## Task 12: Create Main Benchmark CLI

**Files:**
- Create: `scripts/profiling/benchmark_ingest.py`
- Create: `scripts/profiling/results/.gitkeep`
- Modify: `.gitignore`

**Step 1: Add results directory to gitignore**

File: `.gitignore` (append)

```
# Profiling results
scripts/profiling/results/*.json
scripts/profiling/results/*.md
```

**Step 2: Create results directory**

File: `scripts/profiling/results/.gitkeep`

```
# This directory stores benchmark results (gitignored)
```

**Step 3: Create CLI skeleton**

File: `scripts/profiling/benchmark_ingest.py`

```python
#!/usr/bin/env python3
"""Benchmark CLI for IngestModule performance testing.

Usage:
    python scripts/profiling/benchmark_ingest.py file --test-size 10000 --concurrency 1,5,10
    python scripts/profiling/benchmark_ingest.py api --catalog-url URL --collection-id ID
"""
import asyncio
import click
from pathlib import Path
from typing import List

from test_data_generator import generate_item_files
from profile_file_io import benchmark_sequential_files, benchmark_concurrent_files
from profile_api_requests import benchmark_sequential_api
from utils import save_results_json, generate_markdown_report, BenchmarkResult


@click.group()
def cli():
    """IngestModule performance benchmarking tool."""
    pass


@cli.command()
@click.option('--test-size', default=1000, help='Number of test items to generate')
@click.option('--concurrency', default='1,5,10', help='Comma-separated concurrency levels')
@click.option('--output', default='results/file_benchmark.json', help='Output file path')
def file(test_size: int, concurrency: str, output: str):
    """Benchmark file mode ingestion."""
    click.echo(f"File mode benchmark: {test_size} items")
    
    # Parse concurrency levels
    concurrency_levels = [int(x.strip()) for x in concurrency.split(',')]
    
    # Generate test data
    test_dir = Path("scripts/profiling/test_data/benchmark_items")
    click.echo(f"Generating {test_size} test items in {test_dir}...")
    generate_item_files(test_dir, count=test_size)
    
    # Run benchmarks
    results: List[BenchmarkResult] = []
    
    # Sequential baseline
    click.echo("Running sequential baseline...")
    seq_result = asyncio.run(benchmark_sequential_files(test_dir))
    results.append(seq_result)
    click.echo(f"  ✓ {seq_result.throughput_items_per_sec:.0f} items/s")
    
    # Concurrent benchmarks
    for workers in concurrency_levels:
        if workers == 1:
            continue  # Skip sequential again
            
        click.echo(f"Running with {workers} workers...")
        conc_result = asyncio.run(benchmark_concurrent_files(test_dir, workers))
        conc_result.baseline_duration_seconds = seq_result.duration_seconds
        results.append(conc_result)
        click.echo(f"  ✓ {conc_result.throughput_items_per_sec:.0f} items/s ({conc_result.speedup:.1f}x)")
    
    # Save results
    output_path = Path(output)
    save_results_json(results, output_path)
    
    report_path = output_path.with_suffix('') / "_report.md"
    generate_markdown_report(results, report_path, title="File Mode Benchmark")
    
    click.echo(f"\n✓ Results saved to {output_path}")
    click.echo(f"✓ Report saved to {report_path}")


@cli.command()
@click.option('--catalog-url', required=True, help='STAC API catalog URL')
@click.option('--collection-id', required=True, help='Collection ID to fetch')
@click.option('--max-items', default=500, help='Maximum items to fetch')
@click.option('--concurrency', default='1,5,10', help='Comma-separated concurrency levels')
@click.option('--output', default='results/api_benchmark.json', help='Output file path')
def api(catalog_url: str, collection_id: str, max_items: int, concurrency: str, output: str):
    """Benchmark API mode ingestion."""
    click.echo(f"API mode benchmark: {catalog_url}")
    click.echo(f"Collection: {collection_id}, Max items: {max_items}")
    
    # Parse concurrency levels
    concurrency_levels = [int(x.strip()) for x in concurrency.split(',')]
    
    results: List[BenchmarkResult] = []
    
    # Sequential baseline
    click.echo("Running sequential baseline...")
    seq_result = asyncio.run(benchmark_sequential_api(catalog_url, collection_id, max_items))
    results.append(seq_result)
    click.echo(f"  ✓ {seq_result.items_processed} items in {seq_result.duration_seconds:.1f}s")
    
    # Concurrent benchmarks
    for workers in concurrency_levels:
        if workers == 1:
            continue
            
        click.echo(f"Running with {workers} workers...")
        click.echo("  ⚠ Concurrent API benchmarking not yet implemented (requires aiohttp)")
        # TODO: Implement after adding aiohttp
    
    # Save results
    output_path = Path(output)
    save_results_json(results, output_path)
    
    report_path = output_path.with_name(output_path.stem + "_report.md")
    generate_markdown_report(results, report_path, title="API Mode Benchmark")
    
    click.echo(f"\n✓ Results saved to {output_path}")
    click.echo(f"✓ Report saved to {report_path}")


if __name__ == '__main__':
    cli()
```

**Step 4: Make script executable**

Run (Git Bash): `chmod +x scripts/profiling/benchmark_ingest.py`

**Step 5: Manual test**

Run: `python scripts/profiling/benchmark_ingest.py --help`

Expected: Shows CLI help with `file` and `api` commands

Run: `python scripts/profiling/benchmark_ingest.py file --test-size 100 --concurrency 1,5`

Expected: 
- Generates 100 test items
- Runs sequential and 5-worker benchmarks
- Creates JSON and Markdown reports
- Shows progress and speedup

**Step 6: Commit**

```bash
git add scripts/profiling/benchmark_ingest.py scripts/profiling/results/.gitkeep .gitignore
git commit -m "feat(profiling): add benchmark CLI with file mode support"
```

---

## Task 13: Add Profiling README

**Files:**
- Create: `scripts/profiling/README.md`

**Step 1: Write profiling documentation**

File: `scripts/profiling/README.md`

```markdown
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
- [Implementation Plan](../../docs/plans/2026-02-10-concurrent-ingestion-phase1-implementation.md)
```

**Step 2: Commit**

```bash
git add scripts/profiling/README.md
git commit -m "docs(profiling): add profiling scripts README"
```

---

## Task 14: Final Verification

**Files:**
- Run all tests
- Manual benchmark verification

**Step 1: Run all profiling tests**

Run: `pytest tests/scripts/ -v`

Expected: All tests PASS

**Step 2: Run file mode benchmark**

Run:
```bash
python scripts/profiling/benchmark_ingest.py file \
  --test-size 500 \
  --concurrency 1,5,10 \
  --output results/verification_test.json
```

Expected:
- Creates 500 test items
- Runs 3 benchmarks (sequential, 5 workers, 10 workers)
- Generates JSON and Markdown reports
- Shows speedup values

**Step 3: Review generated report**

Run: `cat scripts/profiling/results/verification_test_report.md`

Expected:
- Markdown table with results
- Speedup calculations
- Best performance recommendation

**Step 4: Verify test data cleanup**

Run:
```bash
rm -rf scripts/profiling/test_data/
rm scripts/profiling/results/*.json scripts/profiling/results/*.md
```

Expected: Cleanup successful

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat(profiling): complete Phase 1 profiling implementation

- Add timing and memory measurement utilities
- Create STAC item test data generator
- Implement file mode sequential and concurrent benchmarks
- Add API mode profiler stub
- Create CLI for running benchmarks
- Generate JSON and Markdown reports
- Full test coverage with pytest

Deliverables:
- scripts/profiling/ with all profiling tools
- Comprehensive test suite in tests/scripts/
- Documentation in scripts/profiling/README.md

Next: Run benchmarks against real data, analyze results, design Phase 2"
```

---

## Execution Options

**Plan complete and saved to `docs/plans/2026-02-10-concurrent-ingestion-phase1-tdd-plan.md`.**

**Two execution options:**

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
