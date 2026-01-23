import pytest
from pydantic import ValidationError
from stac_manager.modules.config import SeedConfig, UpdateConfig, ValidateConfig


def test_seed_config_validation():
    """SeedConfig validates required fields."""
    config = SeedConfig(items=["item-001", "item-002"])
    assert config.items == ["item-001", "item-002"]
    assert config.source_file is None


def test_seed_config_with_defaults():
    """SeedConfig accepts defaults."""
    config = SeedConfig(
        items=["item-001"],
        defaults={"collection": "test"}
    )
    assert config.defaults["collection"] == "test"


def test_update_config_validation():
    """UpdateConfig validates updates dict."""
    config = UpdateConfig(
        updates={"properties.license": "CC-BY-4.0"}
    )
    assert config.updates["properties.license"] == "CC-BY-4.0"
    assert config.auto_update_timestamp is True  # default


def test_validate_config_defaults():
    """ValidateConfig uses defaults."""
    config = ValidateConfig()
    assert config.strict is False
    assert config.extension_schemas == []
