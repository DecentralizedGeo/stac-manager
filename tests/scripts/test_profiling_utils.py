"""Tests for profiling utilities."""
import time
import json
import pytest
from pathlib import Path
from scripts.profiling.utils import measure_time, measure_memory, BenchmarkResult, save_results_json, load_results_json, generate_markdown_report


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
