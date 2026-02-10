---
description: Transform a high-level design or specification (blueprint) into a granular, TDD-ready implementation plan
---

# Blueprint to Implementation Plan (BIP) Workflow

## Overview

This workflow is the bridge between **Design** and **Execution**. It takes a verified specification (the "Blueprint") and decomposes it into a sequence of bite-sized, TDD-compliant development tasks.

---

## Senior Engineer Mindset

As a Senior Software Engineer, you are expected to:

- **Be Brutally Honest**: Call out bad ideas, unreasonable expectations, or technical misalignments.
- **Push Back**: If a design choice conflicts with YAGNI or Pythonic best practices.
- **Never Invent**: If unsure of a technical detail, STOP and research it. NEVER hallucinate.
- **Collaborative Spirit**: You are a partner in design. You do not work in a vacuum.

---

## The Workflow

### Phase 1: Context & Memory Sync

// turbo

1. **Recall Memory**: Use the `.github/skills/agent-memory/SKILL.md` skill to read existing decisions, semantic mapping, and procedural standards.
2. **Roadmap Alignment**: Review the [Roadmap](file:///c:/Users/seth/github/DecentralizedGeo/stac-manager/docs/plans/2026-01-22-stac-manager-roadmap.md) to understand dependencies and success criteria for the target phase.
3. **Initialize if New**: If this is a new project, create the `.github/memory/` directory and seed it with the "Project Vision" from the blueprint.

### Phase 2: Blueprint Verification

// turbo

1. **Review Specification**: Thoroughly read the input specification documents and [System Overview](file:///c:/Users/seth/github/DecentralizedGeo/stac-manager/docs/spec/stac-manager-v1.0.0/00-system-overview.md).
2. **Gap Analysis**: If the spec has "Magic Steps" or vague contracts, STOP and refine it first using the `/spec-driven-development` workflow.
3. **Brainstorming**: If you encounter ambiguous paths, invoke `.github/skills/brainstorming/SKILL.md` to propose 2-3 approaches with trade-offs.

### Phase 3: Research & Grounding

// turbo

1. **Deep Read External**: Perform a "Deep Read" of official docs (e.g., PySTAC, PyStac-Client) via browser tools to verify class signatures and behavior.
2. **Codebase Audit**: Audit the current `src/` and `tests/` directories to ensure the new plan maintains structural continuity and reuses existing logic/utilities.

### Phase 4: Plan Generation

1. **Identify Tasks**: Break the implementation into logical **Phases** (Foundation, Core, Orchestration, UX).
2. **TDD-Enforced Tasks**: Use the `@writing-plans` skill to create bite-sized (2-5 min) tasks. Every task MUST specify:
   - **Red**: Exact test file and expected failure message.
   - **Green**: Minimal implementation steps.
   - **No Mocks**: Use real or synthetic domain data.
3. **Organization**: The plan must reside in `docs/plans/YYYY-MM-DD-stac-manager-[PHASE_NAME]-specification.md` with a linked **Table of Contents**.

### Phase 5: Quality Checklist

Before finalizing the plan, verify:

- [ ] No "critical" gaps remain.
- [ ] No speculative features (YAGNI).
- [ ] Error handling follows the **Three-Tier Model** (recorded in memory).
- [ ] Plan includes a `walkthrough.md` generation task.

---

## Handoff

Once the plan is created:

1. Present the **Plan Overview** (Goal + Scope) to the user.
2. Ask: *"Ready to set up for implementation with the `/implement-task-plan` workflow?"*
