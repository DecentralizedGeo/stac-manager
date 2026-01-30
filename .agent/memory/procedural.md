# Procedural Memory: STAC Manager Best Practices

## Specification Writing Patterns (v1.1.0)

### Comprehensive Specification Structure
**When Documenting Feature Enhancements**:
- Include BOTH completed work AND remaining work in single document
- Completed sections provide context and establish patterns
- Remaining sections reference completed patterns ("follow UpdateModule approach")
- Use clear phase markers: "✅ Completed" vs "📋 Pending"

### Terminology Clarification
**Roadmap Phases vs Feature Enhancements**:
- **Roadmap Phases**: Major architectural components (Utilities, Modules, Orchestration)
- **Feature Enhancements**: Cross-cutting improvements to existing functionality (logging, caching, metrics)
- **ALWAYS clarify with user** if work is a new phase or enhancement to existing phase
- Document placement: Phases in roadmap.md, Enhancements in dated specification docs

### Pattern Validation Approach
**Before Rolling Out Changes Across Modules**:
1. **Prototype**: Implement fully on ONE representative module (e.g., UpdateModule)
2. **Validate**: Manual testing + unit tests + integration tests
3. **Document Pattern**: Capture exact code structure, message format, test approach
4. **Roll Out**: Apply validated pattern to remaining modules
5. **Benefit**: Reduces rework, ensures consistency, validates assumptions early

### TDD Specification Format (writing-plans skill)
**For Each Task**:
- Step 1: Write failing test (EXACT code, not "add test for X")
- Step 2: Run test command (EXACT pytest command)
- Step 3: Minimal implementation (EXACT code)
- Step 4: Verify test passes (EXACT command)
- Step 5: Commit (EXACT git commands)

**Task Granularity**:
- 2-5 minutes per task
- One logical unit of work (e.g., "Logger Injection" not "All Logging")
- 4 tasks per module typical: Injection, INFO logging, DEBUG logging, Integration test

### Sprint Retrospective Pattern
**At End of Planning Session**:
- Invoke agent-memory skill explicitly for retrospective
- Update episodic.md with milestone, context, decisions, outcomes
- Update procedural.md with new patterns discovered
- Update semantic.md with new architectural concepts
- Focus on 1-3 critical insights (not comprehensive log)

## Development Workflow
- **Spec-First**: Always read `docs/spec/` before proposing designs.
- **TDD Pattern**: 
  1. Red (write failing test)
  2. Watch it fail (verify failure reason)
  3. Green (minimal implementation)
  4. Refactor (clean and optimize)
- **Granularity**: Keep tasks "bite-sized" (2-5 minutes) to ensure high-velocity, meaningful commits.
- **Large Plans**: For 30+ task plans, split into parts of 10-20 tasks each (~1000-1500 lines) for manageability:
  - Group by natural dependency boundaries (phases/components)
  - Each part should be logically cohesive and executable
  - Create skeleton outlines for unwritten parts
  - Example: Phase 3 split into 3 parts (Part 1: Config+Checkpoints, Part 2: Orchestration, Part 3: CLI+Testing)

## Python Standards
- Use Python 3.12+ features (Generics, TypeVar, Structural Pattern Matching).
- Prefer readability and maintainability over complex "clever" one-liners.
- No mocks in end-to-end tests; use real or synthetic STAC data.

## Error Handling
- **Three-Tier Model**:
  1. **Tier 1: Fail Fast**: Configuration/startup errors (Abort workflow).
  2. **Tier 2: Step Out**: Item-level non-critical errors (Log to FailureCollector, continue pipeline).
  3. **Tier 3: Graceful Degradation**: Optional feature failures (Fallback safely with warning).
