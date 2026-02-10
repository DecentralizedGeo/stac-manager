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

# Support both direct execution and pytest imports
try:
    from .utils import BenchmarkResult, measure_time, measure_memory, create_benchmark_context
except ImportError:
    from utils import BenchmarkResult, measure_time, measure_memory, create_benchmark_context


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
    context = create_benchmark_context()
    
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
