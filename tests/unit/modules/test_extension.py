import pytest
import requests_mock
from stac_manager.modules.extension import ExtensionModule
from tests.fixtures.context import MockWorkflowContext
from stac_manager.exceptions import ConfigurationError


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


def test_extension_module_implements_modifier_protocol():
    """ExtensionModule implements Modifier protocol."""
    from stac_manager.protocols import Modifier
    
    with requests_mock.Mocker() as m:
        m.get("https://example.com/schema.json", json=SIMPLE_SCHEMA)
        
        module = ExtensionModule({"schema_uri": "https://example.com/schema.json"})
        assert isinstance(module, Modifier)
