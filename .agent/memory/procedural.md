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

