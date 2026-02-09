from tests.fixtures.stac_items import (
    VALID_ITEM, VALID_POLYGON, MULTI_POLYGON, INVALID_GEOMETRY
)
from stac_manager.utils.geometry import (
    ensure_bbox, validate_and_repair_geometry
)


def test_ensure_bbox_from_point():
    """ensure_bbox calculates bbox for Point geometry."""
    geometry = {"type": "Point", "coordinates": [10.0, 20.0]}
    result = ensure_bbox(geometry)
    assert result == [10.0, 20.0, 10.0, 20.0]


def test_ensure_bbox_from_none():
    """ensure_bbox returns None for None geometry."""
    result = ensure_bbox(None)
    assert result is None


def test_ensure_bbox_from_polygon():
    """ensure_bbox calculates bbox for Polygon geometry."""
    result = ensure_bbox(VALID_POLYGON)
    assert result == [0.0, 0.0, 1.0, 1.0]


def test_ensure_bbox_from_multipolygon():
    """ensure_bbox calculates bbox for MultiPolygon geometry."""
    result = ensure_bbox(MULTI_POLYGON)
    assert result == [0.0, 0.0, 3.0, 3.0]


def test_validate_and_repair_valid_geometry():
    """validate_and_repair_geometry returns valid geometry unchanged (normalized to lists/floats)."""
    result = validate_and_repair_geometry(VALID_POLYGON)
    # Convert everything to lists of floats for comparison
    def _normalize(obj):
        if isinstance(obj, (list, tuple)):
            return [_normalize(x) for x in obj]
        if isinstance(obj, (int, float)):
            return float(obj)
        return obj

    assert _normalize(result) == _normalize(VALID_POLYGON)


def test_validate_and_repair_invalid_geometry():
    """validate_and_repair_geometry repairs invalid geometry."""
    # INVALID_GEOMETRY is an unclosed polygon: [[[0, 0], [1, 0], [1, 1]]]
    result = validate_and_repair_geometry(INVALID_GEOMETRY)
    
    assert result["type"] == "Polygon"
    # Result must have 4 points (closed)
    coords = result["coordinates"][0]
    assert len(coords) == 4
    # Closed: first == last
    assert coords[0] == coords[-1]



