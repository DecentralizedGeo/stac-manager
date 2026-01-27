# Tutorial 03: Extension Pipeline - Adding STAC Extensions and Enriching with Sidecar Data

Learn how to enrich STAC items with standardized extensions and external data sources.

---

## Overview

This tutorial builds on [Tutorial 02](02-update-pipeline.md) by introducing **STAC Extensions** and **data enrichment** - adding standardized metadata and merging with external data sources.

**What you'll learn:**

- How to add STAC extensions to items (EO, Projection, Raster)
- How to merge sidecar data (external CSV/JSON) with items
- Real-world data enrichment patterns
- Complete end-to-end pipeline design

**Time required:** ~15 minutes

---

## Prerequisites

- STAC Manager installed ([Installation Guide](../installation.md))
- Completed [Tutorial 02: Update Pipeline](02-update-pipeline.md)
- Sample data and sidecar data available

---

## The Workflow

Open `samples/sentinel-2-l2a-api/workflows/03-extension-pipeline.yaml`:

```yaml
name: extension-pipeline

steps:
  - id: ingest
    module: IngestModule
    config:
      mode: file
      source: samples/sentinel-2-l2a-api/data/items.json
      collection_id: sentinel-2-l2a

  - id: extend
    module: ExtensionModule
    depends_on: [ingest]
    config:
      extensions:
        - name: eo
          properties:
            bands:
              - name: "B2"
                description: "Blue"
                common_name: "blue"
              # ... more bands

        - name: projection
          properties:
            epsg: 32633

        - name: raster
          properties:
            type: "COG"

  - id: enrich
    module: TransformModule
    depends_on: [extend]
    config:
      input_file: samples/sentinel-2-l2a-api/sidecar-data/cloud-cover.json
      sidecar_id_path: "id"
      strategy: "merge"
      field_mapping:
        cloud_cover: "cloud_cover"
        snow_cover: "snow_cover"

  - id: validate
    module: ValidateModule
    depends_on: [enrich]
    config:
      strict: true

  - id: output
    module: OutputModule
    depends_on: [validate]
    config:
      base_dir: ./outputs
      format: json
      collection_id: sentinel-2-l2a-tutorial-03
```

### Pipeline Flow

```
IngestModule (Local File)
        ↓
   20 Items
        ↓
   ExtensionModule (Add EO, Projection, Raster)
        ↓
   20 Extended Items
        ↓
   TransformModule (Merge with Sidecar Data)
        ↓
   20 Enriched Items
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
stac-manager run-workflow samples/sentinel-2-l2a-api/workflows/03-extension-pipeline.yaml
```

**Expected output:**

```
Starting workflow: extension-pipeline
[ingest] Loaded 20 items from file
[extend] Adding extensions: eo, projection, raster
[extend] Added extensions to 20 items
[enrich] Loading sidecar data from cloud-cover.json
[enrich] Merged sidecar data for 20 items
[validate] Validated 20 items (0 errors)
[output] Wrote 20 items to ./outputs/sentinel-2-l2a-tutorial-03
✓ Workflow completed successfully
```

---

## Understanding STAC Extensions

### What are STAC Extensions?

STAC Extensions are standardized schemas that add domain-specific properties to STAC items. Common extensions include:

| Extension | Purpose | Example Use |
| --- | --- | --- |
| **eo** | Electro-optical imagery | Bands, wavelengths, cloud cover |
| **projection** | Geospatial projections | EPSG code, transforms |
| **raster** | Raster data properties | Pixel types, nodata values |
| **sar** | Synthetic Aperture Radar | Polarization, frequency |
| **view** | Viewing geometry | Incidence angle, azimuth |
| **pointcloud** | Point cloud data | Point count, density |
| **table** | Tabular data | Schemas, columns |

### ExtensionModule in Detail

The ExtensionModule adds extensions to items using schema-driven scaffolding:

```yaml
- id: add_alternate_assets
  module: ExtensionModule
  depends_on: [ingest]
  config:
    schema_uri: "https://stac-extensions.github.io/alternate-assets/v1.2.0/schema.json"
    defaults:
      # Use wildcards to apply to ALL assets
      assets.*.alternate.s3.href: "s3://example-bucket/{collection_id}/{asset_key}/"
      assets.*.alternate.s3.alternate:name: "S3"
      assets.*.alternate:name: "HTTPS"
    required_fields_only: true
```

