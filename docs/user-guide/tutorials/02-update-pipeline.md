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
      source: samples/sentinel-2-l2a-api/data/items.json
      collection_id: sentinel-2-l2a

  - id: modify
    module: ModifyModule
    depends_on: [ingest]
    config:
      operations:
        - type: add_property
          path: properties.processed
          value: true
        - type: add_property
          path: properties.processing_date
          value: "2024-01-26T00:00:00Z"
        - type: add_property
          path: properties.processing_note
          value: "Processed via tutorial 02 workflow"

  - id: validate
    module: ValidateModule
    depends_on: [modify]
    config:
      strict: true

  - id: output
    module: OutputModule
    depends_on: [validate]
    config:
      base_dir: ./outputs
      format: json
      collection_id: sentinel-2-l2a-tutorial-02
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
- type: add_property
  path: properties.custom_field
  value: "my_value"

# Works with nested paths
- type: add_property
  path: properties.metadata.processing.tool
  value: "stac-manager"

# Works with arrays
- type: add_property
  path: properties.tags
  value: ["sentinel-2", "processed", "tutorial"]

# Works with objects
- type: add_property
  path: properties.metadata
  value:
    source: "planetary_computer"
    version: "1.0"
```

#### 2. rename_property

Rename a property from one path to another:

```yaml
- type: rename_property
  from_path: properties.old_name
  to_path: properties.new_name
```

#### 3. delete_property

Remove a property:

```yaml
- type: delete_property
  path: properties.obsolete_field
```

#### 4. conditional_property

Add property only if a condition is met:

```yaml
- type: conditional_property
  condition: "properties.eo:cloud_cover < 20"
  path: properties.is_clear_sky
  value: true
```

---

## Common Patterns

### Pattern 1: Add Processing Metadata

Track where and when items were processed:

```yaml
- id: modify
  module: ModifyModule
  depends_on: [ingest]
  config:
    operations:
      - type: add_property
        path: properties.processed_by
        value: "stac-manager"

      - type: add_property
        path: properties.processing_date
        value: "2024-01-26T12:00:00Z"

      - type: add_property
        path: properties.processing_version
        value: "2.0"

      - type: add_property
        path: properties.workflow_id
        value: "update-pipeline-v1"
```

**Result:** Each item now has a processing trail showing what tool processed it and when.

### Pattern 2: Quality Flagging

Add flags based on data properties:

```yaml
- id: modify
  module: ModifyModule
  depends_on: [ingest]
  config:
    operations:
      # Flag clear-sky images
      - type: conditional_property
        condition: "properties.eo:cloud_cover < 10"
        path: properties.is_clear_sky
        value: true

      # Flag recent data
      - type: conditional_property
        condition: "properties.datetime > 2024-01-01"
        path: properties.is_recent
        value: true

      # Flag high-quality products
      - type: conditional_property
        condition: "properties.quality_score > 0.8"
        path: properties.is_high_quality
        value: true
```

### Pattern 3: Standardize Property Names

Convert collection-specific properties to standard names:

```yaml
- id: modify
  module: ModifyModule
  depends_on: [ingest]
  config:
    operations:
      # Sentinel-2 uses "eo:cloud_cover", we want "cloud_cover"
      - type: add_property
        path: properties.cloud_cover
        value: "{{ properties.eo:cloud_cover }}"

      # Rename acquisition time for consistency
      - type: rename_property
        from_path: properties.datetime
        to_path: properties.acquisition_date

      # Add standardized quality metric
      - type: add_property
        path: properties.quality_tier
        value: "standard"
```

### Pattern 4: Add Upstream Processing Info

Track what preprocessing was applied:

```yaml
- id: modify
  module: ModifyModule
  depends_on: [validate]
  config:
    operations:
      - type: add_property
        path: properties.preprocessing
        value:
          atmospheric_correction: "applied"
          cloud_masking: "applied"
          terrain_correction: "applied"
          version: "sen2cor_2.10"
```

---

## Advanced Usage

### Chaining Modifiers

You can chain multiple ModifyModule steps:

```yaml
steps:
  - id: ingest
    module: IngestModule
    # ...

  # First pass: Add metadata
  - id: modify_metadata
    module: ModifyModule
    depends_on: [ingest]
    config:
      operations:
        - type: add_property
          path: properties.processed
          value: true

  # Second pass: Add quality flags
  - id: modify_quality
    module: ModifyModule
    depends_on: [modify_metadata]
    config:
      operations:
        - type: conditional_property
          condition: "properties.eo:cloud_cover < 20"
          path: properties.acceptable_quality
          value: true

  - id: validate
    module: ValidateModule
    depends_on: [modify_quality]
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

- 🔧 **[Tutorial 03: Extension Pipeline](03-extension-pipeline.md)** - Add STAC extensions and enrich with sidecar data
- 📚 **[Concepts Guide](../concepts.md)** - Deep dive into ModifyModule patterns
- 💡 **[Tutorial 01](01-basic-pipeline.md)** - Review API-based ingestion basics

---

## Key Takeaways

✅ ModifyModule transforms items **without loading all into memory**  
✅ Operations chain together for **complex transformations**  
✅ Conditional operations enable **intelligent data enrichment**  
✅ Processing metadata creates an **audit trail**  

---

## Reference: All Operation Types

| Operation | Purpose | Example |
| --- | --- | --- |
| `add_property` | Add or update a property | `path: properties.field`, `value: "value"` |
| `rename_property` | Rename a property | `from_path: old`, `to_path: new` |
| `delete_property` | Remove a property | `path: properties.field` |
| `conditional_property` | Add if condition met | `condition: "...", path: ..., value: ...` |

See [ModifyModule Reference](../spec/stac-manager-v1.0.0/03-module-reference.md#modifymodule) for complete documentation.
