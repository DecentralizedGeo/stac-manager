# Project Requirements Document (PRD)

## STAC Manager

**Project**: STAC Manager — A comprehensive Python toolkit for building, managing, and extending STAC catalogs at scale.

**Version**: 1.0.3 (v1 PRD - Updated with STAC-Utils Ecosystem Integration)  
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

**STAC Manager** is an open-source Python toolkit designed to simplify the creation, modification, and management of STAC (SpatioTemporal Asset Catalog) metadata at scale. The primary goal is to reduce complexity and friction in STAC workflows—enabling users to scaffold, ingest, extend, and maintain STAC catalogs (Collections, Items) from diverse sources (CMR-STAC, other STAC APIs, non-STAC APIs, local data files).

This toolkit builds upon the **stac-utils ecosystem** of Python libraries (PySTAC, stac-validator, pystac-client, stac-geoparquet), providing a higher-level orchestration and workflow automation layer optimized for production-scale operations (800K+ items).

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

8. **Ecosystem Integration**: Build upon standard stac-utils libraries (PySTAC, stac-validator, pystac-client, etc.) to avoid duplication and maximize interoperability with the broader STAC ecosystem.

### Intended Use Cases

1. One-off bulk catalog creation from CMR-STAC
2. Scaffolding new STAC metadata (Catalogs, Collections, Items) following STAC v1.1.0 spec
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

- **Discover Collections**: Query a STAC API v1.0.0 catalog URL and retrieve available collections
- **Filter Collections**: Support filtering by collection ID, provider, temporal range, and spatial bounds
- **Retrieve Metadata**: Fetch Collection-level metadata from specified STAC API endpoints
- **Support Multiple Sources**: Work with CMR-STAC, STAC Index catalogs, and any standard STAC API v1.0.0 endpoint

**Inputs:**

- Catalog URL (string): Base URL of STAC API v1.0.0 endpoint
- List of collection IDs or wildcard selectors
- Optional temporal/spatial filters

**Outputs:**

- Collection metadata (JSON)
- Linked Items metadata or pagination tokens

---

### 2. Item Ingestion & Retrieval

- **Fetch Items**: Retrieve Items from a Collection via STAC API pagination
- **Support Pagination**: Handle paginated responses correctly (cursors, limits, offsets per STAC API v1.0.0 spec)
- **Batch Processing**: Support parallel/asynchronous fetching of Items with configurable concurrency
- **Partial Failure Handling**: Continue processing if some Items fail; log failures for later review

**Inputs:**

- Collection ID
- Pagination parameters (limit, offset, cursor)
- Concurrency configuration

**Outputs:**

- Item metadata (GeoJSON/JSON per STAC v1.1.0)
- Failed Items log with error details

---

### 3. STAC Item Scaffolding

- **Create Minimal Items**: Generate baseline STAC v1.1.0 Items from source data
- **Required Fields**: Ensure all mandatory Item fields are present per STAC v1.1.0 spec (id, geometry, bbox, properties, links, assets)
- **Field Mapping**: Support declarative field mapping from source schema to STAC properties/assets
- **Geometry/Bbox Generation**: Compute valid GeoJSON geometries and bounding boxes from spatial metadata

**Inputs:**

- Source data (JSON, CSV, Parquet, etc.)
- Field mapping configuration (YAML/JSON schema)
- Spatial reference information

**Outputs:**

- Valid STAC v1.1.0 Item JSON

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
- **Versioning**: Track updates using RFC 3339 timestamps in the `updated` field (per STAC v1.1.0 common metadata)

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

- **STAC Validation**: Validate all Items against STAC v1.1.0 JSON schema using `stac-validator`
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
- **Environment Variables**: Support secrets and sensitive data via environment variables (e.g., API credentials)
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
- **Docker Support**: Toolkit can be containerized as a Docker image for use in workflow orchestration (custom scripts, Kubernetes, etc.)

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
- **Asynchronous Requests**: Use async I/O (e.g., `aiohttp`, `asyncio`) to parallelize API calls and Item processing.
  - *Note*: Since `pystac-client` is synchronous, high-concurrency fetching will use `ThreadPoolExecutor` or `ProcessPoolExecutor` to wrap client calls, or use raw `aiohttp` for fetching Item JSONs after discovery.
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

