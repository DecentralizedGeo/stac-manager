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
