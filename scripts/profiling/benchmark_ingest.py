#!/usr/bin/env python3
"""Benchmark CLI for IngestModule performance testing.

Usage:
    python scripts/profiling/benchmark_ingest.py file --test-size 10000 --concurrency 1,5,10
    python scripts/profiling/benchmark_ingest.py api --catalog-url URL --collection-id ID
"""
import asyncio
import sys
import click
from pathlib import Path
from typing import List

# Add scripts/profiling to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from test_data_generator import generate_item_files
from profile_file_io import benchmark_sequential_files, benchmark_concurrent_files
from profile_api_requests import benchmark_sequential_api
from utils import save_results_json, generate_markdown_report, BenchmarkResult


@click.group()
def cli():
    """IngestModule performance benchmarking tool."""
    pass


@cli.command()
@click.option('--test-size', default=1000, help='Number of test items to generate')
@click.option('--concurrency', default='1,5,10', help='Comma-separated concurrency levels')
@click.option('--output', default='results/file_benchmark.json', help='Output file path')
def file(test_size: int, concurrency: str, output: str):
    """Benchmark file mode ingestion."""
    click.echo(f"File mode benchmark: {test_size} items")
    
    # Parse concurrency levels
    concurrency_levels = [int(x.strip()) for x in concurrency.split(',')]
    
    # Generate test data
    test_dir = Path("scripts/profiling/test_data/benchmark_items")
    click.echo(f"Generating {test_size} test items in {test_dir}...")
    generate_item_files(test_dir, count=test_size)
    
    # Run benchmarks
    results: List[BenchmarkResult] = []
    
    # Sequential baseline
    click.echo("Running sequential baseline...")
    seq_result = asyncio.run(benchmark_sequential_files(test_dir))
    results.append(seq_result)
    click.echo(f"  ✓ {seq_result.throughput_items_per_sec:.0f} items/s")
    
    # Concurrent benchmarks
    for workers in concurrency_levels:
        if workers == 1:
            continue  # Skip sequential again
            
        click.echo(f"Running with {workers} workers...")
        conc_result = asyncio.run(benchmark_concurrent_files(test_dir, workers))
        conc_result.baseline_duration_seconds = seq_result.duration_seconds
        results.append(conc_result)
        click.echo(f"  ✓ {conc_result.throughput_items_per_sec:.0f} items/s ({conc_result.speedup:.1f}x)")
    
    # Save results
    output_path = Path(output)
    save_results_json(results, output_path)
    
    report_path = output_path.with_name(output_path.stem + "_report.md")
    generate_markdown_report(results, report_path, title="File Mode Benchmark")
    
    click.echo(f"\n✓ Results saved to {output_path}")
    click.echo(f"✓ Report saved to {report_path}")


@cli.command()
@click.option('--catalog-url', required=True, help='STAC API catalog URL')
@click.option('--collection-id', required=True, help='Collection ID to fetch')
@click.option('--max-items', default=500, help='Maximum items to fetch')
@click.option('--concurrency', default='1,5,10', help='Comma-separated concurrency levels')
@click.option('--output', default='results/api_benchmark.json', help='Output file path')
def api(catalog_url: str, collection_id: str, max_items: int, concurrency: str, output: str):
    """Benchmark API mode ingestion."""
    click.echo(f"API mode benchmark: {catalog_url}")
    click.echo(f"Collection: {collection_id}, Max items: {max_items}")
    
    # Parse concurrency levels
    concurrency_levels = [int(x.strip()) for x in concurrency.split(',')]
    
    results: List[BenchmarkResult] = []
    
    # Sequential baseline
    click.echo("Running sequential baseline...")
    seq_result = asyncio.run(benchmark_sequential_api(catalog_url, collection_id, max_items))
    results.append(seq_result)
    click.echo(f"  ✓ {seq_result.items_processed} items in {seq_result.duration_seconds:.1f}s")
    
    # Concurrent benchmarks
    for workers in concurrency_levels:
        if workers == 1:
            continue
            
        click.echo(f"Running with {workers} workers...")
        click.echo("  ⚠ Concurrent API benchmarking not yet implemented (requires aiohttp)")
        # TODO: Implement after adding aiohttp
    
    # Save results
    output_path = Path(output)
    save_results_json(results, output_path)
    
    report_path = output_path.with_name(output_path.stem + "_report.md")
    generate_markdown_report(results, report_path, title="API Mode Benchmark")
    
    click.echo(f"\n✓ Results saved to {output_path}")
    click.echo(f"✓ Report saved to {report_path}")


if __name__ == '__main__':
    cli()
