# API/Interface Specification

## STAC Manager v1.0

**Status**: Draft  
**Version**: 1.0.0  
**Last Updated**: January 13, 2026  
**Based On**: [STAC-Manager-PRD-v1.0.3](../../development/STAC-Manager-PRD-v1.0.3.md)  
**Architecture**: [Technical Architecture Specification](./technical-architecture-spec.md)

---

## Table of Contents

1. [Overview](#overview)
2. [CLI Interface](#cli-interface)
3. [YAML Configuration Schema](#yaml-configuration-schema)
4. [Python Library API](#python-library-api)
5. [Module I/O Contracts](#module-io-contracts)
6. [Extension Interface](#extension-interface)
7. [Output Formats](#output-formats)

---

## Overview

This specification defines the user-facing interfaces for the STAC Manager:

- **CLI**: Command-line tool for workflow execution
- **YAML Configuration**: Declarative workflow definitions
- **Python Library**: Programmatic API for custom scripts
- **Module Contracts**: Input/output specifications for each module
- **Extension Interface**: How to create custom STAC extensions

---

## CLI Interface

The CLI provides a single entry point with subcommands for different operations.

### Main Command

```bash
stac-manager [OPTIONS] COMMAND [ARGS]...
```

**Global Options:**

- `--config PATH`: Path to YAML configuration file (default: `./config.yaml`)
- `--log-level [DEBUG|INFO|WARNING|ERROR]`: Override log level from config
- `--log-file PATH`: Override log file path from config
- `--help`: Show help message
- `--version`: Show version information

### Subcommands

#### 1. `run-workflow` - Execute a workflow from YAML config

```bash
stac-manager run-workflow --config WORKFLOW.yaml [OPTIONS]
```

**Options:**

- `--config PATH`: Path to workflow YAML file (required)
- `--dry-run`: Validate workflow without executing
- `--output-failures PATH`: Path for failure report JSON (default: `./failures.json`)

**Example:**

```bash
stac-manager run-workflow --config workflows/cmr-stac-ingest.yaml
```

#### 2. `validate-workflow` - Validate workflow configuration

```bash
stac-manager validate-workflow --config WORKFLOW.yaml
```

**Output:**

- Validation errors (if any)
- Workflow DAG visualization (mermaid diagram)
- Exit code 0 if valid, 1 if invalid

**Example:**

```bash
stac-manager validate-workflow --config my-workflow.yaml
```

#### 3. `discover` - List collections from a STAC API

```bash
stac-manager discover --catalog-url URL [OPTIONS]
```

**Options:**

- `--catalog-url URL`: STAC API endpoint (required)
- `--collection-ids ID [ID...]`: Filter by collection IDs
- `--output PATH`: Save results to JSON file (default: stdout)

**Example:**

```bash
stac-manager discover \
  --catalog-url https://cmr.earthdata.nasa.gov/stac/v1 \
  --output collections.json
```

#### 4. `validate-stac` - Validate STAC Items/Collections

```bash
stac-manager validate-stac --input PATH [OPTIONS]
```

**Options:**

- `--input PATH`: Path to STAC JSON file or directory (required)
- `--extensions URL [URL...]`: Additional extension schemas to validate
- `--strict`: Fail on warnings

**Example:**

```bash
stac-manager validate-stac \
  --input ./output/items/ \
  --extensions https://stac-extensions.github.io/dgeo/v1.0.0/schema.json
```

#### 5. `list-extensions` - List available extensions

```bash
stac-manager list-extensions
```

**Output:**

```
Built-in Extensions:
  - dgeo (DecentralizedGeo Extension)
    Module: stac_manager.extensions.dgeo.DgeoExtension
    Schema: https://raw.githubusercontent.com/DecentralizedGeo/dgeo-asset/.../schema.json
  
  - alternate-assets (Alternate Assets Extension)
    Module: stac_manager.extensions.alternate_assets.AlternateAssetsExtension
    Schema: https://stac-extensions.github.io/alternate-assets/v1.0.0/schema.json
```

---

## YAML Configuration Schema

Workflows are defined in YAML files following this schema.

### Root Structure

```yaml
workflow:
  name: string (required)
  description: string (optional)
  steps: list<Step> (required)

logging:
  level: DEBUG | INFO | WARNING | ERROR (default: INFO)
  file: string (optional, path to log file)

processing:
  concurrency: integer (default: 5)
  rate_limit: float (default: 10.0, requests per second)
  retry_max_attempts: integer (default: 3)
  retry_backoff_base: float (default: 2.0)
```

### Step Definition

```yaml
steps:
  - id: string (required, unique within workflow)
    module: string (required, module class name)
    config: dict (module-specific configuration)
    depends_on: list<string> (optional, list of step IDs)
```

### Module-Specific Configurations

#### DiscoveryModule

```yaml
- id: discover
  module: DiscoveryModule
  config:
    catalog_url: string (required)
    collection_ids: list<string> (optional)
    filters:
      temporal:
        start_date: string (ISO 8601)
        end_date: string (ISO 8601)
      spatial:
        bbox: [minx, miny, maxx, maxy]
```

#### IngestModule

```yaml
- id: ingest
  module: IngestModule
  config:
    # Direct collection specification (alternative to depending on discover)
    collection_ids: list<string> (optional, if not using DiscoveryModule)
    
    # Fetching parameters
    limit: integer (optional, max items to fetch)
    concurrency: integer (optional, default from global)
    rate_limit: float (optional, default from global)
    
    # Item-level filters (separate from Collection-level filters)
    filters:
      temporal:
        start_date: string (ISO 8601)
        end_date: string (ISO 8601)
      spatial:
        bbox: [minx, miny, maxx, maxy]
      query:
        "properties.eo:cloud_cover": {"lt": 10}  # Example CQL2 query
  
  depends_on: [discover]  # Optional if collection_ids specified
```

#### TransformModule

```yaml
- id: transform
  module: TransformModule
  config:
    source_file: string (path to source data file)
    schema_file: string (path to transformation schema.yaml)
    # OR inline schema
    schema:
      mappings:
        - source_field: string
          target_field: string
          type: string | integer | float | datetime
          default: any (optional)
```

#### ScaffoldModule

```yaml
- id: scaffold
  module: ScaffoldModule
  config:
    # Scaffold mode
    mode: items | collection | catalog | template (default: items)
    
    # Collection/Catalog information
    collection_id: string (required for items mode)
    base_url: string (optional, for absolute link generation)
    
    # Default values for scaffolded objects
    defaults:
      license: string (e.g., "CC0-1.0")
      providers: list (default provider info)
      geometry: null | object (default geometry if source lacks one)
      
    # Template scaffolding (when mode: template)
    template:
      type: catalog | collection | item
      output_path: string (where to write template JSON)
      include_sample_item: boolean (default: true for collection/catalog types)
```

#### ExtensionModule

```yaml
- id: apply_dgeo
  module: ExtensionModule
  config:
    extension: dgeo  # Built-in shortcut
    # OR full module path
    # extension: my_package.extensions.MyExtension
    config:
      # Extension-specific fields
      ownership:
        did: string
      licensing:
        license: string
```

#### ValidateModule

```yaml
- id: validate
  module: ValidateModule
  config:
    strict: boolean (default: false)
    extension_schemas: list<string> (URLs to schemas)
```

#### UpdateModule

```yaml
- id: update
  module: UpdateModule
  config:
    # Source of Items/Collections to update
    source_file: string (path to JSON/Parquet file with existing STAC metadata)
    # OR use items from previous step via depends_on
    
    # Update specifications
    updates:
      properties.datetime: "2024-01-15T00:00:00Z"
      assets.thumbnail.href: "./thumbnails/{id}.png"  # {id} replaced with Item ID
    mode: merge | replace (default: merge)
```

#### OutputModule

```yaml
- id: output
  module: OutputModule
  config:
    format: json | parquet
    output_path: string (required)
    organize_by: item_id | flat (default: item_id)
    # item_id: Each Item in subdirectory named by its ID (for sidecar files)
    # flat: All Items in single directory (no sidecar files)
```

### Complete Example

> [!NOTE]
> **Multiple Workflows**: Currently, each YAML file defines a single workflow. To run different workflows, use separate YAML files and specify via `--config` flag. Future versions may support multiple workflow definitions in a single file with workflow selection.

```yaml
workflow:
  name: nasa_earth_catalog
  description: Ingest NASA Earth data from CMR-STAC, apply dgeo, and output

  steps:
    - id: discover
      module: DiscoveryModule
      config:
        catalog_url: https://cmr.earthdata.nasa.gov/stac/v1
        collection_ids:
          - MODIS_*
    
    - id: ingest
      module: IngestModule
      config:
        limit: 10000
      depends_on: [discover]
    
    - id: apply_dgeo
      module: ExtensionModule
      config:
        extension: dgeo
        config:
          ownership:
            did: "did:geo:nasa"
      depends_on: [ingest]
    
    - id: validate
      module: ValidateModule
      config:
        strict: false
      depends_on: [apply_dgeo]
    
    - id: output
      module: OutputModule
      config:
        format: parquet
        output_path: ./output/cmr-stac
        organize_by: item_id  # Each Item in subdirectory by ID
      depends_on: [validate]

logging:
  level: INFO
  file: ./logs/nasa-catalog.log

processing:
  concurrency: 10
  rate_limit: 10.0
```

---

## Python Library API

The toolkit can be used programmatically as a Python library.

### High-Level API (Orchestrator)

```python
from stac_catalog_manager import WorkflowOrchestrator
import asyncio

# Load workflow from YAML file
config = {
    'workflow': {
        'name': 'my_workflow',
        'steps': [...]
    }
}

# Create and run orchestrator
orchestrator = WorkflowOrchestrator(config)
orchestrator.load_workflow(config['workflow'])

# Execute workflow
result = asyncio.run(orchestrator.execute())

# Check results
print(f"Total steps: {result['total_steps']}")
print(f"Successful: {result['successful_steps']}")
print(f"Failures: {result['total_failures']}")
```

### Module-Level API

Each module can be used independently:

```python
from stac_manager.modules import (
    DiscoveryModule,
    IngestModule,
    ExtensionModule,
    OutputModule
)
from stac_manager.core import WorkflowContext, FailureCollector
import logging
import asyncio

# Set up context
context = WorkflowContext(
    config={'catalog_url': 'https://cmr.earthdata.nasa.gov/stac/v1'},
    logger=logging.getLogger(__name__),
    failure_collector=FailureCollector(),
    data={}
)

async def main():
    # Step 1: Discover collections
    discovery = DiscoveryModule({'catalog_url': 'https://cmr.earthdata.nasa.gov/stac/v1'})
    collections = await discovery.execute(context)
    context.data['collections'] = collections
    
    # Step 2: Ingest items
    ingest = IngestModule({'limit': 100})
    items = await ingest.execute(context)
    context.data['items'] = items
    
    # Step 3: Apply extension
    ext = ExtensionModule({
        'extension': 'dgeo',
        'config': {'ownership': {'did': 'did:geo:test'}}
    })
    extended_items = await ext.execute(context)
    context.data['extended_items'] = extended_items
    
    # Step 4: Output
    output = OutputModule({
        'format': 'json',
        'output_path': './output'
    })
    await output.execute(context)

asyncio.run(main())
```

### Utility Functions

```python
from stac_manager.utils import (
    validate_workflow_config,
    generate_processing_summary,
    setup_logger
)

# Validate workflow YAML before execution
errors = validate_workflow_config(config)
if errors:
    print(f"Invalid configuration: {errors}")
    sys.exit(1)

# Set up logging
logger = setup_logger(config)

# Generate summary report
summary = generate_processing_summary(result, failure_collector)
print(summary)
```

---

## Module I/O Contracts

This section defines the input and output contracts for each module.

### DiscoveryModule

**Input (config):**

```python
{
    'catalog_url': str,                    # Required
    'collection_ids': list[str] | None,   # Optional
    'filters': {                           # Optional
        'temporal': {
            'start_date': str,             # ISO 8601
            'end_date': str                # ISO 8601
        },
        'spatial': {
            'bbox': [float, float, float, float]
        }
    }
}
```

**Output:**

```python
list[pystac.Collection]  # List ofCollection objects
```

---

### IngestModule

**Input (config):**

```python
{
    'limit': int | None,           # Optional, max items to fetch
    'concurrency': int,            # Optional, default 5
    'rate_limit': float            # Optional, default 10.0
}
```

**Input (context.data):**

```python
{
    'discover': list[pystac.Collection]  # From DiscoveryModule
}
```

**Output:**

```python
list[pystac.Item]  # List of Item objects
```

---

### TransformModule

**Input (config):**

```python
{
    'source_file': str,            # Path to source data file
    'schema_file': str | None,     # Path to transformation schema
    'schema': dict | None          # Inline transformation schema
}
```

**Input (context.data):**

- None (reads from source file)

**Output:**

```python
list[dict]  # List of transformed data dictionaries
```

**Transformation Schema Format:**

```yaml
mappings:
  - source_field: source.metadata.datetime
    target_field: properties.datetime
    type: datetime
    format: "%Y-%m-%dT%H:%M:%SZ"
  
  - source_field: geometry.coordinates
    target_field: geometry
    type: geometry
    default: null
```

---

### ScaffoldModule

**Input (config):**

```python
{
    'collection_id': str,          # Required
    'base_url': str | None         # Optional, for link generation
}
```

**Input (context.data):**

```python
{
    'transform': list[dict]        # From TransformModule
}
```

**Output:**

```python
list[pystac.Item]  # List of scaffolded STAC Items
```

---

### ExtensionModule

**Input (config):**

```python
{
    'extension': str,              # Extension name or module path
    'config': dict                 # Extension-specific configuration
}
```

**Input (context.data):**

```python
{
    'items': list[pystac.Item]    # From previous step
}
```

**Output:**

```python
list[pystac.Item]  # List of Items with extension fields applied
```

---

### ValidateModule

**Input (config):**

```python
{
    'strict': bool,                      # Default False
    'extension_schemas': list[str]       # Optional, URLs to schemas
}
```

**Input (context.data):**

```python
{
    'items': list[pystac.Item]          # From previous step
}
```

**Output:**

```python
list[pystac.Item]  # List of valid Items (invalid ones logged to failures)
```

---

### UpdateModule

**Input (config):**

```python
{
    'updates': dict,               # Field paths to new values
    'mode': 'merge' | 'replace'    # Default 'merge'
}
```

**Input (context.data):**

```python
{
    'items': list[pystac.Item]    # From previous step
}
```

**Output:**

```python
list[pystac.Item]  # List of updated Items
```

---

### OutputModule

**Input (config):**

```python
{
    'format': 'json' | 'parquet',         # Required
    'output_path': str,                    # Required
    'organize_by': 'item_id' | 'flat'      # Default 'item_id'
}
```

**Input (context.data):**

```python
{
    'items': list[pystac.Item]            # From previous step
}
```

**Output:**

```python
{
    'files_written': list[str],            # Paths to output files
    'total_items': int,                    # Total Items written
    'manifest_path': str                   # Path to output manifest
}
```

---

## Extension Interface

Custom extensions must implement the `Extension` protocol.

### Extension Protocol

```python
from typing import Protocol
import pystac

class Extension(Protocol):
    """Protocol for custom STAC extensions."""
    
    # Class attributes
    extension_name: str      # e.g., "my-extension"
    schema_url: str          # URL to JSON schema
    
    def apply(
        self,
        item: pystac.Item | pystac.Collection,
        config: dict
    ) -> pystac.Item | pystac.Collection:
        """
        Apply extension fields to STAC object.
        
        Args:
            item: STAC Item or Collection to extend
            config: Extension-specific config from workflow YAML
        
        Returns:
            Extended STAC object with extension fields added
        """
        ...
    
    def validate(
        self,
        item: pystac.Item | pystac.Collection
    ) -> tuple[bool, list[str]]:
        """
        Validate extension fields.
        
        Args:
            item: STAC Item or Collection with extension fields
        
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        ...
```

### Example Custom Extension

```python
import pystac
from stac_validator import stac_validator

class CompanyMetadataExtension:
    """Custom extension for company-specific metadata."""
    
    extension_name = "company-metadata"
    schema_url = "https://example.com/schemas/company-metadata.json"
    
    def apply(
        self,
        item: pystac.Item,
        config: dict
    ) -> pystac.Item:
        """Apply company metadata fields."""
        
        # Add extension to stac_extensions array
        if self.schema_url not in item.stac_extensions:
            item.stac_extensions.append(self.schema_url)
        
        # Apply extension fields
        item.properties['company:classification'] = config.get('classification', 'public')
        item.properties['company:retention_years'] = config.get('retention_years', 7)
        item.properties['company:department'] = config.get('department')
        
        return item
    
    def validate(self, item: pystac.Item) -> tuple[bool, list[str]]:
        """Validate against company metadata schema."""
        
        validator = stac_validator.StacValidator()
        is_valid = validator.validate_dict(
            item.to_dict(),
            custom_schema=self.schema_url
        )
        
        errors = []
        if not is_valid:
            errors = validator.message if isinstance(validator.message, list) else [validator.message]
        
        return is_valid, errors
```

### Using Custom Extension in Workflow

```yaml
# workflow.yaml
steps:
  - id: apply_custom
    module: ExtensionModule
    config:
      extension: my_company.extensions.CompanyMetadataExtension  # Full module path
      config:
        classification: "internal"
        retention_years: 10
        department: "Earth Sciences"
```

### Template Mode - Full Hierarchy Example

When scaffolding a Collection template with `include_sample_item: true` (default), the output provides a complete "starter pack":

```yaml
# Scaffold collection template with sample item
steps:
  - id: scaffold_collection_template
    module: ScaffoldModule
    config:
      mode: template
      template:
        type: collection
        output_path: ./templates/my-collection
        include_sample_item: true  # Creates full hierarchy
```

**Generated Structure:**

```
templates/my-collection/
├── collection.json              # Collection template
└── items/
    └── sample-item/
        └── sample-item.json     # Sample Item template
```

**collection.json** (minimal valid template):

```json
{
  "type": "Collection",
  "stac_version": "1.1.0",
  "id": "example-collection",
  "description": "Collection template - replace with your description",
  "license": "CC0-1.0",
  "extent": {
    "spatial": {"bbox": [[-180, -90, 180, 90]]},
    "temporal": {"interval": [[null, null]]}
  },
  "links": [
    {"rel": "self", "href": "./collection.json"},
    {"rel": "item", "href": "./items/sample-item/sample-item.json"}
  ]
}
```

**items/sample-item/sample-item.json** (minimal valid Item template):

```json
{
  "type": "Feature",
  "stac_version": "1.1.0",
  "id": "sample-item",
  "collection": "example-collection",
  "geometry": null,
  "bbox": [],
  "properties": {"datetime": null},
  "links": [
    {"rel": "self", "href": "./sample-item.json"},
    {"rel": "parent", "href": "../../collection.json"},
    {"rel": "collection", "href": "../../collection.json"}
  ],
  "assets": {}
}
```

### Packaging Custom Extension

```toml
# pyproject.toml for custom extension package
[project]
name = "stac-extension-company-metadata"
version = "1.0.0"

dependencies = [
    "pystac >= 1.10.0",
    "stac-validator >= 3.0.0"
]

# Optional: Register extension via entrypoint for auto-discovery (future)
[project.entry-points."stac_manager.extensions"]
company-metadata = "my_company.extensions:CompanyMetadataExtension"
```

---

## Output Formats

### JSON Output

**File Structure (organize_by: item_id):**

Follows [STAC Best Practices](https://github.com/radiantearth/stac-spec/blob/master/best-practices.md#catalog-layout) for catalog layout:

```
output/
├── catalog.json                    # Root catalog
├── collection_A/
│   ├── collection.json             # Collection metadata
│   └── items/
│       ├── item_001/               # Item subdirectory (named by Item ID)
│       │   └── item_001.json       # Item file
│       ├── item_002/
│       │   └── item_002.json
│       └── ...
└── collection_B/
    ├── collection.json
    └── items/
        ├── item_001/
        │   └── item_001.json
        └── ...
```

> [!NOTE]
> **Item Directory Structure**: With `organize_by: item_id`, each Item is stored in a subdirectory under `items/` named by its `id` (e.g., `items/item_001/item_001.json`). This follows STAC best practices and allows for sidecar files (thumbnails, metadata, etc.) to be stored alongside the Item JSON. If your workflow does not generate sidecar files, use `organize_by: flat` to place all Items directly in the `items/` directory.

**File Structure (organize_by: flat):**

```
output/
├── items/
│   ├── item_001.json
│   ├── item_002.json
│   └── ...
└── manifest.json
```

**JSON Format:**
Standard STAC v1.1.0 JSON (pretty-printed):

```json
{
  "type": "Feature",
  "stac_version": "1.1.0",
  "stac_extensions": [
    "https://raw.githubusercontent.com/DecentralizedGeo/dgeo-asset/.../schema.json"
  ],
  "id": "item-001",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[...]]
  },
  "bbox": [-180, -90, 180, 90],
  "properties": {
    "datetime": "2024-01-15T00:00:00Z",
    "dgeo:ownership": {
      "did": "did:geo:nasa"
    }
  },
  "links": [...],
  "assets": {...}
}
```

---

### Parquet Output

**File Structure:**

```
output/
├── items.parquet                   # All items in single file (flat mode)
└── manifest.json
```

**OR (organize_by: collection):**

```
output/
├── collection_A.parquet
├── collection_B.parquet
└── manifest.json
```

**Parquet Schema:**
Uses `stac-geoparquet` library for conversion. Schema includes:

- All STAC properties as columns
- Extension fields as nested structs
- Geometry as WKB column (or GeoParquet geometry type)
- Metadata columns: `stac_version`, `stac_extensions`, `id`

**Reading Parquet Output:**

```python
import pandas as pd
import stac_geoparquet

# Read Parquet file
df = pd.read_parquet('output/items.parquet')

# Convert back to STAC Items
items = stac_geoparquet.to_items(df)
```

---

### Output Manifest

Generated by `OutputModule`, contains metadata about the output:

```json
{
  "workflow": "nasa_earth_catalog",
  "timestamp": "2024-01-15T12:30:00Z",
  "format": "parquet",
  "organize_by": "item_id",
  "files": [
    {
      "path": "output/collection_A.parquet",
      "collection_id": "MODIS_Terra_L3",
      "item_count": 5432,
      "size_bytes": 12456789
    },
    {
      "path": "output/collection_B.parquet",
      "collection_id": "SENTINEL_1A",
      "item_count": 8921,
      "size_bytes": 23456789
    }
  ],
  "total_items": 14353,
  "total_size_bytes": 35913578
}
```

---

## Summary

This API/Interface Specification defines:

1. **CLI Interface**: 5 primary commands for workflow execution, validation, discovery, STAC validation, and extension listing
2. **YAML Schema**: Complete workflow configuration format with module-specific configs
3. **Python Library API**: High-level orchestrator API and module-level programmatic access
4. **Module I/O Contracts**: Clear input/output specifications for all 8 modules
5. **Extension Interface**: Protocol-based contract for creating custom STAC extensions
6. **Output Formats**: JSON and Parquet output structures with manifest generation

These interfaces provide comprehensive user-facing APIs for both declarative (YAML) and programmatic (Python) usage of the toolkit.