## Component Implementation Patterns
- **Geometry Normalization**: Always use the `_to_list` recursive pattern when converting Shapely shapes to GeoJSON dicts to ensure type consistency (Floats and Lists, not Tuples).
- **Dot-Notation Paths**: Strictly follow the `a.b.c` dot-notation for nested fields to maintain compatibility with `get_nested_field` and `set_nested_field`.
- **JMESPath Errors**: Wrap JMESPath searches in `DataProcessingError` to distinguish extraction failures from system/core logic failures.
- **Non-Critical Failures**: For data mismatches (e.g., missing sidecar item) or optional data failures, use `context.failure_collector.add(item_id, message, step_id)` instead of raising exceptions to keep the pipeline flowing.
- **Deep Copy for Dict Values**: ALWAYS use `copy.deepcopy()` when assigning dict values in merge operations to prevent object reference sharing. This is critical in wildcard expansion where multiple assets could share the same dict object, causing mutations to affect all assets.
- **Wildcard Expansion Timing**: Expand wildcards per-item during `modify()`, not during `__init__`, to support dynamic template variables that depend on item context (`{item_id}`, `{collection_id}`, `{asset_key}`).
- **Template Variable Substitution**: Use recursive string replacement in `_apply_template_variables()` to handle nested values. Process entire value tree, not just top-level strings.

## Wildcard Pattern Best Practices (v1.1.0)

### Design Principles
- **Separation of Concerns**: Keep wildcard logic in shared utilities for consistency across modules
  - `expand_wildcard_paths`: For updates/additions (returns dict of path→value)
  - `expand_wildcard_removal_paths`: For removals (returns list of path tuples)
- **Backward Compatibility**: Preserve support for nested dict defaults (non-wildcard) for ExtensionModule template building
- **Filter Expandable Defaults**: Only process defaults with `*` or `.` in keys as wildcards to avoid over-expansion
- **Object Independence**: Each expanded path must get a deep copy of dict values to prevent reference sharing

### Implementation Pattern

**For Updates/Additions:**
```python
# In modify() method (per-item processing)
if has_wildcards(config.defaults):
    expanded = expand_wildcard_paths(
        config.defaults, 
        item, 
        {"item_id": item["id"], "collection_id": ctx.collection_id}
    )
    # Apply each expanded path individually
    for path, value in expanded.items():
        set_nested_field(item, path, value)
```

**For Removals:**
```python
# In modify() method (for field removal)
if config.removes:
    # Expand wildcards to get all matching paths
    expanded_paths = expand_wildcard_removal_paths(
        config.removes,
        item
    )
    
    # Remove each expanded path
    for path_tuple in expanded_paths:
        target = item
        for key in path_tuple[:-1]:
            if key in target and isinstance(target[key], dict):
                target = target[key]
            else:
                break
        else:
            if path_tuple[-1] in target:
                del target[path_tuple[-1]]
```

### Testing Requirements
- **Unique Values**: Verify each asset receives asset-specific expanded values
- **Object Isolation**: Modify one asset, verify others unchanged (test deep copy)
- **Template Variables**: Test all variables (`{item_id}`, `{collection_id}`, `{asset_key}`) expand correctly
- **Backward Compatibility**: Test that old nested dict defaults still work (non-wildcard paths)

## TransformModule Field Mapping Rules

### Direction Clarity
- **Key = Target**: Dot-notation path where data will be stored in item (e.g., `properties.cloud_cover`, `assets.blue.dgeo:cid`)
- **Value = Source**: JMESPath query or direct key applied to input entry to extract data
- **Example**: `"properties.cloud_cover": "cloud_cover"` means "Put input's cloud_cover into item's properties.cloud_cover"
- **Wildcards (v1.1.0)**: `"assets.*.dgeo:cid": "assets.{asset_key}.cid"` expands to all assets

### Wildcard Pattern Selection
- **When to Use**: 10+ repetitive asset mappings (e.g., Landsat with 24 assets)
- **When NOT to Use**: Single asset or unique field mappings (overhead not worth it)
- **Template Variables**: Always use `{asset_key}` for per-asset substitution in values
- **Impact**: Can reduce config from 75+ lines to 3 lines (96% reduction)

### Strategy Selection (Default: update_existing)
- **`update_existing`** (DEFAULT - safer):
  - Only updates paths that already exist in item
  - Won't create unexpected assets or fields
  - **Use When**: Enriching existing structures, safety critical
  - **Example**: Adding CIDs to existing assets without creating new ones
