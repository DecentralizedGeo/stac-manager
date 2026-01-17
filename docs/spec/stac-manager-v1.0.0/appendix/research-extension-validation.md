# Research: Extension Architecture & Validation Performance

**Status**: Proposed / Analysis Needed  
**Related Components**: `ExtensionModule`, `ValidateModule`, `TransformModule`

---

## 1. The Problem
Extensions are the core of `stac-manager`'s value, but they add complexity.
- **Validation Bottleneck**: `stac-validator` (using `jsonschema`) can be slow (100ms+ per item).
- **Partial Conformance**: During transformation, an item might have the fields for an extension but not yet be valid against the schema (e.g., missing enum values).
- **dgeo Complexity**: The `dgeo` extension has deep nesting (Roles, Rights, Context) that is hard to "patch" onto existing items.

## 2. Why Research is Needed
- **Performance**: Validating 1 million items at 100ms/item = 27 hours. We need sub-millisecond validation checks or "Optimistic" validation.
- **Development Experience**: Developers need to write simple `dict` updates, not wrestle with complex schema validation errors during the Transform phase.
- **Versioning**: When `dgeo` extension v1.1 comes out, how do we upgrade v1.0 items?

## 3. Key Questions to Answer

### 3.1 Validation Optimization
- **Question**: Can we use a faster validator than `jsonschema` (Python)?
- **Hypothesis**: Rust-based validators or compiling schemas to code?
- **Alternative**: "Structural Validation" (checking keys exist) vs "Semantic Validation" (checking enum values/logic). Do we really need full semantic validation in every intermediate step?

### 3.2 The Extension Application Flow
- **Question**: Should extensions be applied as "Patches" (Merge Strategy) or "Rebuilds"?
- **Scenario**: Adding `dgeo:assets` to a `Sentinel-2` item.
- **Risk**: Overwriting existing properties. We need a strict "Merge Logic" spec.

### 3.3 Deferred Validation
- **Question**: Can we skip validation for intermediate steps and only validate at the `OutputModule`?
- **Trade-off**: Faster workflow vs risk of finding errors only at the very end (waste of compute).

## 4. Proposed Action Items
1. Benchmark `jsonschema` vs direct Python checks for the `dgeo` schema.
2. Define a "Partial Schema" for `dgeo` that allows for loose validation during transform steps.
3. Prototype a `pydantic` model for the `dgeo` extension to see if it simplifies validation.
