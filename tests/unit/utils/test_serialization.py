import pytest
import pystac
from stac_manager.utils.serialization import ensure_dict
from tests.fixtures.stac_items import VALID_ITEM


def test_ensure_dict_with_dict():
    """ensure_dict returns dict unchanged when given dict."""
    result = ensure_dict(VALID_ITEM)
    assert result == VALID_ITEM
    assert result is VALID_ITEM  # Same object
