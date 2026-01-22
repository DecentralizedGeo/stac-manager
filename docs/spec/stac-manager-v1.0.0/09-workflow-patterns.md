# Workflow Patterns
## STAC Manager v1.0

> [!NOTE]
> This document outlines common business use cases and how to configure the STAC Manager pipeline to achieve them.

## 1. Zero-to-One Scaffolding
**Goal**: Create a brand new STAC Collection from scratch using a list of known scene IDs.

- **Source**: `SeedModule` (Generates items from IDs).
- **Processor**: `ExtensionModule` (Adds dgeo ownership data).
- **Sink**: `OutputModule` (Writes structure).

**Configuration**:
```yaml
name: "scaffold-new-collection"
description: "Scaffold a new collection from explicit IDs"

strategy: {} # Single execution (no matrix)

steps:
  - id: generator
    module: SeedModule
    config:
      items: ["scene_001", "scene_002"]
      defaults:
        collection: "my-new-collection"

  - id: enrich
    module: ExtensionModule
    config:
      schema_uri: "https://example.com/schemas/dgeo.json"
      defaults:
        "properties.dgeo:ownership.type": "individual"
        "properties.dgeo:ownership.did": "did:key:z6Mk..."

  - id: write
    module: OutputModule
    config:
      base_dir: "./stac-data"
      format: "json"
```

---

## 2. Appending Items (Loader Pattern)
**Goal**: Add a batch of new items (e.g., from a recent processing run) to an *existing* static collection.

- **Philosophy**: Process only the delta. Do not re-read the entire collection.
- **Source**: `IngestModule` (Loads local JSON files/globs).
- **Sink**: `OutputModule` (Writes to the existing collection's directory).

**Configuration**:
```yaml
name: "append-new-items"
strategy: {}
steps:
  - id: load_new_items
    module: IngestModule
    config:
      source_file: "./incoming_data/*.json" # Glob pattern

  - id: write_to_catalog
    module: OutputModule
    config:
      base_dir: "./existing-stac-archive" 
      # Result: ./existing-stac-archive/{collection_id}/items/{item_id}.json
```

---

## 3. Metadata Patching (Maintenance)
**Goal**: Fix a specific metadata error in a list of existing items.

- **Source**: `IngestModule` (Fetches specific items to fix, e.g. via API or ID list).
- **Processor**: `UpdateModule` (Applies patch).
- **Sink**: `OutputModule` (Overwrites the files).

**Configuration**:
```yaml
name: "fix-cloud-cover"
strategy: {}
steps:
  - id: fetch_targets
    module: IngestModule
    config:
      collection_id: "sentinel-2"
      filters:
        ids: ["S2A_..."] # Only fetch what needs fixing

  - id: patch
    module: UpdateModule
    config:
      updates:
        "properties.eo:cloud_cover": 0.0
      auto_update_timestamp: true
      create_missing_paths: true

  - id: overwrite
    module: OutputModule
    config:
      base_dir: "./stac-data" # Overwrites existing files in place
```

---

## 4. Bulk API Mirroring (ETL)
**Goal**: Copy a collection from an external STAC API to local storage, optimizing for throughput.

- **Strategy**: Use `strategy: matrix` to split the job by year or grid cell.
- **Source**: `IngestModule` (API Mode with `RequestSplitter`).
- **Sink**: `OutputModule` (Parquet format for analytics).

**Configuration**:
```yaml
name: "bulk-api-mirroring"
strategy:
  matrix:
    - years: 2020
    - years: 2021
    - years: 2022

steps:
  - id: crawl_api
    module: IngestModule
    config:
      catalog_url: "https://landsatlook.usgs.gov/stac-server"
      collection_id: "landsat-c2-l2"
      filters:
        datetime: "${years}-01-01/${years}-12-31"

  - id: save_analytics
    module: OutputModule
    config:
      format: "parquet"
      base_dir: "./analytics-data"
```

---

## 5. Legacy Data Migration (Sidecar Pattern)
**Goal**: Generate STAC items from a static list of IDs, hydrating metadata from a separate CSV dump (Sidecar).

- **Source**: `SeedModule` (Emits bare IDs or skeleton items).
- **Processor**: `TransformModule` (Joins stream with CSV sidecar by ID).
- **Sink**: `OutputModule` (Writes valid STAC).

**Configuration**:
```yaml
name: "migrate-legacy-csv"
strategy: {}
steps:
  - id: generate_ids
    module: SeedModule
    config:
      items: ["scene_001", "scene_002", "scene_003"]
      defaults:
        collection: "legacy-collection"

  - id: hydrate_from_csv
    module: TransformModule
    config:
      input_file: "./legacy/metadata_dump.csv" # Sidecar lookup source
      schema:
        mappings:
          # System joins automatically on 'id' match
          - source_field: "Cloud_Cover"
            target_field: "properties.eo:cloud_cover"
            type: "float"
          - source_field: "Date_Acquired"
            target_field: "properties.datetime"
            type: "datetime"

  - id: save
    module: OutputModule
    config:
      base_dir: "./stac-output"
```

---

## 6. Deeply Nested JSON Migration (Complex Sidecar)
**Goal**: Generate STAC items using a complex, nested JSON sidecar file (e.g., raw telemetry logs) using JMESPath queries to extract specific values.

- **Source**: `SeedModule` (Generates IDs).
- **Processor**: `TransformModule` (Extracts data from complex JSON structure).
- **Sink**: `OutputModule` (Writes valid STAC).

**Scenario**:
Mapping a raw instrument payload that looks like this:
```json
{
  "data": {
    "logs": [
      {
        "meta": { "scene_id": "scene_001", "time": "..." },
        "telemetry": { ... }
      },
      ...
    ]
  }
}
```

**Configuration**:
```yaml
name: "migrate-complex-json"
strategy: {}
steps:
  - id: generate_ids
    module: SeedModule
    config:
      items: ["scene_001"]
      defaults:
        collection: "telemetry-collection"

  - id: hydrate_complex
    module: TransformModule
    config:
      input_file: "./raw/instrument_log.json"
      # The file contains a list of records under "data.logs"
      data_path: "data.logs" 
      # Each record has the ID in a nested field "meta.scene_id"
      sidecar_id_path: "meta.scene_id"
      
      schema:
        mappings:
          # Extract nested dictionary value
          - source_field: "telemetry.platform"
            target_field: "properties.platform"
            type: "string"

          # Extract value from array of objects using filter
          - source_field: "telemetry.sensors[?type=='optical'].gain | [0]"
            target_field: "properties.optical_gain"
            type: "float"
            
          # Extract list of values
          - source_field: "telemetry.sensors[0].bands"
            target_field: "properties.eo:bands"
            type: "string" # Lists are stored as strings or mapped further

          # Simple nested path
          - source_field: "acquisition_meta.start_time"
            target_field: "properties.datetime"
            type: "datetime"

  - id: save
    module: OutputModule
    config:
      base_dir: "./stac-output"
```
