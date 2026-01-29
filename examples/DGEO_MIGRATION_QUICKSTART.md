# DGEO Migration Quick Start

Complete workflow for migrating STAC collections to the dgeo extension using STAC Manager.

## Prerequisites

- Python 3.12+
- STAC Manager installed
- Access to https://stac.easierdata.info/

## Quick Steps

### 1. Extract Asset Data

```bash
# Extract assets from your collection
python scripts/extract_assets_for_dgeo.py extract landsat-c2l1 \
  --output data/landsat_assets.csv \
  --max-items 10  # Test with 10 items first
```

### 2. Edit CSV

1. Open `data/landsat_assets.csv` in Excel/LibreOffice
2. Review and update the `ipfs_cid` and `filecoin_piece_cid` columns
3. Save as `data/landsat_assets_edited.csv`

### 3. Convert to JSON

```bash
# Convert edited CSV to JSON formats for STAC Manager
python scripts/extract_assets_for_dgeo.py convert data/landsat_assets_edited.csv
```

This generates:
- `landsat_assets_edited_metadata.json` (for TransformModule)
- `landsat_assets_edited_asset_cids.json` (for UpdateModule)
- `landsat_assets_edited_full.json` (reference)

### 4. Run Migration Workflow

```bash
# Run the STAC Manager pipeline
stac-manager run-workflow examples/landsat-dgeo-migration.yaml
```

### 5. Verify Results

```bash
# Check output directory
ls -lh outputs/landsat-dgeo-migrated/landsat-c2l1/

# Verify dgeo extension
jq '.stac_extensions' outputs/landsat-dgeo-migrated/landsat-c2l1/*.json | grep dgeo

# View dgeo:cids
jq '.properties["dgeo:cids"]' outputs/landsat-dgeo-migrated/landsat-c2l1/*.json | head

# Check asset-level dgeo:cid
jq '.assets[].["dgeo:cid"]' outputs/landsat-dgeo-migrated/landsat-c2l1/*.json | head
```

### 6. Process All Items (Production)

Once satisfied with test results:

1. Edit `examples/landsat-dgeo-migration.yaml`
2. Change `max_items: 10` to `max_items: null`
3. Re-run the workflow

## For Multiple Collections

Repeat the process for each collection:

```bash
# HLSS30
python scripts/extract_assets_for_dgeo.py extract HLSS30_2.0 -o data/hlss30_assets.csv
# ... edit, convert, run workflow ...

# Sentinel-2
python scripts/extract_assets_for_dgeo.py extract sentinel-2-l2a -o data/sentinel2_assets.csv
# ... edit, convert, run workflow ...
```

## Documentation

- **Full Guide**: [docs/user-guide/dgeo-migration-workflow.md](../docs/user-guide/dgeo-migration-workflow.md)
- **Data Formats**: [examples/dgeo-data-formats.md](dgeo-data-formats.md)
- **Workflow Template**: [examples/landsat-dgeo-migration.yaml](landsat-dgeo-migration.yaml)

## Support

- dgeo Extension: https://github.com/DecentralizedGeo/dgeo
- STAC Manager: https://github.com/DecentralizedGeo/stac-manager
