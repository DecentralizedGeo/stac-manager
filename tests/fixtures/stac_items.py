"""
Shared STAC test fixtures - real STAC data for testing.
No mocks on domain data.
"""

# Valid STAC 1.0.0 Item
VALID_ITEM = {
    "type": "Feature",
    "stac_version": "1.0.0",
    "id": "test-item-001",
    "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
    "bbox": [0.0, 0.0, 0.0, 0.0],
    "properties": {
        "datetime": "2024-01-01T00:00:00Z"
    },
    "assets": {},
    "links": []
}

# Partial item (for hydration tests)
PARTIAL_ITEM = {
    "id": "partial-001"
}

# Item with nested properties
NESTED_ITEM = {
    "type": "Feature",
    "stac_version": "1.0.0",
    "id": "nested-001",
    "geometry": None,
    "bbox": None,
    "properties": {
        "datetime": None,
        "instruments": ["OLI", "TIRS"],
        "eo:cloud_cover": 15.5
    },
    "assets": {},
    "links": []
}

# Invalid geometry (unclosed polygon)
INVALID_GEOMETRY = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [1, 0], [1, 1]]]  # Missing closing coordinate
}

# Valid polygon geometry
VALID_POLYGON = {
    "type": "Polygon",
    "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
}

# MultiPolygon
MULTI_POLYGON = {
    "type": "MultiPolygon",
    "coordinates": [
        [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
        [[[2, 2], [3, 2], [3, 3], [2, 3], [2, 2]]]
    ]
}
