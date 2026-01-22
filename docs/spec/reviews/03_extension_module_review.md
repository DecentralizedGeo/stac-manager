# Extension Module Spec Review

**Document**: `docs/spec/stac-manager-v1.0.0/modules/extension.md`
**Reviewer**: Senior Engineer Persona
**Date**: 2026-01-21

## Executive Summary
The `extension.md` specification has been completely overhauled from a "Registry/Plugin" architecture to a **"Configuration-Driven Auto-Scaffolding"** architecture. This shift reduces user complexity, eliminates boilerplate Python code for extensions, and leverages JSON Schema for automated structural updates.

## Critical Decisions & Resolutions

### 1. Architecture Shift: Plugins vs. Scaffolding
- **Initial State**: The spec proposed a heavy "Extension Protocol" requiring custom Python classes to modify items.
- **Decision**: Simpler is better. Most users just want to "stamp" an item with a schema and some default fields.
- **Resolution**: The module now:
    1.  **Fetches** the JSON Schema at startup.
    2.  **Parses** the schema (resolving `$ref` and `oneOf` to find Item properties) to build a "Template Cache".
    3.  **Scaffolds** incoming items by merging this template.
    4.  **Defaults** are overlaid from configuration.

### 2. Schema Parsing Logic
- **Challenge**: JSON Schemas can be complex (`oneOf`, `$ref`).
- **Resolution**: The parser will implement a deterministic heuristic:
    1.  Inspect `oneOf` for the `Feature` type (STAC Item).
    2.  Resolve `$ref` pointers to definitions.
    3.  Construct the template dictionary from those resolved definitions.

### 3. Pipeline Separation of Concerns
- **Decision**: The `ExtensionModule` is responsible for **Structure** (Shape) and **Constants** (Defaults). The `TransformModule` is responsible for **Values** (Mapping dynamic data).
- **Benefit**: This decoupling allows the `TransformModule` to remain ignorant of extension schemas; it simply maps data to the fields scaffolded by the `ExtensionModule`.

### 4. Validation
- **Decision**: Validation is optional but fully supported via the `validate: true` config flag, which runs the `stac-validator` against the item's new schema.

## Spec Updates Summary
- **Removed**: `ExtensionRegistry`, `ExtensionLoader`, `ExtensionApplicator`, Custom Python Protocol.
- **Added**: `SchemaParser`, `TemplateBuilder`, `Auto-Scaffolding` logic.
- **Configuration**: Simplified to `schema_uri` (Required) and `defaults` (Optional).

## Implementation Impact
- **Reduced Effort**: No need to maintain a registry of built-in Python extensions.
- **New Dependency**: Requires a robust JSON Schema traversing library (likely `jsonschema` or `referencing`) to handle `$ref` resolution during the "Parse" phase.
- **Performance**: High. Expensive parsing happens once at startup. Per-item cost is just a dictionary merge.
