# Procedural Memory: STAC Manager Best Practices

## Development Workflow
- **Spec-First**: Always read `docs/spec/` before proposing designs.
- **TDD Pattern**: 
  1. Red (write failing test)
  2. Watch it fail (verify failure reason)
  3. Green (minimal implementation)
  4. Refactor (clean and optimize)
- **Granularity**: Keep tasks "bite-sized" (2-5 minutes) to ensure high-velocity, meaningful commits.
- **Large Plans**: For 50+ task plans, split into parts of 15-20 tasks each (~1500 lines) for manageability:
  - Group by natural dependency boundaries
  - Each part should be executable independently
  - Create skeleton outlines for unwritten parts

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

## IngestModule Implementation Patterns
- **File Mode**: Use synchronous file reads wrapped in `asyncio.to_thread()` for async interface compatibility.
  - JSON: Read entire file, parse as dict, extract `features` array from FeatureCollection.
  - Parquet: Use `pyarrow.parquet.read_table()` → `to_pylist()` for dict conversion.
- **API Mode**: Use `pystac_client.Client.open()` for STAC API connections.
  - Call `client.search()` with filter parameters (bbox, datetime, query, collections).
  - Use `search.items_as_dicts()` to iterate items in wire format (dict).
  - Implement `max_items` limit using `itertools.islice()`.
- **Context Override**: Check `context.data` for parameter overrides before using module config.
- **Error Handling**: 
  - Strict mode: Raise exceptions immediately on errors.
  - Permissive mode: Log to `failure_collector` with item ID, continue processing.
- **Testing**: Mock `pystac_client.Client.open` with `unittest.mock.patch`, return mock client with `search()` method.

## OutputModule Implementation Patterns
- **Atomic Writes**: ALWAYS use temp file pattern for crash safety:
  ```python
  temp_path = path.with_suffix(path.suffix + ".tmp")
  temp_path.write_text(content)
  os.replace(str(temp_path), str(path))  # Atomic on POSIX/Windows
  ```
- **Buffer Management**: Maintain single `self.buffer: List[dict]` for all items.
  - Check buffer size after each `bundle()` call.
  - Flush when `len(buffer) >= config.buffer_size`.
  - Clear buffer after successful flush.
- **Format-Specific Flush**:
  - JSON: Iterative flush (write each item individually).
  - Parquet: Bulk flush (convert all to Arrow Table, write once).
- **Link Updates**: If `base_url` configured, modify item `links` array before buffering:
  - Find `rel="self"` link.
  - Update `href` to match output location: `{base_url}/{item_id}.{format}`.
- **Collection Writing**: In `finalize()`, check for `config.include_collection` and `context.data["collection"]`:
  - Write to `collection.json` using atomic pattern.
  - Log warning if collection requested but not found in context.
- **Async I/O**: Wrap all file operations in `asyncio.to_thread()` to maintain async interface.
- **Testing**: Use `tmp_path` fixture, verify files exist with correct content, test atomic write cleanup on errors.

## Integration Testing Patterns
- **No Domain Mocks**: Use real module implementations; only mock external I/O (HTTP clients, file systems where necessary).
- **Context Sharing**: Create single `WorkflowContext.create()` instance, pass to all modules in pipeline.
- **Pipeline Structure**:
  1. Fetch phase: `async for item in fetcher.fetch(context)`
  2. Transform phase: `modified = await modifier.modify(item, context)`
  3. Bundle phase: `await bundler.bundle(item, context)`
  4. Finalize phase: `result = await bundler.finalize(context)`
- **Failure Verification**: After pipeline completion, call `context.get_failures()` to verify error collection.
- **File Verification**: For output modules, verify files exist in expected locations with correct content.
- **Mock External APIs**: Use `unittest.mock.patch()` for `pystac_client.Client.open` to avoid real API calls in tests.

## Documentation Standards
- **Module README Structure**:
  1. Overview of module types (Fetcher/Modifier/Bundler).
  2. Per-module sections with config schema dict examples.
  3. Python usage examples (initialization + basic operation).
  4. Error handling examples (strict vs permissive modes).
  5. Context integration examples (data override patterns).
  6. Testing patterns (fixtures, assertions).
  7. Protocol compliance verification.
- **Config Schema Format**: Show as Python dict literals with inline comments for each option.
- **Code Examples**: Must be runnable (imports, context creation, actual method calls).
- **Commit Message**: Use conventional commits format: `docs(modules): add comprehensive module documentation`.
