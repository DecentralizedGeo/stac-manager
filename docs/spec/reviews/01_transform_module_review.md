# Transform Module Spec Review

**Document**: `docs/spec/stac-manager-v1.0.0/modules/transform.md`
**Reviewer**: Senior Engineer Persona
**Date**: 2026-01-21

## Executive Summary
The `transform.md` specification provides a high-level overview of the module's components (SchemaLoader, Sidecar Indexing, FieldMapper) but lacks critical implementation details required for a "blueprint". The most significant gap is the undefined mechanics of joining the Input Stream with the Sidecar Data. Without this, the module cannot be implemented deterministically.

## Critical Gaps

### 1. Undefined Join Logic (Stream vs. Sidecar)
- **Issue**: The specification assumes the Input Stream (`Iterator[dict]`) can be joined with the Sidecar File (`input_file`), but fails to define the join key on the *stream* side.
- **Missing Config**: `sidecar_id_path` exists (for the sidecar side), but there is no corresponding `item_id_path` or `stream_id_path` to extract the join key from the pipeline items.
- **Ambiguity**: It is unclear if the module supports:
    - **Enrichment Mode**: Stream contains full items, Sidecar adds metadata (Merge).
    - **Lookup Mode**: Stream contains just IDs, Sidecar provides all data (Hydrate).
    - **Stream-Only Mode**: No sidecar, just transforming the stream items directly.
- **Recommendation**: Explicitly define the `JoinStrategy` in the config, including:
    - `join_key_stream`: JMESPath to key in Item.
    - `join_key_sidecar`: JMESPath to key in Sidecar (currently `sidecar_id_path`).
    - `strategy`: `merge` | `replace` | `none`.

#### Answer to 1: Here's my response to the review:

Undefined Join Logic (Stream vs. Sidecar): (A) By default, content from the input_file is joined to the `id` field from an item. See spec details on what that field represents for items and collections: https://github.com/radiantearth/stac-spec/blob/master/item-spec/item-spec.md#id

For what this module was designed for, we join the input data to items.

We'll need to add some logic into TransformConfig or somewhere in the module build the source key join field. if the user passes in a value for `data_path` and ``sidecar_id_path`. we'll need to concatenate both values.

On second thought, do we really need a `data_path` value? Doesn't JMESPath support complex querying for nested content or is it because of how the query needs to be constructed with the JMESPath python library? 

The `id` field for STAC Items (from the stream side) will always serve as the destination field for the join key.

Resolving your comment about **Ambiguity**, the module is purely for enrichement mode.

As for the strategy:
1. **merge**: should mean adding 1. overwriting existing field values. 2. Add new fields to the item that may not exist in the item. 
2. **update**: Update existing fields with the new values. Fields that don't exist in the item are not added. 

### 2. FieldMapper "Setter" Logic
- **Issue**: The pseudocode for `FieldMapper` only shows extraction (`map_field` returns `Any`). It does not show how this value is applied to the nested structure of the `TransformedItem`.
- **Gap**: There is no logic handling the *construction* of the target dictionary, specifically creating intermediate nested dictionaries (e.g., `properties.datetime` requires creating the `properties` dict if it doesn't exist).
- **Recommendation**: Add pseudocode for `apply_mapping(target: dict, path: str, value: Any)` that handles nested dict creation.

#### Answer to 2: Here's my response to the review:

I beleive we would use **Simple Dot Notation** (e.g., `properties.eo:cloud_cover`, `assets.thumbnail.href`) for simple path setters for *modification*.

### 3. Missing/Ambiguous Pseudocode
- **Sidecar Indexing**: Section 2.2 describes logic ("Last Record Wins") but provides no pseudocode for the indexing process or memory management.
- **TypeConverter**: Section 2.3 (second occurrence) lists operations but shows no pseudocode for the interface or behavior.
- **Execution Flow**: The `modify` method pseudocode is empty. It needs to show the orchestration:
    ```python
    id = get_id(item)
    sidecar_data = index.get(id)
    # Merge or Select?
    source_data = merge(item, sidecar_data)
    target = {}
    for rule in schema:
        val = field_mapper.map(source_data, rule)
        set_value(target, rule.target, val)
    return target
    ```

#### Answer to 3: Here's my response to the review:

This is more of an implementation detail. We can make note of this in the spec letting users know about some additional process that would take place e.g. the indexing process, type conversion process, etc.

### 4. Spec Structure & Errors
- **Numbering**: duplicate **2.3** (FieldMapper and TypeConverter).
- **Input Contract**: Section 4 states `input_file` is in `config`, but Section 2.2 says it's loaded "once at startup". `modify` happens per item. This implies the `TransformModule` has a `setup()` phase that is not clearly defined in the architecture section (though implied by "Sidecar Indexing").

#### Answer to 4: Here's my response to the review:

That is correct, it's expected that a setup() phase would take place before the modify() method is called. Mainly so we can index the sidecar file once modify item data as it's recieved.

## Recommendations
1.  **Add `JoinConfig`**: Formalize how the stream and sidecar interact.
2.  **Detail `FieldMapper`**: Show the `set_path` logic.
3.  **Fix Numbering**: Correct Section 2.x sequence.
4.  **Expand Pseudocode**: Add the `modify` orchestration logic to bind the components together.
