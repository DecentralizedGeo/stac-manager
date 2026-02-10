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
        "timestamp": datetime.now(datetime.UTC).isoformat(),
        "duration_seconds": 0.0
    }
    
    start = time.perf_counter()
    try:
        yield result
    finally:
        end = time.perf_counter()
        result["duration_seconds"] = end - start
