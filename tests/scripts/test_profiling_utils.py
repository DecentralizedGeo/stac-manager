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