**Key Features (New in v1.1.0):**

#### Wildcard Syntax

The `assets.*` wildcard matches **all assets** in an item, eliminating the need to specify each asset individually:

```yaml
# Without wildcards (verbose)
defaults:
  assets.visual.alternate.s3.href: "s3://bucket/visual/"
  assets.B04.alternate.s3.href: "s3://bucket/B04/"
  assets.B08.alternate.s3.href: "s3://bucket/B08/"
  # ... repeat for 20+ assets

# With wildcards (concise)
defaults:
  assets.*.alternate.s3.href: "s3://bucket/{asset_key}/"
```

#### Template Variables

Template variables are dynamically replaced for each item/asset:

- **`{item_id}`** - The item's ID (e.g., `"S2A_MSIL2A_20240101..."`)
- **`{collection_id}`** - The collection ID (e.g., `"sentinel-2-l2a"`)
- **`{asset_key}`** - The asset's key name (e.g., `"visual"`, `"B04"`, `"B08"`)

**Example:**

For an item with ID `S2A_001` in collection `sentinel-2-l2a` with assets `visual` and `B04`:

```yaml
assets.*.alternate.s3.href: "s3://my-bucket/{collection_id}/{asset_key}/"
```

Expands to:

```json
{
  "assets": {
    "visual": {
      "alternate": {
        "s3": {
          "href": "s3://my-bucket/sentinel-2-l2a/visual/"
        }
      }
    },
    "B04": {
      "alternate": {
        "s3": {
          "href": "s3://my-bucket/sentinel-2-l2a/B04/"
        }
      }
    }
  }
}
```

#### Schema-Driven Scaffolding

The ExtensionModule automatically:

1. **Fetches** the JSON Schema from `schema_uri`
2. **Parses** the schema structure
3. **Scaffolds** required fields with null values
4. **Applies** your defaults using wildcards and template variables
5. **Tags** items with the extension URI in `stac_extensions`

This approach is much simpler than the old method of manually adding extension properties!

---

## Understanding Data Enrichment

### What is Sidecar Data?

"Sidecar data" is external data (CSV, JSON) that supplements main STAC items. Examples:

**cloud-cover.json (Dict format - keys are item IDs):**

```json
{
  "S2A_MSIL2A_20240101T000000_001": {
    "cloud_cover": 15.3,
    "snow_cover": 2.1
  },
  "S2A_MSIL2A_20240102T000000_002": {
    "cloud_cover": 8.7,
    "snow_cover": 0.0
  }
}
```

**cloud-cover.json (List format - with id field):**

```json
[
  {
    "id": "S2A_MSIL2A_20240101T000000_001",
    "cloud_cover": 15.3,
    "snow_cover": 2.1
  },
  {
    "id": "S2A_MSIL2A_20240102T000000_002",
    "cloud_cover": 8.7,
    "snow_cover": 0.0
  }
]
```

> **Note**: TransformModule only supports JSON format, not CSV.

### TransformModule in Detail

The TransformModule merges sidecar data with items:

```yaml
- id: enrich
  module: TransformModule
  depends_on: [extend]
  config:
    # Source of sidecar data (JSON file)
    input_file: samples/sentinel-2-l2a-api/sidecar-data/cloud-cover.json

    # How to merge: 'merge' (keep existing) or 'update' (overwrite)
    strategy: "merge"

    # Optional: Map sidecar fields to item properties
    # Key = target field name in item properties
    # Value = JMESPath query applied to sidecar entry
    field_mapping:
      cloud_cover: "cloud_cover"  # item.properties.cloud_cover ← sidecar_entry.cloud_cover
      snow_cover: "snow_cover"    # item.properties.snow_cover ← sidecar_entry.snow_cover

    # Optional: How to handle missing sidecar data
    handle_missing: "ignore"  # or 'warn', 'error'
```

**How field_mapping works:**

For dict format sidecar data (keys are item IDs), TransformModule:

1. Looks up item ID in sidecar data
2. Applies JMESPath queries to the sidecar entry
3. Merges results into `item.properties` using the mapping keys

