import pytest
import requests_mock
from stac_manager.modules.extension import ExtensionModule
from tests.fixtures.context import MockWorkflowContext
from stac_manager.exceptions import ConfigurationError
from tests.fixtures.schemas import get_dgeo_schema, get_alternate_assets_schema, DGEO_ASSET_SCHEMA_URL, ALTERNATE_ASSETS_SCHEMA_URL


SIMPLE_SCHEMA = {
    "type": "object",
    "properties": {
        "properties": {
            "type": "object",
            "properties": {
                "test:field": {"type": "string"}
            }
        }
    }
}

ONEOF_SCHEMA = {
    "oneOf": [
        {
            "properties": {
                "type": {"const": "Feature"},
                "properties": {
                    "properties": {
                        "custom:value": {"type": "number"}
                    }
                }
            }
        }
    ]
}

def test_extension_module_fetches_schema():
    """ExtensionModule fetches schema from URI during init."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({
            "schema_uri": "https://example.com/schema.json"
        })
        
        assert module.schema is not None
        assert "properties" in module.schema


def test_extension_module_schema_fetch_failure():
    """ExtensionModule raises ConfigurationError on fetch failure."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/missing.json", status_code=404)
        
        with pytest.raises(ConfigurationError) as exc_info:
            ExtensionModule({"schema_uri": "https://example.com/missing.json"})
        
        assert "schema" in str(exc_info.value).lower()


def test_extension_module_builds_template():
    """ExtensionModule builds template from schema properties."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({
            "schema_uri": "https://example.com/schema.json"
        })
        
        assert module.template is not None
        assert "properties" in module.template
        assert "test:field" in module.template["properties"]


def test_extension_module_handles_oneof():
    """ExtensionModule parses oneOf schemas."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/oneof.json", json=ONEOF_SCHEMA)
        
        module = ExtensionModule({
            "schema_uri": "https://example.com/oneof.json"
        })
        
        assert "custom:value" in module.template["properties"]


def test_extension_module_applies_defaults():
    """ExtensionModule overlays user defaults onto template."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({
            "schema_uri": "https://example.com/schema.json",
            "defaults": {
                "properties": {
                    "test:field": "custom_value"
                }
            }
        })
        
        assert module.template["properties"]["test:field"] == "custom_value"


def test_extension_module_applies_to_item():
    """ExtensionModule tags and merges template into item."""
    from tests.fixtures.stac_items import VALID_ITEM
    
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({
            "schema_uri": "https://example.com/schema.json",
            "defaults": {"properties": {"test:field": "value"}}
        })
        context = MockWorkflowContext.create()
        
        item = VALID_ITEM.copy()
        result = module.modify(item, context)
        
        # Check tagging
        assert "stac_extensions" in result
        assert "https://example.com/schema.json" in result["stac_extensions"]
        
        # Check scaffolding applied
        assert result["properties"]["test:field"] == "value"
        
        # Check existing data preserved
        assert result["properties"]["datetime"] == "2024-01-01T00:00:00Z"


def test_extension_module_handles_real_dgeo_schema():
    """ExtensionModule handles complex dgeo-asset schema with refs and assets."""
    from tests.fixtures.stac_items import VALID_ITEM
    
    dgeo_schema = get_dgeo_schema()
    
    with requests_mock.Mocker() as m:
        m.get(DGEO_ASSET_SCHEMA_URL, json=dgeo_schema)
        
        module = ExtensionModule({"schema_uri": DGEO_ASSET_SCHEMA_URL})
        context = MockWorkflowContext.create()
        
        # Test 1: Apply to item with no assets
        item = VALID_ITEM.copy()
        if "assets" in item:
            del item["assets"]
            
        result = module.modify(item, context)
        
        # Check properties scaffolded
        assert "dgeo:cids" in result["properties"]
        assert result["properties"]["dgeo:cids"] is None
        assert "dgeo:piece_cids" in result["properties"]
        assert result["properties"]["dgeo:piece_cids"] is None
        
        # Check default asset created and extended
        assert "assets" in result
        assert "AssetId" in result["assets"]
        asset = result["assets"]["AssetId"]
        assert "dgeo:cid" in asset
        assert "dgeo:cid_profile" in asset
        assert asset["dgeo:cid_profile"]["cid_version"] is None
        assert asset["dgeo:cid_profile"]["hash_function"] is None

def test_extension_module_implements_modifier_protocol():
    """ExtensionModule implements Modifier protocol."""
    from stac_manager.protocols import Modifier
    
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({"schema_uri": "https://example.com/schema.json"})
        assert isinstance(module, Modifier)


def test_extension_module_handles_alternate_assets():
    """ExtensionModule handles Alternate Assets extension schema."""
    from tests.fixtures.stac_items import VALID_ITEM
    
    schema = get_alternate_assets_schema()

    with requests_mock.Mocker() as m:
        m.get(ALTERNATE_ASSETS_SCHEMA_URL, json=schema)
        
        module = ExtensionModule({"schema_uri": ALTERNATE_ASSETS_SCHEMA_URL})
        context = MockWorkflowContext.create()
        
        item = VALID_ITEM.copy()
        result = module.modify(item, context)
        
        # Check assets template applied
        assert "AssetId" in result["assets"]
        asset = result["assets"]["AssetId"]
        
        # 'alternate' field should be scaffolded in the asset
        assert "alternate" in asset
        # 'alternate:name' field should also be scaffolded
        assert "alternate:name" in asset


def test_extension_module_honors_required_fields_only():
    """ExtensionModule only scaffolds required fields when flag is set."""
    SCHEMA_WITH_OPTIONAL = {
        "type": "object",
        "properties": {
            "properties": {
                "type": "object",
                "required": ["req:field"],
                "properties": {
                    "req:field": {"type": "string"},
                    "opt:field": {"type": "string"}
                }
            }
        }
    }
    
    uri = "https://example.com/optional.json"
    with requests_mock.Mocker() as m:
        m.get(uri, json=SCHEMA_WITH_OPTIONAL)
        
        # Test 1: Only required
        module_req = ExtensionModule({
            "schema_uri": uri,
            "required_fields_only": True
        })
        assert "req:field" in module_req.template["properties"]
        assert "opt:field" not in module_req.template["properties"]
        
        # Test 2: All fields (default)
        module_all = ExtensionModule({
            "schema_uri": uri,
            "required_fields_only": False
        })
        assert "req:field" in module_all.template["properties"]
        assert "opt:field" in module_all.template["properties"]


def test_defaults_with_quoted_keys():
    """ExtensionModule handles quoted keys in defaults."""
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({
            "schema_uri": "https://example.com/schema.json",
            "defaults": {
                # This should parse to ["assets", "ANG.txt", "title"]
                'assets."ANG.txt".title': "My Title"
            }
        })
        
        # Build a valid item
        from tests.fixtures.stac_items import VALID_ITEM
        item = VALID_ITEM.copy()
        item["assets"] = {
            "ANG.txt": {"href": "s3://ang.txt"},
            "normal": {"href": "s3://normal.tif"}
        }
        
        context = MockWorkflowContext.create()
        result = module.modify(item, context)
        
        # Check quoted key default applied correctly
        assert "ANG.txt" in result["assets"]
        # With the fix, the path should be parsed correctly and set on the asset
        assert result["assets"]["ANG.txt"].get("title") == "My Title"
        
        # Check normal asset (not affected since default was specific to ANG.txt)
        assert "title" not in result["assets"]["normal"]
