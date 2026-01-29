"""Tests for TransformConfig validation."""
import pytest
from pydantic import ValidationError
from stac_manager.modules.config import TransformConfig


def test_transform_config_default_strategy():
    """Default strategy should be update_existing."""
    config = TransformConfig(
        input_file="data.json",
        field_mapping={"properties.foo": "bar"}
    )
    assert config.strategy == "update_existing"


def test_transform_config_accepts_merge_strategy():
    """Should accept merge strategy."""
    config = TransformConfig(
        input_file="data.json",
        field_mapping={"properties.foo": "bar"},
        strategy="merge"
    )
    assert config.strategy == "merge"


def test_transform_config_accepts_update_existing_strategy():
    """Should accept update_existing strategy."""
    config = TransformConfig(
        input_file="data.json",
        field_mapping={"properties.foo": "bar"},
        strategy="update_existing"
    )
    assert config.strategy == "update_existing"


def test_transform_config_rejects_old_update_strategy():
    """Should reject old 'update' strategy name."""
    with pytest.raises(ValidationError) as exc_info:
        TransformConfig(
            input_file="data.json",
            field_mapping={"properties.foo": "bar"},
            strategy="update"
        )
    # Check that the error contains message about invalid value
    error_msg = str(exc_info.value).lower()
    assert "literal_error" in error_msg or "'update'" in error_msg


def test_transform_config_rejects_invalid_strategy():
    """Should reject invalid strategy values."""
    with pytest.raises(ValidationError):
        TransformConfig(
            input_file="data.json",
            field_mapping={"properties.foo": "bar"},
            strategy="invalid"
        )