- **`merge`**:
  - Creates new paths from input data as needed
  - **Use When**: Integrating external metadata with additional assets
  - **Example**: Adding thumbnail asset from metadata not in original item
- **Composability**: For "overwrite" behavior, use UpdateModule to remove fields/assets first, then TransformModule with `merge`

### Format-Specific Behavior
- **Dict Format** (keys are item IDs):
  - No `input_join_key` needed (uses "id" by default)
  - Automatic lookup: `input_data[item_id]`
  - Recommended for simple key-value input files
- **List Format** (array of objects):
  - Requires `input_join_key` parameter
  - Uses direct key or JMESPath to extract ID from each entry
  - Use when input has nested structure or different ID field name
- **CSV Format**: 
  - Supported via `pyarrow.csv` with type inference
  - **Critical**: `input_join_key` column forced to string (prevents "007" → 7 conversion)

### Common Pitfalls
- **Backward Mapping**: Don't put target paths in JMESPath queries (value side)
- **Missing input_join_key**: List format will fail without this parameter
- **Over-Nesting**: Don't use nested JMESPath like `properties.field` when input is flat dict
- **Wrong Default Strategy**: Old default was `merge`, now `update_existing` (safer)

## Sentinel Value Pattern for Field Existence

### Problem
Need to distinguish between:
1. Field doesn't exist → should return "not found"
2. Field exists with `None` value → should return `None`

Using `None` as default in `get_nested_field(item, path, default=None)` creates ambiguity.

### Solution
Use `object()` as sentinel value with identity check:

```python
_MISSING = object()  # Unique sentinel instance
result = get_nested_field(item, path, default=_MISSING)
if result is not _MISSING:
    # Field exists (even if value is None)
    process(result)
else:
    # Field truly doesn't exist
    skip()
```

### Why This Works
- `object()` creates guaranteed-unique instance
- Identity check (`is`) won't match any real data
- Equality check (`==`) could match user data

### When to Use
- `update_existing` strategy filtering (only update existing paths)
- Conditional logic based on field presence vs value
- Any case where `None` is a valid field value

## Sprint Workflow Best Practices

### Pre-Sprint Baseline Checklist
**Action**: Run full test suite before starting implementation  
**Why**: Distinguish new failures from pre-existing issues  
**When**: First step after task acceptance  
**Command**: `pytest tests/ -v --tb=short`

**Baseline Recording**:
1. Record total pass/fail count
2. List failing test names
3. Verify module-specific tests all pass
4. Document known failures in task.md

### Config Field Implementation Verification
**Problem**: Pydantic validates field exists, but doesn't ensure it's used in code  
**Example**: `strategy` field was validated in config but never checked in `modify()`

**Verification Steps**:
1. After defining config field: `grep -r "self.config.field_name" src/`
2. Expect at least one usage in implementation
3. If zero results: Field is defined but unused (bug!)

**When to Check**: During implementation, before writing tests

### Global Terminology Change Checklist
When renaming core concepts (e.g., "sidecar" → "input"):

**Systematic Order**:
1. Spec files: `docs/spec/*.md`
2. Config models: `src/*/config.py`
3. Implementation: `src/*/*.py`
4. Tests: `tests/**/*.py`
5. Examples: `examples/*.yaml`, `samples/**/*`
6. Scripts: `scripts/*.py`
7. Documentation: `docs/**/*.md`, `README.md`

**Tools**: Use `grep -r "old_term" .` then IDE find/replace with preview


## Documentation Accuracy Patterns

### Module Name Verification
- **Before Documenting**: Verify module exists in `src/stac_manager/modules/`
- **Check Imports**: Use `list_dir()` to confirm module files before referencing in docs
- **Find/Replace Carefully**: Use grep to find all occurrences before global replace
- **Cross-Reference**: Check workflow YAML files match documentation examples

### Configuration Schema Accuracy
- **Source of Truth**: Always check Pydantic models in `modules/config.py` for correct field names
- **Field Name Validation**: Never assume field names, always verify against `Config` class
- **Type Checking**: Verify field types (Optional, Literal, dict, list) match documentation
- **Default Values**: Document default values from Pydantic `Field()` definitions

