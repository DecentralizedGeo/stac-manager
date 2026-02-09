"""
Integration test: Transform Module with wildcard patterns for Landsat STAC items.

This example demonstrates the real-world usage of wildcard field mapping
to enrich multiple assets with DGEO metadata in a single mapping rule.
"""
import json
from pathlib import Path
from stac_manager.modules.transform import TransformModule
from stac_manager.core.context import WorkflowContext
from stac_manager.core.failures import FailureCollector
import logging


def test_landsat_dgeo_enrichment_with_wildcards(tmp_path):
    """
    Real-world scenario: Enrich Landsat STAC item assets with DGEO metadata.
    
    Uses wildcard patterns to apply dgeo:cid and dgeo:size to ALL assets
    without needing to enumerate each asset name explicitly.
    """
    # Create input data file with DGEO metadata for Landsat assets
    input_file = tmp_path / "landsat_dgeo_data.json"
    dgeo_data = {
        "LC08_L2SP_044034_20131228_20200912_02_T1": {
            "assets": {
                "red": {"cid": "bafkreiabcd1234", "size": 12345678},
                "green": {"cid": "bafkreiefgh5678", "size": 12234567},
                "blue": {"cid": "bafkreiijkl9012", "size": 12123456},
                "nir08": {"cid": "bafkreimnop3456", "size": 12012345},
                "swir16": {"cid": "bafkreiqrst7890", "size": 11901234},
                "swir22": {"cid": "bafkreiuvwx1234", "size": 11890123},
                "coastal": {"cid": "bafkreiyzab5678", "size": 11779012},
                "lwir11": {"cid": "bafkreicdef9012", "size": 11768901}
            }
        }
    }
    input_file.write_text(json.dumps(dgeo_data))
    
    # Configure TransformModule with wildcard patterns
    config = {
        "input_file": str(input_file),
        "field_mapping": {
            # Wildcard pattern: applies to ALL assets
            # Template variable {asset_key} substitutes the actual asset name
            "assets.*.dgeo:cid": "assets.{asset_key}.cid",
            "assets.*.dgeo:size": "assets.{asset_key}.size"
        },
        "strategy": "merge"  # Create new fields
    }
    
    module = TransformModule(config)
    
    # Sample Landsat STAC item (simplified)
    landsat_item = {
        "id": "LC08_L2SP_044034_20131228_20200912_02_T1",
        "type": "Feature",
        "stac_version": "1.0.0",
        "geometry": {"type": "Point", "coordinates": [0, 0]},
        "properties": {
            "datetime": "2013-12-28T16:46:42Z",
            "platform": "landsat-8",
            "instruments": ["oli", "tirs"]
        },
        "assets": {
            "red": {
                "href": "s3://landsat-pds/c1/L8/044/034/LC08_L2SP_044034_20131228_20200912_02_T1/LC08_L2SP_044034_20131228_20200912_02_T1_SR_B4.TIF",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "title": "Red Band (B4)",
                "eo:bands": [{"name": "B4", "common_name": "red"}]
            },
            "green": {
                "href": "s3://landsat-pds/.../LC08_L2SP_044034_20131228_20200912_02_T1_SR_B3.TIF",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "title": "Green Band (B3)",
                "eo:bands": [{"name": "B3", "common_name": "green"}]
            },
            "blue": {
                "href": "s3://landsat-pds/.../LC08_L2SP_044034_20131228_20200912_02_T1_SR_B2.TIF",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "title": "Blue Band (B2)",
                "eo:bands": [{"name": "B2", "common_name": "blue"}]
            },
            "nir08": {
                "href": "s3://landsat-pds/.../LC08_L2SP_044034_20131228_20200912_02_T1_SR_B5.TIF",
                "type": "image/tiff; application=geotiff; profile=cloud-optimized",
                "title": "Near Infrared Band 0.8 (B5)",
                "eo:bands": [{"name": "B5", "common_name": "nir08"}]
            }
        }
    }
    
    # Create workflow context
    context = WorkflowContext(
        workflow_id="landsat-dgeo-enrichment",
        logger=logging.getLogger("test"),
        failure_collector=FailureCollector(),
        config={},
        checkpoints={},
        data={}
    )
    
    # Apply transformation
    enriched_item = module.modify(landsat_item, context)
    
    # Verify wildcard expansion worked for all assets
    assert enriched_item["assets"]["red"]["dgeo:cid"] == "bafkreiabcd1234"
    assert enriched_item["assets"]["red"]["dgeo:size"] == 12345678
    
    assert enriched_item["assets"]["green"]["dgeo:cid"] == "bafkreiefgh5678"
    assert enriched_item["assets"]["green"]["dgeo:size"] == 12234567
    
    assert enriched_item["assets"]["blue"]["dgeo:cid"] == "bafkreiijkl9012"
    assert enriched_item["assets"]["blue"]["dgeo:size"] == 12123456
    
    assert enriched_item["assets"]["nir08"]["dgeo:cid"] == "bafkreimnop3456"
    assert enriched_item["assets"]["nir08"]["dgeo:size"] == 12012345
    
    # Verify original asset properties are preserved
    assert enriched_item["assets"]["red"]["title"] == "Red Band (B4)"
    assert enriched_item["assets"]["red"]["type"] == "image/tiff; application=geotiff; profile=cloud-optimized"
    
    print("✅ Landsat DGEO enrichment with wildcards: SUCCESS")
    print(f"   Enriched {len(enriched_item['assets'])} assets with dgeo:cid and dgeo:size")
    print(f"   Using single wildcard rule: assets.*.dgeo:cid")
