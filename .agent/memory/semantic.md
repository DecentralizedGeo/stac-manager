# Semantic Memory: STAC Manager Concepts

## Core Abstractions
- **Pipes and Filters**: The fundamental architectural pattern. Components are "Filters" (Fetchers, Modifiers, Bundlers) connected by "Pipes" (the orchestration engine).
- **Fetcher (Async Source)**: Handles high-concurrency I/O (STAC APIs, S3).
- **Modifier (Sync Filter)**: Performs item-level logic (Transform, Update). Kept sync for CPU efficiency and developer simplicity.
- **Bundler (Sync/Async Sink)**: Aggregates and serializes items (Parquet, JSON).

## Tooling Context
- **PySTAC**: The foundation library for all data models.
- **pystac-client**: Primary engine for API-based fetchers.
- **stac-geoparquet**: Used by Bundlers for optimized spatial storage.
## STAC Manager Architecture
- **Phase 1: Utilities Foundation**: Foundational layer (`stac_manager/utils/`) for field manipulation, geometry processing, and streaming.
- **Phase 2: Pipeline Modules**: Domain-specific filters (Ingest, Transform, etc.) built on utils.
- **Phase 3: Orchestration Layer**: The workflow engine connecting modules.

## Data Structure Policies
- **Wire Format**: Items flow through the pipeline as pure `dict` for performance and stability.
- **Serialization**: Conversion to PySTAC objects is only done at I/O boundaries or where rich API is required.
## Library Quirks & Verified Behaviors
- **Shapely 2.x**: `mapping(shape)` returns tuples for coordinates. Pipeline standardization requires explicit recursion to convert these to `List[List[float]]` for GeoJSON compatibility.
- **stac-validator**: Requires `StacValidate` class (not `StacValidator`) and direct access to `message` attribute for details.
- **Async Streaming**: `chunk_stream` and `limit_stream` designed as non-blocking async generators to preserve backpressure in the pipeline.

## Module Internal Patterns
- **UpdateModule Logic**: While it uses `set_nested_field` utility, it wraps logic locally (`set_field_with_path_creation`) to provide granular control over path creation (`create_missing_paths` flag) and specific error mapping (`DataProcessingError`).
- **Patching Strategy**: Patches can be applied via `deep_merge` (default) or full `replace`, allowing flexible item modification strategies.
- **Merge Strategy Semantics**: Different modules use different terminology for similar concepts:
  - **UpdateModule**: Uses `mode` parameter (`merge`, `replace`, `update_only`) for STAC item field updates.
  - **TransformModule**: Uses `strategy` parameter (`merge`, `update`) for sidecar data enrichment (no `replace` option).
  - **`deep_merge` Utility**: Supports three strategies: `keep_existing` (default), `overwrite`, `update_only` (only modifies existing paths).
- **ExtensionModule Template Building**: Parses JSON Schemas to build templates; uses `oneOf` heuristic (selects first object schema with `type: Feature`).
- **ExtensionModule Asset Scaffolding**: 
    - Heuristic for assets: Merges all defined properties from a schema's `assets` definition into a single `*` template. 
    - Support for `additionalProperties` (catch-all) and explicit `properties` (specific variants) in schemas.
- **Recursive Parsing (`_parse_field`)**: Extension builder uses recursion to handle `$ref`, `allOf`, and nested object scaffolding. Leaf nodes return `default` values or `None`.
- **Local Fixture Caching**: `tests/fixtures/downloader.py` provides transparent caching of remote schemas to `tests/fixtures/data/`. Tests should prioritize these cached versions to minimize network dependency and ensure determinism.
- **Required Fields Only**: `ExtensionModule` can filter scaffolding to only include fields listed in a schema's `required` array, controlled by the `required_fields_only` config flag.

## TransformModule Sidecar Indexing & Enrichment
- Supports dictionary files (ID ↔ Data mapping).
- Supports list files using JMESPath `sidecar_id_path` for ID extraction.
- **Field Mapping**: Allows renaming/transforming sidecar fields before they are merged into STAC item properties. Runs `apply_jmespath` on sidecar data per mapping entry.
- **Missing Item Handling**: Configurable via `handle_missing` (`ignore`, `warn`, `error`). Warnings are directed to the `failure_collector`.
- Indexing occurs during module `__init__` (setup phase) to facilitate fast lookups during `modify`.

## Infrastructure & Mocking Policies
- **Failure Collector Protocol**: Modules use `context.failure_collector.add(item_id, error, step_id)` for non-critical logging.
- **Test Fidelity**: `MockFailureCollector` must provide a `get_all()` method returning `Record`-like objects (with `.message`, `.item_id`, etc.) to ensure tests reliably catch failures as they appear in production.
- **Context Integrity**: The `WorkflowContext` is the single point of truth for state; modules should never store transient state in global variables.

