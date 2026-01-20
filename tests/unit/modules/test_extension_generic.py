import pytest
from stac_manager.modules.extension import ExtensionModule

def test_generic_extension_apply():
    config = {
        "extension": "generic",
        "schema_uri": "http://example.com/schema",
        "properties": {"new:prop": "value"}
    }
    module = ExtensionModule(config)
    item = {"id": "1", "type": "Feature", "properties": {}, "stac_extensions": []}
    
    # We pass None as context because modify shouldn't need it if logic is simple
    # But checking implementation: it calls context.logger.debug.
    # So we need a mock context
    from unittest.mock import MagicMock
    mock_context = MagicMock()
    
    result = module.modify(item, mock_context)
    
    assert "http://example.com/schema" in result["stac_extensions"]
    assert result["properties"]["new:prop"] == "value"
