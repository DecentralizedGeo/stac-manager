from tests.fixtures.downloader import download_fixture

# Remote schema URLs
DGEO_ASSET_SCHEMA_URL = "https://raw.githubusercontent.com/DecentralizedGeo/dgeo-asset/refs/heads/pgstac-variant/json-schema/schema.json"
STAC_ITEM_SCHEMA_URL = "https://schemas.stacspec.org/v1.1.0/item-spec/json-schema/item.json"
ALTERNATE_ASSETS_SCHEMA_URL = "https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json#"

def get_dgeo_schema():
    """Returns the DGEO Asset extension schema."""
    return download_fixture(DGEO_ASSET_SCHEMA_URL, "dgeo-asset-schema.json")

def get_stac_item_schema():
    """Returns the base STAC Item schema."""
    return download_fixture(STAC_ITEM_SCHEMA_URL, "stac-item-schema.json")

def get_alternate_assets_schema():
    """Returns the alternate assets schema."""
    return download_fixture(ALTERNATE_ASSETS_SCHEMA_URL, "alternate-assets-schema.json")
