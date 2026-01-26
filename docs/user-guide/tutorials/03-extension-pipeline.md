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
    module: EnrichModule
    depends_on: [extend]
    config:
      sidecar_source: samples/sentinel-2-l2a-api/sidecar-data/cloud-cover.json
      merge_key: item_id
      properties_to_merge:
        - cloud_cover
        - snow_cover

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
   EnrichModule (Merge with Sidecar Data)
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

The ExtensionModule adds extensions to items:

```yaml
- id: extend
  module: ExtensionModule
  depends_on: [ingest]
  config:
    extensions:
      # Add EO extension with band information
      - name: eo
        properties:
          bands:
            - name: "B2"
              description: "Blue"
              common_name: "blue"
              center_wavelength: 0.490
              full_width_half_max: 0.098
            - name: "B3"
              description: "Green"
              common_name: "green"
              center_wavelength: 0.560
              full_width_half_max: 0.045

      # Add Projection extension
      - name: projection
        properties:
          epsg: 32633          # UTM zone 33N
          wkt2: "..."          # Optional WKT representation
          proj4: "+proj=utm..."

      # Add View extension (viewing geometry)
      - name: view
        properties:
          incidence_angle: 10.5
          azimuth: 180.0
```

---

## Understanding Data Enrichment

### What is Sidecar Data?

"Sidecar data" is external data (CSV, JSON) that supplements main STAC items. Examples:

**cloud-cover.json:**
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

**cloud-cover.csv:**
```
item_id,cloud_cover,snow_cover
S2A_MSIL2A_20240101T000000_001,15.3,2.1
S2A_MSIL2A_20240102T000000_002,8.7,0.0
```

### EnrichModule in Detail

The EnrichModule merges sidecar data with items:

```yaml
- id: enrich
  module: EnrichModule
  depends_on: [extend]
  config:
    # Source of sidecar data (JSON or CSV)
    sidecar_source: samples/sentinel-2-l2a-api/sidecar-data/cloud-cover.json

    # Key to match items with sidecar records
    merge_key: item_id

    # Properties to extract and merge
    properties_to_merge:
      - cloud_cover
      - snow_cover

    # Optional: namespace to separate enrichment
    namespace: sidecar

    # Optional: only merge if condition is met
    condition: "sidecar.cloud_cover < 30"
```

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

Merge quality scores from a CSV:

```yaml
steps:
  - id: ingest
    module: IngestModule
    # ...

  - id: enrich_quality
    module: EnrichModule
    depends_on: [ingest]
    config:
      sidecar_source: data/quality-metrics.csv
      merge_key: item_id
      properties_to_merge:
        - quality_score
        - processing_level
        - validation_status

  - id: output
    module: OutputModule
    depends_on: [enrich_quality]
    config:
      base_dir: ./outputs
```

**data/quality-metrics.csv:**
```
item_id,quality_score,processing_level,validation_status
S2A_MSI...,0.95,L2A,passed
S2B_MSI...,0.87,L2A,passed
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
    module: EnrichModule
    depends_on: [ingest]
    config:
      sidecar_source: data/cloud-cover.json
      merge_key: item_id
      properties_to_merge:
        - eo:cloud_cover
        - snow_ice_percentage

  # Second enrichment: Processing metadata
  - id: enrich_metadata
    module: EnrichModule
    depends_on: [enrich_clouds]
    config:
      sidecar_source: data/processing-metadata.csv
      merge_key: item_id
      properties_to_merge:
        - processor_version
        - processing_date

  - id: output
    module: OutputModule
    depends_on: [enrich_metadata]
    # ...
```

### Pattern 3: Conditional Enrichment

Only merge data matching certain conditions:

```yaml
- id: enrich
  module: EnrichModule
  depends_on: [ingest]
  config:
    sidecar_source: data/calibration.json
    merge_key: item_id
    properties_to_merge:
      - calibration_factor
      - correction_applied

    # Only merge if date is recent (avoid stale calibration)
    condition: "properties.datetime > 2024-01-01"
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
  module: EnrichModule
  config:
    sidecar_source: data/quality-metrics.json
    merge_key: item_id
    properties_to_merge:
      - quality_score
      - recommended_action
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
    module: EnrichModule
    depends_on: [extend]
    config:
      sidecar_source: data/analysis-results.json
      merge_key: item_id
      properties_to_merge:
        - ndvi
        - ndwi
        - classification

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

**Error**: `[enrich] 0 items matched in sidecar data`

**Cause**: `merge_key` doesn't match between items and sidecar

**Solution**: Verify keys match:

```bash
# Check item IDs
cat samples/sentinel-2-l2a-api/data/items.json | jq '.[] | .id' | head -3

# Check sidecar keys
cat samples/sentinel-2-l2a-api/sidecar-data/cloud-cover.json | jq 'keys' | head -3
```

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
