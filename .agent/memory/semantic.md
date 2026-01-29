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
- **Phase 1: Utilities Foundation**: Foundational layer (`stac_manager/utils/`) for field manipulation, geometry processing, and streaming. ✅ COMPLETE
- **Phase 2: Pipeline Modules**: Domain-specific filters (Ingest, Transform, etc.) built on utils. ✅ COMPLETE
  - 7 modules: IngestModule, SeedModule, TransformModule, UpdateModule, ValidateModule, ExtensionModule, OutputModule
  - All implement proper protocols (Fetcher, Modifier, Bundler)
  - Comprehensive integration tests validate end-to-end pipelines
- **Phase 3: Orchestration Layer**: The workflow engine connecting modules. � IN PROGRESS
  - **Part 1** (Tasks 1-12): Configuration + State Persistence ✅ COMPLETE
    - Pydantic models, YAML loading, DAG validation (Kahn's algorithm)
    - CheckpointManager with Parquet storage, atomic writes, resume capability
  - **Part 2** (Tasks 13-20): Orchestration Engine ✅ COMPLETE
    - Module registry with dynamic loading
    - StacManager orchestrator with sequential streaming
    - Matrix strategy with parallel execution (asyncio.gather)
    - WorkflowResult with comprehensive error reporting
    - Top-level public API for programmatic usage
  - **Part 3** (Tasks 21-30): CLI + Integration Testing 📋 PENDING
    - Click-based CLI with `run-workflow` and `validate-workflow`
    - End-to-end integration tests with real modules
    - Matrix, checkpoint, and CLI verification tests


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

## Wildcard Pattern System (v1.1.0)

### Core Concept
- **Purpose**: Apply updates/extensions to ALL assets in STAC items without manual enumeration
- **Syntax**: `assets.*` matches any asset key (e.g., `visual`, `B04`, `thumbnail`)
- **Use Cases**: 
  - Add alternate locations to all assets: `assets.*.alternate.s3.href`
  - Set common metadata: `assets.*.roles: ["data"]`
  - Apply consistent updates across dynamic asset sets

### Implementation (`expand_wildcard_paths`)
- **Location**: `stac_manager/utils/field_ops.py`
- **Algorithm**:
  1. Filter input dict for keys containing `*` (wildcard patterns)
  2. For each pattern, match against actual asset keys in item
  3. Generate expanded keys by replacing `*` with actual asset key
  4. Apply template variable substitution to values
  5. Return fully expanded dict with concrete paths

### Template Variables
- **Available Variables**:
  - `{item_id}`: Item's unique identifier
  - `{collection_id}`: Collection ID from context
  - `{asset_key}`: Current asset's key name
- **Substitution Pattern**: `_apply_template_variables(value, context)` recursively replaces placeholders
- **Example**: `s3://bucket/{collection_id}/{asset_key}/` → `s3://bucket/sentinel-2-l2a/B04/`

### Critical Pattern: Deep Copy for Dict Values
- **Problem**: Python assigns dicts by reference → all assets share same object
- **Symptom**: Last value applied wins for all assets (object mutation)
- **Solution**: Use `copy.deepcopy(value)` when assigning dict values in `deep_merge()`
- **Location**: `field_ops.py` lines 73, 76
- **Impact**: Each asset gets independent dict object, preventing data corruption

### Module Integration

#### ExtensionModule
- **Expandable Defaults**: Filters defaults by presence of `*` or `.` in keys
- **Non-Wildcard Defaults**: Nested dict defaults preserved for template building (backward compatibility)
- **Application**: Uses `set_nested_field()` to apply each expanded default individually
- **Storage**: Separates `raw_defaults` from expanded wildcards in `__init__`

#### UpdateModule
- **Wildcard Updates**: Expands `self.config.updates` if wildcards present
- **Application**: Uses `set_field_with_path_creation()` after expansion
- **Consistency**: Uses same `expand_wildcard_paths()` utility as ExtensionModule

### Testing Pattern
- **Verification**: Test that each asset receives unique values after expansion
- **Assertion**: Check expanded values contain asset-specific content (e.g., asset key in path)
- **Isolation**: Verify no object sharing between assets (modify one asset, check others unchanged)

## TransformModule Input Indexing & Enrichment

### Terminology (v1.1.0+)
- **Standard**: "Input Data", "Input File", `input_index`, `input_entry`
- **Deprecated**: "Sidecar" terminology (removed in v1.1.0 for spec alignment)

### Indexing & File Support
- Supports dictionary files (ID ↔ Data mapping).
- Supports list files using JMESPath `input_join_key` for ID extraction.
- **Dict Format**: Keys are item IDs, no `input_join_key` needed (automatic lookup)
- **List Format**: Array of objects, requires `input_join_key` to extract ID field
- **CSV Support**: Uses `pyarrow.csv` with forced string type for join key (prevents "007" → 7 conversion)
- Indexing occurs during module `__init__` (setup phase) to facilitate fast lookups during `modify`.

### Field Mapping
- **Direction**: 
  - **Key**: Target field path in item (where data goes) - supports dot-notation
  - **Value**: JMESPath query applied to input entry (where data comes from)
  - **Example**: `"properties.cloud_cover": "cloud_cover"` means `item.properties.cloud_cover ← input_entry.cloud_cover`
- **Wildcard Support (v1.1.0)**: Uses `expand_wildcard_paths` utility (same as UpdateModule/ExtensionModule)
  - **Pattern**: `assets.*.field` matches all assets
  - **Template Variables**: `{item_id}`, `{collection_id}`, `{asset_key}` in values
  - **Example**: `"assets.*.dgeo:cid": "assets.{asset_key}.cid"`
  - **Quoted Keys**: `'assets."ANG.txt".field'` for keys with dots
- **Execution**: Runs `_extract_value` (hybrid: direct key → JMESPath fallback) on input data per mapping entry

### Strategy Semantics (v1.1.0)
- **`strategy: "update_existing"`** (DEFAULT - changed in v1.1.0):
  - Filters expanded wildcards to only paths that **already exist** in item
  - Uses `get_nested_field` check before applying mapping
  - **Behavior**: Won't create new assets or fields not in original item
  - **Use Case**: Safely enrich existing structures without side effects
- **`strategy: "merge"`**:
  - Applies all expanded wildcards from input (no filtering)
  - Creates new paths as needed via `set_nested_field`
  - **Behavior**: Creates new assets/fields from input data
  - **Use Case**: Integrate external metadata that may contain additional assets
- **Rejected Strategy**: `"overwrite"` - use UpdateModule to remove + TransformModule merge instead

### Missing Item Handling
- Configurable via `handle_missing` (`ignore`, `warn`, `error`)
- Warnings are directed to the `failure_collector`


## Infrastructure & Mocking Policies
- **Failure Collector Protocol**: Modules use `context.failure_collector.add(item_id, error, step_id)` for non-critical logging.
- **Test Fidelity**: Use real `FailureCollector` in test fixtures (lightweight, stable API) to ensure tests reliably catch failures as they appear in production. Avoid mock drift by using actual implementations.
- **Context Integrity**: The `WorkflowContext` is the single point of truth for state; modules should never store transient state in global variables.

## IngestModule & OutputModule Patterns

- **IngestModule File Detection**: Auto-detects JSON vs Parquet via file extension, loads collections or individual items.
- **IngestModule API Mode**: Uses `pystac-client` with configurable filters (bbox, datetime, query). Returns async generator for streaming.
- **OutputModule Collection Structure**: Self-contained collections with `{collection_id}/collection.json` and `items/` subfolder.
- **OutputModule Relative Links**: All hrefs use relative paths for portability: `../collection.json`, `{item_id}.json`.
- **OutputModule Buffered Writes**: Accumulates items in memory buffer, writes atomically on flush with proper directory creation.

## pystac Extension Registry

- **EXTENSION_HOOKS**: Global registry in `pystac.extensions` containing all registered extensions.
- **Registration Check**: Use `schema_uri in EXTENSION_HOOKS.hooks` to verify if extension is officially supported.
- **Extension Migration**: Check `hook.prev_extension_ids` for older extension schema URIs to support version transitions.
- **Import Pattern**: Prefer `from pystac import EXTENSION_HOOKS` over importing entire `pystac` module for cleaner code.

## CheckpointManager (v1.0.0) - Pipeline Completion Tracking

### Core Concept
- **Purpose**: Track whether items have completed the ENTIRE pipeline (not per-step progress)
- **Question Answered**: "Did this item finish the full workflow and produce output?"
- **Use Case**: Resume incomplete workflows by skipping already-completed items

### Storage & Schema
- **Location**: `./checkpoints/{workflow_id}/{collection_id}.parquet`
- **Schema**: `(item_id, collection_id, output_path, completed, timestamp, error)`
- **Single File**: One checkpoint file per collection (not per step)
- **Completion Set**: Only items with `completed=True` loaded into `_completed_items` for O(1) lookup

### API Methods
- `is_completed(item_id) -> bool`: Check if item finished full pipeline (O(1) lookup)
- `mark_completed(item_id, output_path)`: Record successful pipeline completion
- `mark_failed(item_id, error)`: Record failure (enables retry on next run)
- **Deprecated**: `contains()`, `add()`, `save()` (kept for backward compatibility)

### Integration Pattern
- **Single Manager**: One `CheckpointManager` per workflow (shared across all steps)
- **Check Timing**: After IngestModule fetch, before processing
- **Mark Timing**: After OutputModule succeeds (or fails)
- **Constructor**: `CheckpointManager(workflow_id, collection_id, checkpoint_root, buffer_size, resume_from_existing)`

### Key Design Principles
- **Completion-Based**: Track if item reached end of pipeline, not intermediate steps
- **Failed Item Retry**: Failed items NOT added to completed set → automatic retry
- **Path Verification**: Records `output_path` to verify item actually written to disk
- **Atomic Writes**: Maintains temp file + rename pattern from original implementation

## CacheManager (v1.1.0) - HTTP Response Caching

### Core Concept
- **Purpose**: Avoid redundant HTTP requests to STAC APIs during development/testing
- **Question Answered**: "Have I already fetched this item from the API?"
- **Use Case**: Speed up re-runs during modifier development, avoid rate limits, enable offline work

### Critical Distinction from Checkpoints
| Aspect | **Checkpoint** | **Cache** |
|--------|---------------|-----------|
| **Scope** | Entire pipeline | IngestModule only |
| **When Checked** | After ingest, before processing | Before HTTP request |
| **Data Stored** | Completion status + output_path | Full STAC Item JSON |
| **Purpose** | Resume incomplete workflows | Avoid redundant API calls |

### Storage & Schema (Design Phase - v1.1.0)
- **Location**: `./cache/{collection_id}.parquet` (single file per collection)
- **Schema**: `(item_id, collection_id, cached_at, expires_at, item_data)`
- **item_data Field**: JSON-serialized STAC Item stored as string (preserves flexibility)
- **Format Benefits**: 10-100x compression vs JSON, predicate pushdown, built-in compression

### API Design (Not Yet Implemented)
- **In-Memory Index**: `Dict[str, datetime]` for O(1) existence/expiration checks
- `exists(item_id) -> bool`: Check presence and expiration (single call)
- `load(item_id) -> Dict`: Load STAC item using predicate pushdown
- `save(item_id, item)`: Append to Parquet with automatic deduplication
- `clear(older_than_days)`: Age-based or full cache cleanup
- **TTL Support**: Configurable expiration via `ttl_hours` (default: 24h)

### Integration Pattern (Design Phase)
```python
# IngestModule.fetch()
if self.cache_enabled and self.cache.exists(item_id):
    item = self.cache.load(item_id)  # Load from cache (no HTTP)
else:
    item = await self._fetch_item_from_api(item_id)  # HTTP fetch
    if self.cache_enabled:
        self.cache.save(item_id, item)  # Save to cache
```

### Configuration (Design Phase)
- `enable_cache: true` (opt-in, default: false)
- `cache_ttl_hours: 24` (expiration time)
- `cache_root: ./cache` (storage location)

### Status
- **v1.0.0**: NOT implemented (checkpoints only)
- **v1.1.0**: Design complete in `docs/improvements/cache-strategy-design-v1.1.0.md`
- **Future**: 4-phase implementation plan defined

## StacManager (v1.0.0) - Orchestration Engine

### Core Concept
- **Purpose**: The "conductor" that wires all pipeline modules together and manages execution
- **Question Answered**: "How do I run a multi-module workflow with config, checkpoints, and error handling?"
- **Use Case**: Execute complete STAC data pipelines with automatic resume, matrix strategies, and graceful failure handling

### Module Registry & Loading
- **MODULE_REGISTRY**: Hardcoded dict mapping module names to import paths (7 modules)
- **Dynamic Loading**: Uses `importlib.import_module()` to load module classes at runtime
- **Error Handling**: Raises `ModuleLoadError` if module missing or invalid
- **Registration**: `{'IngestModule': 'stac_manager.modules.ingest', ...}`

### Architecture Components
- **Configuration**: `WorkflowDefinition` from Pydantic (validated YAML)
- **DAG Execution**: Topological sort via `build_execution_order()` ensures correct step sequence
- **Module Instantiation**: Factory pattern creates modules with merged configs (step.config + matrix_entry)
- **Context Management**: `WorkflowContext` with shared checkpoint manager, failure collector, logger

### Pipeline Execution Pattern
```python
# Sequential streaming within pipeline
async def _execute_pipeline(modules, context):
    fetcher = modules[0]  # First module must be Fetcher
    bundler = modules[-1]  # Last module must be Bundler
    modifiers = modules[1:-1]  # Middle modules are Modifiers
    
    async for item in fetcher.fetch():
        # Sequential processing through modifiers
        for modifier in modifiers:
            item = await _wrap_modifier(modifier, item)
            if item is None:
                break  # Filtered out
        
        # Drain to bundler
        if item:
            await bundler.add(item)
    
    await bundler.finalize()
```

### Matrix Strategy
- **Parallel Execution**: Uses `asyncio.gather()` to run multiple pipelines concurrently
- **Context Forking**: Each matrix entry gets isolated WorkflowContext (shallow copy with shared checkpoint)
- **Config Merging**: Matrix data merged into context.data, accessible via step configs
- **Result Aggregation**: Returns `list[WorkflowResult]` with per-entry failure tracking
- **No Variable Substitution**: v1.0 uses direct config merging (${var} syntax deferred to v1.1)

### WorkflowResult Structure
```python
@dataclass
class WorkflowResult:
    success: bool  # Overall success flag
    status: Literal['completed', 'completed_with_failures', 'failed']
    summary: str  # Human-readable summary
```

## CLI Interface (v1.0.0) - Command-Line Orchestration

### Core Commands
- **`stac-manager --version`**: Display package version from `stac_manager.__version__`
- **`stac-manager --help`**: Show all available commands with descriptions
- **`stac-manager validate-workflow <config>`**: Validate YAML config, check DAG cycles, report execution order
- **`stac-manager run-workflow <config>`**: Execute workflow with optional `--dry-run` and `--checkpoint-dir` flags

### Architecture
- **Click Group**: Main `cli()` function with `@click.group()` decorator
- **Logging Setup**: `setup_logging(level)` configures console handler with formatter
- **Config Loading**: Uses `load_workflow_from_yaml()` and `build_execution_order()` from orchestration layer
- **Async Execution**: Wraps `StacManager.execute()` with `asyncio.run()` for compatibility

### validate-workflow Command
- **Purpose**: Pre-flight config validation without execution
- **Checks**: YAML syntax, Pydantic validation, DAG cycle detection
- **Output**: Execution order display, module list per step
- **Exit Codes**: 0 if valid, 1 if invalid

### run-workflow Command
- **Parameters**:
  - `config_path`: Required positional argument (path to YAML config)
  - `--dry-run`: Optional flag (validates only, no execution)
  - `--checkpoint-dir`: Optional path override (default from config)
- **Execution**: Instantiates `StacManager`, calls `execute()`, reports results
- **Result Reporting**:
  - Single result: Shows status, summary, item counts
  - Matrix results: Iterates list, reports per-entry with index
  - Colored output: Green checkmarks for success, red X for failures
- **Error Handling**: Catches all exceptions, prints user-friendly message, exits with code 1

### Integration with Orchestration
- **WorkflowDefinition**: CLI loads config using `WorkflowDefinition.from_yaml()`
- **StacManager**: CLI creates manager instance, delegates all execution logic
- **WorkflowResult**: CLI interprets result structure for user-friendly display
- **CheckpointManager**: Respects `--checkpoint-dir` override or uses config default
    failure_count: int  # Number of item-level failures
    total_items_processed: int  # Total items through pipeline
    matrix_entry: dict[str, Any] | None  # Matrix config for this run
    failure_collector: FailureCollector | None  # Detailed failure records

### Error Handling Strategies
- **Critical Errors**: Try-catch around `_execute_pipeline()` catches module initialization failures, returns `status='failed'`
- **Item-Level Failures**: Collected via `FailureCollector` in context, continues processing, returns `status='completed_with_failures'`
- **Zero Items**: Special handling for pipelines with no items (returns `status='completed'` not `failed`)
- **Status Determination**: `completed` (all success), `completed_with_failures` (some failed), `failed` (critical error)

### Public API Usage
```python
# Programmatic usage
from stac_manager import StacManager

config = {
    "name": "my-workflow",
    "steps": [
        {"id": "seed", "module": "SeedModule", "config": {...}},
        {"id": "output", "module": "OutputModule", "config": {...}}
    ]
}

manager = StacManager(config=config)
result = await manager.execute()

# YAML usage
from stac_manager import load_workflow_from_yaml, StacManager
from pathlib import Path

workflow = load_workflow_from_yaml(Path("workflow.yaml"))
manager = StacManager(config=workflow)
result = await manager.execute()
```

### Integration with Checkpoints
- **Single Manager**: One `CheckpointManager` per workflow (passed via WorkflowContext)
- **Check Timing**: After fetcher yields item, before processing
- **Mark Timing**: After bundler finalizes successfully
- **Resume Capability**: Skips items where `checkpoint_manager.is_completed(item_id)` returns True

### StacManager Constructor
```python
StacManager(
    config: dict | WorkflowDefinition,  # Workflow configuration
    checkpoint_dir: Path = "./checkpoints",  # Checkpoint storage location
    log_level: str = "INFO"  # Logging verbosity
)
```

### Methods
- `execute() -> WorkflowResult | list[WorkflowResult]`: Entry point (handles single/matrix strategies)
- `_instantiate_modules(context) -> list`: Factory for creating module instances
- `_execute_single(matrix_entry) -> WorkflowResult`: Single workflow execution
- `_execute_matrix() -> list[WorkflowResult]`: Parallel matrix execution
- `_execute_pipeline(modules, context) -> int`: Sequential streaming pipeline
- `_wrap_modifier(modifier, item)`: Sync wrapper for modifier execution
- `_drain_to_bundler(bundler, item)`: Async drain to bundler

### Key Design Principles
- **Async-First**: All execution is async, modifiers wrapped in executor
- **Streaming**: Maintains async generator flow (no buffering)
- **Protocol Compliance**: Enforces Fetcher/Modifier/Bundler protocols at instantiation
- **Fail Fast**: Config/DAG errors raise before execution begins
- **Graceful Degradation**: Item-level failures don't stop pipeline

### Test Coverage
- 12 manager unit tests (100% pass rate)
- Module registry validation
- Dynamic loading (valid/invalid cases)
- Initialization (dict and WorkflowDefinition)
- DAG validation and cycle detection
- Module instantiation with config merging
- Pipeline execution (simple and matrix)
- Error handling and result aggregation

### Files
- **Implementation**: `src/stac_manager/core/manager.py` (420+ lines)
- **Tests**: `tests/unit/core/test_manager.py` (280+ lines)
- **Public API**: `src/stac_manager/__init__.py` (exports StacManager, WorkflowResult)

### Terminology Constraint (v1.0.0 Refactor)
- **Deprecated**: "Sidecar", "Sidecar File".
- **Standard**: "Input Data", "Input File".
- **Reasoning**: "Sidecar" implies a specific 1:1 relationship often used in k8s/metadata, whereas "Input Data" is more generic for enrichment sources (CSVs, external JSONs).

### Hybrid Field Mapping
- **Definition**: The ability to mix simple key lookups and JMESPath queries in the same `field_mapping`.
- **Mechanism**: 
    1. Try `input_data[source]` (Direct key lookup - handles spaces/special chars).
    2. If missing, try `jmespath.search(source, input_data)` (Complex extraction).
    3. If both fail, return `None`.
