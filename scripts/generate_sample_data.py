"""Generate sample STAC data for tutorials and documentation.

This script fetches real STAC items from public catalogs, converts them to
multiple formats (JSON, Parquet), and generates sidecar data for tutorials.
"""
import csv
import json
import logging
from typing import Dict, List, Optional

import click
import pyarrow.parquet as pq
import stac_geoparquet
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


def save_items_as_json(items: List[Dict], output_path: Path) -> None:
    """Save STAC items to JSON file.
    
    Args:
        items: List of STAC item dictionaries
        output_path: Path to output JSON file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(items, f, indent=2)
    
    logger.info(f"Saved {len(items)} items to {output_path}")


def convert_to_parquet(json_path: Path, parquet_path: Path) -> None:
    """Convert JSON STAC items to Parquet format.
    
    Args:
        json_path: Path to input JSON file
        parquet_path: Path to output Parquet file
    """
    with open(json_path) as f:
        items = json.load(f)
    
    # Use stac-geoparquet for conversion to GeoDataFrame, then to Parquet
    gdf = stac_geoparquet.to_geodataframe(items)
    
    parquet_path.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(parquet_path)
    
    logger.info(f"Converted {len(items)} items to Parquet: {parquet_path}")


def extract_collection_metadata(catalog_url: str, collection_id: str) -> Dict:
    """Extract minimal collection metadata from catalog.
    
    Args:
        catalog_url: STAC API root URL
        collection_id: Collection ID
        
    Returns:
        Filtered collection dictionary
    """
    client = Client.open(catalog_url)
    collection = client.get_collection(collection_id)
    full_metadata = collection.to_dict()
    
    # Keep only essential fields
    essential_fields = ["id", "description", "extent", "license", "stac_version", "type"]
    filtered = {k: v for k, v in full_metadata.items() if k in essential_fields}
    
    logger.info(f"Extracted collection metadata for {collection_id}")
    return filtered


def generate_sidecar_data(items: List[Dict]) -> Dict[str, Dict]:
    """Generate sidecar data from STAC items.
    
    Extracts cloud cover and snow cover properties for use in tutorials.
    
    Args:
        items: List of STAC item dictionaries
        
    Returns:
        Dictionary mapping item_id to properties
    """
    sidecar = {}
    
    for item in items:
        item_id = item["id"]
        props = item.get("properties", {})
        
        sidecar[item_id] = {
            "cloud_cover": props.get("eo:cloud_cover", 0.0),
            "snow_cover": props.get("s2:snow_ice_percentage", 0.0)
        }
    
    logger.info(f"Generated sidecar data for {len(sidecar)} items")
    return sidecar


def save_sidecar_formats(sidecar_data: Dict[str, Dict], json_path: Path, csv_path: Path) -> None:
    """Save sidecar data in both JSON and CSV formats.
    
    Args:
        sidecar_data: Dictionary of item_id -> properties
        json_path: Path to output JSON file
        csv_path: Path to output CSV file
    """
    # Save JSON (dict format)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, 'w') as f:
        json.dump(sidecar_data, f, indent=2)
    
    # Save CSV (flat format)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with open(csv_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["item_id", "cloud_cover", "snow_cover"])
        writer.writeheader()
        
        for item_id, props in sidecar_data.items():
            writer.writerow({
                "item_id": item_id,
                "cloud_cover": props["cloud_cover"],
                "snow_cover": props["snow_cover"]
            })
    
    logger.info(f"Saved sidecar data to {json_path} and {csv_path}")


@click.command(name='generate-sample-data')
@click.option(
    '--catalog-url',
    default='https://planetarycomputer.microsoft.com/api/stac/v1',
    type=str,
    help='STAC catalog URL (default: Planetary Computer)'
)
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
def cli(catalog_url: str, collection: str, items: int, output_dir: str):
    """Generate sample STAC data for documentation and tutorials."""
    click.echo(f"Generating {items} items for collection: {collection}")
    click.echo(f"Catalog: {catalog_url}")
    click.echo(f"Output directory: {output_dir}")


if __name__ == '__main__':
    cli()
