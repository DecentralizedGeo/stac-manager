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