- **STAC API Endpoints**: Flexible client for any STAC v1.0.0–compliant API
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
│    Foundation Libraries (stac-utils ecosystem)      │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │  PySTAC          │  │ stac-validator   │        │
│  │  (I/O, model)    │  │ (validation)     │        │
│  └──────────────────┘  └──────────────────┘        │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │ pystac-client    │  │ stac-geoparquet  │        │
│  │ (API search)     │  │ (format conv)    │        │
│  └──────────────────┘  └──────────────────┘        │
│  ┌──────────────────┐  ┌──────────────────┐        │
│  │ stac-pydantic    │  │  HTTPClient      │        │
│  │ (types)          │  │  (async, retry)  │        │
│  └──────────────────┘  └──────────────────┘        │
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
9. **Ecosystem Reuse**: Leverage standard stac-utils libraries (PySTAC, stac-validator, pystac-client, stac-geoparquet) for foundational STAC operations to avoid duplication and maximize interoperability.

---

## Integration Points

### 1. STAC API v1.0.0 Endpoints

The toolkit acts as a client to standard STAC v1.0.0 API endpoints:

- **CMR-STAC**: <https://cmr.earthdata.nasa.gov/stac/v1>
- **STAC Index**: <https://stacindex.org> (catalog registry, not direct API)
- **Custom STAC APIs**: Any endpoint implementing STAC API v1.0.0

**Expected Endpoints**:

- `GET /` – Root catalog
- `GET /collections` – List collections
- `GET /collections/{id}` – Collection metadata
- `GET /collections/{id}/items` – Items with pagination
- `GET /search` – Search endpoint (optional, may be used for advanced filtering)

**Implementation**: Uses **pystac-client** (from stac-utils) for API discovery and search

---

### 2. pgstac / stac-fastapi-pgstac

The toolkit generates metadata **compatible with pgstac ingestion**:

- **Output Formats**: JSON or Parquet (pgstac can ingest from these)
- **No Direct DB Access**: Toolkit does not write to pgstac database; it produces files for external ingestion
- **Future Integration**: A separate step (pgstac CLI or API call) ingests the generated metadata

**Implementation**: Uses **stac-geoparquet** (from stac-utils) for Parquet format conversion

---

### 3. Validation Integration

- **stac-validator**: Python package for STAC v1.1.0 validation (from stac-utils)
- **Extension Schemas**: Load from upstream (DecentralizedGeo, STAC extensions repo) or local
- **Custom Validation**: Users can provide custom JSON schema files

**Implementation**: Direct integration with **stac-validator** from stac-utils ecosystem

---

### 4. File I/O Integration

**Supported Input Formats**:

- JSON (array of objects or single object)
- CSV (with header row)
- Parquet (columnar)
- Streams from STAC API

**Supported Output Formats**:

- JSON (pretty-printed) - using **PySTAC** serialization
- Parquet (with schema preservation) - using **stac-geoparquet**

**Libraries**:

- `PySTAC` (STAC object I/O from stac-utils)
- `stac-geoparquet` (Parquet format from stac-utils)
- `pandas` (CSV, Parquet I/O)
- `pyarrow` (Parquet)
- `json` (standard library)

---

### 5. STAC-Utils Ecosystem Integration

The toolkit is built upon the **stac-utils** organization's ecosystem of Python libraries, which provide the standard foundation for STAC tooling across the community.

#### Foundation Libraries (Required Dependencies)

| Library | Role | Usage in Toolkit |
|---------|------|------------------|
| **PySTAC** | Core STAC data model, I/O operations, catalog traversal | Foundation for all STAC object creation, reading, writing, and manipulation |
| **stac-validator** | JSON schema validation for STAC spec compliance | Validate all Items/Collections against STAC v1.1.0 and extension schemas |
| **pystac-client** | Python client for searching STAC APIs | Discover and ingest Items/Collections from external STAC APIs |
| **stac-geoparquet** | Convert STAC between JSON, GeoParquet, and pgstac formats | Output bulk Item metadata in Parquet format for efficient storage/processing |

#### Specialized Libraries (Optional/Conditional Dependencies)

| Library | Role | Usage in Toolkit |
|---------|------|------------------|
| **stac-pydantic** | Pydantic models for type-safe STAC objects | Optional: Type checking and validation in configuration parsing |
| **stac-asset** | Read/download STAC assets with authentication | Optional: If complex asset authentication/download needed |
| **pgstac** | PostgreSQL schema for STAC storage and search | Post-v1: Alternative storage backend |
| **stac-fastapi** | FastAPI implementation of STAC API spec | Post-v1: Serve generated catalogs as STAC API endpoints |

