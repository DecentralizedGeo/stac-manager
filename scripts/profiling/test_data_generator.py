"""Generate test STAC data for benchmarking."""
import json
from datetime import datetime, timezone
from typing import Dict, Any
from pathlib import Path


def generate_stac_item(item_id: str, collection_id: str = "test-collection") -> Dict[str, Any]:
    """Generate a minimal valid STAC item.
    
    Args:
        item_id: Unique item identifier
        collection_id: Collection identifier
        
    Returns:
        STAC Item dictionary (~5KB JSON)
    """
    return {
        "type": "Feature",
        "stac_version": "1.0.0",
        "id": item_id,
        "collection": collection_id,
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [-122.5, 37.5],
                [-122.0, 37.5],
                [-122.0, 38.0],
                [-122.5, 38.0],
                [-122.5, 37.5]
            ]]
        },
        "bbox": [-122.5, 37.5, -122.0, 38.0],
        "properties": {
            "datetime": datetime.now(timezone.utc).isoformat(),
            "title": f"Test Item {item_id}",
            "description": "Test STAC item for benchmarking",
            "platform": "test-platform",
            "instruments": ["test-sensor"],
            "gsd": 10.0,
            "proj:epsg": 4326
        },
        "assets": {
            "visual": {
                "href": f"https://example.com/{item_id}/visual.tif",
                "type": "image/tiff; application=geotiff",
                "roles": ["visual"]
            },
            "B01": {
                "href": f"https://example.com/{item_id}/B01.tif",
                "type": "image/tiff; application=geotiff",
                "roles": ["data"]
            },
            "B02": {
                "href": f"https://example.com/{item_id}/B02.tif",
                "type": "image/tiff; application=geotiff",
                "roles": ["data"]
            },
            "B03": {
                "href": f"https://example.com/{item_id}/B03.tif",
                "type": "image/tiff; application=geotiff",
                "roles": ["data"]
            },
            "metadata": {
                "href": f"https://example.com/{item_id}/metadata.xml",
                "type": "application/xml",
                "roles": ["metadata"]
            }
        },
        "links": [
            {
                "rel": "self",
                "href": f"https://example.com/collections/{collection_id}/items/{item_id}"
            },
            {
                "rel": "collection",
                "href": f"https://example.com/collections/{collection_id}"
            }
        ]
    }


def generate_item_files(
    output_dir: Path,
    count: int,
    collection_id: str = "test-collection"
) -> Path:
    """Generate N individual JSON item files in a directory.
    
    Args:
        output_dir: Directory to create items in
        count: Number of items to generate
        collection_id: Collection identifier for items
        
    Returns:
        Path to output directory
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i in range(count):
        item_id = f"item-{i:06d}"
        item = generate_stac_item(item_id, collection_id)
        
        file_path = output_dir / f"{item_id}.json"
        file_path.write_text(json.dumps(item, indent=2))
    
    return output_dir


def generate_feature_collection(
    output_path: Path,
    count: int,
    collection_id: str = "test-collection"
) -> Path:
    """Generate a FeatureCollection JSON file with N items.
    
    Args:
        output_path: Path to output JSON file
        count: Number of items to include
        collection_id: Collection identifier for items
        
    Returns:
        Path to output file
    """
    features = [
        generate_stac_item(f"item-{i:06d}", collection_id)
        for i in range(count)
    ]
    
    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(feature_collection, indent=2))
    
    return output_path