**Note**: `sidecar_id_path` is only needed for list format sidecar data. Dict format automatically uses keys as item IDs.

After enrichment, each item includes the merged properties:

```json
{
  "id": "S2A_MSIL2A_20240101T000000_001",
  "properties": {
    "datetime": "2024-01-01T00:00:00Z",
    "cloud_cover": 15.3,      // ← From sidecar
    "snow_cover": 2.1,         // ← From sidecar
    // ... other properties
  }
}
```

---

## Common Enrichment Patterns

### Pattern 1: Quality Metrics from External Database

Merge quality scores from a JSON file:

```yaml
steps:
  - id: ingest
    module: IngestModule
    # ...

  - id: enrich_quality
    module: TransformModule
    depends_on: [ingest]
    config:
      input_file: data/quality-metrics.json
      sidecar_id_path: "id"
      strategy: "merge"
      field_mapping:
        quality_score: "quality_score"
        processing_level: "processing_level"
        validation_status: "validation_status"
      handle_missing: "warn"

  - id: output
    module: OutputModule
    depends_on: [enrich_quality]
    config:
      base_dir: ./outputs
```

**data/quality-metrics.json:**

```json
{
  "S2A_MSI...": {
    "quality_score": 0.95,
    "processing_level": "L2A",
    "validation_status": "passed"
  },
  "S2B_MSI...": {
    "quality_score": 0.87,
    "processing_level": "L2A",
    "validation_status": "passed"
  }
}
```

### Pattern 2: Multiple Sidecar Sources

Chain enrichment from multiple sources:

```yaml
steps:
  - id: ingest
    module: IngestModule
    # ...

  # First enrichment: Cloud cover
  - id: enrich_clouds
    module: TransformModule
    depends_on: [ingest]
    config:
      input_file: data/cloud-cover.json
      sidecar_id_path: "id"
      strategy: "merge"
      field_mapping:
        eo:cloud_cover: "eo:cloud_cover"
        snow_ice_percentage: "snow_ice_percentage"

  # Second enrichment: Processing metadata
  - id: enrich_metadata
    module: TransformModule
    depends_on: [enrich_clouds]
    config:
      input_file: data/processing-metadata.json
      sidecar_id_path: "id"
      strategy: "merge"
      field_mapping:
        processor_version: "processor_version"
        processing_date: "processing_date"

  - id: output
    module: OutputModule
    depends_on: [enrich_metadata]
    # ...
```

### Pattern 3: Using JMESPath in field_mapping

Extract nested fields from sidecar data using JMESPath queries:

```yaml
- id: enrich
  module: TransformModule
  depends_on: [ingest]
  config:
    input_file: data/calibration.json
    sidecar_id_path: "id"  # Required for list format
    strategy: "update"  # Overwrite existing values
    field_mapping:
      # Key = target field in item.properties
      # Value = JMESPath query applied to sidecar entry
      calibration_factor: "metadata.calibration.factor"
      correction_applied: "metadata.calibration.applied"
      sensor_info: "sensor.name"
    handle_missing: "warn"
```

**data/calibration.json (list format):**

```json
[
  {
    "id": "S2A_MSI...",
    "metadata": {
      "calibration": {
        "factor": 1.05,
        "applied": true
      }
    },
    "sensor": {
      "name": "MSI"
    }
  }
]
```

**Result in item.properties:**

```json
{
  "calibration_factor": 1.05,
  "correction_applied": true,
  "sensor_info": "MSI"
}
```


---

## Comparing Pipeline Outputs

Compare items across all three tutorials:

```bash
# Tutorial 01: API ingestion (basic)
echo "=== Tutorial 01 ===" 
cat outputs/sentinel-2-l2a/items/S2A_*.json | jq '.properties | keys' | head -5

# Tutorial 02: Modified properties
echo "=== Tutorial 02 ===" 
cat outputs/sentinel-2-l2a-tutorial-02/items/S2A_*.json | jq '.properties | keys' | head -5

# Tutorial 03: Extended + enriched
echo "=== Tutorial 03 ===" 
cat outputs/sentinel-2-l2a-tutorial-03/items/S2A_*.json | jq '.properties | keys' | head -5
```

**You should see progressive enrichment:**