### Documentation Update Workflow
1. **Identify Changes**: List all affected files (tutorials, concepts, README)
2. **Update Systematically**: Work file-by-file, section-by-section
3. **Cross-Reference**: Ensure examples in tutorials match workflow YAML files
4. **Verify Execution**: Run actual workflows after doc updates to confirm accuracy
5. **Check Consistency**: Ensure terminology consistent across all docs (e.g., "sidecar data" not "external data")


## Module Implementation Rules
- **Protocol Verification**: Always include a test case `assert isinstance(module, Protocol)` to strictly enforce architectural contracts.
- **Config Validation**: Use Pydantic models in `config.py` for all module initialization. Fail fast (Tier 1) on invalid config.
- **Modifier Error Handling**: Catch native Python errors (TypeError, AttributeError) during deep traversal and re-raise as `DataProcessingError` (Tier 2) to identify data issues without crashing the pipeline.
- **Validation Module Testing**: When testing ValidateModule, use `stac-validator`'s `StacValidate` class (not `StacValidator`). Access validation messages via `.message` attribute for error details.
- **Schema Fetching**: For modules that fetch external schemas (e.g., ExtensionModule), perform fetching during `__init__` to fail fast (Tier 1) if schemas are unreachable or invalid.
- **Iterator Testing Pattern**: When testing modifiers that process items, convert the iterator result to a list (`list(module.process(...))`) to verify output items in assertions.
- **HTTP Mocking in Tests**: Use `requests-mock` library with context manager pattern: `with requests_mock.Mocker() as m:` to mock HTTP requests. Register endpoints before module initialization to test schema fetching and error handling.
- **Validator Error String Conversion**: When handling `stac-validator` messages, always convert dict messages to strings explicitly: `errors = [str(msg) for msg in validator.message]` before joining or displaying.
- **Extension Scaffolding Heuristics**: When building templates from schemas for STAC items and assets:
    - Prefer `oneOf` variants where `type.const == "Feature"`.
    - Handle `assets` by merging all discovered asset-level properties into a `*` (catch-all) template to ensure maximum compatibility.
- **Local Schema Caching**: For modules fetching remote schemas (e.g., ExtensionModule), implement a local caching downloader in tests. Use URLs in code but verify against local files in `tests/fixtures/data/` to ensure test stability and performance.
- **Recursive Scaffolding (`_parse_field`)**: Use recursive functions that handle `$ref` and `allOf` at every level to build accurate scaffolding templates. Distinguish between object nodes (returns dict) and leaf nodes (returns default/None).
- **Required Fields Filtering**: Implement a configuration-driven flag (`required_fields_only`) that uses the schema's `required` arrays to filter out optional scaffolded fields during template generation.

## TransformModule Sidecar Loading
- Perform sidecar file loading and primary indexing in `__init__`.
- Raise `ConfigurationError` (Tier 1) if the input file is missing.
- Modularize indexing logic to handle different formats (dict, list).

## Pydantic Model Best Practices

- **Avoid Field Name Collisions**: Never use field names that shadow Pydantic BaseModel methods (e.g., `validate`, `dict`, `json`, `copy`).
- **Descriptive Field Names**: Prefer `validate_extension`, `serialize_format` over generic names that could collide.
- **Collision Detection**: Pylance will warn when field type is incompatible with shadowed method signature.

## Test Fixture Design

- **Use Real Implementations When Lightweight**: Prefer real classes over mocks when the implementation is simple, stable, and has no external dependencies.
- **Avoid Mock Drift**: Mocks require maintenance to stay synchronized with actual APIs. Use real implementations (e.g., `FailureCollector`) to ensure test fidelity.
- **Mock Only Complex Dependencies**: Only mock components with heavy I/O, external services, or complex state (e.g., `CheckpointManager` with file operations).

## Integration Testing Patterns

- **End-to-End Pipelines**: Test realistic flows combining multiple modules (Ingest→Transform→Output).
- **Failure Propagation**: Verify that errors are properly collected via `failure_collector` and don't crash the pipeline.
- **Data Validation**: Assert on output file structure, relative links, and collection metadata.
- **Real Fixtures**: Use actual STAC items in test data rather than minimal stubs to catch real-world issues.

