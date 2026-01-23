"""Test fixtures specific to pipeline modules."""

# Valid module configurations
SEED_CONFIG_BASIC = {
    "items": ["item-001", "item-002", "item-003"]
}

SEED_CONFIG_WITH_DEFAULTS = {
    "items": [
        "item-001",
        {"id": "item-002", "properties": {"platform": "Landsat-8"}}
    ],
    "defaults": {
        "collection": "test-collection",
        "properties": {
            "instrument": "OLI"
        }
    }
}

UPDATE_CONFIG_BASIC = {
    "updates": {
        "properties.license": "CC-BY-4.0"
    }
}

UPDATE_CONFIG_WITH_REMOVES = {
    "updates": {
        "properties.license": "CC-BY-4.0"
    },
    "removes": ["properties.deprecated_field"]
}
