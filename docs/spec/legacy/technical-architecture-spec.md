# Technical Architecture Specification
## STAC Manager v1.0

**Status**: Draft  
**Version**: 1.0.0  
**Last Updated**: January 13, 2026  
**Based On**: [STAC-Manager-PRD-v1.0.3](../../development/STAC-Manager-PRD-v1.0.3.md)

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architectural Layers](#architectural-layers)
3. [Core Module Catalog](#core-module-catalog)
4. [Module Protocol Definitions](#module-protocol-definitions)
5. [Extension System Architecture](#extension-system-architecture)
6. [Workflow Orchestrator](#workflow-orchestrator)
7. [Data Flow Patterns](#data-flow-patterns)
8. [Error Handling Architecture](#error-handling-architecture)
9. [Async & Concurrency Model](#async--concurrency-model)
10. [Dependency Integration](#dependency-integration)

---

## System Overview

### Architectural Philosophy

The STAC Manager is designed as a **composable orchestration layer** built on top of the stac-utils ecosystem. The architecture follows these core principles:

- **Modularity**: Self-contained modules with focused responsibilities
- **Protocol-Based Contracts**: Type-safe interfaces using Python Protocols
- **Configuration-Driven**: Workflows defined in YAML, not hardcoded pipelines
- **Async-First**: Concurrent execution for I/O-bound operations
- **Graceful Degradation**: Collect-and-continue error handling for production scale

### System Context

```
┌─────────────────────────────────────────────────────────────┐
│                        User Space                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  CLI Tool    │  │ Python API   │  │ YAML Configs │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────┐
│              STAC Manager (This System)             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         Workflow Orchestrator (DAG Execution)        │  │
│  └────────────────────────┬─────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Core Business Logic Layer               │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │  │
│  │  │Discovery│ │ Ingest │ │Transform│ │Scaffold│       │  │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │  │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐       │  │
│  │  │Extension│ │Validate│ │ Update │ │ Output │       │  │
│  │  └────────┘ └────────┘ └────────┘ └────────┘       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│           Foundation Libraries (stac-utils ecosystem)       │
│  ┌────────────┐ ┌───────────────┐ ┌──────────────┐        │
│  │  PySTAC    │ │ pystac-client │ │stac-validator│        │
│  └────────────┘ └───────────────┘ └──────────────┘        │
│  ┌────────────┐ ┌───────────────┐ ┌──────────────┐        │
│  │stac-       │ │   aiohttp     │ │   pandas     │        │
│  │geoparquet  │ │   (async)     │ │   (data)     │        │
│  └────────────┘ └───────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                         │
│  ┌───────────┐  ┌────────────┐  ┌─────────────┐           │
│  │ STAC APIs │  │ File System│  │  pgstac DB  │           │
│  │(CMR-STAC) │  │(JSON,CSV)  │  │  (optional) │           │
│  └───────────┘  └────────────┘  └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

Based on the PRD requirements and brainstorming phase, the following architectural patterns have been selected:

| Decision Area | Pattern Selected | Rationale |
|---------------|------------------|-----------|
| **Data Flow** | Orchestrator Pattern | Supports both linear and branching workflows via YAML config |
| **Module Design** | Hybrid Granularity | Simple modules remain coarse; complex modules decompose as needed |
| **Pluggability** | Protocol-Based (Core) + Hybrid Registry (Extensions) | Type-safe contracts for modules; user-friendly shortcuts for extensions |
| **Error Handling** | Collect & Continue | Graceful degradation for production scale (800K+ items) |
| **Concurrency** | Async-First | Parallel execution for I/O-bound operations |

---

## Architectural Layers

The system is organized into four distinct layers, each with clear responsibilities and boundaries.

### Layer 1: User Interface Layer

**Responsibilities:**
- Parse command-line arguments (CLI)
- Expose Python library API
- Load and validate YAML configuration files
- Translate user intentions into workflow definitions

**Components:**
- `cli/` - Click-based CLI application
- `config/` - Configuration loading and validation
- Public Python API (module exports)

**Key Decisions:**
- CLI is a thin wrapper around the workflow orchestrator
- Configuration parsing happens once at startup
- Validation errors fail fast before workflow execution

### Layer 2: Orchestration Layer

**Responsibilities:**
- Build workflow DAGs from configuration
- Schedule and execute workflow steps
- Manage step dependencies and parallelization
- Coordinate error handling and logging
- Track workflow state and progress

**Components:**
- `WorkflowOrchestrator` - DAG builder and executor
- `WorkflowContext` - Shared state across steps
- `StepExecutor` - Individual step execution wrapper
- `FailureCollector` - Error aggregation

**Key Decisions:**
- Orchestrator is stateless (can be serialized/resumed if needed in future)
- Steps communicate via `WorkflowContext` (shared data structure)
- Parallelization is automatic based on dependency graph

### Layer 3: Business Logic Layer (Core Modules)

**Responsibilities:**
- Implement STAC catalog operations
- Provide focused, composable capabilities
- Enforce STAC spec compliance
- Integrate with foundation libraries

**Components:**
- 8 core modules (Discovery, Ingest, Transform, Scaffold, Extension, Validate, Update, Output)
- Each module implements `ModuleProtocol`
- Submodules for complex domains (Transform, Extension, Ingest)

**Key Decisions:**
- Modules are stateless classes (instantiated per step)
- All I/O operations return Python objects (not side effects)
- Modules use dependency injection for testability

### Layer 4: Foundation Layer (External Libraries)

**Responsibilities:**
- STAC data model and I/O (PySTAC)
- API client functionality (pystac-client)
- Validation logic (stac-validator)
- Format conversion (stac-geoparquet)
- Async HTTP (aiohttp)
- Data manipulation (pandas, pyarrow)

**Components:**
- Direct imports from stac-utils ecosystem
- Standard library utilities
- Third-party data processing libraries

**Key Decisions:**
- No custom STAC object models (use PySTAC)
- No custom validation logic (use stac-validator)
- Minimal wrappers around foundation libraries

---

## Core Module Catalog

This section defines the 8 core business logic modules. Each module implements the `ModuleProtocol` and can be composed into workflows via the orchestrator.

### Module Overview Table

| Module | Primary Responsibility | Complexity | Decomposition |
|--------|----------------------|------------|---------------|
| **DiscoveryModule** | Query STAC APIs for available collections | Low | Monolithic |
| **IngestModule** | Fetch Items from STAC APIs with pagination | Medium | Potential submodules for async fetching |
| **TransformModule** | Map source data to STAC schema | High | **Decomposed**: FieldMapper, TypeConverter, SchemaLoader |
| **ScaffoldModule** | Generate valid STAC Items from transformed data | Medium | Monolithic initially |
| **ExtensionModule** | Apply STAC extensions to Items/Collections | Medium | **Decomposed**: ExtensionLoader, ExtensionRegistry, ExtensionApplicator |
| **ValidateModule** | Validate STAC compliance using stac-validator | Low | Monolithic wrapper |
| **UpdateModule** | Modify existing STAC metadata | Low | Monolithic |
| **OutputModule** | Write STAC metadata to JSON/Parquet | Low | Monolithic |

### 1. DiscoveryModule

**Purpose**: Query STAC API endpoints to discover available collections and their metadata.

**Inputs:**
- Catalog URL (STAC API v1.0.0 endpoint)
- Optional filters (collection IDs, temporal range, spatial bbox)

**Outputs:**
- List of `pystac.Collection` objects
- Metadata for downstream processing

**Design Approach:**
- Wraps `pystac_client.Client` for API discovery
- Supports filtering by collection ID patterns (wildcards, lists)
- Handles pagination for large collection lists
- Returns standard PySTAC objects (no custom models)

**Key Methods:**
```python
def discover_collections(
    catalog_url: str,
    collection_ids: list[str] | None = None,
    temporal_filter: dict | None = None,
    spatial_filter: dict | None = None
) -> list[pystac.Collection]
```

**Error Handling:**
- Network errors: Log and return empty list (collect-and-continue)
- Invalid catalog URL: Fail fast with clear error message
- Malformed collection metadata: Log warning, skip collection

---

### 2. IngestModule

**Purpose**: Fetch STAC Items from collections with support for pagination and parallel/async retrieval.

**Inputs:**
- Collection ID or `pystac.Collection` object (from DiscoveryModule or direct config)
- Pagination parameters (limit, cursor)
- Concurrency configuration
- **Item-level filters** (temporal, spatial, query parameters)

**Outputs:**
- Iterator/generator of `pystac.Item` objects
- Failed Items log with error details

**Design Approach:**
- Uses `pystac_client.Client.search()` for Item retrieval
- Implements async pagination with configurable batch sizes
- Supports rate limiting to respect API constraints
- **Supports Item-level filters separate from Collection-level filters** (e.g., filter Collections broadly, then filter Items more specifically)
- Yields Items as they are fetched (streaming, not buffering all in memory)

**Dependency Note:**
- Can run standalone if `collection_ids` are provided in config
- Typically depends on `DiscoveryModule` to get Collection objects from context

**Potential Submodules (if complexity grows):**
- `PaginationHandler`: Manages cursors and batch fetching
- `RateLimiter`: Enforces rate limits with exponential backoff
- `ItemFetcher`: Async HTTP client for raw Item JSON

**Key Methods:**
```python
async def fetch_items(
    collection: pystac.Collection,
    limit: int | None = None,
    concurrency: int = 5
) -> AsyncIterator[pystac.Item]
```

**Error Handling:**
- Item fetch failures: Log error, yield to failure collector, continue
- Rate limiting (429 responses): Exponential backoff, retry
- Network timeouts: Retry with backoff, eventually log and skip

---

### 3. TransformModule

**Purpose**: Transform heterogeneous source data (JSON, CSV, Parquet) into STAC-compatible field structures using declarative mapping schemas.

**Inputs:**
- Source data files or objects
- Transformation schema (YAML/JSON mapping config)
- Optional lookup tables or reference data

**Outputs:**
- Transformed data dictionaries ready for scaffolding
- Transformation audit log

**Design Approach:**
- **DECOMPOSED** into submodules due to high complexity
- Schema-driven transformations (declarative, not procedural)
- Supports field mapping, type conversions, computed fields
- Reusable transformation schemas stored as configs

**Submodules:**

#### 3.1. SchemaLoader
- Loads and validates transformation schema from YAML/JSON
- Provides schema structure to other submodules

#### 3.2. FieldMapper
- Maps source fields to target STAC properties
- Supports nested object paths (e.g., `source.metadata.date` → `properties.datetime`)
- Handles missing fields with defaults or required checks

#### 3.3. TypeConverter
- Converts data types (string → datetime, array → single value, etc.)
- Validates converted values
- Handles RFC 3339 datetime formatting

#### 3.4. DataNormalizer (optional, can defer)
- Normalizes values (e.g., uppercase to lowercase, unit conversions)
- Applies computed transformations (e.g., bbox from geometry)

**Key Methods:**
```python
def transform_data(
    source_data: dict | pd.DataFrame,
    schema: TransformationSchema
) -> dict
```

**Error Handling:**
- Required field missing: Log error, add to failure report
- Type conversion failure: Log warning, use default or skip field
- Invalid schema: Fail fast at workflow start (config validation)

---

### 4. ScaffoldModule

**Purpose**: Generate valid STAC v1.1.0 Items and Collections from transformed data or empty templates, ensuring all required fields are present.

**Inputs:**
- Transformed data dictionaries (from TransformModule) OR empty template request
- Scaffold configuration (defaults, required fields, geometry defaults)

**Outputs:**
- Valid `pystac.Item` and/or `pystac.Collection` objects
- Scaffold validation report

**Design Approach:**
- Uses `pystac.Item()` and `pystac.Collection()` constructors with required fields
- Generates geometry and bbox from spatial metadata if present
- **Supports default geometry** (null or configurable default polygon) when source data lacks geometry
-    # Template scaffolding (when mode: template)
    template:
      type: catalog | collection | item
      output_path: string (where to write template JSON)
      include_sample_item: boolean (default: true for collection, creates full hierarchy)
- Ensures STAC v1.1.0 compliance (required fields, valid GeoJSON)
- Adds minimal required links (self, parent, collection)
- **Link generation**: Links are relative by default (e.g., `./collection.json`, `../items/item-001.json`), or absolute if `base_url` is provided in config
- **Field defaults**: Supports setting default values for optional fields via config (e.g., default license, default provider)

**Key Methods:**
```python
def scaffold_item(
    data: dict,
    collection_id: str,
    base_url: str | None = None
) -> pystac.Item
```

**Error Handling:**
- Missing required STAC fields (id, geometry, bbox, properties.datetime): Log error, skip Item
- Invalid geometry: Attempt repair with Shapely, else log and skip
- Malformed datetime: Attempt parse with dateutil, else log and skip

---

### 5. ExtensionModule

**Purpose**: Apply STAC extensions (dgeo, alternate-assets, custom) to Items or Collections.

**Inputs:**
- Base STAC Item/Collection
- Extension name or module path
- Extension-specific configuration

**Outputs:**
- Extended STAC Item/Collection with extension fields
- Extension validation report

**Design Approach:**
- **DECOMPOSED** to support pluggable architecture
- Hybrid registry: shortcuts for built-ins, module paths for custom
- Protocol-based extension interface for type safety
- Validates extended metadata against extension JSON schemas

**Submodules:**

#### 5.1. ExtensionRegistry
- Maintains dictionary of built-in extension shortcuts
- Maps extension names to module paths

#### 5.2. ExtensionLoader
- Loads extensions by name (registry) or module path (import)
- Verifies extensions implement `Extension` Protocol
- Caches loaded extensions for reuse

#### 5.3. ExtensionApplicator
- Applies extension fields to STAC objects
- Manages `stac_extensions` array in metadata
- Delegates to extension's `apply()` method

**Key Methods:**
```python
def apply_extension(
    item: pystac.Item,
    extension_ref: str,  # 'dgeo' or 'my.module.Extension'
    config: dict
) -> pystac.Item
```

**Error Handling:**
- Extension not found: Fail fast (config error)
- Extension apply() failure: Log error, skip extension, continue
- Validation failure: Log warning, optionally skip Item based on config

---

### 6. ValidateModule

**Purpose**: Validate STAC Items/Collections against STAC v1.1.0 spec and extension schemas.

**Inputs:**
- STAC Item/Collection objects
- Extension schemas (URLs or local paths)
- Validation configuration (strict vs permissive)

**Outputs:**
- Validation report (pass/fail, error details)
- List of invalid Items

**Design Approach:**
- Thin wrapper around `stac_validator` from stac-utils
- Validates core STAC spec + extension schemas
- Batch validation for performance (validate multiple Items concurrently)

**Key Methods:**
```python
def validate_item(
    item: pystac.Item,
    extension_schemas: list[str] | None = None
) -> tuple[bool, list[str]]  # (is_valid, errors)
```

**Error Handling:**
- Validation failures: Collect errors, add to failure report
- Schema not found: Log warning, skip extension validation
- Invalid JSON: Log error, mark Item as invalid

---

### 7. UpdateModule

**Purpose**: Modify existing STAC Item/Collection metadata (properties, assets, links).

**Inputs:**
- Item/Collection ID or selection criteria
- Update payload (new field values, additions, removals)

**Outputs:**
- Updated STAC objects
- Change audit log

**Design Approach:**
- Supports field-level updates (set, delete, append to arrays)
- Updates `updated` timestamp per STAC common metadata
- Can operate on single Item or bulk selection

**Key Methods:**
```python
def update_item(
    item: pystac.Item,
    updates: dict,  # Field paths and new values
    mode: Literal['merge', 'replace'] = 'merge'
) -> pystac.Item
```

**Error Handling:**
- Item not found: Log error, skip
- Invalid update (e.g., set required field to null): Log error, skip update
- Validation failure after update: Revert or log based on config

---

### 8. OutputModule

**Purpose**: Write STAC metadata to persistent storage in JSON or Parquet format.

**Inputs:**
- STAC Items/Collections/Catalogs
- Output format (JSON, Parquet)
- Output directory or cloud path
- Organization strategy (flat or by item ID)

**Outputs:**
- Organized STAC files on disk or cloud storage
- Output manifest (list of files written)

**Design Approach:**
- Uses `pystac.Item.to_dict()` for JSON serialization
- Uses `stac_geoparquet` for Parquet conversion
- Supports hierarchical directory structure (catalog/collection/items/)
- Generates output manifest for downstream ingestion (e.g., pgstac)

**Key Methods:**
```python
def write_items(
    items: Iterable[pystac.Item],
    output_path: str,
    format: Literal['json', 'parquet'] = 'json',
    organize_by: Literal['item_id', 'flat'] = 'item_id'
) -> OutputManifest
```

**Error Handling:**
- Write failures (disk full, permissions): Log error, skip file, continue
- Invalid path: Fail fast (config validation)
- Format conversion errors: Log error, skip Item

---

## Module Protocol Definitions

All core modules implement the `ModuleProtocol`, ensuring consistent interfaces for the workflow orchestrator. This section defines the protocol contracts.

### Base Module Protocol

```python
from typing import Protocol, Any
from dataclasses import dataclass

@dataclass
class WorkflowContext:
    """Shared state across workflow steps."""
    config: dict
    logger: logging.Logger
    failure_collector: FailureCollector
    data: dict[str, Any]  # Keyed by step_id for data passing

class ModuleProtocol(Protocol):
    """Base protocol all modules must implement."""
    
    def __init__(self, config: dict): ...
    
    async def execute(self, context: WorkflowContext) -> Any:
        """
        Execute the module's core logic.
        
        Args:
            context: Shared workflow context with config, logger, data
        
        Returns:
            Module-specific output (pystac objects, dicts, etc.)
        
        Raises:
            ModuleException: For critical failures (config errors)
            Logs errors for non-critical failures (via context.failure_collector)
        """
        ...
```

**Design Notes:**
- Modules are async to support concurrent orchestration
- `WorkflowContext` provides dependency injection (config, logger, shared data)
- Return values are stored in `context.data[step_id]` for downstream steps
- Critical errors (config issues) raise exceptions; data errors are collected

### Example Module Implementation

```python
import pystac
from pystac_client import Client

class DiscoveryModule:
    """Discover collections from STAC API endpoints."""
    
    def __init__(self, config: dict):
        self.catalog_url = config['catalog_url']
        self.collection_ids = config.get('collection_ids')
        self.filters = config.get('filters', {})
    
    async def execute(self, context: WorkflowContext) -> list[pystac.Collection]:
        try:
            client = Client.open(self.catalog_url)
            collections = []
            
            for collection in client.get_collections():
                if self._matches_filters(collection):
                    collections.append(collection)
            
            context.logger.info(f"Discovered {len(collections)} collections")
            return collections
            
        except Exception as e:
            context.logger.error(f"Discovery failed: {e}")
            raise ModuleException(f"Cannot discover collections: {e}")
    
    def _matches_filters(self, collection: pystac.Collection) -> bool:
        # Filter logic
        ...
```

---

## Extension System Architecture

The extension system uses a **hybrid approach**: Protocol-based contracts for type safety with a simple registry for built-in extensions.

### Extension Protocol

```python
from typing import Protocol
import pystac

class Extension(Protocol):
    """Protocol for STAC extension implementations."""
    
    # Class attributes
    extension_name: str  # e.g., "dgeo", "alternate-assets"
    schema_url: str      # URL to extension JSON schema
    
    def apply(
        self, 
        item: pystac.Item | pystac.Collection, 
        config: dict
    ) -> pystac.Item | pystac.Collection:
        """
        Apply extension fields to a STAC object.
        
        Args:
            item: STAC Item or Collection to extend
            config: Extension-specific configuration
        
        Returns:
            Extended STAC object with extension fields added
        """
        ...
    
    def validate(
        self, 
        item: pystac.Item | pystac.Collection
    ) -> tuple[bool, list[str]]:
        """
        Validate extension fields against schema.
        
        Args:
            item: STAC Item or Collection with extension fields
        
        Returns:
            Tuple of (is_valid, list_of_error_messages)
        """
        ...
```

### Built-in Extension: dgeo

```python
import pystac

class DgeoExtension:
    """dgeo STAC Extension for decentralized ownership and licensing."""
    
    extension_name = "dgeo"
    schema_url = "https://raw.githubusercontent.com/DecentralizedGeo/dgeo-asset/refs/heads/pgstac-variant/json-schema/schema.json"
    
    def apply(
        self, 
        item: pystac.Item, 
        config: dict
    ) -> pystac.Item:
        """Apply dgeo extension fields."""
        
        # Add dgeo extension to stac_extensions array
        if self.extension_name not in item.stac_extensions:
            item.stac_extensions.append(self.schema_url)
        
        # Add dgeo fields to properties
        item.properties['dgeo:ownership'] = config.get('ownership', {})
        item.properties['dgeo:licensing'] = config.get('licensing', {})
        
        if 'tokenization' in config:
            item.properties['dgeo:tokenization'] = config['tokenization']
        
        if 'provenance' in config:
            item.properties['dgeo:provenance'] = config['provenance']
        
        return item
    
    def validate(self, item: pystac.Item) -> tuple[bool, list[str]]:
        """Validate dgeo fields against schema."""
        # Use stac-validator with extension schema
        from stac_validator import stac_validator
        
        validator = stac_validator.StacValidator()
        is_valid = validator.validate_dict(
            item.to_dict(), 
            custom_schema=self.schema_url
        )
        
        errors = validator.message if not is_valid else []
        return is_valid, errors
```

### Extension Registry & Loader

```python
from typing import Type
from importlib import import_module

class ExtensionRegistry:
    """Simple registry for built-in extensions."""
    
    BUILTIN_EXTENSIONS = {
        'dgeo': 'stac_manager.extensions.dgeo.DgeoExtension',
        'alternate-assets': 'stac_manager.extensions.alternate_assets.AlternateAssetsExtension',
    }
    
    @classmethod
    def get_module_path(cls, name: str) -> str | None:
        """Get module path for a built-in extension name."""
        return cls.BUILTIN_EXTENSIONS.get(name)


class ExtensionLoader:
    """Load and cache extensions by name or module path."""
    
    def __init__(self):
        self._cache: dict[str, Extension] = {}
    
    def load(self, extension_ref: str) -> Extension:
        """
        Load extension by shortcut name or full module path.
        
        Args:
            extension_ref: Either a built-in name ('dgeo') or 
                          full module path ('my.module.MyExtension')
        
        Returns:
            Extension instance implementing Extension protocol
        
        Raises:
            ExtensionNotFoundError: If extension cannot be loaded
            ExtensionInvalidError: If loaded object doesn't match protocol
        """
        if extension_ref in self._cache:
            return self._cache[extension_ref]
        
        # Check if it's a built-in shortcut
        module_path = ExtensionRegistry.get_module_path(extension_ref)
        if module_path is None:
            # Assume it's a full module path
            module_path = extension_ref
        
        # Import the extension
        try:
            extension_class = self._import_class(module_path)
            extension = extension_class()
            
            # Verify it implements Extension protocol (duck typing)
            self._validate_protocol(extension)
            
            # Cache and return
            self._cache[extension_ref] = extension
            return extension
            
        except ImportError as e:
            raise ExtensionNotFoundError(
                f"Cannot import extension '{extension_ref}': {e}"
            )
    
    def _import_class(self, module_path: str) -> Type:
        """Import a class from a module path like 'package.module.ClassName'."""
        module_name, class_name = module_path.rsplit('.', 1)
        module = import_module(module_name)
        return getattr(module, class_name)
    
    def _validate_protocol(self, extension: Any) -> None:
        """Verify extension implements Extension protocol."""
        required_attrs = ['extension_name', 'schema_url', 'apply', 'validate']
        for attr in required_attrs:
            if not hasattr(extension, attr):
                raise ExtensionInvalidError(
                    f"Extension missing required attribute: {attr}"
                )
```

### Extension Module Usage

```python
class ExtensionModule:
    """Apply STAC extensions to Items or Collections."""
    
    def __init__(self, config: dict):
        self.extension_ref = config['extension']  # 'dgeo' or 'my.module.Extension'
        self.extension_config = config.get('config', {})
        self.loader = ExtensionLoader()
    
    async def execute(self, context: WorkflowContext) -> list[pystac.Item]:
        """Apply extension to Items from previous step."""
        
        # Load input Items from context (from previous step)
        items = context.data.get('items', [])
        
        # Load extension
        extension = self.loader.load(self.extension_ref)
        
        extended_items = []
        for item in items:
            try:
                # Apply extension
                extended_item = extension.apply(item, self.extension_config)
                
                # Optionally validate
                if context.config.get('validate_extensions', True):
                    is_valid, errors = extension.validate(extended_item)
                    if not is_valid:
                        context.logger.warning(
                            f"Extension validation failed for {item.id}: {errors}"
                        )
                        context.failure_collector.add(item.id, errors)
                        continue
                
                extended_items.append(extended_item)
                
            except Exception as e:
                context.logger.error(f"Failed to apply extension to {item.id}: {e}")
                context.failure_collector.add(item.id, str(e))
                continue
        
        context.logger.info(
            f"Applied {extension.extension_name} to {len(extended_items)}/{len(items)} items"
        )
        return extended_items
```

### YAML Configuration Example

```yaml
workflow:
  name: apply_dgeo_extension
  steps:
    - id: load_items
      module: IngestModule
      config:
        source: local_files.json
    
    - id: apply_dgeo
      module: ExtensionModule
      config:
        extension: dgeo  # ← Built-in shortcut
        config:
          ownership:
            did: "did:geo:nasa"
            rights: "public_domain"
          licensing:
            license: "CC0-1.0"
      depends_on: [load_items]
    
    - id: apply_custom
      module: ExtensionModule
      config:
        extension: acme_corp.extensions.ComplianceExtension  # ← Full path
        config:
          classification: "internal"
      depends_on: [load_items]
```

---

## Workflow Orchestrator

The orchestrator is the central component that builds and executes workflow **DAGs (Directed Acyclic Graphs)** from YAML configuration files. A DAG is a graph structure where workflow steps are nodes and dependencies are directed edges, with no circular dependencies. The orchestrator coordinates module execution, manages dependencies, and handles parallelization.

### Orchestrator Architecture

```
┌──────────────────────────────────────────────────────────┐
│              WorkflowOrchestrator                        │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  1. Config Loader & Validator                      │ │
│  └────────────┬───────────────────────────────────────┘ │
│               ↓                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  2. DAG Builder (Topological Sort)                 │ │
│  └────────────┬───────────────────────────────────────┘ │
│               ↓                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  3. Step Executor (Async Scheduler)                │ │
│  │     • Parallel execution of independent steps       │ │
│  │     • Dependency resolution                         │ │
│  │     • Error collection                              │ │
│  └────────────┬───────────────────────────────────────┘ │
│               ↓                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  4. Result Aggregator & Reporter                   │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### Core Components

#### WorkflowOrchestrator

```python
from typing import Any
import asyncio
from dataclasses import dataclass

@dataclass
class WorkflowStep:
    """Definition of a single workflow step."""
    id: str
    module_class: str  # Module class name (e.g., 'IngestModule')
    config: dict
    depends_on: list[str]

class WorkflowOrchestrator:
    """Build and execute workflow DAGs from configuration."""
    
    def __init__(self, config: dict):
        self.config = config
        self.steps: dict[str, WorkflowStep] = {}
        self.context = self._init_context()
    
    def _init_context(self) -> WorkflowContext:
        """Initialize workflow context."""
        return WorkflowContext(
            config=self.config,
            logger=self._setup_logger(),
            failure_collector=FailureCollector(),
            data={}
        )
    
    def load_workflow(self, workflow_config: dict) -> None:
        """
        Load workflow steps from configuration.
        
        Args:
            workflow_config: Workflow definition from YAML
        """
        for step_def in workflow_config['steps']:
            step = WorkflowStep(
                id=step_def['id'],
                module_class=step_def['module'],
                config=step_def.get('config', {}),
                depends_on=step_def.get('depends_on', [])
            )
            self.steps[step.id] = step
    
    def build_dag(self) -> list[list[str]]:
        """
        Build execution order from dependency graph.
        
        Returns:
            List of execution levels (each level can run in parallel)
            Example: [['step1'], ['step2', 'step3'], ['step4']]
        """
        # Topological sort with Kahn's algorithm
        in_degree = {step_id: 0 for step_id in self.steps}
        
        # Calculate in-degrees
        for step in self.steps.values():
            for dep in step.depends_on:
                if dep not in self.steps:
                    raise WorkflowConfigError(
                        f"Step '{step.id}' depends on unknown step '{dep}'"
                    )
                in_degree[step.id] += 1
        
        # Build execution levels
        execution_levels = []
        remaining = set(self.steps.keys())
        
        while remaining:
            # Find all steps with no remaining dependencies
            ready = [
                step_id for step_id in remaining 
                if in_degree[step_id] == 0
            ]
            
            if not ready:
                raise WorkflowConfigError(
                    "Circular dependency detected in workflow"
                )
            
            execution_levels.append(ready)
            
            # Remove ready steps and update in-degrees
            for step_id in ready:
                remaining.remove(step_id)
                
                # Decrease in-degree for dependent steps
                for other_id in remaining:
                    other_step = self.steps[other_id]
                    if step_id in other_step.depends_on:
                        in_degree[other_id] -= 1
        
        return execution_levels
    
    async def execute(self) -> WorkflowResult:
        """
        Execute the workflow DAG.
        
        Returns:
            WorkflowResult with success/failure summary
        """
        execution_levels = self.build_dag()
        
        self.context.logger.info(
            f"Executing workflow '{self.config['workflow']['name']}' "
            f"with {len(self.steps)} steps in {len(execution_levels)} levels"
        )
        
        for level_idx, level in enumerate(execution_levels):
            self.context.logger.info(
                f"Executing level {level_idx + 1}: {level}"
            )
            
            # Execute all steps in this level concurrently
            tasks = [
                self._execute_step(step_id) 
                for step_id in level
            ]
            await asyncio.gather(*tasks)
        
        # Generate final report
        return self._generate_result()
    
    async def _execute_step(self, step_id: str) -> None:
        """Execute a single workflow step."""
        step = self.steps[step_id]
        
        try:
            # Dynamically import module class
            module_class = self._import_module(step.module_class)
            
            # Instantiate module with config
            module = module_class(step.config)
            
            # Execute module
            self.context.logger.info(f"Starting step '{step_id}'")
            result = await module.execute(self.context)
            
            # Store result in context for downstream steps
            self.context.data[step_id] = result
            
            self.context.logger.info(
                f"Completed step '{step_id}' successfully"
            )
            
        except Exception as e:
            self.context.logger.error(
                f"Step '{step_id}' failed: {e}"
            )
            # Store error in context
            self.context.data[step_id] = {'error': str(e)}
            
            # Critical failure stops workflow
            if isinstance(e, ModuleException):
                raise WorkflowExecutionError(
                    f"Critical failure in step '{step_id}': {e}"
                )
    
    def _import_module(self, module_class_name: str):
        """Import module class by name."""
        # Map class name to module path
        module_map = {
            'DiscoveryModule': 'stac_manager.modules.discovery.DiscoveryModule',
            'IngestModule': 'stac_manager.modules.ingest.IngestModule',
            'TransformModule': 'stac_manager.modules.transform.TransformModule',
            'ScaffoldModule': 'stac_manager.modules.scaffold.ScaffoldModule',
            'ExtensionModule': 'stac_manager.modules.extension.ExtensionModule',
            'ValidateModule': 'stac_manager.modules.validate.ValidateModule',
            'UpdateModule': 'stac_manager.modules.update.UpdateModule',
            'OutputModule': 'stac_manager.modules.output.OutputModule',
        }
        
        module_path = module_map.get(module_class_name)
        if not module_path:
            raise WorkflowConfigError(
                f"Unknown module class: {module_class_name}"
            )
        
        # Import and return class
        from importlib import import_module
        module_name, class_name = module_path.rsplit('.', 1)
        module = import_module(module_name)
        return getattr(module, class_name)
    
    def _generate_result(self) -> dict:
        """Generate workflow execution summary."""
        failures = self.context.failure_collector.get_all()
        
        return {
            'workflow_name': self.config['workflow']['name'],
            'total_steps': len(self.steps),
            'successful_steps': len([
                s for s in self.context.data.values() 
                if not isinstance(s, dict) or 'error' not in s
            ]),
            'failed_steps': len([
                s for s in self.context.data.values() 
                if isinstance(s, dict) and 'error' in s
            ]),
            'total_failures': len(failures),
            'failures': failures
        }
```

### FailureCollector

```python
@dataclass
class FailureRecord:
    """Record of a single failure."""
    item_id: str
    error_message: str
    step_id: str
    timestamp: str

class FailureCollector:
    """Collect and manage failures during workflow execution."""
    
    def __init__(self):
        self._failures: list[FailureRecord] = []
    
    def add(self, item_id: str, error: str, step_id: str = None) -> None:
        """Add a failure record."""
        from datetime import datetime
        
        self._failures.append(FailureRecord(
            item_id=item_id,
            error_message=error,
            step_id=step_id or 'unknown',
            timestamp=datetime.utcnow().isoformat()
        ))
    
    def get_all(self) -> list[FailureRecord]:
        """Get all failure records."""
        return self._failures.copy()
    
    def write_report(self, output_path: str) -> None:
        """Write failures to a JSON file."""
        import json
        
        with open(output_path, 'w') as f:
            json.dump(
                [vars(f) for f in self._failures],
                f,
                indent=2
            )
```

### YAML Workflow Example (Complex)

```yaml
workflow:
  name: cmr_stac_bulk_ingest
  description: Ingest from CMR-STAC, apply dgeo extension, validate, and output
  
  steps:
    # Step 1: Discover collections (no dependencies)
    - id: discover
      module: DiscoveryModule
      config:
        catalog_url: https://cmr.earthdata.nasa.gov/stac/v1
        collection_ids:
          - SENTINEL-1A_*
          - MODIS_*
    
    # Step 2: Ingest items (depends on discover)
    - id: ingest
      module: IngestModule
      config:
        limit: 10000
        concurrency: 10
      depends_on: [discover]
    
    # Step 3a & 3b: Apply extensions in parallel (both depend on ingest)
    - id: apply_dgeo
      module: ExtensionModule
      config:
        extension: dgeo
        config:
          ownership:
            did: "did:geo:nasa"
      depends_on: [ingest]
    
    - id: apply_alternate_assets
      module: ExtensionModule
      config:
        extension: alternate-assets
        config:
          alternate_locations: []
      depends_on: [ingest]
    
    # Step 4: Validate (depends on both extensions)
    - id: validate
      module: ValidateModule
      config:
        strict: false
      depends_on: [apply_dgeo, apply_alternate_assets]
    
    # Step 5: Output (depends on validation)
    - id: output
      module: OutputModule
      config:
        format: parquet
        output_path: ./output/cmr-stac
        organize_by: collection
      depends_on: [validate]

# Global configuration
logging:
  level: INFO
  file: ./logs/workflow.log

processing:
  concurrency: 10
  rate_limit: 10.0
```

---

## Data Flow Patterns

### Inter-Step Data Passing

Data flows between steps via the `WorkflowContext.data` dictionary:

```python
# Step 1: DiscoveryModule
async def execute(self, context):
    collections = [...]  # Discover collections
    return collections  # Stored in context.data['discover']

# Step 2: IngestModule (depends on discover)
async def execute(self, context):
    # Access previous step's output
    collections = context.data.get('discover', [])
    
    items = []
    for collection in collections:
        items.extend(await self.fetch_items(collection))
    
    return items  # Stored in context.data['ingest']
```

### Data Flow Diagram (Example Workflow)

```
discover
   ↓
   └─ collections (list[Collection])
         ↓
       ingest
         ↓
         └─ items (list[Item])
               ↓
         ┌─────┴─────┐
         ↓           ↓
   apply_dgeo   apply_alternate
         ↓           ↓
         └─ dgeo_items   alternate_items ─┘
                     ↓
                  validate
                     ↓
                     └─ valid_items (list[Item])
                           ↓
                        output
                           ↓
                           └─ manifest (OutputManifest)
```

### Handling Multiple Dependencies

When a step depends on multiple upstream steps, it accesses each via `context.data`:

```python
class MergeModule:
    """Example: Merge outputs from multiple upstream steps."""
    
    async def execute(self, context):
        # Access two upstream dependencies
        dgeo_items = context.data.get('apply_dgeo', [])
        alternate_items = context.data.get('apply_alternate_assets', [])
        
        # Merge logic (example: combine by ID)
        merged = {}
        for item in dgeo_items:
            merged[item.id] = item
        
        for item in alternate_items:
            if item.id in merged:
                # Merge alternate-assets into dgeo item
                merged[item.id].assets.update(item.assets)
            else:
                merged[item.id] = item
        
        return list(merged.values())
```

---

## Error Handling Architecture

The system uses a **collect-and-continue** strategy with detailed failure tracking. This section defines how errors are categorized, collected, and reported.

### Error Categories

| Error Type | Handling Strategy | Example |
|------------|-------------------|---------|
| **Configuration Errors** | Fail fast at startup | Invalid YAML syntax, missing required config fields |
| **Module Errors** | Fail fast, stop workflow | Module not found, invalid module configuration |
| **Data Errors** | Collect and continue | Invalid Item geometry, missing required STAC field |
| **Network Errors** | Retry with backoff, then collect | API timeout, 429 rate limit, connection refused |
| **Validation Errors** | Collect and continue | STAC validation failure, extension schema mismatch |
| **I/O Errors** | Collect and continue | File write failure, disk full |

### Error Classes

```python
class StacManagerError(Exception):
    """Base exception for all toolkit errors."""
    pass

class ConfigurationError(StacManagerError):
    """Configuration validation failed (fail fast)."""
    pass

class ModuleException(StacManagerError):
    """Critical module error (fail fast)."""
    pass

class WorkflowConfigError(StacManagerError):
    """Invalid workflow definition (fail fast)."""
    pass

class WorkflowExecutionError(StacManagerError):
    """Workflow execution failed (fail fast)."""
    pass

class DataProcessingError(StacManagerError):
    """Non-critical data error (collect and continue)."""
    pass
```

### Error Handling in Modules

```python
class TransformModule:
    """Example of collect-and-continue error handling."""
    
    async def execute(self, context: WorkflowContext) -> list[dict]:
        source_data = self._load_source_data()
        transformed = []
        
        for record in source_data:
            try:
                result = self._transform_record(record, context.config['schema'])
                transformed.append(result)
                
            except DataProcessingError as e:
                # Non-critical error: log and collect
                context.logger.warning(f"Transform failed for record {record.get('id')}: {e}")
                context.failure_collector.add(
                    item_id=record.get('id', 'unknown'),
                    error=str(e),
                    step_id='transform'
                )
                continue
            
            except Exception as e:
                # Unexpected error: log and collect
                context.logger.error(f"Unexpected error transforming record: {e}")
                context.failure_collector.add(
                    item_id=record.get('id', 'unknown'),
                    error=f"Unexpected: {str(e)}",
                    step_id='transform'
                )
                continue
        
        context.logger.info(
            f"Transformed {len(transformed)}/{len(source_data)} records successfully"
        )
        return transformed
```

### Retry Logic with Exponential Backoff

```python
import asyncio
from typing import Callable, Any

async def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> Any:
    """
    Retry a function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_attempts: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        exponential_base: Backoff multiplier
    
    Returns:
        Result from successful function call
    
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_attempts):
        try:
            return await func()
        except Exception as e:
            last_exception = e
            
            if attempt < max_attempts - 1:
                delay = min(base_delay * (exponential_base ** attempt), max_delay)
                logging.warning(
                    f"Attempt {attempt + 1}/{max_attempts} failed: {e}. "
                    f"Retrying in {delay:.1f}s"
                )
                await asyncio.sleep(delay)
            else:
                logging.error(
                    f"All {max_attempts} attempts failed. Last error: {e}"
                )
    
    raise last_exception
```

### Usage in IngestModule

```python
class IngestModule:
    async def fetch_items(self, collection: pystac.Collection) -> list[pystac.Item]:
        items = []
        
        async def fetch_page(url: str):
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 429:
                        # Rate limited
                        raise aiohttp.ClientResponseError(
                            request_info=response.request_info,
                            history=response.history,
                            status=429,
                            message="Rate limited"
                        )
                    response.raise_for_status()
                    return await response.json()
        
        # Fetch with retry logic
        try:
            data = await retry_with_backoff(
                lambda: fetch_page(collection.links['items'].href),
                max_attempts=3
            )
            items.extend([pystac.Item.from_dict(item) for item in data['features']])
        except Exception as e:
            logging.error(f"Failed to fetch items from {collection.id}: {e}")
            # Collect error and continue
        
        return items
```

---

## Async & Concurrency Model

The toolkit uses Python's `asyncio` for concurrent I/O operations and parallelization.

### Concurrency Strategy

- **Orchestrator level**: Steps within an execution level run in parallel (`asyncio.gather`)
- **Module level**: Modules can fetch/process data concurrently (e.g., fetching Items from multiple collections)
- **Rate limiting**: Semaphore-based limits to respect API constraints

### Semaphore-Based Rate Limiting

```python
import asyncio
from typing import Callable, Any

class RateLimiter:
    """Rate limiter using semaphore and token bucket."""
    
    def __init__(self, requests_per_second: float, max_concurrent: int = 10):
        self.requests_per_second = requests_per_second
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0
    
    async def acquire(self):
        """Acquire rate limit token."""
        async with self.semaphore:
            # Ensure minimum interval between requests
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
            
            self.last_request_time = asyncio.get_event_loop().time()
    
    async def execute(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with rate limiting."""
        await self.acquire()
        return await func(*args, **kwargs)
```

### Usage in IngestModule

```python
class IngestModule:
    def __init__(self, config: dict):
        self.rate_limiter = RateLimiter(
            requests_per_second=config.get('rate_limit', 10.0),
            max_concurrent=config.get('concurrency', 5)
        )
    
    async def fetch_all_items(
        self, 
        collections: list[pystac.Collection]
    ) -> list[pystac.Item]:
        """Fetch items from multiple collections concurrently."""
        
        async def fetch_collection_items(collection):
            return await self.rate_limiter.execute(
                self._fetch_items_for_collection,
                collection
            )
        
        # Fetch from all collections concurrently with rate limiting
        results = await asyncio.gather(
            *[fetch_collection_items(col) for col in collections],
            return_exceptions=True  # Don't fail entire gather on single error
        )
        
        # Flatten results and filter exceptions
        all_items = []
        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Collection fetch failed: {result}")
                continue
            all_items.extend(result)
        
        return all_items
```

### AsyncIO and PySTAC Client Integration

Since `pystac-client` is synchronous, we wrap it with async executors:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class DiscoveryModule:
    def __init__(self, config: dict):
        self.executor = ThreadPoolExecutor(max_workers=config.get('workers', 4))
    
    async def execute(self, context: WorkflowContext) -> list[pystac.Collection]:
        """Run synchronous pystac-client in thread pool."""
        loop = asyncio.get_event_loop()
        
        # Run blocking operation in thread pool
        collections = await loop.run_in_executor(
            self.executor,
            self._discover_collections_sync,
            context.config['catalog_url']
        )
        
        return collections
    
    def _discover_collections_sync(self, catalog_url: str) -> list[pystac.Collection]:
        """Synchronous collection discovery."""
        from pystac_client import Client
        
        client = Client.open(catalog_url)
        return list(client.get_collections())
```

---

## Logging Architecture

Structured, consistent logging across all modules using Python's standard `logging` module.

### Logger Configuration

```python
import logging
import sys
from pathlib import Path

def setup_logger(config: dict) -> logging.Logger:
    """Configure structured logger from config."""
    
    logger = logging.getLogger('stac_manager')
    logger.setLevel(config.get('logging', {}).get('level', 'INFO'))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(console_handler)
    
    # File handler (optional)
    log_file = config.get('logging', {}).get('file')
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        logger.addHandler(file_handler)
    
    return logger
```

### Structured Log Messages

```python
# Module-level logging
class IngestModule:
    async def execute(self, context: WorkflowContext):
        context.logger.info(
            f"[IngestModule] Starting ingestion from {self.catalog_url}"
        )
        
        items = await self.fetch_items(context)
        
        context.logger.info(
            f"[IngestModule] Completed: fetched {len(items)} items"
        )
        
        return items
```

### Log Levels Usage

| Level | Usage |
|-------|-------|
| **DEBUG** | Detailed diagnostic info (field mappings, API responses) |
| **INFO** | Progress updates (step completion, counts) |
| **WARNING** | Non-critical errors (validation failures, skipped items) |
| **ERROR** | Critical failures (module exceptions, I/O errors) |

### Processing Summary Report

```python
def generate_processing_summary(
    workflow_result: dict,
    failure_collector: FailureCollector
) -> str:
    """Generate human-readable processing summary."""
    
    failures_by_step = {}
    for failure in failure_collector.get_all():
        step = failure.step_id
        failures_by_step.setdefault(step, []).append(failure)
    
    summary = f"""
=== Workflow Processing Summary ===
Workflow: {workflow_result['workflow_name']}
Total Steps: {workflow_result['total_steps']}
Successful Steps: {workflow_result['successful_steps']}
Failed Steps: {workflow_result['failed_steps']}

=== Failure Breakdown ===
Total Failures: {workflow_result['total_failures']}
"""
    
    for step_id, failures in failures_by_step.items():
        summary += f"\n{step_id}: {len(failures)} failures"
    
    summary += f"\n\nDetailed failure report written to: failures.json"
    
    return summary
```

---

## Dependency Integration

### Foundation Library Usage Summary

| Library | Integration Point | Wrapper Strategy |
|---------|-------------------|------------------|
| **PySTAC** | All modules (STAC object I/O) | Direct usage, no wrapper |
| **pystac-client** | DiscoveryModule, IngestModule | Thread pool executor for async |
| **stac-validator** | ValidateModule | Direct usage with batch processing |
| **stac-geoparquet** | OutputModule | Direct usage for Parquet conversion |
| **aiohttp** | IngestModule (async HTTP) | Rate-limited wrapper |
| **pandas** | TransformModule (CSV/Parquet I/O) | Direct usage |

### Import Strategy

```python
# Core STAC libraries (direct imports)
import pystac
from pystac import Catalog, Collection, Item
from pystac_client import Client
from stac_validator import stac_validator
import stac_geoparquet

# Async and data libraries
import aiohttp
import asyncio
import pandas as pd
import pyarrow

# Standard library
import logging
from pathlib import Path
from typing import Any, Protocol
from dataclasses import dataclass
```

### Version Compatibility

From PRD `pyproject.toml` requirements:

```toml
# Core STAC libraries (stac-utils ecosystem)
pystac >= 1.10.0           # STAC v1.1.0 support
stac-validator >= 3.0.0    # STAC v1.1.0 validation
pystac-client >= 0.8.0     # STAC API v1.0.0+ client
stac-geoparquet >= 0.4.0   # GeoParquet format

# Async and HTTP
aiohttp >= 3.8.0
asyncio >= 3.4.3

# Data processing
pyarrow >= 10.0
pandas >= 1.5.0

# Configuration and CLI
pyyaml >= 6.0
click >= 8.0

# Utilities
python-dateutil >= 2.8.0
shapely >= 2.0.0
```

---

## Summary

This Technical Architecture Specification defines:

1. **Four-layer architecture**: User Interface → Orchestration → Business Logic → Foundation
2. **Eight core modules**: Discovery, Ingest, Transform, Scaffold, Extension, Validate, Update, Output
3. **Protocol-based contracts**: `ModuleProtocol` and `Extension` for type safety
4. **Hybrid extension system**: Built-in registry shortcuts + full module path support
5. **Workflow orchestrator**: DAG-based execution with dependency resolution and parallelization
6. **Collect-and-continue error handling**: Graceful degradation for production scale
7. **Async-first concurrency**: Rate-limited parallel processing
8. **Structured logging**: Comprehensive tracking and failure reporting
9. **Foundation library integration**: Direct use of stac-utils ecosystem

The architecture supports all PRD requirements while maintaining modularity, extensibility, and production-grade reliability.