## Phase 3: Orchestration Layer Patterns

### Configuration System
- **Pydantic v2**: Use for all config models (`WorkflowDefinition`, `StepConfig`, `StrategyConfig`)
- **YAML Loading**: Use `yaml.safe_load()` for security, validate immediately with Pydantic
- **DAG Validation**: Implement Kahn's algorithm for topological sort, detect cycles with path tracking
- **Fail Fast**: All config errors raise `ConfigurationError` before execution begins

### CheckpointManager
- **Storage Format**: Use Parquet via `pyarrow` for performance and size
- **Partitioning**: Partition by workflow name and matrix entry for isolation
- **Atomic Operations**: Write to temp file, then rename for atomicity
- **Resume Logic**: Check if `(item_id, step_id)` exists before processing
- **Single Manager**: One CheckpointManager per workflow (tracks all steps via `step_id` field)

### StacManager Orchestration
- **Module Registry**: Hardcoded `MODULE_REGISTRY` dict mapping names to classes (v1.0)
- **Sequential Execution**: Within a pipeline, execute steps in topological order sequentially
- **Matrix Parallelism**: Use `asyncio.gather()` to run matrix entries in parallel
- **Context Forking**: Create separate `WorkflowContext` per matrix entry with merged config
- **Streaming**: Maintain async generator flow through entire pipeline (no buffering)

### CLI Design
- **Click Framework**: Use for all CLI commands (industry standard)
- **Command Structure**: Group-based with `@cli.command()` decorators
- **Progress Reporting**: Use `click.echo()` for structured output (avoid raw print)
- **Exit Codes**: 0 for success, 1 for failure (follow POSIX conventions)
- **Dry Run**: Always provide `--dry-run` flag for validation-only mode

### CLI Implementation Patterns (v1.0.0)
- **Entry Point Setup**: Register CLI in `pyproject.toml` under `[tool.poetry.scripts]`
- **Logging Configuration**: Create `setup_logging(level)` function with console handler and formatter
- **Command Parameters**: Use `@click.argument()` for required positional args, `@click.option()` for flags
- **File Operations**: Use `Path` objects for cross-platform compatibility
- **Async Integration**: Wrap async manager calls with `asyncio.run()` for Click compatibility
- **Error Handling**: Catch exceptions at command level, print user-friendly messages, exit with code 1
- **Result Reporting**: 
  - Use colored output: `click.secho("✓ Success", fg="green")` / `click.secho("✗ Failed", fg="red")`
  - Report counts: "Processed 10 items", "3 failures occurred"
  - Distinguish single vs. matrix results (check if result is list)
- **Test Isolation**: Use `CliRunner.isolated_filesystem()` for CLI tests to avoid test pollution

## Checkpoint System Patterns (v1.0.0)

### Architecture
- **Single Manager Per Workflow**: One `CheckpointManager` instance tracks all steps via `step_id` field in records
- **Completion-Based Tracking**: Track "Did item finish ENTIRE pipeline?" not "Did item pass step X?"
- **Check After Ingest**: Place `is_completed()` check after IngestModule fetch, before processing begins
- **Mark After Output**: Call `mark_completed()` after OutputModule succeeds, `mark_failed()` on errors

### Schema Design
- **Required Fields**: `(item_id, collection_id, output_path, completed, timestamp, error)`
- **completed Boolean**: Only items with `completed=True` are loaded into completion set
- **output_path Verification**: Record actual output location to verify item reached disk
- **error Field**: Optional string for failure details (enables debugging failed items)

### Path Structure
- **Pattern**: `./checkpoints/{workflow_id}/{collection_id}.parquet`
- **Rationale**: Single file per collection (not per step) simplifies management and resume logic
- **Avoid**: Nested per-step structures like `checkpoints/{workflow}/{step}/checkpoint.parquet`

