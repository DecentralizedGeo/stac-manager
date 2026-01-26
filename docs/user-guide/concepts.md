# Concepts Guide: Understanding STAC Manager Architecture

A comprehensive guide to STAC Manager's design, components, and patterns.

---

## Table of Contents

1. [Core Architecture](#core-architecture)
2. [Pipes and Filters Pattern](#pipes-and-filters-pattern)
3. [Module Types](#module-types)
4. [Configuration Patterns](#configuration-patterns)
5. [Data Flow](#data-flow)
6. [Workflow Design](#workflow-design)
7. [Advanced Topics](#advanced-topics)

---

## Core Architecture

### What is STAC Manager?

STAC Manager is a **production-grade orchestration framework** for processing Spatial-Temporal Asset Catalog (STAC) data. It enables users to:

- **Fetch** STAC items from remote APIs or local files
- **Transform** items through configurable pipeline stages
- **Validate** data quality at each step
- **Output** results in multiple formats (JSON, Parquet, GeoPackage)

### Design Philosophy

STAC Manager follows three core principles:

| Principle | Meaning | Benefit |
| --- | --- | --- |
| **Stream-Oriented** | Process items one-at-a-time | Memory-efficient, handles billions of items |
| **Modular** | Chain independent processors | Flexible, reusable, testable |
| **Configuration-Driven** | YAML-based workflows | No code changes, reproducible |

---

## Pipes and Filters Pattern

### Pattern Overview

STAC Manager implements the **Pipes and Filters** architectural pattern, a Unix-inspired model for composable data processing:

```
Input Stream → Filter → Pipe → Filter → Pipe → Filter → Output
                  ↓              ↓              ↓
              Module 1      Module 2      Module 3
```

**Key characteristics:**

- **Filters** (modules) process data independently
- **Pipes** (connections) stream data between filters
- Each filter has a **single responsibility**
- Filters are **stateless** - order independence (usually)
- Data flows **asynchronously** for efficiency

### Real-World Example

Fetching and processing satellite imagery:

```
┌─────────────┐    ┌────────────┐    ┌─────────────┐    ┌──────────┐
│ STAC API    │    │  Filter    │    │  Enrich     │    │ Output   │
│ (Planetary  ├───→│ by cloud   ├───→│ with quality├───→│ to disk  │
│ Computer)   │    │ coverage   │    │ metrics     │    │ (JSON)   │
└─────────────┘    └────────────┘    └─────────────┘    └──────────┘
      Pipe              Pipe              Pipe
```

### Benefits of This Architecture

| Benefit | Why It Matters |
| --- | --- |
| **Scalability** | Process millions of items without loading all into memory |
| **Modularity** | Mix and match modules for different workflows |
| **Testability** | Each module is independently testable |
| **Resilience** | One filter's failure doesn't crash the entire pipeline |
| **Reusability** | Common patterns become shareable modules |

---

## Module Types

### IngestModule (Fetcher)

**Purpose**: Generate STAC items from external sources

**Modes:**

```yaml
# 1. File Mode: Read from JSON/Parquet
mode: file
source: data/items.json

# 2. API Mode: Fetch from remote STAC catalog
mode: api
source: https://planetarycomputer.microsoft.com/api/stac/v1
collection_id: sentinel-2-l2a
max_items: 1000
bbox: [-122.5, 37.5, -122.0, 38.0]
datetime: 2024-01-01/2024-12-31
```

**Output**: Stream of STAC item dictionaries

**When to use:**
- Starting any workflow
- Fetching fresh data from catalogs
- Testing with pre-generated samples

---

### ValidateModule (Filter)

**Purpose**: Verify STAC compliance and data quality

**Configuration:**

```yaml
module: ValidateModule
config:
  strict: true          # Fail on any error vs. warn only
  check_assets: true    # Verify all assets are accessible
  check_extensions: true # Verify all extensions are valid
```

**Output**: Validated items (filtering out invalid ones if `strict: false`)

**When to use:**
- Ensure data quality before output
- Catch issues early in the pipeline
- Debug data source problems

---

### ModifyModule (Filter)

**Purpose**: Transform item properties in-flight

**Operations:**

```yaml
module: ModifyModule
config:
  operations:
    # Add or update properties
    - type: add_property
      path: properties.custom_field
      value: "processed"

    # Rename properties
    - type: rename_property
      from_path: properties.old_name
      to_path: properties.new_name

    # Remove properties
    - type: delete_property
      path: properties.obsolete_field

    # Conditional operations
    - type: conditional_property
      condition: "properties.eo:cloud_cover < 20"
      path: properties.is_clear
      value: true
```

**Output**: Modified items

**When to use:**
- Add processing metadata
- Standardize property names
- Filter by computed conditions

---

### ExtensionModule (Filter)

**Purpose**: Add STAC extensions to items

**Configuration:**

```yaml
module: ExtensionModule
config:
  extensions:
    - name: eo
      properties:
        bands:
          - name: "B2"
            common_name: "blue"
            center_wavelength: 0.490

    - name: projection
      properties:
        epsg: 32633

    - name: view
      properties:
        incidence_angle: 10.5
```

**Output**: Extended items with standardized properties

**When to use:**
- Add domain-specific metadata
- Standardize item structure across collections
- Enable downstream analysis tools

---

### EnrichModule (Filter)

**Purpose**: Merge external sidecar data with items

**Configuration:**

```yaml
module: EnrichModule
config:
  sidecar_source: data/metrics.json  # or .csv
  merge_key: item_id
  properties_to_merge:
    - cloud_cover
    - quality_score
    - processing_level
```

**Sidecar Format (JSON):**
```json
{
  "S2A_MSI..._001": {
    "cloud_cover": 15.3,
    "quality_score": 0.95
  }
}
```

**Sidecar Format (CSV):**
```
item_id,cloud_cover,quality_score
S2A_MSI..._001,15.3,0.95
```

**Output**: Enriched items with merged data

**When to use:**
- Combine STAC items with external analysis
- Add quality metrics from separate systems
- Merge multi-source datasets

---

### OutputModule (Bundler)

**Purpose**: Persist items to storage in standard formats

**Configurations:**

```yaml
module: OutputModule
config:
  base_dir: ./outputs
  format: json              # json, parquet, geopackage, etc.
  collection_id: my-data
  partition_by: date        # Optional: partition output
```

**Output Structures:**

```
outputs/
├── collection.json        # Collection metadata
├── catalog.json          # STAC Catalog
└── items/
    ├── S2A_MSI_001.json
    ├── S2A_MSI_002.json
    └── ...
```

**When to use:**
- Final stage of any pipeline
- Creating shareable datasets
- Long-term storage

---

## Configuration Patterns

### Pattern 1: Linear Pipeline

Sequential processing with single output:

```yaml
steps:
  - id: ingest
    module: IngestModule
    config: {...}

  - id: validate
    module: ValidateModule
    depends_on: [ingest]
    config: {...}

  - id: output
    module: OutputModule
    depends_on: [validate]
    config: {...}
```

**Data flow:** Ingest → Validate → Output

**Use case:** Simple data ingestion and storage

---

### Pattern 2: Enrichment Pipeline

Multiple transformation stages:

```yaml
steps:
  - id: ingest
    module: IngestModule
    config: {...}

  - id: modify
    module: ModifyModule
    depends_on: [ingest]
    config: {...}

  - id: extend
    module: ExtensionModule
    depends_on: [modify]
    config: {...}

  - id: enrich
    module: EnrichModule
    depends_on: [extend]
    config: {...}

  - id: validate
    module: ValidateModule
    depends_on: [enrich]
    config: {...}

  - id: output
    module: OutputModule
    depends_on: [validate]
    config: {...}
```

**Data flow:** Ingest → Modify → Extend → Enrich → Validate → Output

**Use case:** Complex data preparation with multiple enrichment sources

---

### Pattern 3: Branching Pipeline

Multiple paths from single source:

```yaml
steps:
  - id: ingest
    module: IngestModule
    config: {...}

  # Path 1: Direct output
  - id: output_raw
    module: OutputModule
    depends_on: [ingest]
    config:
      collection_id: raw-data

  # Path 2: Processed output
  - id: modify
    module: ModifyModule
    depends_on: [ingest]
    config: {...}

  - id: output_processed
    module: OutputModule
    depends_on: [modify]
    config:
      collection_id: processed-data
```

**Data flow:** Ingest → {Output Raw, Modify → Output Processed}

**Use case:** Generate multiple outputs from single source

---

## Data Flow

### Item Lifecycle

Every STAC item progresses through the pipeline:

```
┌─────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐   ┌────────┐
│ Created │→ │ Modified │→ │ Extended │→ │Enriched│→ │Validated
└─────────┘   └──────────┘   └──────────┘   └────────┘   └────────┘
                                                                │
                                                                ↓
                                                          ┌──────────┐
                                                          │  Output  │
                                                          │  (Disk)  │
                                                          └──────────┘
```

### Example: Sentinel-2 Processing

**Step 1: Ingest**
```json
{
  "id": "S2A_MSIL2A_20240101T000000_N0509_R002_T33UUP_20240101T000000",
  "type": "Feature",
  "properties": {
    "datetime": "2024-01-01T00:00:00Z",
    "eo:cloud_cover": 15.3
  }
}
```

**Step 2: Modify**
```json
{
  // ... same as above, plus:
  "properties": {
    "processed": true,
    "processing_date": "2024-01-26T00:00:00Z"
  }
}
```

**Step 3: Extend (Add EO Extension)**
```json
{
  // ... same as above, plus:
  "stac_extensions": ["https://stac-extensions.github.io/eo/v1.0.0/schema.json"],
  "properties": {
    "eo:bands": [
      {"name": "B2", "common_name": "blue"},
      {"name": "B3", "common_name": "green"},
      {"name": "B4", "common_name": "red"}
    ]
  }
}
```

**Step 4: Enrich (Merge Quality Data)**
```json
{
  // ... same as above, plus:
  "properties": {
    "quality_score": 0.95,
    "validation_status": "passed"
  }
}
```

**Step 5: Output**
Saved to: `outputs/sentinel-2-l2a-tutorial-03/items/S2A_MSIL2A_*.json`

---

## Workflow Design

### Workflow Structure

Every workflow is a directed acyclic graph (DAG) of modules:

```yaml
name: my-workflow
version: "1.0"
description: "..."

steps:
  - id: unique_name
    module: ModuleType
    depends_on: [optional_dependencies]
    config:
      # Module-specific configuration
```

### Best Practices

**1. Naming Convention**

Use descriptive, action-oriented names:

```yaml
# ✓ Good
- id: ingest_sentinel2
- id: filter_by_cloud_cover
- id: validate_stac_compliance
- id: output_to_parquet

# ✗ Avoid
- id: step1
- id: filter
- id: validate
- id: output
```

**2. Dependency Management**

Define explicit dependencies:

```yaml
# ✓ Good: Clear dependencies
- id: modify
  depends_on: [ingest]

- id: validate
  depends_on: [modify]

# ✗ Avoid: Implicit ordering
# (relies on configuration order, fragile)
```

**3. Configuration Reusability**

Use variables and anchors for common configurations:

```yaml
# YAML anchors for reuse
common_output: &common_output
  base_dir: ./outputs
  format: json

steps:
  - id: output_raw
    module: OutputModule
    config:
      <<: *common_output
      collection_id: raw

  - id: output_processed
    module: OutputModule
    config:
      <<: *common_output
      collection_id: processed
```

---

## Advanced Topics

### Async Streaming

STAC Manager uses async streams for efficiency:

```python
# Items flow through the pipeline without loading all into memory
async for item in ingest_module.process():
    modified_item = modify_module.process(item)
    extended_item = extend_module.process(modified_item)
    # ... process one at a time
    await output_module.write(extended_item)
```

**Benefits:**
- Handle millions of items with minimal RAM
- Process can start before all data is fetched
- Early error detection stops unnecessary processing

---

### Error Handling

Modules have built-in error recovery:

```yaml
- id: validate
  module: ValidateModule
  config:
    strict: false          # Continue on validation errors
    error_threshold: 0.05  # Fail if > 5% of items error
    error_log: logs/errors.json
```

---

### Custom Modules

Extend STAC Manager with custom processors:

```python
from stac_manager.core import Module

class CustomFilterModule(Module):
    """Custom module for domain-specific filtering."""
    
    async def process(self, item):
        """Process a single item."""
        if self.config.get('filter_condition'):
            if evaluate(self.config['filter_condition'], item):
                return item
        return None
```

Use in workflow:

```yaml
- id: custom_filter
  module: CustomFilterModule
  depends_on: [ingest]
  config:
    filter_condition: "properties.eo:cloud_cover < 20"
```

---

### Performance Optimization

**1. Batch Processing**

Process items in batches:

```yaml
- id: enrich
  module: EnrichModule
  config:
    batch_size: 100  # Process 100 items at a time
    sidecar_source: data/metrics.json
```

**2. Parallel Execution**

Process independent paths concurrently:

```yaml
steps:
  - id: ingest
    module: IngestModule
    config: {...}

  # Path 1: Process for quality
  - id: validate
    module: ValidateModule
    depends_on: [ingest]
    config: {...}

  # Path 2: Process for enrichment (runs in parallel)
  - id: enrich
    module: EnrichModule
    depends_on: [ingest]
    config: {...}

  # Merge paths
  - id: output
    module: OutputModule
    depends_on: [validate, enrich]
    config: {...}
```

---

## Workflow Examples

### Example 1: Simple Data Import

```yaml
name: import-sentinel2
steps:
  - id: ingest
    module: IngestModule
    config:
      mode: api
      source: https://planetarycomputer.microsoft.com/api/stac/v1
      collection_id: sentinel-2-l2a
      max_items: 100

  - id: validate
    module: ValidateModule
    depends_on: [ingest]
    config:
      strict: true

  - id: output
    module: OutputModule
    depends_on: [validate]
    config:
      base_dir: ./data
      format: json
```

### Example 2: Data Preparation

```yaml
name: prepare-analysis
steps:
  - id: ingest
    module: IngestModule
    config:
      mode: file
      source: raw-data/items.json

  - id: filter
    module: ModifyModule
    depends_on: [ingest]
    config:
      operations:
        - type: conditional_property
          condition: "properties.eo:cloud_cover < 20"
          path: properties.passes_filter
          value: true

  - id: extend
    module: ExtensionModule
    depends_on: [filter]
    config:
      extensions:
        - name: eo
        - name: projection

  - id: validate
    module: ValidateModule
    depends_on: [extend]
    config:
      strict: true

  - id: output
    module: OutputModule
    depends_on: [validate]
    config:
      base_dir: ./processed
      format: parquet
```

---

## Summary

### Key Concepts

| Concept | Description |
| --- | --- |
| **Pipes and Filters** | Modular data processing architecture |
| **IngestModule** | Fetches data from sources |
| **Modifier Modules** | Transform data in-flight |
| **OutputModule** | Persists processed data |
| **Workflow** | YAML-based DAG of modules |
| **Streaming** | Process data asynchronously |

### Next Steps

1. **[Tutorial 01](01-basic-pipeline.md)** - Learn API ingestion
2. **[Tutorial 02](02-update-pipeline.md)** - Learn item modification
3. **[Tutorial 03](03-extension-pipeline.md)** - Learn enrichment
4. Explore custom workflows for your use case

---

## Related Documentation

- [System Architecture](../../spec/stac-manager-v1.0.0/00-system-overview.md)
- [Module Reference](../../spec/stac-manager-v1.0.0/03-module-reference.md)
- [Configuration Guide](../../spec/stac-manager-v1.0.0/02-configuration-schema.md)
- [Python API](../../spec/stac-manager-v1.0.0/04-python-library-api.md)