#### Toolkit's Unique Value Proposition

The **stac-utils ecosystem** provides foundational libraries and infrastructure components. **STAC Manager** builds on this foundation by adding the **orchestration and workflow automation layer** that is missing from the ecosystem:

**What stac-utils Provides**:

- ✅ Core STAC data model and I/O (PySTAC)
- ✅ API client for search and discovery (pystac-client)
- ✅ Schema validation (stac-validator)
- ✅ Format conversion utilities (stac-geoparquet)
- ✅ Infrastructure (pgstac, stac-fastapi)

**What STAC Manager Adds**:

- 🚀 **Workflow Orchestration**: Configuration-driven composition of multiple operations
- 🚀 **Async Scaling**: Parallel processing and rate limiting for 800K+ items
- 🚀 **Declarative Transformations**: YAML/JSON-based field mapping schemas
- 🚀 **Pluggable Extensions**: Architecture for custom STAC extensions
- 🚀 **Production Deployment**: CLI + library + Docker containerization
- 🚀 **Comprehensive Logging**: Structured logging, error tracking, processing summaries
- 🚀 **Incremental Processing**: Full/incremental/targeted catalog rebuild modes
- 🚀 **Operational Interfaces**: Production-ready CLI and configuration management

#### Integration Strategy

```python
# STAC Manager leverages stac-utils libraries:

import pystac                          # Core STAC objects
from pystac import Catalog, Collection, Item
from pystac_client import Client       # API discovery
from stac_validator import StacValidator  # Validation
import stac_geoparquet                 # Parquet I/O

# STAC Manager adds orchestration layer:
from stac_manager import (
    DiscoveryModule,      # Wraps pystac_client with parallel processing
    IngestModule,         # Async bulk fetching with rate limiting
    TransformModule,      # Declarative field mapping to PySTAC objects
    ExtensionModule,      # Pluggable extension architecture
    ValidateModule,       # Wraps stac-validator with batch processing
    OutputModule,         # Outputs via PySTAC + stac-geoparquet
)
```

#### Benefits of This Approach

1. **Standard Foundation**: Built on community-maintained, widely-adopted libraries
2. **No Duplication**: Reuses proven STAC data models and validation logic
3. **Interoperability**: Output compatible with all stac-utils tools (pgstac, stac-fastapi, etc.)
4. **Maintainability**: Updates to STAC spec are handled by upstream stac-utils libraries
5. **Community Integration**: Contributions benefit broader STAC ecosystem
6. **Clear Separation**: Foundation libraries (stac-utils) vs. orchestration layer (this toolkit)

#### Why Not Use stactools as Base?

While **stactools** (from stac-utils) provides CLI utilities for catalog operations, it has limitations for production-scale workflows:

| Aspect | stactools | STAC Manager |
|--------|-----------|---------------------|
| **Scale** | Sequential processing | Async/parallel (800K+ items) |
| **Workflows** | CLI arguments | YAML/JSON configuration |
| **Extensions** | Limited | Pluggable architecture |
| **Rate Limiting** | None | Built-in with exponential backoff |
| **Transformations** | Basic | Declarative field mapping schemas |
| **Deployment** | CLI only | CLI + Library + Docker |
| **Maintenance** | Last update Nov 2023 | Active development |

**Decision**: Use **PySTAC** as foundation, not stactools. STAC Manager provides more comprehensive orchestration than stactools offers.

#### References

- **stac-utils GitHub Organization**: <https://github.com/stac-utils>
- **PySTAC**: <https://github.com/stac-utils/pystac>
- **pystac-client**: <https://github.com/stac-utils/pystac-client>
- **stac-validator**: <https://github.com/stac-utils/stac-validator>
- **stac-geoparquet**: <https://github.com/stac-utils/stac-geoparquet>
- **stactools**: <https://github.com/stac-utils/stactools>
- **pgstac**: <https://github.com/stac-utils/pgstac>
- **stac-fastapi**: <https://github.com/stac-utils/stac-fastapi>

---

## Data Model & Specifications

### STAC Data Model Compliance

All metadata produced by the toolkit must comply with:

- **STAC Spec Version**: v1.1.0 (<https://github.com/radiantearth/stac-spec/releases/tag/v1.1.0>)
- **STAC API Spec Version**: v1.0.0 (<https://github.com/radiantearth/stac-api-spec/>)
- **JSON Schema**: Valid against STAC v1.1.0 JSON schemas (validated via stac-validator)
- **Datetime Handling**: RFC 3339 Section 5.6 format (e.g., "2024-01-12T13:50:00Z")
- **Implementation**: All STAC objects use **PySTAC** data model

### Minimal STAC Item Structure (STAC v1.1.0)

```json
{
  "type": "Feature",
  "stac_version": "1.1.0",
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

### Dependencies (pyproject.toml)

```toml
[project]
name = "stac-manager"
version = "1.0.0"
requires-python = ">=3.12"

dependencies = [
    # Core STAC libraries (stac-utils ecosystem)
    "pystac>=1.10.0",                   # Core STAC data model (supports STAC v1.1.0)
    "stac-validator>=3.0.0",            # Schema validation
    "pystac-client>=0.8.0",             # API client for discovery
    "stac-geoparquet>=0.4.0",           # Format conversion
    
    # Optional STAC libraries
    "pystac-pydantic>=2.0.0",           # Type definitions (optional)
    
    # Async and HTTP
    "aiohttp>=3.8.0",                   # Async HTTP
    "asyncio>=3.4.3",                   # Async I/O
    
    # Data processing
    "pyarrow>=10.0",                    # Parquet I/O
    "pandas>=1.5.0",                    # Data transformation
    
    # Configuration and CLI
    "pyyaml>=6.0",                      # Config file parsing
    "click>=8.0",                       # CLI framework
    
    # Utilities
    "python-dateutil>=2.8.0",           # Date parsing
    "shapely>=2.0.0",                   # Geometry validation
]
```

---

## Appendix A: Reference Links

### STAC Specification & Standards

- **STAC Spec v1.1.0**: <https://github.com/radiantearth/stac-spec/releases/tag/v1.1.0>
- **STAC API Spec v1.0.0**: <https://github.com/radiantearth/stac-api-spec/>
- **RFC 3339**: <https://tools.ietf.org/html/rfc3339>
- **STAC Index**: <https://stacindex.org>

### STAC-Utils Ecosystem (Foundation Libraries)

- **stac-utils GitHub Organization**: <https://github.com/stac-utils>
- **PySTAC**: <https://github.com/stac-utils/pystac>
- **pystac-client**: <https://github.com/stac-utils/pystac-client>
- **stac-validator**: <https://github.com/stac-utils/stac-validator>
- **stac-geoparquet**: <https://github.com/stac-utils/stac-geoparquet>
- **stac-pydantic**: <https://github.com/stac-utils/stac-pydantic>
- **stac-asset**: <https://github.com/stac-utils/stac-asset>
- **stactools**: <https://github.com/stac-utils/stactools>
- **pgstac**: <https://github.com/stac-utils/pgstac>
- **stac-fastapi**: <https://github.com/stac-utils/stac-fastapi>
- **stac-fastapi-pgstac**: <https://github.com/stac-utils/stac-fastapi-pgstac>
- **stac-check**: <https://github.com/stac-utils/stac-check>

### STAC Catalogs & APIs

- **CMR-STAC**: <https://github.com/nasa/cmr-stac>
- **Astral API**: <https://github.com/DecentralizedGeo/astral-api>

### STAC Extensions

- **dgeo Extension**: <https://github.com/DecentralizedGeo/dgeo-asset>
- **alternate-assets Extension**: <https://github.com/stac-extensions/alternate-assets>

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
| **pgstac** | PostgreSQL-based STAC catalog implementation (from stac-utils) |
| **PySTAC** | Core Python library for STAC data model and I/O (from stac-utils) |
| **stac-utils** | GitHub organization hosting core STAC utility libraries |
| **pystac-client** | Python client for searching STAC APIs (from stac-utils) |
| **stac-validator** | Validation tool for STAC spec compliance (from stac-utils) |
| **stac-geoparquet** | Library for converting STAC to/from Parquet format (from stac-utils) |
| **stactools** | CLI and library for STAC catalog operations (from stac-utils, last updated 2023) |
| **RFC 3339** | Standard format for date/time representation (ISO 8601 profile) |
| **GeoJSON** | JSON-based format for geospatial features |
| **Parquet** | Columnar data format optimized for analytics |
| **Rate Limiting** | Controlling the number of API requests to avoid overwhelming servers |
| **Async I/O** | Asynchronous input/output for concurrent operations |
| **Materialization** | The process of fetching and persisting metadata |
| **Transformation** | Converting metadata from one format/schema to another |
| **Validation** | Checking metadata compliance with schemas/standards |

---
