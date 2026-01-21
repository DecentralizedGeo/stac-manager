# Workflow Patterns
## STAC Manager v1.0

> [!NOTE]
> This document outlines common business use cases and how to configure the STAC Manager pipeline to achieve them.

## 1. Zero-to-One Scaffolding
**Goal**: Create a brand new STAC Collection from scratch using a list of known scene IDs.

- **Source**: `SeedModule` (Generates items from IDs).
- **Processor**: `ExtensionModule` (Adds EO/View extension data).
- **Sink**: `OutputModule` (Writes structure).

**Configuration**:
```yaml
name: "scaffold-new-collection"
steps:
  - id: generator
    module: SeedModule
    config:
      items: ["scene_001", "scene_002"]
      defaults:
        collection: "my-new-collection"

  - id: enrich
    module: ExtensionModule
    config: ...

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
      # Optional: removes: ["properties.deprecated_field"]

  - id: overwrite
    module: OutputModule
    config: ...
```

---

## 4. Bulk API Mirroring (ETL)
**Goal**: Copy a collection from an external STAC API to local storage, optimizing for throughput.

- **Strategy**: Use `strategy: matrix` to split the job by year or grid cell.
- **Source**: `IngestModule` (API Mode with `RequestSplitter`).
- **Sink**: `OutputModule` (Parquet format for analytics).

**Configuration**:
```yaml
strategy:
  matrix:
    years: [2020, 2021, 2022]

steps:
  - id: crawl_api
    module: IngestModule
    config:
      collection_id: "landsat-c2-l2"
      filters:
        datetime: "${years}-01-01/${years}-12-31"

  - id: save_analytics
    module: OutputModule
    config:
      format: "parquet"
```