### API Usage
```python
# Initialize (once per workflow)
checkpoint = CheckpointManager(workflow_id, collection_id, "./checkpoints")

# Check before processing (after ingest)
if checkpoint.is_completed(item_id):
    continue  # Skip already-completed items

# Mark success (after output)
checkpoint.mark_completed(item_id, output_path)

# Mark failure (on exception)
checkpoint.mark_failed(item_id, str(error))

# Flush buffer
checkpoint.flush()
```

### Resume Behavior
- **Failed Items Retry**: Items with errors are NOT in completion set → automatic retry
- **Completed Items Skip**: Items with `completed=True` are skipped at check point
- **Idempotent**: Multiple runs with same workflow/collection are safe (deduplicates by item_id)

## Cache Strategy Patterns (v1.1.0 - Design Phase)

### Separation of Concerns
- **Never Confuse with Checkpoints**: Checkpoints = pipeline completion, Cache = HTTP optimization
- **Different Scopes**: Checkpoints track end-to-end, Cache tracks IngestModule only
- **Different Timing**: Checkpoints checked after ingest, Cache checked before HTTP
- **Different Data**: Checkpoints store status, Cache stores full STAC Items

### Storage Design (Future Implementation)
- **Format**: Use Parquet with JSON-serialized STAC Items (not individual JSON files)
- **Benefits**: 10-100x compression, predicate pushdown, single file per collection
- **Schema**: `(item_id, collection_id, cached_at, expires_at, item_data)` where `item_data` is JSON string
- **In-Memory Index**: Maintain `Dict[str, datetime]` for O(1) existence checks

### Integration Pattern (Future)
- **Check Before HTTP**: `if cache.exists(item_id): item = cache.load(item_id)`
- **Save After HTTP**: `else: item = fetch(); cache.save(item_id, item)`
- **Opt-In**: Cache disabled by default, enabled via `enable_cache: true` config
- **TTL Support**: Automatic expiration via `cache_ttl_hours` parameter

### CLI Pattern (Future)
- **Clear Command**: `stac-manager cache clear [--collection X] [--older-than-days N]`
- **Stats Command**: `stac-manager cache stats [--collection X]` (show size, counts, expiration)
- **Age-Based Cleanup**: Support clearing items older than N days for cache hygiene



