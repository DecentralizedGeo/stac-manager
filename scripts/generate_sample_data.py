"""Generate sample STAC data for tutorials and documentation.

This script fetches real STAC items from public catalogs, converts them to
multiple formats (JSON, Parquet), and generates sidecar data for tutorials.
"""
import click
from pathlib import Path


@click.command(name='generate-sample-data')
@click.option(
    '--collection',
    required=True,
    help='Collection ID to fetch (e.g., sentinel-2-l2a)'
)
@click.option(
    '--items',
    default=20,
    type=int,
    help='Number of items to fetch (default: 20)'
)
@click.option(
    '--output-dir',
    default='samples',
    type=click.Path(),
    help='Output directory for samples (default: samples/)'
)
def cli(collection: str, items: int, output_dir: str):
    """Generate sample STAC data for documentation and tutorials."""
    click.echo(f"Generating {items} items for collection: {collection}")
    click.echo(f"Output directory: {output_dir}")


if __name__ == '__main__':
    cli()
