"""Tests for test data generation."""
import json
from pathlib import Path
from scripts.profiling.test_data_generator import generate_stac_item, generate_item_files, generate_feature_collection


def test_generate_stac_item_structure():
    """Test that generated STAC item has valid structure."""
    item = generate_stac_item("test-item-001", "test-collection")
    
    assert item["type"] == "Feature"
    assert item["id"] == "test-item-001"
    assert item["collection"] == "test-collection"
    assert "geometry" in item
    assert "properties" in item
    assert "assets" in item
    assert len(item["assets"]) == 5


def test_generate_stac_item_unique_ids():
    """Test that items have unique IDs."""
    item1 = generate_stac_item("item-1")
    item2 = generate_stac_item("item-2")
    
    assert item1["id"] != item2["id"]


def test_generate_item_files_creates_directory(tmp_path):
    """Test generating directory of JSON item files."""
    output_dir = tmp_path / "items"
    
    result_path = generate_item_files(output_dir, count=10)
    
    assert result_path == output_dir
    assert output_dir.exists()
    assert output_dir.is_dir()
    
    # Check files created
    json_files = list(output_dir.glob("*.json"))
    assert len(json_files) == 10
    
    # Validate one file
    first_file = json_files[0]
    item = json.loads(first_file.read_text())
    assert item["type"] == "Feature"
    assert "id" in item


def test_generate_item_files_custom_collection(tmp_path):
    """Test generating items with custom collection ID."""
    output_dir = tmp_path / "custom_items"
    
    generate_item_files(output_dir, count=5, collection_id="my-collection")
    
    json_files = list(output_dir.glob("*.json"))
    item = json.loads(json_files[0].read_text())
    assert item["collection"] == "my-collection"


def test_generate_feature_collection(tmp_path):
    """Test generating FeatureCollection JSON file."""
    output_file = tmp_path / "collection.json"
    
    result_path = generate_feature_collection(output_file, count=100)
    
    assert result_path == output_file
    assert output_file.exists()
    
    data = json.loads(output_file.read_text())
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) == 100
    assert data["features"][0]["type"] == "Feature"