### Error Handling in Orchestration
- **WorkflowResult**: Aggregate all failures from pipeline execution
- **Matrix Failures**: Isolate failures per matrix entry (one failure doesn't stop others)
- **Failure Summary**: Provide structured summary at end (counts, status, per-step details)
- **Graceful Degradation**: Continue execution even with item-level failures (collect via FailureCollector)

## StacManager Implementation Patterns (v1.0.0)

### Module Registry
- **Hardcoded in v1.0**: Use `MODULE_REGISTRY` dict mapping names to import paths
- **No Dynamic Discovery**: Defer plugin system to v1.1 (YAGNI principle)
- **Registration Pattern**: `'ModuleName': 'stac_manager.modules.module_name'`
- **Loading**: Use `importlib.import_module()` then `getattr()` for class extraction

### DAG Validation
- **Before Execution**: Always call `build_execution_order()` in `__init__`
- **Fail Fast**: Raise `ConfigurationError` for cycles or missing dependencies
- **Path Reporting**: Include cycle path in error message for debugging
- **Kahn's Algorithm**: Use for topological sort (handles complex dependencies)

### Module Instantiation
- **Factory Pattern**: Create modules dynamically in `_instantiate_modules()`
- **Config Merging**: Merge step.config + matrix_entry before passing to module constructor
- **Context Injection**: Pass same `WorkflowContext` to all modules (shared checkpoint/failure collector)
- **Protocol Verification**: Verify module implements correct protocol (Fetcher/Modifier/Bundler) at instantiation

### Pipeline Execution
- **Sequential Streaming**: Process items one-at-a-time through pipeline (no buffering)
- **Async Flow**: Maintain async generators throughout (modifiers wrapped in sync executor)
- **None Handling**: Check for `None` returns from modifiers (filtered items)
- **Item Counting**: Track `total_items_processed` for result reporting

### Matrix Strategy
- **Parallel Execution**: Use `asyncio.gather(*tasks)` for concurrent pipeline runs
- **Context Forking**: Create shallow copy of WorkflowContext per matrix entry
- **Config Merging**: Inject matrix data into context.data (accessible by modules)
- **Isolated Failures**: Each matrix entry has own FailureCollector
- **Result Aggregation**: Return `list[WorkflowResult]` with per-entry status

### Error Handling
- **Try-Catch Pattern**: Wrap `_execute_pipeline()` in try-catch within `_execute_single()`
- **Critical vs Item-Level**: Critical errors return `status='failed'`, item failures return `status='completed_with_failures'`
- **Zero Items**: Handle zero items as success (not failure) - return `status='completed'`
- **Failure Collector Access**: Include `failure_collector` in `WorkflowResult` for post-execution inspection

### Result Reporting
- **WorkflowResult Dataclass**: Use for all execution results (single or matrix)
- **Status Values**: `completed`, `completed_with_failures`, `failed`
- **Summary Generation**: Create human-readable summary based on items processed and failures
- **Matrix Entry Tracking**: Include matrix config in result for traceability

### Testing Patterns
- **Mock Modules**: Create minimal mock Fetcher/Modifier/Bundler classes in tests
- **Config Validation**: Test both dict and WorkflowDefinition input formats
- **DAG Edge Cases**: Test cycles, missing dependencies, parallel branches
- **Pipeline Flow**: Verify items flow through all steps correctly
- **Matrix Isolation**: Verify failures in one matrix entry don't affect others

### Public API Design
- **Top-Level Exports**: Export key classes in `stac_manager/__init__.py`
- **Clean Imports**: Enable `from stac_manager import StacManager` pattern
- **Documentation**: Include usage examples in module docstring
- **Version Declaration**: Set `__version__` for version tracking



## CSV Handling Patterns
- **Library Choice**: Use `pyarrow.csv` for read performance and type inference.
- **ID Column Safety**: ALWAYS strictly define the ID column type as `string` (`pa.string()`) in `ConvertOptions` to avoid auto-conversion of leading-zero identifiers (e.g., "007" -> 7).

## Breaking Change Refactoring Workflow
- **Order of Operations**:
    1. **Spec**: Update the blueprint first (`docs/spec/`).
    2. **Config**: Update Pydantic models to fail fast (`config.py`).
    3. **Implementation**: refactor the logic (`module.py`).
    4. **Tests**: Update unit tests to match new config/terminology.
    5. **Documentation/Scripts**: Update usage examples and auxiliary scripts (often forgotten).
- **Terminology Consistency**: When renaming a core concept (e.g., Sidecar -> Input), grep the ENTIRE repository, including comments and docstrings.
## YAML/JSON Key Quoting Rules
- **Dot-Separated Keys**: When a key in a dot-separated path contains dots itself (e.g., filenames like `ANG.txt`), it MUST be double-quoted within the path string.
- **YAML Syntax**: In YAML, you must wrap the entire key in single quotes to preserve the internal double quotes.
  - **Correct**: `'assets."ANG.txt".alternate': "source"`
  - **Incorrect**: `assets.ANG.txt.alternate: "source"` (Parses as `assets` -> `ANG` -> `txt` -> `alternate`)

## Nested Field Operations (Refactored)
- **Centralized Logic**: Do not implement ad-hoc dictionary traversal or path creation. Always use `stac_manager.utils.field_ops`.
  - `set_nested_field(item, path, value, create_missing=True)`: Safely sets values, creating intermediate dicts if needed.
  - `get_nested_field(item, path, default=obj)`: Safely retrieves values.
  - `dot_notation_to_nested(dict)`: Converts flat dot-notation dicts to nested structures.
- **Path Parsing**: Never use `path.split('.')`. Always use `parse_field_path(path)` to respect quoted keys (e.g., `assets."ANG.txt"`).

## Asset Handling
- **Dot-in-Keys**: Asset keys often contain filenames with dots (e.g., `ANG.txt`).
- **Quoting**: When referencing these in configuration (YAML), always quote the segment: `'assets."ANG.txt".href'`.
- **Wildcard Expansion**: Use `expand_wildcard_paths` which uses `parse_field_path` internally to safely handle these keys.
