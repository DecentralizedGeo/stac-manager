---
description: Review and refine specifications to ensure they are complete blueprints for implementation
---

# Spec-Driven Development (SDD) Workflow

## The Core Principle

**The Specification is the Source of Truth.**

This workflow is a **Quality Gate**. Its purpose is to ensure a specification document is sufficiently detailed to serve as a "blueprint" for implementation. You should NOT proceed to implementation planning until the spec passes this review.

## The Review-Refine Cycle

### Step 1: Deep Read & Architecture Check

// turbo

1. Read the provided specification documents thoroughly
2. Assess compliance with the **3-Tier Detail Strategy**:
   - **Tier 1 (contracts)**: Are stricter schemas/interfaces defined?
   - **Tier 2 (Algorithms)**: Is complex logic described (pseudocode/flow)?
   - **Tier 3 (Concepts)**: Is there high-level context?
3. Verify **Structural Completeness**:
   - Does it define *Input* -> *Process* -> *Output*?
   - Are error states and edge cases handled?

### Step 2: Gap Analysis (The Blueprint Test)

// turbo
4. Ask yourself: *"Could I write the code for this exclusively from this document without asking the user extra questions?"*
5. Identify **"Reference Leaks"**: Places where the spec assumes knowledge not in the document.
6. Identify **"Magic Steps"**: Logic described as "then we process it" without the *how*.
7. List these gaps as distinct questions or TODOs.

### Step 3: Refine the Spec

8. **Clarify**: Rewrite vague sections with precise language.
2. **Expand**: Add pseudo-code or schemas where missing.
3. **Defer**: Explicitly mark out-of-scope items as "Future Work" (don't leave them ambiguous).
4. **Collaborate**: if critical information is missing, ask the User.

## Definition of Done (Greenlight)

The workflow is complete when:

- [ ] No "critical" gaps remain.
- [ ] The Spec is a self-contained "Blueprint".
- [ ] You are confident you could hand this spec to another engineer (or agent) to build without confusion.

After all edits have finished, you must output a walkthrough (or `walkthrough.md`) summary of changes.

## Output Artifacts

- **Updated Spec**: The polished, verified "blueprint" ready for the Planning phase.
