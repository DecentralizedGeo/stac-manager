"""File I/O profiling utilities."""
import asyncio
import json
from pathlib import Path
from typing import Optional
import sys

# Add src and tests to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "tests"))

from stac_manager.modules.ingest import IngestModule
from tests.fixtures.context import MockWorkflowContext
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
    context = MockWorkflowContext.create()
    
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
