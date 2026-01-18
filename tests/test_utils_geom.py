import pytest
from stac_manager.utils import ensure_bbox

def test_ensure_bbox():
    geom = {
        "type": "Polygon",
        "coordinates": [[[0,0], [0,1], [1,1], [1,0], [0,0]]]
    }
    bbox = ensure_bbox(geom)
    assert bbox == [0.0, 0.0, 1.0, 1.0]

def test_ensure_bbox_none():
    assert ensure_bbox(None) is None
