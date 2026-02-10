"""Profiling utilities for measuring performance."""
import time
import tracemalloc
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
        "timestamp": datetime.now(datetime.UTC).isoformat(),
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
