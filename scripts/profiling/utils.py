"""Profiling utilities for measuring performance."""
import time
import json
import tracemalloc
from contextlib import contextmanager
from typing import Iterator, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path


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
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_seconds": 0.0
    }
    
    start = time.perf_counter()
    try:
        yield result
    finally:
        end = time.perf_counter()
        result["duration_seconds"] = end - start


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
        f"**Generated**: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n",
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
        lines.append("|----------|-------------|----------|----------------------|-------------|---------|")
        
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
