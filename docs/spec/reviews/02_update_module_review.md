# Update Module Spec Review

**Document**: `docs/spec/stac-manager-v1.0.0/modules/update.md`
**Reviewer**: Senior Engineer Persona
**Date**: 2026-01-21

## Executive Summary
The `update.md` specification outlines a clear role for the `UpdateModule` but lacks handling for edge cases in path navigation and list modifications.

## Critical Gaps

### 1. Ambiguous List Modification
- **Issue**: The spec mentions `removes` and `updates` using "Simple Dot Notation" but does not define how to address items within a list.
- **Example**: How does one update the role of the *first* provider? `properties.providers[0].roles`?
- **Ambiguity**: Does "Simple Dot Notation" support array indexing (e.g., `[0]`)? If not, how are lists modified? (A) Good question, I assume simple dot notation does support array indexing.
- **Recommendation**: Explicitly define if array indexing `properties.providers[0]` is supported. If not, clarify that lists can only be replaced entirely. (A) Alternatively, we can use JMSEPath to address items within a list and dictionaries.

### 2. Path Collision & Type Safety
- **Issue**: `create_missing_paths=True` creates dictionaries if missing. It does not specify behavior if a path segment exists but is *not* a dictionary (e.g., a string or list). (A) I think what I mean here is create missing properties if they do not exist. Since we are using simple dot notation, it should be able to create missing nested properties if they do not exist e.g. `properties.first_provider.roles` and `properties.first_provider` does not exist.
- **Example**: `properties.eo:cloud_cover = 10`. If `properties` is unexpectedly `null`, it works. But if `properties` is a string `"invalid"`, does it raise an error or overwrite?
- **Recommendation**: Clarify behavior: "If a path segment exists and is not a container (dict), raise `DataProcessingError`."

### 3. Dot Notation Escaping
- **Issue**: STAC Extensions often use colons (e.g., `eo:cloud_cover`). While the example shows this working, what if a key *contains* a dot? Good question, I don't think we support this.
- **Recommendation**: Clarify escaping rules (e.g., `properties."my.field"`) or state that keys with dots are not supported.

### 4. Patch File Performance
- **Observation**: The spec warns about loading `patch_file` entirely into memory.
- **Recommendation**: For V1, this is acceptable, but consider adding a `patch_strategy` config to allow for future optimize (e.g., `memory` vs `stream` or `db_lookup`). (A) disregard this recommendation.

## Recommendations
1.  **Define List Indexing**: Explicitly support or ban `[N]` syntax.
2.  **Clarify Collision Logic**: Define behavior when overwriting scalars with dicts.
3.  **Specify Escaping**: Define how to handle keys with special characters.
