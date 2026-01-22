# Technical Spec Review: Extension Module

**Target Documents**:
1.  `docs/spec/stac-manager-v1.0.0/modules/extension.md`
2.  `docs/spec/stac-manager-v1.0.0/06-protocols.md`

**Reviewer**: Senior Engineer Persona
**Workflow**: `@/spec-review-technical`

## Phase 1: Diagnostic Scan (Planning)

### 1. `modules/extension.md` (Extension Module)

#### Tier 1 Gaps (Contracts)
*   [ ] **Initialization Contract**: `__init__` takes `config: dict` in pseudocode, but `ExtensionConfig` is defined separately. The pseudocode uses `config.schema_uri` implying it is already a Pydantic object, but the arguments say `config`.
    *   *Action*: Update `__init__` signature to `def __init__(self, config: dict) -> None:` and explicitly show the Pydantic parsing: `self.config = ExtensionConfig(**config)`.
*   [ ] **Pydantic Field Strictness**: `defaults: Optional[Dict[str, Any]]`.
    *   *Action*: This is acceptable for simple dot notation, but let's see if we can be more specific? `Any` is likely needed here for values.

#### Tier 2 Gaps (Algorithmic Logic)
*   [ ] **Parsing Logic**: The core value proposition "Auto-Scaffolding" depends on `_build_template`. Currently, this is referenced but defined nowhere in the spec file (only in implementation plan).
    *   *Action*: Add a dedicated Pseudocode block for `_build_template(schema: dict) -> dict` that shows the "Best Effort" heuristic (handling `properties`, ignoring `oneOf` unless simple, filtering `stac_extensions`).
*   [ ] **Deep Merge Logic**: `deep_merge` is used but not defined.
    *   *Action*: Briefly define the merge strategy (e.g., does it append to lists or replace? Does it overwrite scalars?). It should be "Keep Existing".

#### Tier 3 Violations (Conceptual)
*   [ ] **Fetch Implementation**: `fetch_json` is conceptual. No major violations found.

### 2. `06-protocols.md` (Protocols)

#### Legacy Content Removal
*   [ ] **Extension Protocol**: The entire Section 4 "Extension Protocol" describes the old `Extension` class interface with `apply` and `validate` methods. This is now obsolete as the ExtensionModule is config-driven.
    *   *Action*: Remove Section 4 entirely.
*   [ ] **References**: Remove references to "Plugin Strategy" in Section 7 Summary.

## Phase 2: Execution Plan

1.  **Refine `modules/extension.md`**:
    *   Update `ExtensionModule` pseudocode to align `__init__` and `self.config`.
    *   Add `_build_template` pseudocode block.
    *   Clarify `deep_merge` behavior.
2.  **Clean `06-protocols.md`**:
    *   Delete Section 4.
    *   Renumber subsequent sections if necessary (Section 5 -> 4, etc).

## Phase 3: Verification
*   Verify strict contracts in extension module.
*   Verify no legacy "Extension Protocol" remains in docs.
