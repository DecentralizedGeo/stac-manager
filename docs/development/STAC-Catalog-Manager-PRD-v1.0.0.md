# Project Requirements Document (PRD)

## STAC Catalog Manager

**Project**: STAC Catalog Manager — A comprehensive Python toolkit for building, managing, and extending STAC catalogs at scale.

**Version**: 1.0.0 PRD
**Status**: Draft  
**Last Updated**: January 12, 2026

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Project Vision & Goals](#project-vision--goals)
3. [Core Capabilities (v1)](#core-capabilities-v1)
4. [Architecture & Design Principles](#architecture--design-principles)
5. [Functional Requirements](#functional-requirements)
6. [Data Model & Specifications](#data-model--specifications)
7. [Integration Points](#integration-points)
8. [Quality & Validation](#quality--validation)
9. [Configuration & Deployment](#configuration--deployment)
10. [Non-Functional Requirements](#non-functional-requirements)
11. [Success Criteria & Acceptance Scenarios](#success-criteria--acceptance-scenarios)
12. [Future Considerations (Post-v1)](#future-considerations-post-v1)

---

## Executive Summary

**STAC Catalog Manager** is an open-source Python toolkit designed to simplify the creation, modification, and management of STAC (SpatioTemporal Asset Catalog) metadata at scale. The primary goal is to reduce complexity and friction in STAC workflows—enabling users to scaffold, ingest, extend, and maintain STAC catalogs (Collections, Items) from diverse sources (CMR-STAC, other STAC APIs, non-STAC APIs, local data files).

**Key Capabilities:**

- Bulk ingestion from STAC APIs (CMR-STAC, STAC Index catalogs, etc.)
- Metadata transformation & field mapping (JSON, CSV, Parquet, etc.)
- STAC Item scaffolding and bulk creation
- Extension application (dgeo, alternate-assets, and pluggable custom extensions)
- Metadata updates and deletion
- Incremental and full catalog rebuilds
- Asynchronous, parallelized processing for performance at scale (800K+ Items)
- CLI + library interfaces for both direct use and Docker containerization

**Success Metric:** Simplify the management workflows (creation, modification, extension) of STAC metadata by reducing operational friction through a composable, maintainable, and extensible toolkit.

---

## Project Vision & Goals

### Vision Statement

Empower users and organizations to confidently build, maintain, and extend large-scale STAC catalogs by providing a flexible, modular Python toolkit that handles the repetitive, error-prone aspects of metadata management.

### Primary Goals

1. **Workflow Simplification**: Reduce operational complexity in creating and managing STAC catalogs through composable, well-documented tools.

2. **Reusability & Extensibility**: Design the toolkit as an open-source library/CLI usable by diverse organizations and use cases, not just internal pipelines.

3. **Multi-Source Ingestion**: Support ingestion from multiple sources (STAC APIs, non-STAC APIs, local files) with flexible transformation logic.

4. **Extension Support**: Provide pluggable module architecture for STAC extensions (dgeo, alternate-assets, etc.) to reduce coupling and enable custom extensions.

5. **Scale & Performance**: Handle 800K+ Items efficiently through asynchronous operations, parallelization, and rate-limited API access.

6. **Reliable Partial Processing**: Log failures gracefully, flag problematic Items, and allow workflows to continue rather than failing entirely.

7. **Spec-Driven Development**: Design the toolkit with clear specifications and acceptance tests to enable coding agents to implement and extend features.

### Intended Use Cases

1. One-off bulk catalog creation from CMR-STAC
2. Scaffolding new STAC metadata (Catalogs, Collections, Items) following STAC 1.0.0 spec
3. Bulk updates to existing metadata
4. Extending metadata with additional extension fields (dgeo, alternate-assets, custom)
5. Cloning and copying STAC components from external STAC APIs (CMR-STAC, STAC Index catalogs)
6. Continuous/recurring synchronization of new content to existing catalogs
7. Onboarding and transforming non-standard STAC sources (e.g., Astral API) into STAC-compliant metadata
8. Modifying, updating, and removing existing STAC metadata

---

## Core Capabilities (v1)

All of the following capabilities are **required in v1** and are not deferred to later phases.

### 1. Catalog & Collection Discovery & Ingestion

- **Discover Collections**: Query a STAC API catalog URL and retrieve available collections
- **Filter Collections**: Support filtering by collection ID, provider, temporal range, and spatial bounds
- **Retrieve Metadata**: Fetch Collection-level metadata from specified STAC API endpoints
- **Support Multiple Sources**: Work with CMR-STAC, STAC Index catalogs, and any standard STAC 1.0.0 API endpoint

**Inputs:**

- Catalog URL (string)
- List of collection IDs or wildcard selectors
- Optional temporal/spatial filters

**Outputs:**

- Collection metadata (JSON)
- Linked Items metadata or pagination tokens

---

### 2. Item Ingestion & Retrieval

- **Fetch Items**: Retrieve Items from a Collection via STAC API pagination
- **Support Pagination**: Handle paginated responses correctly (cursors, limits, offsets)
- **Batch Processing**: Support parallel/asynchronous fetching of Items with configurable concurrency
- **Partial Failure Handling**: Continue processing if some Items fail; log failures for later review

**Inputs:**

- Collection ID
- Pagination parameters (limit, offset, cursor)
- Concurrency configuration

**Outputs:**

- Item metadata (GeoJSON/JSON)
- Failed Items log with error details

---

### 3. STAC Item Scaffolding

- **Create Minimal Items**: Generate baseline STAC 1.0.0 Items from source data
- **Required Fields**: Ensure all mandatory Item fields are present (id, geometry, bbox, properties, links, assets)
- **Field Mapping**: Support declarative field mapping from source schema to STAC properties/assets
- **Geometry/Bbox Generation**: Compute valid GeoJSON geometries and bounding boxes from spatial metadata

**Inputs:**

- Source data (JSON, CSV, Parquet, etc.)
- Field mapping configuration (YAML/JSON schema)
- Spatial reference information

**Outputs:**

- Valid STAC 1.0.0 Item JSON

---

### 4. Metadata Transformation & Field Mapping

- **Transform Data**: Convert heterogeneous source metadata (JSON, CSV, Parquet, non-STAC APIs) into STAC-compatible fields
- **Field Mapping Strategy**: Support declarative, schema-driven transformations via YAML/JSON config files
- **Data Type Conversion**: Handle type conversions (strings to dates, arrays to single values, nested objects to flat properties, etc.)
- **Reusable Transformations**: Store and reuse transformation schemas for consistency across workflows

**Inputs:**

- Source data files (JSON, CSV, Parquet)
- Transformation schema/mapping configuration (YAML/JSON)
- Optional lookup tables or reference data

**Outputs:**

- Transformed metadata (JSON, Parquet, or CSV)
- Transformation audit log

---

### 5. Extension Application (Pluggable Architecture)

- **dgeo Extension Support**: Apply dgeo extension fields to Items/Collections (supports ownership, licensing, tokenization, provenance)
- **alternate-assets Extension Support**: Apply alternate-assets to Items (alternate locations for the same asset)
- **Pluggable Module System**: Architecture enabling custom extension modules to be plugged in without modifying core code
- **Extension Validation**: Validate extended metadata against extension JSON schemas

**Inputs:**

- Base STAC metadata (Item/Collection)
- Extension configuration (YAML/JSON)
- Extension module (Python class implementing extension interface)

**Outputs:**

- Extended STAC metadata (Item/Collection with extension fields)
- Validation report

---

### 6. Metadata Updates & Deletion

- **Update Items**: Modify existing Item metadata fields (properties, assets, links)
- **Bulk Updates**: Apply updates to multiple Items based on selection criteria
- **Delete Items**: Remove Items from a catalog
- **Update Collections**: Modify Collection-level metadata
- **Versioning**: Track updates using RFC 3339 timestamps in the `updated` field

**Inputs:**

- Item/Collection ID or selection query
- Update payload (new fields, values, or removal specs)

**Outputs:**

- Updated STAC metadata
- Audit log with change summary

---

### 7. Catalog Rebuild Modes

- **Full Rebuild**: Complete replacement of catalog metadata
  - Drop existing Items, re-fetch and re-transform all source data, re-apply extensions, save output
- **Incremental Update**: Add only new/modified Items
  - Compare source with existing catalog, fetch/transform only delta, merge into existing metadata
- **Targeted Updates**: Update specific Items/Collections by ID

**Inputs:**

- Rebuild mode (full, incremental, targeted)
- Source configuration (catalog URL, collection IDs, etc.)
- Target output location

**Outputs:**

- Updated catalog (JSON or Parquet files)
- Change summary (added, modified, deleted counts)

---

### 8. Output Formats & Storage

- **JSON Output**: Save catalog/collection/item metadata as standard JSON files
- **Parquet Output**: Save bulk Item metadata as Parquet for efficient storage and downstream processing
- **File Organization**: Organize output by catalog/collection/item hierarchy
- **Metadata Preservation**: Retain all STAC metadata fields, extensions, and lineage information

**Inputs:**

- Transformed/extended STAC metadata
- Output format preference (JSON, Parquet)
- Output directory or cloud path

**Outputs:**

- Organized, valid STAC files ready for pgstac ingestion

---

### 9. Data Quality, Validation & Logging

- **STAC Validation**: Validate all Items against STAC 1.0.0 JSON schema using `stac-validator`
- **Extension Validation**: Validate extended metadata against extension schemas
- **Error Logging**: Log all errors, warnings, and processing events with timestamps
- **Failed Items Tracking**: Collect failed Items with error details and save to a file (format TBD during implementation)
- **Processing Summary**: Generate end-of-run summary (total processed, successful, failed, skipped) for user review

**Inputs:**

- STAC metadata (JSON)
- Validation schemas (core + extensions)
- Logging configuration

**Outputs:**

- Validation report (pass/fail, error details)
- Failed Items file
- Structured logs

---

### 10. Configuration & Environment Management

- **YAML/JSON Config**: Support declarative workflow configuration (catalog URLs, collection lists, field mappings, extensions, output paths)
- **Environment Variables**: Support secrets and sensitive data via environment variables (e.g., NASA Earthdata Login credentials)
- **Pyproject.toml**: Use `pyproject.toml` for Python dependency management (Python 3.12+)
- **Config Validation**: Validate configuration files against an internal schema before processing

**Inputs:**

- Config file (YAML/JSON)
- Environment variables

**Outputs:**

- Parsed, validated configuration object
- Configuration validation report

---

### 11. CLI & Library Interfaces

- **CLI Subcommands**: Provide a command-line interface with subcommands for each major capability
  - `discover-collections`, `fetch-items`, `transform-metadata`, `scaffold-items`, `apply-extensions`, `validate`, `rebuild-catalog`, `update-metadata`, `output`
  - (Exact command names TBD during specification phase)
- **Python Library**: Expose all capabilities as importable Python classes/functions for programmatic use
- **Docker Support**: Toolkit can be containerized as a Docker image for use in workflow orchestration (Airflow, custom scripts, etc.)

**Inputs:**

- CLI arguments (catalog URL, collection ID, config file, etc.)
- Python function arguments (same as CLI)

**Outputs:**

- Processed STAC metadata
- Status/exit codes
- Log output

---

### 12. Rate Limiting & Asynchronous Processing

- **Rate Limiting**: Implement exponential backoff and configurable rate limits for API requests to avoid throttling
- **Asynchronous Requests**: Use async I/O (e.g., `aiohttp`, `asyncio`) to parallelize API calls and Item processing
- **Configurable Concurrency**: Allow users to control the number of concurrent requests/workers
- **Retry Logic**: Implement intelligent retry strategies for transient failures

**Inputs:**

- Rate limit configuration (requests per second, backoff parameters)
- Concurrency configuration (worker count)
- Retry configuration (max attempts, backoff strategy)

**Outputs:**

- Successfully fetched/processed Items
- Failed Items with retry context

---

### 13. Integration with External Services (Optional in Core, Documented)

- **NASA Earthdata Login**: Support optional integration via `earthaccess` library for authentication if needed for metadata enrichment
- **STAC API Endpoints**: Flexible client for any STAC 1.0.0–compliant API
- **pgstac Output**: Generate metadata in formats compatible with pgstac ingestion (Parquet or JSON)

**Inputs:**

- Catalog URLs
- Optional credentials/tokens (via environment variables)

**Outputs:**

- Ingestion-ready metadata

---

## Architecture & Design Principles

### Design Philosophy: Composable, Loosely Coupled Modules

The toolkit is designed as a **"Swiss Army Knife"** of modular tools that can be composed into larger workflows. Each module:

- Performs a **focused, well-defined task** (e.g., fetch Items, transform data, apply extension)
- Has **minimal coupling** to other modules (easy to swap/replace components)
- Exposes both a **library interface** (Python classes/functions) and a **CLI interface** (subcommands)
- Is **testable in isolation** with clear input/output contracts

### Core Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│            CLI Layer (click/argparse)               │
│      (subcommands: discover, fetch, transform, etc) │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│      Orchestration/Workflow Layer                   │
│   (config parsing, pipeline composition, logging)   │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│      Core Business Logic Modules                    │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │ DiscoveryModule  │  │  IngestModule    │        │
│  │ (collections)    │  │ (fetch Items)    │        │
│  └──────────────────┘  └──────────────────┘        │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │ TransformModule  │  │  ScaffoldModule  │        │
│  │ (field mapping)  │  │ (create Items)   │        │
│  └──────────────────┘  └──────────────────┘        │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │ ExtensionModule  │  │  ValidateModule  │        │
│  │ (pluggable exts) │  │ (STAC validation)│        │
│  └──────────────────┘  └──────────────────┘        │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │   OutputModule   │  │  UpdateModule    │        │
│  │ (JSON/Parquet)   │  │ (metadata mods)  │        │
│  └──────────────────┘  └──────────────────┘        │
└─────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────┐
│        Utility / Support Layers                     │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │  HTTPClient      │  │  FileI/O         │        │
│  │  (async, retry)  │  │  (JSON, Parquet) │        │
│  └──────────────────┘  └──────────────────┘        │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │  Logging         │  │  Config Parser   │        │
│  └──────────────────┘  └──────────────────┘        │
│  ┌──────────────────┐                              │
│  │  Error Handling  │                              │
│  └──────────────────┘                              │
└─────────────────────────────────────────────────────┘
```

### Key Design Principles

1. **Modularity**: Each capability is a self-contained module with clear inputs/outputs.
2. **Low Coupling**: Modules depend on shared abstractions (interfaces), not concrete implementations.
3. **Testability**: Modules can be tested in isolation with mocked dependencies.
4. **Extensibility**: New modules (e.g., custom extensions, transformations) can be added without modifying existing code.
5. **Composability**: Modules can be combined in various ways via CLI or library interfaces.
6. **Async-First**: Use async/await patterns for I/O-bound operations (API calls, file I/O).
7. **Configuration-Driven**: Behavior is controlled via YAML/JSON configs, not code changes.
8. **Graceful Degradation**: Partial failures are logged and tracked; the system continues processing.

---

## Functional Requirements

### FR-1: Catalog & Collection Discovery

**Requirement**: Users can discover and list available Collections from a STAC API endpoint.

**Inputs**:

- `catalog_url` (string): Base URL of STAC API catalog
- `filters` (dict, optional):
  - `collection_ids` (list): Specific collection IDs to fetch; if not provided, list all
  - `temporal` (dict, optional): `{start_date, end_date}` to filter by temporal range
  - `spatial` (dict, optional): `{bbox: [minx, miny, maxx, maxy]}` to filter by spatial bounds

**Outputs**:

- List of Collection metadata (dict or JSON) with:
  - `id` (string): Collection identifier
  - `title` (string): Human-readable title
  - `description` (string): Collection description
  - `extent` (dict): Spatial and temporal extent
  - Links to parent catalog and items
- Error log if any requests fail

**Module**: `discovery.py` (DiscoveryModule)

---

### FR-2: Item Ingestion & Retrieval

**Requirement**: Users can fetch Items from a Collection via STAC API with support for pagination and parallelization.

**Inputs**:

- `collection_id` (string)
- `catalog_url` (string)
- `concurrency` (int, default 5): Number of concurrent requests
- `rate_limit` (float, default 10): Requests per second
- `limit` (int, optional): Max Items to fetch (if not specified, fetch all)

**Outputs**:

- Item data (list of GeoJSON features)
- Metadata about fetch process:
  - Total fetched
  - Total failed
  - Duration
  - Failed Items log

**Module**: `ingest.py` (IngestModule)

**Notes**:

- Must handle STAC API pagination (cursors, offsets)
- Must retry transient failures with exponential backoff
- Must log all failures and continue processing

---

### FR-3: STAC Item Scaffolding

**Requirement**: Users can create minimal valid STAC 1.0.0 Items from source data.

**Inputs**:

- `source_data` (dict or list of dicts): Raw source metadata
- `mapping_schema` (dict): Field mapping configuration defining how source fields map to STAC properties/assets
- `spatial_info` (dict, optional): Geometry/bbox if not in source data
  - Keys: `geometry` (GeoJSON), `bbox` (list)

**Outputs**:

- Valid STAC 1.0.0 Item (dict/JSON) with:
  - `type` = "Feature"
  - `stac_version` = "1.0.0"
  - `id` (string)
  - `geometry` (GeoJSON)
  - `bbox` (list)
  - `properties` (dict with at least `datetime` or `start_datetime`/`end_datetime`)
  - `links` (list, initially empty or with self-link)
  - `assets` (dict, may be empty initially)
  - `stac_extensions` (list, empty unless extensions added)

**Module**: `scaffold.py` (ScaffoldModule)

**Notes**:

- Items must pass STAC 1.0.0 JSON schema validation
- Geometry validation (valid GeoJSON, valid coordinates)
- Bbox validation (2D or 3D)

---

### FR-4: Metadata Transformation & Field Mapping

**Requirement**: Users can transform heterogeneous source data into STAC-compatible metadata using declarative field mapping schemas.

**Inputs**:

- `source_data` (list or file path): Raw metadata (JSON array, CSV, Parquet)
- `mapping_schema` (dict): Declarative mapping:

  ```yaml
  mappings:
    - source_field: "source_property"
      target_field: "stac_property"
      transform: "string"  # or "date", "number", "array", "object", etc.
      optional: false
    - source_field: "nested.field"
      target_field: "properties.custom_field"
      transform: "number"
  ```

- `reference_data` (dict, optional): Lookup tables for value transformations

**Outputs**:

- Transformed data (list of dicts, JSON, or Parquet)
- Transformation audit log:
  - Records mapped (count)
  - Records failed (count)
  - Transformation details for failed records

**Module**: `transform.py` (TransformModule)

**Notes**:

- Must support nested field access (dot notation)
- Must handle type conversions gracefully
- Must log transformation errors

---

### FR-5: Extension Application (Pluggable)

**Requirement**: Users can apply STAC extensions (dgeo, alternate-assets, custom) to Items/Collections.

**Inputs**:

- `metadata` (dict): STAC Item or Collection to extend
- `extension_name` (string): Name of extension (e.g., "dgeo", "alternate-assets")
- `extension_config` (dict): Extension-specific configuration
- `extension_module` (Python module, optional): Custom extension module implementing the extension interface

**Outputs**:

- Extended STAC metadata with:
  - New fields in `properties` or root level (per extension spec)
  - `stac_extensions` array updated with extension URI
  - Valid per extension JSON schema

**Modules**:

- `extensions/base.py` (ExtensionBase abstract class)
- `extensions/dgeo.py` (DgeoExtension)
- `extensions/alternate_assets.py` (AlternateAssetsExtension)
- `extensions/plugin_loader.py` (PluginLoader for custom extensions)

**Notes**:

- Extension modules must implement `ExtensionBase` interface
- Must validate extended metadata against extension schema
- Must gracefully handle missing or invalid extension config

---

### FR-6: Metadata Updates & Deletion

**Requirement**: Users can modify or remove existing Item/Collection metadata.

**Inputs**:

- `metadata_id` (string): Item or Collection ID to update
- `update_payload` (dict): Fields to update/add
  - Keys: STAC property paths (e.g., "properties.custom_field")
  - Values: new values
- `delete_fields` (list, optional): Fields to remove
- `selection_criteria` (dict, optional): For bulk updates (e.g., collection_id, temporal range)

**Outputs**:

- Updated STAC metadata with:
  - Modified fields
  - `updated` timestamp (RFC 3339)
  - Audit trail in logs

**Module**: `update.py` (UpdateModule)

**Notes**:

- Must preserve existing STAC structure
- Must update `updated` field with current timestamp
- Must validate updated metadata against STAC schema

---

### FR-7: Catalog Rebuild Modes

**Requirement**: Users can rebuild catalogs in full or incremental modes.

**Inputs**:

- `rebuild_mode` (string): "full", "incremental", or "targeted"
- `source_config` (dict):
  - `catalog_url` (string)
  - `collection_ids` (list)
  - Optional filters (temporal, spatial)
- `target_config` (dict):
  - `output_path` (string)
  - `output_format` (string): "json" or "parquet"
- `existing_catalog` (dict or path, optional): For incremental mode
- `transformation_schema` (dict): Field mapping and extension configs

**Outputs**:

- Rebuilt catalog metadata (JSON or Parquet files)
- Change summary:
  - Full mode: total items, duration
  - Incremental mode: added (count), modified (count), deleted (count)
  - Targeted mode: affected items (count)

**Module**: `rebuild.py` (RebuildModule)

**Notes**:

- Full rebuild: Refetch all source data, transform, apply extensions, save
- Incremental: Compare source catalog with existing catalog, fetch/transform only delta, merge
- Targeted: Update specific items by ID

---

### FR-8: Output Formats & Storage

**Requirement**: Users can save catalog metadata in multiple formats.

**Inputs**:

- `metadata` (dict or list): STAC metadata (Items, Collections, Catalog)
- `output_format` (string): "json" or "parquet"
- `output_path` (string): File path or directory
- `organize_by` (string, optional): "catalog" or "collection" (directory structure)

**Outputs**:

- Files written to disk:
  - JSON: One or more `.json` files (organized by hierarchy or flat)
  - Parquet: Columnar `.parquet` files (bulk Item data)
- Write log with:
  - Files written (count, paths)
  - Records written (count)
  - Errors (if any)

**Module**: `output.py` (OutputModule)

**Notes**:

- JSON must be pretty-printed for readability
- Parquet must preserve all STAC fields (use JSON-serializable schema)
- Directory structure should mirror STAC hierarchy (catalog/collection/items)

---

### FR-9: Data Quality, Validation & Logging

**Requirement**: Users can validate STAC metadata and track processing issues.

**Inputs**:

- `metadata` (dict): STAC metadata to validate
- `validation_level` (string, optional): "strict" or "lenient" (default: "strict")
- `log_config` (dict, optional): Logging configuration

**Outputs**:

- Validation report (dict):
  - `valid` (bool)
  - `errors` (list): Validation errors
  - `warnings` (list): Non-critical issues
- Logs with timestamps at multiple levels (DEBUG, INFO, WARNING, ERROR)
- Failed Items file (format TBD):
  - Item ID
  - Error message
  - Error context (source data, transformation step)

**Module**: `validate.py` (ValidateModule)

**Notes**:

- Use `stac-validator` for core STAC validation
- Use extension JSON schemas for extension validation
- Log all processing steps (discovery, fetch, transform, validate, output)

---

### FR-10: Configuration & Environment Management

**Requirement**: Users can define workflows via YAML/JSON config files with environment variable support.

**Inputs**:

- `config_file` (string, path to YAML/JSON)
- `env_overrides` (dict, optional): Environment variable values

**Config Structure** (YAML example):

```yaml
workflow:
  name: "CMR STAC to pgstac"
  description: "Ingest CMR collections into pgstac"

source:
  type: "stac_api"
  catalog_url: "https://cmr.earthdata.nasa.gov/stac"
  collections:
    - "MODIS_AQUA_L2"
    - "SENTINEL_1"
  filters:
    temporal:
      start_date: "2020-01-01"
      end_date: "2024-12-31"
    spatial:
      bbox: [-180, -90, 180, 90]

transformation:
  mapping_schema:
    - source_field: "properties.date"
      target_field: "properties.datetime"
      transform: "date"

extensions:
  - name: "dgeo"
    config:
      ownership: "public"
  - name: "alternate-assets"
    config:
      locations:
        - "s3://bucket1"
        - "https://mirror.example.com"

output:
  format: "parquet"
  path: "/data/output"
  organize_by: "collection"

logging:
  level: "INFO"
  file: "/logs/workflow.log"

processing:
  concurrency: 10
  rate_limit: 20
  retry_max_attempts: 3
```

**Outputs**:

- Parsed configuration object (dict)
- Validation report
- Error message if config is invalid

**Module**: `config.py` (ConfigParser)

**Notes**:

- Support environment variable substitution (e.g., `${NASA_EARTHDATA_TOKEN}`)
- Validate config against internal JSON schema
- Provide clear error messages for invalid configs

---

### FR-11: CLI & Library Interfaces

**Requirement**: All capabilities are accessible via CLI subcommands and Python library.

**CLI Subcommands** (TBD exact names during specification):

```bash
stac-catalog-manager discover-collections \
  --catalog-url <url> \
  --collection-ids <id1,id2> \
  --output <json|csv>

stac-catalog-manager fetch-items \
  --catalog-url <url> \
  --collection-id <id> \
  --concurrency 10 \
  --output-format parquet \
  --output-path <path>

stac-catalog-manager transform-metadata \
  --input <file> \
  --mapping-schema <yaml|json> \
  --output-format <json|parquet> \
  --output-path <path>

stac-catalog-manager scaffold-items \
  --input <file> \
  --mapping-schema <yaml|json> \
  --output-format <json|parquet> \
  --output-path <path>

stac-catalog-manager apply-extensions \
  --input <file> \
  --extension <dgeo|alternate-assets|custom> \
  --extension-config <yaml|json> \
  --output-path <path>

stac-catalog-manager validate \
  --input <file> \
  --output-report <path>

stac-catalog-manager rebuild-catalog \
  --config <yaml|json> \
  --mode <full|incremental|targeted>

stac-catalog-manager update-metadata \
  --input <file> \
  --updates <yaml|json> \
  --output-path <path>

# Help and version
stac-catalog-manager --help
stac-catalog-manager --version
```

**Python Library Usage**:

```python
from stac_catalog_manager import DiscoveryModule, IngestModule, TransformModule, ...

# Example workflow
discovery = DiscoveryModule()
collections = discovery.discover_collections(
    catalog_url="https://cmr.earthdata.nasa.gov/stac",
    collection_ids=["MODIS_AQUA_L2"]
)

ingest = IngestModule()
items = ingest.fetch_items(
    collection_id="MODIS_AQUA_L2",
    catalog_url="https://cmr.earthdata.nasa.gov/stac",
    concurrency=10
)

transform = TransformModule()
transformed = transform.transform_metadata(
    source_data=items,
    mapping_schema=mapping_config
)

# ... apply extensions, validate, output
```

**Module**: `cli.py` (CLI using Click or argparse), `__init__.py` (package exports)

**Notes**:

- CLI output should be clear and progress-oriented (spinners, progress bars for long operations)
- Library exports should be well-documented with docstrings
- Both interfaces should support dry-run mode (print what would happen without modifying files)

---

### FR-12: Rate Limiting & Asynchronous Processing

**Requirement**: The toolkit handles high-volume API requests efficiently with rate limiting and async I/O.

**Inputs**:

- `concurrency` (int): Number of concurrent requests (default: 5)
- `rate_limit` (float): Requests per second (default: 10 per second)
- `retry_config` (dict):
  - `max_attempts` (int, default: 3)
  - `backoff_strategy` (string, default: "exponential")
  - `backoff_base` (float, default: 2.0)

**Outputs**:

- Successfully processed items/requests
- Failed requests with retry context

**Modules**: `http_client.py` (AsyncHTTPClient with rate limiting and retry logic)

**Notes**:

- Use `aiohttp` for async HTTP requests
- Implement token bucket or sliding window rate limiting
- Implement exponential backoff (base 2, capped at max_wait)
- Log retry attempts with details
- Gracefully handle rate-limit headers (429, Retry-After)

---

## Data Model & Specifications

### STAC Data Model Compliance

All metadata produced by the toolkit must comply with:

- **STAC Spec Version**: 1.0.0 (<https://github.com/radiantearth/stac-spec/blob/master/stac-spec/overview.md>)
- **JSON Schema**: Valid against STAC 1.0.0 JSON schemas
- **Datetime Handling**: RFC 3339 Section 5.6 format (e.g., "2024-01-12T13:50:00Z")

### Minimal STAC Item Structure

```json
{
  "type": "Feature",
  "stac_version": "1.0.0",
  "stac_extensions": [],
  "id": "item-id-123",
  "description": "Brief description",
  "geometry": {
    "type": "Polygon",
    "coordinates": [[...]]
  },
  "bbox": [minx, miny, maxx, maxy],
  "properties": {
    "datetime": "2024-01-12T13:50:00Z"
  },
  "links": [
    {
      "rel": "self",
      "href": "./item.json"
    }
  ],
  "assets": {}
}
```

### Extension Schemas

**dgeo Extension** (v0.1.0, per DecentralizedGeo spec):

- Reference: <https://raw.githubusercontent.com/DecentralizedGeo/dgeo-asset/refs/heads/pgstac-variant/json-schema/schema.json>
- Key fields: `ownership`, `licensing`, `tokenization`, `provenance`, etc.
- Location: Root level or in `properties` (per extension spec)

**alternate-assets Extension**:

- Per STAC extensions repo
- Key fields: `alternate_locations` (array of alternate asset URLs/paths)
- Location: Within `assets[asset_key]` or root level (per extension spec)

### Configuration Schema

```yaml
ConfigSchema:
  workflow:
    name: string
    description: string (optional)
  source:
    type: enum ["stac_api", "local_files", "other"]
    catalog_url: string (if STAC API)
    collections: list of strings
    filters:
      temporal:
        start_date: string (ISO 8601)
        end_date: string (ISO 8601)
      spatial:
        bbox: list of 4 or 6 numbers
  transformation:
    mapping_schema: object (field mapping rules)
  extensions:
    - name: string
      config: object
  output:
    format: enum ["json", "parquet"]
    path: string
    organize_by: enum ["catalog", "collection"] (optional)
  logging:
    level: enum ["DEBUG", "INFO", "WARNING", "ERROR"]
    file: string (path to log file, optional)
  processing:
    concurrency: integer (default 5)
    rate_limit: float (default 10)
    retry_max_attempts: integer (default 3)
```

### Error & Failure Tracking

**Failed Items Structure**:

```json
{
  "item_id": "some-item-123",
  "error_type": "validation_error" | "transformation_error" | "api_error" | "other",
  "error_message": "Description of what went wrong",
  "error_context": {
    "source_data": {...},  // Raw source data that failed
    "step": "fetch" | "transform" | "validate" | "output",
    "timestamp": "2024-01-12T13:50:00Z"
  }
}
```

### Logging Format

Structured JSON logs with fields:

- `timestamp` (ISO 8601)
- `level` (DEBUG, INFO, WARNING, ERROR)
- `module` (e.g., "ingest.py", "transform.py")
- `message` (log message)
- `context` (dict with relevant context, e.g., item_id, error_code)

Example:

```json
{
  "timestamp": "2024-01-12T13:50:00Z",
  "level": "INFO",
  "module": "ingest.py",
  "message": "Fetching items from collection",
  "context": {
    "collection_id": "MODIS_AQUA_L2",
    "total_items": 10000,
    "page": 1
  }
}
```

---

## Integration Points

### 1. STAC API Endpoints

The toolkit acts as a client to standard STAC 1.0.0 API endpoints:

- **CMR-STAC**: <https://cmr.earthdata.nasa.gov/stac/v1>
- **STAC Index**: <https://stacindex.org> (catalog registry, not direct API)
- **Custom STAC APIs**: Any endpoint implementing STAC API 1.0.0

**Expected Endpoints**:

- `GET /` – Root catalog
- `GET /collections` – List collections
- `GET /collections/{id}` – Collection metadata
- `GET /collections/{id}/items` – Items with pagination
- `GET /search` – Search endpoint (optional, may be used for advanced filtering)

---

### 2. NASA Earthdata Login (Optional)

If metadata enrichment requires NASA Earth Science data access:

- **Library**: `earthaccess` (<https://earthaccess.readthedocs.io/>)
- **Purpose**: Authenticate to EDL for accessing restricted or detailed metadata
- **Configuration**: Via environment variables (e.g., `EARTHDATA_USERNAME`, `EARTHDATA_PASSWORD`)
- **Note**: Not required for baseline CMR-STAC queries, but available if needed

---

### 3. pgstac / stac-fastapi-pgstac

The toolkit generates metadata **compatible with pgstac ingestion**:

- **Output Formats**: JSON or Parquet (pgstac can ingest from these)
- **No Direct DB Access**: Toolkit does not write to pgstac database; it produces files for external ingestion
- **Future Integration**: A separate step (pgstac CLI or API call) ingests the generated metadata

---

### 4. Validation Integration

- **stac-validator**: Python package for STAC validation
- **Extension Schemas**: Load from upstream (DecentralizedGeo, STAC extensions repo) or local
- **Custom Validation**: Users can provide custom JSON schema files

---

### 5. File I/O Integration

**Supported Input Formats**:

- JSON (array of objects or single object)
- CSV (with header row)
- Parquet (columnar)
- Streams from STAC API

**Supported Output Formats**:

- JSON (pretty-printed)
- Parquet (with schema preservation)

**Libraries**:

- `pandas` (CSV, Parquet I/O)
- `pyarrow` (Parquet)
- `json` (standard library)

---

## Quality & Validation

### Validation Strategy

1. **Schema Validation**: All Items/Collections must validate against STAC 1.0.0 JSON schema
2. **Extension Validation**: Extended metadata must validate against extension schemas
3. **Geometry Validation**: GeoJSON geometries must be valid (using `shapely` or similar)
4. **Datetime Validation**: All datetime fields must conform to RFC 3339
5. **Error Handling**: Invalid metadata is flagged, logged, and collected in a failed Items file; processing continues

### Testing Strategy

- **Unit Tests**: Test individual modules in isolation with mocked dependencies
- **Integration Tests**: Test module interactions and full workflows
- **Scenario Tests**: Test acceptance scenarios (e.g., "ingest 1000 CMR items, apply dgeo extension, validate, output to Parquet")
- **Fixture Data**: Use small sample STAC catalogs for testing

### Code Quality Standards

- **Type Hints**: Use Python type hints throughout
- **Docstrings**: Document all public functions/classes with parameter and return documentation
- **Code Style**: Follow PEP 8 (enforced via `black`, `flake8`)
- **Test Coverage**: Aim for >80% coverage
- **Dependency Management**: Pin versions in `pyproject.toml` to ensure reproducibility

---

## Configuration & Deployment

### Development Environment

- **Python Version**: 3.12+
- **Package Manager**: `pip` (via `pyproject.toml`)
- **Virtual Environment**: `venv` or `poetry`

### Production Deployment

- **Docker Image**: Create a Dockerfile for containerization

  ```dockerfile
  FROM python:3.12-slim
  WORKDIR /app
  COPY pyproject.toml pyproject.lock* ./
  RUN pip install -e .
  ENTRYPOINT ["stac-catalog-manager"]
  ```

- **Environment Variables**: Pass secrets via environment (not hardcoded in config)
- **Volumes**: Mount input/output directories as volumes if using Docker

### Configuration Files

- **Format**: YAML or JSON
- **Location**: User-specified or default locations (e.g., `~/.stac-catalog-manager/config.yaml`)
- **Environment Variable Substitution**: Support `${VAR_NAME}` syntax for secrets

### Logging Configuration

- **Log File**: Written to specified path or stdout
- **Log Level**: Configurable (DEBUG, INFO, WARNING, ERROR)
- **Structured Logs**: JSON format for easy parsing by log aggregation systems

---

## Non-Functional Requirements

### Performance

- **Throughput**: Process Items asynchronously with configurable concurrency to maximize throughput
- **Scalability**: Handle 800K+ Items without excessive memory usage (use streaming/pagination)
- **Latency**: API requests should complete within configured timeout (e.g., 30 seconds)
- **Resource Usage**: Memory usage should not exceed available system RAM; use generators/streaming for large datasets

### Reliability

- **Error Recovery**: Implement retry logic with exponential backoff for transient failures
- **Partial Failures**: Continue processing on failure; log and track failed Items
- **Idempotency**: Workflows should be safe to re-run without corrupting state
- **Data Integrity**: Validate all metadata before writing; use atomic writes where possible

### Maintainability

- **Code Organization**: Clear module structure with separation of concerns
- **Documentation**: Comprehensive docstrings, README, and usage examples
- **Testing**: High test coverage with clear test organization
- **Extensibility**: Plugin architecture for custom extensions and transformations

### Usability

- **CLI UX**: Clear subcommands, helpful error messages, progress indicators
- **Library UX**: Intuitive Python API with clear function signatures and documentation
- **Configuration**: Simple YAML/JSON configs with sensible defaults
- **Logging**: Informative logs that help users debug issues

---

## Success Criteria & Acceptance Scenarios

### Scenario 1: Bulk Ingest from CMR-STAC

**Goal**: Clone 800K Items from CMR-STAC Collections into local catalog with dgeo extension.

**Steps**:

1. User creates a YAML config specifying CMR-STAC catalog URL, collection IDs, and extension config
2. User runs `stac-catalog-manager rebuild-catalog --config config.yaml --mode full`
3. Toolkit discovers collections, fetches all Items (with pagination), applies dgeo extension, validates, outputs to Parquet
4. Process completes with summary: "Processed 800K items, 799K valid, 1K failed"
5. Failed items saved to `failed_items.json` for review

**Acceptance Criteria**:

- ✅ All 799K valid items are in output Parquet file
- ✅ Failed items are logged and tracked
- ✅ Process completes in reasonable time (TBD, e.g., <4 hours on commodity hardware)
- ✅ Output Items pass STAC validation with `stac-validator`
- ✅ dgeo extension fields are present and valid

---

### Scenario 2: Clone & Update EasierData Catalog

**Goal**: Clone EasierData STAC Catalog, apply alternate-assets extension, and save to JSON.

**Steps**:

1. User creates a YAML config specifying EasierData catalog URL
2. User defines alternate-assets config (alternate S3 buckets)
3. User runs `stac-catalog-manager rebuild-catalog --config config.yaml`
4. Toolkit fetches all Collections and Items, applies alternate-assets extension, validates
5. Saves updated catalog to JSON files organized by collection
6. User reviews output and (optionally) modifies before publishing

**Acceptance Criteria**:

- ✅ All collections and items from EasierData are present in output
- ✅ alternate-assets extension fields are added to each Item
- ✅ Output validates against STAC + alternate-assets schemas
- ✅ JSON files are human-readable and organized by collection

---

### Scenario 3: Incremental Update

**Goal**: Incrementally update an existing catalog with new Items from a source, avoiding re-processing old data.

**Steps**:

1. User has an existing catalog (in Parquet)
2. User runs `stac-catalog-manager rebuild-catalog --config config.yaml --mode incremental`
3. Toolkit compares source with existing catalog, fetches only new/modified Items
4. Applies transformations and extensions only to delta
5. Merges delta into existing catalog
6. Outputs updated catalog to Parquet

**Acceptance Criteria**:

- ✅ Only new/modified items are fetched and processed
- ✅ Existing items remain unchanged
- ✅ Output catalog includes both old and new items
- ✅ Processing time is significantly faster than full rebuild

---

### Scenario 4: Custom Field Mapping

**Goal**: Transform non-STAC CSV data into STAC Items with custom field mappings.

**Steps**:

1. User has a CSV file with columns: `dataset_id`, `collection_name`, `acquisition_date`, `geometry_wkt`, `url`
2. User creates a YAML mapping schema defining how CSV columns map to STAC properties
3. User runs `stac-catalog-manager scaffold-items --input data.csv --mapping-schema mapping.yaml --output-path items.json`
4. Toolkit reads CSV, transforms to STAC Items using mapping, outputs to JSON
5. User validates output with `stac-catalog-manager validate --input items.json`

**Acceptance Criteria**:

- ✅ All CSV records are converted to valid STAC Items
- ✅ Custom fields are preserved in `properties`
- ✅ Geometry is correctly parsed from WKT
- ✅ Items pass STAC validation

---

### Scenario 5: Plugin Extension

**Goal**: Extend toolkit with a custom extension module (not dgeo or alternate-assets).

**Steps**:

1. User creates a Python module implementing `ExtensionBase` interface
2. User places module in a discoverable location (e.g., `~/.stac-catalog-manager/extensions/`)
3. User updates config to reference custom extension: `extensions: [name: "custom_ext"]`
4. User runs workflow; toolkit loads and applies custom extension
5. Resulting metadata is extended with custom fields

**Acceptance Criteria**:

- ✅ Custom extension module is automatically discovered and loaded
- ✅ Custom extension fields are applied to metadata
- ✅ No modification to core toolkit code is required
- ✅ Extended metadata validates if custom schema is provided

---

### Scenario 6: Docker Containerization

**Goal**: Run toolkit in Docker container for integration with orchestration systems.

**Steps**:

1. User has a Docker image built from the toolkit's Dockerfile
2. User mounts input and output directories as Docker volumes
3. User runs: `docker run -v /data:/data stac-catalog-manager rebuild-catalog --config /data/config.yaml`
4. Toolkit processes metadata and outputs to mounted volume
5. User accesses results from host system

**Acceptance Criteria**:

- ✅ Docker image builds successfully
- ✅ Toolkit runs in container without modification
- ✅ Volume mounts work correctly
- ✅ Output is accessible from host system

---

## Future Considerations (Post-v1)

These capabilities are **not required for v1** but are documented for future roadmap planning:

1. **Workflow Orchestration**: Integration with Apache Airflow, Prefect, or Dagster for complex, scheduled workflows
2. **Cloud Storage**: Native support for S3, Azure Blob Storage, GCS for input/output
3. **Direct pgstac Integration**: Write directly to pgstac database via API (currently outputs files for external ingestion)
4. **Advanced Search**: Implement STAC Search API `/search` endpoint for complex queries
5. **Catalog Validation**: Validate entire Catalog structure (parent-child relationships, links integrity)
6. **Metadata Enrichment**: Built-in enrichment from external sources (USGS, Copernicus, etc.)
7. **Web API**: FastAPI-based REST API for toolkit functionality
8. **Multi-Tenancy**: Support for managing multiple catalogs with different configurations
9. **Performance Optimization**: Caching, memoization, and indexing strategies for very large catalogs
10. **Monitoring & Metrics**: Prometheus-compatible metrics for workflow monitoring

---

## Appendix A: Reference Links

- **STAC Spec**: <https://github.com/radiantearth/stac-spec>
- **STAC API Spec**: <https://github.com/radiantearth/stac-api-spec>
- **CMR-STAC**: <https://github.com/nasa/cmr-stac>
- **stac-validator**: <https://github.com/stac-utils/stac-validator>
- **dgeo Extension**: <https://github.com/DecentralizedGeo/dgeo-asset>
- **alternate-assets Extension**: <https://github.com/stac-extensions/alternate-assets>
- **RFC 3339**: <https://tools.ietf.org/html/rfc3339>
- **STAC Index**: <https://stacindex.org>
- **Astral API**: <https://github.com/DecentralizedGeo/astral-api>
- **pgstac**: <https://github.com/stac-utils/pgstac>
- **stac-fastapi-pgstac**: <https://github.com/stac-utils/stac-fastapi-pgstac>
- **earthaccess**: <https://earthaccess.readthedocs.io/>
- **NASA Earthdata Login**: <https://urs.earthdata.nasa.gov/>

---

## Appendix B: Glossary

| Term | Definition |
|------|-----------|
| **STAC** | SpatioTemporal Asset Catalog — a specification for describing geospatial data |
| **Item** | A STAC entity representing a single asset or collection of assets at a specific place/time |
| **Collection** | A STAC entity grouping related Items |
| **Catalog** | A STAC entity linking Collections and Items hierarchically |
| **Extension** | Additional metadata fields following a defined schema (e.g., dgeo, alternate-assets) |
| **CMR** | Common Metadata Repository — NASA's Earth Science metadata catalog |
| **pgstac** | PostgreSQL-based STAC catalog implementation |
| **RFC 3339** | Standard format for date/time representation (ISO 8601 profile) |
| **GeoJSON** | JSON-based format for geospatial features |
| **Parquet** | Columnar data format optimized for analytics |
| **Rate Limiting** | Controlling the number of API requests to avoid overwhelming servers |
| **Async I/O** | Asynchronous input/output for concurrent operations |
| **Materialization** | The process of fetching and persisting metadata |
| **Transformation** | Converting metadata from one format/schema to another |
| **Validation** | Checking metadata compliance with schemas/standards |

---

**End of Document**
