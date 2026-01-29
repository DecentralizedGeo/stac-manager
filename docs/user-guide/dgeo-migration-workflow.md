# DGEO Extension Migration Workflow

This guide walks through the complete process of migrating existing STAC collections to the [dgeo extension](https://github.com/DecentralizedGeo/dgeo), using STAC Manager to automate most of the work.

## Overview

The workflow consists of two phases:

1. **Manual Asset Extraction** - Extract current asset metadata to CSV, edit, and convert to JSON
2. **Automated Pipeline** - Use STAC Manager to transform items with the dgeo extension

---

## Phase 1: Asset Extraction & Preparation

### Step 1: Extract Assets to CSV

Use the extraction script to pull all asset data from your STAC collection:

```bash
# Extract from Landsat collection
python scripts/extract_assets_for_dgeo.py extract landsat-c2l1 \
  --output data/landsat_assets.csv

# For testing, extract only 10 items first
python scripts/extract_assets_for_dgeo.py extract landsat-c2l1 \
  --output data/landsat_test.csv \
  --max-items 10

# Extract from other collections
python scripts/extract_assets_for_dgeo.py extract HLSS30_2.0 \
  --output data/hlss30_assets.csv

python scripts/extract_assets_for_dgeo.py extract sentinel-2-l2a \
  --output data/sentinel2_assets.csv
```

The script will generate a CSV with these columns:

| Column | Description |
|--------|-------------|
| `item_id` | STAC item identifier |
| `collection_id` | Collection this item belongs to |
| `asset_key` | Asset identifier (e.g., "red", "nir") |
| `asset_type` | Always "main" for primary assets |
| `href` | Asset URL |
| `title` | Asset title |
| `media_type` | MIME type |
| `roles` | Comma-separated roles |
| `description` | Asset description |
| `s3_href` | S3 alternate location (if present) |
| `s3_name` | S3 alternate name |
| `ipfs_href` | IPFS alternate location (if present) |
| `ipfs_cid` | Extracted IPFS CID |
| `filecoin_href` | Filecoin alternate location (if present) |
| `filecoin_piece_cid` | Extracted Filecoin piece CID |

### Step 2: Edit the CSV

Open the CSV in Excel, LibreOffice, or your preferred editor:

1. **Review CIDs**: Check that `ipfs_cid` and `filecoin_piece_cid` are correctly extracted
2. **Update values**: Modify any CIDs that need correction
3. **Add missing data**: Fill in any missing CID information
4. **Remove unwanted rows**: Delete any assets you don't want to migrate

**Save the edited file with an `_edited` suffix**, e.g., `landsat_assets_edited.csv`

### Step 3: Convert CSV to JSON

Convert the edited CSV to JSON formats that STAC Manager can consume:

```bash
python scripts/extract_assets_for_dgeo.py convert data/landsat_assets_edited.csv
```

This generates three JSON files:

1. **`*_metadata.json`** - For TransformModule
   - Contains item-level CID arrays
   - Maps to `properties.dgeo:cids` and `properties.dgeo:piece_cids`

2. **`*_asset_cids.json`** - For UpdateModule patch_file
   - Contains asset-specific `dgeo:cid` values
   - Maps to `assets.{key}.dgeo:cid`

3. **`*_full.json`** - Complete reference data
   - All extracted information in one file
   - Use for debugging or custom processing

---

## Phase 2: STAC Manager Pipeline

### Step 4: Create Workflow Configuration

Create a YAML workflow file (e.g., `workflows/landsat_dgeo_migration.yaml`):

```yaml
name: landsat-dgeo-migration
description: "Migrate Landsat collection to dgeo extension"

settings:
  logging:
    level: INFO

steps:
  # ============================================
  # STEP 1: Fetch items from STAC API
  # ============================================
  - id: ingest_landsat
    module: IngestModule
    config:
      mode: api
      source: "https://stac.easierdata.info/api/v1/pgstac"
      collection_id: "landsat-c2l1"
      max_items: 10  # Start with 10 for testing
      concurrency: 5

  # ============================================
  # STEP 2: Remove old alternate assets
  # ============================================
  - id: remove_old_alternates
    module: UpdateModule
    depends_on: [ingest_landsat]
    config:
      removes:
        - "assets.*.alternate.IPFS"
        - "assets.*.alternate.Filecoin"

  # ============================================
  # STEP 3: Add dgeo extension scaffolding
  # ============================================
  - id: add_dgeo_extension
    module: ExtensionModule
    depends_on: [remove_old_alternates]
    config:
      schema_uri: "https://raw.githubusercontent.com/DecentralizedGeo/dgeo/refs/heads/main/json-schema/schema.json"
      required_fields_only: false
      defaults:
        # Initialize empty arrays (populated by TransformModule)
        properties.dgeo:cids: []
        properties.dgeo:piece_cids: []
        # Set default CID profile for all assets
        assets.*.dgeo:cid_profile.cid_version: 1
        assets.*.dgeo:cid_profile.hash_function: "sha2-256"
        assets.*.dgeo:cid_profile.chunk_algorithm: "fixed"
        assets.*.dgeo:cid_profile.chunk_size: 262144
        assets.*.dgeo:cid_profile.dag_layout: "balanced"

  # ============================================
  # STEP 4: Enrich with extracted metadata
  # ============================================
  - id: enrich_with_metadata
    module: TransformModule
    depends_on: [add_dgeo_extension]
    config:
      input_file: "./data/landsat_assets_edited_metadata.json"
      input_join_key: "id"
      strategy: "merge"
      handle_missing: "warn"
      field_mapping:
        # Use JMESPath to wrap scalars in arrays
        dgeo:cids: "ipfs_cids"
        dgeo:piece_cids: "filecoin_piece_cids"

  # ============================================
  # STEP 5: Set asset-specific CIDs
  # ============================================
  - id: set_asset_cids
    module: UpdateModule
    depends_on: [enrich_with_metadata]
    config:
      patch_file: "./data/landsat_assets_edited_asset_cids.json"
      mode: "merge"

  # ============================================
  # STEP 6: Set additional defaults
  # ============================================
  - id: set_final_defaults
    module: UpdateModule
    depends_on: [set_asset_cids]
    config:
      auto_update_timestamp: true

  # ============================================
  # STEP 7: Validate updated items
  # ============================================
  - id: validate_items
    module: ValidateModule
    depends_on: [set_final_defaults]
    config:
      strict: false  # Log warnings but don't fail

  # ============================================
  # STEP 8: Output to JSON files
  # ============================================
  - id: output_json
    module: OutputModule
    depends_on: [validate_items]
    config:
      base_dir: "./outputs/landsat-dgeo-migrated"
      format: "json"
      organize_by: "collection"
      include_collection: true
```

### Step 5: Run the Pipeline

Execute the workflow:

```bash
# Run with small test set first
stac-manager run-workflow workflows/landsat_dgeo_migration.yaml

# Review outputs in ./outputs/landsat-dgeo-migrated/

# If successful, update workflow to process all items (max_items: null)
# and re-run
```

### Step 6: Verify Results

Check the output files:

```bash
# View a sample migrated item
cat outputs/landsat-dgeo-migrated/landsat-c2l1/LC08_L1TP_001001_20210101.json

# Check for dgeo extension in stac_extensions array
jq '.stac_extensions' outputs/landsat-dgeo-migrated/landsat-c2l1/*.json | head

# Verify dgeo:cids are present
jq '.properties["dgeo:cids"]' outputs/landsat-dgeo-migrated/landsat-c2l1/*.json | head

# Verify asset-level dgeo:cid
jq '.assets[].["dgeo:cid"]' outputs/landsat-dgeo-migrated/landsat-c2l1/*.json | head
```

---

## Adapting for Multiple Collections

The extraction script works identically for all collections. The main differences are:

### Collection-Specific Configuration

Create separate workflow files for each collection:

**`workflows/hlss30_dgeo_migration.yaml`**:
```yaml
name: hlss30-dgeo-migration
# ... same structure, but change:
#   - collection_id: "HLSS30_2.0"
#   - input_file: "./data/hlss30_assets_edited_metadata.json"
#   - patch_file: "./data/hlss30_assets_edited_asset_cids.json"
#   - base_dir: "./outputs/hlss30-dgeo-migrated"
```

**`workflows/sentinel2_dgeo_migration.yaml`**:
```yaml
name: sentinel2-dgeo-migration
# ... same structure, but change:
#   - collection_id: "sentinel-2-l2a"
#   - input_file: "./data/sentinel2_assets_edited_metadata.json"
#   - patch_file: "./data/sentinel2_assets_edited_asset_cids.json"
#   - base_dir: "./outputs/sentinel2-dgeo-migrated"
```

### Batch Processing Script

Create a script to process all collections:

```bash
#!/bin/bash
# migrate_all_collections.sh

COLLECTIONS=("landsat-c2l1" "HLSS30_2.0" "sentinel-2-l2a")

for COLLECTION in "${COLLECTIONS[@]}"; do
  echo "Processing $COLLECTION..."
  
  # Extract
  python scripts/extract_assets_for_dgeo.py extract "$COLLECTION" \
    --output "data/${COLLECTION}_assets.csv"
  
  echo "Please edit data/${COLLECTION}_assets.csv and save as data/${COLLECTION}_assets_edited.csv"
  read -p "Press Enter when ready to continue..."
  
  # Convert
  python scripts/extract_assets_for_dgeo.py convert \
    "data/${COLLECTION}_assets_edited.csv"
  
  # Run workflow
  stac-manager run-workflow "workflows/${COLLECTION}_dgeo_migration.yaml"
done

echo "All collections processed!"
```

---

## Advanced: Customizing CID Profiles

Different assets may require different CID profiles. You can override defaults per asset in the workflow:

```yaml
- id: set_custom_profiles
  module: UpdateModule
  depends_on: [set_asset_cids]
  config:
    patch_file: "./data/custom_cid_profiles.json"
    mode: "merge"
```

Where `custom_cid_profiles.json` contains:

```json
{
  "LC08_L1TP_001001_20210101": {
    "assets": {
      "red": {
        "dgeo:cid_profile": {
          "cid_version": 1,
          "chunk_algorithm": "rabin",
          "chunk_size": 131072,
          "dag_layout": "trickle"
        }
      }
    }
  }
}
```

---

## Troubleshooting

### Issue: Missing CIDs in CSV

**Symptom**: `ipfs_cid` or `filecoin_piece_cid` columns are empty

**Solution**: 
- Check if alternate assets exist in the original items
- Verify the href format matches expected patterns (e.g., `ipfs://`, `/ipfs/`)
- Manually add CIDs if they're stored elsewhere in your system

### Issue: Validation Fails

**Symptom**: ValidateModule reports errors

**Solution**:
- Check that `dgeo:cids` is an array (not a string)
- Verify CID format matches dgeo schema requirements (CIDv0: `Qm...`, CIDv1: `b...`)
- Review validation errors and adjust the workflow

### Issue: Asset-Specific CIDs Not Applied

**Symptom**: `dgeo:cid` missing from assets

**Solution**:
- Verify the patch file structure matches item IDs exactly
- Check that asset keys in the patch file match actual asset keys
- Ensure UpdateModule `mode: "merge"` is set correctly

---

## Next Steps

After migration:

1. **Upload to your STAC API**: Use your API's ingestion endpoint
2. **Verify queryability**: Test CQL2 queries on `dgeo:cids`
3. **Update client code**: If you have applications using the old alternate assets structure, update them to use dgeo fields
4. **Document changes**: Update your collection documentation to reference the dgeo extension

---

## Reference

- **dgeo Extension Spec**: https://github.com/DecentralizedGeo/dgeo
- **STAC Manager Docs**: [../README.md](../../README.md)
- **Module Documentation**: [./modules.md](./modules.md)
