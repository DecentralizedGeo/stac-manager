"""Tests for profiling utilities."""
import time
import pytest
from scripts.profiling.utils import measure_time, measure_memory


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