- Tutorial 01: Original properties only
- Tutorial 02: Original + processing metadata
- Tutorial 03: Original + extensions + sidecar data

---

## Advanced Patterns

### Custom Sidecar Generation

Generate sidecar data from external sources:

```bash
# Download external quality metrics
python scripts/fetch_quality_metrics.py \
  --output data/quality-metrics.json

# Generate sidecar data from analysis
python scripts/analyze_cloud_cover.py \
  --input data/items.json \
  --output data/cloud-analysis.json
```

Then use in workflow:

```yaml
- id: enrich
  module: TransformModule
  config:
    input_file: data/quality-metrics.json
    sidecar_id_path: "id"
    strategy: "merge"
    field_mapping:
      quality_score: "quality_score"
      recommended_action: "recommended_action"
```

### Combining Extensions and Enrichment

Add both standard extensions and custom enrichment:

```yaml
steps:
  - id: ingest
    module: IngestModule
    config:
      mode: api
      source: https://planetarycomputer.microsoft.com/api/stac/v1
      collection_id: sentinel-2-l2a
      max_items: 100

  # Add standard STAC extensions
  - id: extend
    module: ExtensionModule
    depends_on: [ingest]
    config:
      extensions:
        - name: eo
        - name: projection
        - name: view

  # Enrich with custom analysis
  - id: enrich
    module: TransformModule
    depends_on: [extend]
    config:
      input_file: data/analysis-results.json
      sidecar_id_path: "id"
      strategy: "merge"
      field_mapping:
        ndvi: "ndvi"
        ndwi: "ndwi"
        classification: "classification"

  - id: output
    module: OutputModule
    depends_on: [enrich]
    config:
      base_dir: ./outputs
      format: parquet  # Export to Parquet instead of JSON
      collection_id: sentinel-2-analysis
```

---

## Troubleshooting

### "Sidecar file not found"

**Error**: `[enrich] Sidecar file not found: ...`

**Cause**: Path is relative or file doesn't exist

**Solution**: Generate sidecar data first:

```bash
python scripts/generate_sample_data.py \
  --output-dir samples \
  --collection sentinel-2-l2a
```

### "No matching items in sidecar"

**Error**: `[transform] Item ID not found in sidecar data`

**Cause**: Item IDs don't match between items and sidecar file, or `sidecar_id_path` is incorrect

**Solution**: Verify item IDs match and sidecar format is correct:

```bash
# Check item IDs
cat samples/sentinel-2-l2a-api/data/items.json | jq '.[] | .id' | head -3

# Check sidecar keys (dict format)
cat samples/sentinel-2-l2a-api/sidecar-data/cloud-cover.json | jq 'keys' | head -3

# Check sidecar IDs (list format)
cat samples/sentinel-2-l2a-api/sidecar-data/cloud-cover.json | jq '.[].id' | head -3
```

If using list format, ensure `sidecar_id_path` points to the correct field (default is `"id"`).

### Validation fails after extensions

**Error**: `[validate] Schema validation failed`

**Cause**: Extensions not properly formatted or conflicting with item

**Solution**: Review STAC extension specifications:

```bash
# Valid extension structure
{
  "stac_extensions": [
    "https://stac-extensions.github.io/eo/v1.0.0/schema.json"
  ],
  "properties": {
    "eo:bands": [...]
  }
}
```

---

## Next Steps

- 📚 **[Concepts Guide](../concepts.md)** - Deep dive into architecture
- 🎯 **[Tutorial 01](01-basic-pipeline.md)** - Review API basics
- 🔧 **[Tutorial 02](02-update-pipeline.md)** - Review item modification

---

## Key Takeaways

✅ STAC Extensions standardize **domain-specific metadata**  
✅ Sidecar data enables **flexible external enrichment**  
✅ Multi-step pipelines combine **multiple transformations**  
✅ Complete workflows demonstrate **real-world data processing**  

---

## Related Resources

- [STAC Extensions Registry](https://stac-extensions.github.io/)
- [EO Extension](https://github.com/stac-extensions/eo)
- [Projection Extension](https://github.com/stac-extensions/projection)
- [View Extension](https://github.com/stac-extensions/view)
- [Complete Extension List](https://github.com/stac-extensions)

