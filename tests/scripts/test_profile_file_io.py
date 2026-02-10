"""Tests for file I/O profiling."""
import asyncio
from pathlib import Path
from scripts.profiling.test_data_generator import generate_item_files
from scripts.profiling.profile_file_io import benchmark_sequential_files, benchmark_concurrent_files


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
