# Tutorial 02: Update Pipeline - Modifying Items In-Flight

Learn how to transform STAC items by adding or modifying properties.

---

## Overview

This tutorial builds on [Tutorial 01](01-basic-pipeline.md) by introducing **ModifyModule** - a processor that transforms STAC items as they flow through the pipeline.

**What you'll learn:**
- How to add custom properties to items
- How to modify existing properties
- How to chain multiple modules in sequence
- Real-world enrichment patterns

**Time required:** ~10 minutes

---

## Prerequisites

- STAC Manager installed ([Installation Guide](../installation.md))
- Completed [Tutorial 01: Basic Pipeline](01-basic-pipeline.md)
- Sample data available (from quickstart or generate with script)

---

## The Workflow

Open `samples/sentinel-2-l2a-api/workflows/02-update-pipeline.yaml`:

```yaml
name: update-pipeline

steps:
  - id: ingest
    module: IngestModule
    config:
      mode: file
      source: samples/sentinel-2-l2a-api/sample-data/items.json
      collection_id: sentinel-2-l2a

  - id: update
    module: UpdateModule
    depends_on: [ingest]
    config:
      mode: merge
      patch_file: samples/sentinel-2-l2a-api/input-data/updates.json
      create_missing_paths: true
      auto_update_timestamp: true

  - id: validate
    module: ValidateModule
    depends_on: [update]
    config:
      strict: false

  - id: output
    module: OutputModule
    depends_on: [validate]
    config:
      base_dir: ./outputs/tutorial-02
      format: json
```

### Pipeline Flow

```
IngestModule (Local File)
        ↓
   20 Items
        ↓
   ModifyModule (Add Properties)
        ↓
   20 Modified Items
        ↓
   ValidateModule (Check Schema)
        ↓
   20 Validated Items
        ↓
   OutputModule (Write to Disk)
```

---

## Running the Workflow

Execute the tutorial workflow:

```bash
stac-manager run-workflow samples/sentinel-2-l2a-api/workflows/02-update-pipeline.yaml
```

**Expected output:**

```
Starting workflow: update-pipeline
[ingest] Loaded 20 items from file
[modify] Processing 20 items
[modify] Added properties to 20 items
[validate] Validated 20 items (0 errors)
[output] Wrote 20 items to ./outputs/sentinel-2-l2a-tutorial-02
✓ Workflow completed successfully
```

---

## Understanding ModifyModule

### Operation Types

ModifyModule supports several operations for transforming items:

#### 1. add_property

Add or update a property at a specific JSON path:

```yaml
updates:
  properties:
    custom_field: "my_value"
    metadata:
      processing:
        tool: "stac-manager"
    tags:
      - "sentinel-2"
      - "processed"
      - "tutorial"
```

#### 2. removes

Remove properties from items:

```yaml
removes:
  - properties.obsolete_field
  - properties.temporary_data
```

#### 3. mode

Control how updates are applied:

```yaml
mode: merge              # Merge updates into item (default)
mode: replace           # Replace entire item with patch
mode: update_only       # Only update existing fields
```

#### 4. create_missing_paths

Automatically create nested paths:

```yaml
create_missing_paths: true    # Create missing nested dicts
create_missing_paths: false   # Fail if path doesn't exist
```

#### 5. auto_update_timestamp

Automatically add an `updated` timestamp:

```yaml
auto_update_timestamp: true   # Adds properties.updated
```

---

## Common Patterns

### Pattern 1: Add Processing Metadata

Track where and when items were processed:

```yaml
- id: update
  module: UpdateModule
  depends_on: [ingest]
  config:
    mode: merge
    updates:
      properties:
        processed_by: "stac-manager"
        processing_date: "2024-01-26T12:00:00Z"
        processing_version: "2.0"
        workflow_id: "update-pipeline-v1"
```

**Result:** Each item now has a processing trail showing what tool processed it and when.

### Pattern 2: Quality Flagging

Add flags based on data properties:

```yaml
- id: update
  module: UpdateModule
  depends_on: [ingest]
  config:
    mode: merge
    updates:
      properties:
        is_clear_sky: false
        is_recent: false
        is_high_quality: false
    # Note: Conditional flagging requires a custom transform
```

### Pattern 3: Standardize Property Names

Convert collection-specific properties to standard names:

```yaml
- id: update
  module: UpdateModule
  depends_on: [ingest]
  config:
    mode: merge
    updates:
      properties:
        cloud_cover: "{{ properties.eo:cloud_cover }}"
        quality_tier: "standard"
```

### Pattern 4: Add Upstream Processing Info

Track what preprocessing was applied:

```yaml
- id: update
  module: UpdateModule
  depends_on: [validate]
  config:
    mode: merge
    updates:
      properties:
        preprocessing:
          atmospheric_correction: "applied"
          cloud_masking: "applied"
          terrain_correction: "applied"
          version: "sen2cor_2.10"
```

### Pattern 5: Using Wildcards to Update All Assets

**New in v1.1.0:** Use wildcard patterns to apply updates to multiple assets at once:

```yaml
- id: update
  module: UpdateModule
  depends_on: [ingest]
  config:
    mode: merge
    updates:
      # Add roles to ALL assets
      assets.*.roles: ["data"]
      
      # Add custom metadata to all assets
      assets.*.custom:processed: true
      assets.*.custom:version: "1.0.0"
      
      # With template variables - unique per asset
      assets.*.alternate.s3.href: "s3://my-bucket/{collection_id}/{asset_key}/"
```

**Why use wildcards?**

- Apply updates to all assets without listing each one
- Maintain consistency across assets
- Reduce configuration verbosity

**Template Variables:**

- `{item_id}` - Replaced with the item's ID
- `{collection_id}` - Replaced with the item's collection ID
- `{asset_key}` - Replaced with each asset's key (e.g., "B04", "visual")

**Example output:**

```json
{
  "assets": {
    "visual": {
      "href": "https://example.com/visual.tif",
      "roles": ["data"],
      "alternate": {
        "s3": {
          "href": "s3://my-bucket/sentinel-2-l2a/visual/"
        }
      }
    },
    "B04": {
      "href": "https://example.com/B04.tif",
      "roles": ["data"],
      "alternate": {
        "s3": {
          "href": "s3://my-bucket/sentinel-2-l2a/B04/"
        }
      }
    }
  }
}
```

---

## Advanced Usage

### Chaining Modifiers

You can chain multiple UpdateModule steps:

```yaml
steps:
  - id: ingest
    module: IngestModule
    # ...

  # First pass: Add metadata
  - id: update_metadata
    module: UpdateModule
    depends_on: [ingest]
    config:
      mode: merge
      updates:
        properties.processed: true

  # Second pass: Add removal list
  - id: update_cleanup
    module: UpdateModule
    depends_on: [update_metadata]
    config:
      mode: merge
      updates:
        properties.acceptable_quality: true
      removes:
        - properties.temporary_field

  - id: validate
    module: ValidateModule
    depends_on: [update_cleanup]
    # ...
```

### Conditional Operations

Use templating to compute values dynamically:

```yaml
- type: add_property
  path: properties.size_category
  value: "{{ 'large' if properties.file_size > 1000000 else 'small' }}"

- type: add_property
  path: properties.season
  value: "{{ 'summer' if 6 <= properties.datetime.month <= 8 else 'winter' }}"
```

---

## Troubleshooting

### "Path not found" Error

**Error**: `Property path not found: properties.eo:cloud_cover`

**Cause**: The property doesn't exist in the item, or path syntax is wrong

**Solution**: Check the actual item structure:

```bash
cat outputs/sentinel-2-l2a/items/S2A_*.json | head -n 100
```

Look for the actual property path and use the correct one.

### Properties Not Updated

**Error**: Items output but properties not modified

**Cause**: ModifyModule is not connected to validation/output

**Solution**: Verify `depends_on` chain:

```yaml
- id: modify
  module: ModifyModule
  depends_on: [ingest]      # ← Receives from ingest

- id: validate
  module: ValidateModule
  depends_on: [modify]      # ← Receives from modify (important!)

- id: output
  module: OutputModule
  depends_on: [validate]    # ← Receives validated items
```

### Validation Fails After Modification

**Error**: `[validate] Schema validation failed after modification`

**Cause**: Added properties violate STAC schema

**Solution**: Ensure properties follow STAC specification:

```yaml
# ✓ Valid: Simple property
- type: add_property
  path: properties.custom_processing
  value: "done"

# ✗ Invalid: Modifying required "id" field
- type: add_property
  path: id
  value: "new_id"

# ✗ Invalid: Breaking geometry
- type: add_property
  path: geometry
  value: "invalid"
```

---

## Comparing Output

Compare the original items with modified ones:

```bash
# Original item from quickstart
echo "=== Original Item ===" 
cat outputs/sentinel-2-l2a/items/S2A_*.json | jq '.properties | keys'

# Modified item from this tutorial
echo "=== Modified Item ===" 
cat outputs/sentinel-2-l2a-tutorial-02/items/S2A_*.json | jq '.properties | keys'
```

**You should see additional keys** in the modified version:
- `processed`
- `processing_date`
- `processing_note`

---

## Next Steps

- 🔧 **[Tutorial 03: Extension Pipeline](03-extension-pipeline.md)** - Add STAC extensions and enrich with input data
- 📚 **[Concepts Guide](../concepts.md)** - Deep dive into ModifyModule patterns
- 💡 **[Tutorial 01](01-basic-pipeline.md)** - Review API-based ingestion basics

---

## Key Takeaways

✅ ModifyModule transforms items **without loading all into memory**  
✅ Operations chain together for **complex transformations**  
✅ Conditional operations enable **intelligent data enrichment**  
✅ Processing metadata creates an **audit trail**  

---

## Reference: UpdateModule Configuration

| Option | Type | Purpose |
| --- | --- | --- |
| `updates` | Dict | Field path → value mapping for updates |
| `removes` | List | List of field paths to remove |
| `mode` | String | `merge` (default), `replace`, or `update_only` |
| `create_missing_paths` | Bool | Auto-create nested dicts (default: true) |
| `auto_update_timestamp` | Bool | Add `properties.updated` timestamp (default: true) |
| `patch_file` | String | Optional JSON file with item-specific patches |

See [UpdateModule Reference](../spec/stac-manager-v1.0.0/03-module-reference.md#updatemodule) for complete documentation.
