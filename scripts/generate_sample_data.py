"""Generate sample STAC data for tutorials and documentation.

This script fetches real STAC items from public catalogs, converts them to
multiple formats (JSON, Parquet), and generates sidecar data for tutorials.
"""
import logging
from typing import Dict, List, Optional

import click
from pathlib import Path
from pystac_client import Client

logger = logging.getLogger(__name__)


def fetch_stac_items(
    catalog_url: str,
    collection_id: str,
    max_items: int,
    bbox: Optional[List[float]] = None,
    datetime: Optional[str] = None
) -> List[Dict]:
    """Fetch STAC items from a catalog.
    
    Args:
        catalog_url: STAC API root URL
        collection_id: Collection to fetch from
        max_items: Maximum number of items to return
        bbox: Optional bounding box [west, south, east, north]
        datetime: Optional datetime filter (ISO8601)
        
    Returns:
        List of STAC item dictionaries
    """
    logger.info(f"Fetching {max_items} items from {collection_id}")
    
    client = Client.open(catalog_url)
    
    search_params = {
        "collections": [collection_id],
        "max_items": max_items
    }
    
    if bbox:
        search_params["bbox"] = bbox
    if datetime:
        search_params["datetime"] = datetime
    
    search = client.search(**search_params)
    items = [item.to_dict() for item in search.items()]
    
    logger.info(f"Fetched {len(items)} items")
    return items


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

