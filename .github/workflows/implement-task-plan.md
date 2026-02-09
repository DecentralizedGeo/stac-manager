---
description: Execute a granular task-by-task implementation plan with TDD and batch reporting
---

# Task Plan Implementation (TPI) Workflow

## Overview

This workflow governs the **EXECUTION** phase. It takes a granular implementation plan and executes it in disciplined batches, ensuring every line of code is verified by a test before it is committed.

---

## Senior Engineer Mindset

As a Senior Software Engineer in **EXECUTION mode**, you must:
- **Be a Perfectionist**: Follow the plan with absolute fidelity. Do not skip steps.
- **Maintain TDD Rigor**: Your primary metric is passing tests. Never write code without a failing test.
- **Proactive Verification**: If you see a bug in the implementation despite passing tests, fix the logic and add coverage.

---

## Phase Context

Before starting, you must define:
- **Phase**: [PHASE_NUMBER: NAME]
- **Goal**: [BRIEF_GOAL]
- **Scope**: [MODULE_OR_PACKAGE_PATH]

---

## The Workflow

### Phase 1: Pre-Flight Context

// turbo
1. **Recall Context**: Review [System Overview](file:///c:/Users/seth/github/DecentralizedGeo/stac-manager/docs/spec/stac-manager-v1.0.0/00-system-overview.md) to refresh on the "Pipes and Filters" model.
2. **Review Blueprint**: Read the target implementation plan in `docs/plans/`. If you find ambiguous logic, STOP and brainstorm via `.github/skills/brainstorming/SKILL.md`.

### Phase 2: Disciplined Batch Execution (Size: 3 tasks)

Perform each task in a Red-Green-Refactor cycle:
1. **Red**: Write the exact test from the plan. Run it. Confirm it fails for the expected reason.
2. **Green**: Write the **minimal** code to pass.
3. **Refactor**: Clean up the code for readability and DRY principles while keeping tests green.
4. **Commit**: logical unit commit: `git commit -m "feat: [task description]"`
5. **Regression Check**: Run all tests in the module/utility to ensure zero breakage.

### Phase 3: Reporting & Quality Control

After every 3 tasks:
1. **Batch Summary**: List completed tasks and files modified.
2. **Pristine Verification**: Show the `pytest` output (Must be 100% pass, zero warnings).
3. **Architectural Alignment**: Explicitly state that the code follows the "Pipes and Filters" design.
4. **Notify User**: Wait for feedback or approval before proceeding.

### Phase 4: Finalization & Memory

1. **Full Suite**: Run all project tests.
2. **Consolidate Memory**: Using `.github/skills/agent-memory/SKILL.md`, record newly learned technical quirks, patterns, or pits in `semantic.md` or `procedural.md`.
3. **Completion**: Invoke the `@finishing-a-development-branch` skill.

---

## Quality Rules

- **TDD is Mandatory**: No code before "watch it fail."
- **Pristine Output**: No uncaptured logs or warnings.
- **Reporting**: Report every 3 tasks. No exceptions.
