---
description: Execute written implementation plans with review checkpoints between batches
---

# Executing Plans

Use this workflow when you have a written implementation plan to execute in a separate session with structured review checkpoints.

**Core principle:** Batch execution with checkpoints for architect review.

## Overview

Load plan, review critically, execute tasks in batches, report for review between batches. This workflow ensures systematic execution of detailed implementation plans while maintaining oversight and quality through regular checkpoint reviews.

## When to Use

- Starting implementation from an approved `implementation_plan.md`
- Executing a detailed plan after design/planning phase
- Working through multi-task implementations systematically
- Need structured checkpoints for review between batches

## Workflow Steps

### Step 1: Announce Intent

At the start, announce that you're using this workflow:

```
I'm using the executing-plans workflow to implement this plan.
```

### Step 2: Load and Review Plan

// turbo
1. Read the implementation plan file (typically `implementation_plan.md` in artifacts directory)
2. Review the plan critically - identify any questions, concerns, or ambiguities
3. Check for:
   - Missing dependencies or prerequisites
   - Unclear instructions or specifications
   - Potential blockers or technical gaps
   - Required skills or sub-workflows referenced

**If concerns found:**
- Raise them with your human partner immediately via `notify_user`
- DO NOT proceed until concerns are addressed
- Wait for plan clarification or updates

**If no concerns:**
- Create or update `task.md` checklist from plan tasks
- Proceed to Step 3

### Step 3: Execute Batch

**Default batch size: First 3 tasks**

For each task in the current batch:

// turbo
1. Mark task as `[/]` (in progress) in `task.md`
2. Follow each step in the task exactly as specified
   - Plans should have bite-sized, clear steps
   - Don't improvise or deviate without reason
3. Run verifications as specified in the plan
4. Mark task as `[x]` (completed) in `task.md` when done

**Important:**
- Reference skills when the plan instructs you to (e.g., "use the git-worktrees skill")
- Follow plan steps exactly - they were designed for this specific implementation
- Don't skip verification steps

### Step 4: Report Completion

When the batch is complete, use `notify_user` to report:

```
Batch complete. I implemented:
- Task 1: <brief description>
- Task 2: <brief description>
- Task 3: <brief description>

Verification results:
- <verification output summary>

Ready for feedback.
```

**Report should include:**
- What was implemented (brief descriptions)
- Verification output (test results, build status, etc.)
- Any deviations from plan (with justification)
- Current status of `task.md` progress

### Step 5: Continue Based on Feedback

After user provides feedback:

**If changes requested:**
- Apply requested changes
- Re-run verifications
- Report completion again

**If approved to continue:**
- Execute next batch (3 more tasks)
- Repeat Steps 3-4 until all tasks complete

### Step 6: Complete Development

After all tasks are complete and verified:

1. Announce completion:
   ```
   All plan tasks completed. Moving to branch finalization.
   ```

2. **Follow branch finalization workflow:**
   - Use the `/code-review` workflow to review implementation
   - Create `walkthrough.md` documenting what was accomplished
   - Verify all tests pass
   - Prepare branch for merge/PR

## When to Stop and Ask for Help

**STOP executing immediately when:**

- Hit a blocker mid-batch (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing you from starting a task
- You don't understand an instruction or specification
- Verification fails repeatedly (more than 2 attempts)
- You discover the plan approach is fundamentally flawed
- Required skill or tool is not available

**Never guess or improvise around blockers.** Stop and ask for clarification.

## When to Revisit Earlier Steps

**Return to Step 2 (Review) when:**
- Partner updates the plan based on your feedback
- You discover fundamental issues requiring plan revision
- Approach needs significant rethinking

**Don't force through blockers** - stop, report clearly, and ask for guidance.

## Quick Reference

| Situation | Action |
|-----------|--------|
| Plan unclear | Stop, ask for clarification before starting |
| Verification fails | Try once more, then stop and report |
| Missing dependency | Stop, report blocker, wait for resolution |
| Plan references skill | Load and follow that skill |
| Batch complete | Report via `notify_user`, wait for feedback |
| All tasks done | Use `/code-review` workflow for finalization |

## Communication Guidelines

**Between batches:**
- Keep reports concise but complete
- Show what was done, not what will be done
- Include verification results
- Wait for feedback before continuing

**When blocked:**
- Report the specific blocker clearly
- Explain what you've tried
- Ask specific questions
- Don't proceed until resolved

**Don't:**
- Skip ahead without completion report
- Batch more than 3 tasks without explicit permission
- Proceed with failing verifications
- Deviate from plan without justification

## Safety Rules

**Never:**
- Skip plan review and jump to implementation
- Ignore verification failures
- Proceed when blocked or confused
- Batch more than 3 tasks by default
- Skip reporting between batches

**Always:**
- Review plan critically before starting
- Follow plan steps exactly
- Run all specified verifications
- Report between batches
- Reference skills when plan specifies
- Stop when blocked and ask for help

## Integration with Other Workflows

This workflow pairs well with:
- **Planning workflows** - Execute plans created during planning phase
- **Code review** (`/code-review`) - Required after all tasks complete
- **Git worktrees** (`/git-worktrees`) - Often used before executing plans
- **TDD** (`/test-driven-development`) - Individual tasks may use TDD approach

## Notes

- Batch size can be adjusted based on task complexity (ask user if unsure)
- Plans should be living documents - updates during execution are normal
- Regular checkpoints catch issues early
- Systematic execution prevents scope creep and missed requirements
- `task.md` provides clear progress tracking for both agent and user
