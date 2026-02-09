---
description: Create isolated git worktrees for parallel development
---

# Using Git Worktrees

Use this workflow to create isolated workspaces for working on multiple branches simultaneously without switching contexts. This ensures clean separation and prevents accidental cross-contamination between different feature branches.

**Core principle:** Systematic directory selection + safety verification = reliable isolation.

## Overview

Git worktrees create isolated workspaces that share the same repository, allowing you to work on multiple branches simultaneously without switching. This workflow ensures you follow a systematic approach with proper safety checks.

## When to Use

- Starting work on a new feature that requires an isolated workspace
- Working on multiple branches in parallel
- Need to quickly switch between different feature implementations
- Want to preserve current working state while testing something else

## Prerequisites

- Must be in a git repository
- Should have a clean working directory (or be willing to commit/stash changes)
- Need appropriate permissions to create directories

## Workflow Steps

### Step 1: Announce Intent

At the start, announce that you're using this workflow:

```
I'm using the git-worktrees workflow to set up an isolated workspace.
```

### Step 2: Determine Worktree Directory Location

Follow this priority order to determine where worktrees should be created:

**Priority 1: Check for existing worktree directories**

// turbo
```bash
# Check in priority order
ls -d .worktrees 2>/dev/null     # Preferred (hidden)
ls -d worktrees 2>/dev/null      # Alternative
```

- If `.worktrees/` exists → use it (proceed to Step 3)
- If `worktrees/` exists → use it (proceed to Step 3)
- If both exist → use `.worktrees/` (proceed to Step 3)
- If neither exists → continue to Priority 2

**Priority 2: Check CLAUDE.md or AGENTS.md for preferences**

// turbo
```bash
# Check for worktree directory preference
grep -i "worktree.*director" CLAUDE.md 2>/dev/null
grep -i "worktree.*director" AGENTS.md 2>/dev/null
```

- If preference specified → use that location (proceed to Step 3)
- If no preference found → continue to Priority 3

**Priority 3: Ask the user**

If no directory exists and no configuration preference is found, ask:

```
No worktree directory found. Where should I create worktrees?

1. .worktrees/ (project-local, hidden - recommended)
2. worktrees/ (project-local, visible)
3. ~/.config/superpowers/worktrees/<project-name>/ (global location)

Which would you prefer?
```

Wait for user response and use their chosen location.

### Step 3: Safety Verification (Project-Local Only)

**CRITICAL:** If using a project-local directory (`.worktrees` or `worktrees`), you MUST verify it's ignored by git.

// turbo
```bash
# Check if directory is ignored
git check-ignore -q .worktrees || git check-ignore -q worktrees
```

**If directory is NOT ignored:**

1. Add the appropriate line to `.gitignore`:
   ```bash
   echo ".worktrees/" >> .gitignore  # or "worktrees/" depending on choice
   ```

2. Commit the change immediately:
   ```bash
   git add .gitignore
   git commit -m "Add worktree directory to gitignore"
   ```

3. Proceed to next step

**Why this is critical:** Prevents accidentally committing worktree contents to the repository, which would pollute git history with development artifacts.

**Note:** Global directory (`~/.config/superpowers/worktrees`) doesn't need gitignore verification since it's outside the project.

### Step 4: Detect Project Name

// turbo
```bash
project=$(basename "$(git rev-parse --show-toplevel)")
```

This will be used for organizing worktrees in global directories.

### Step 5: Create the Worktree

Determine the branch name for your feature (ask user if not specified), then create the worktree:

```bash
# Set branch name (example: feature/auth)
BRANCH_NAME="feature/your-feature-name"

# Determine full path based on location choice
case $LOCATION in
  .worktrees)
    path=".worktrees/$BRANCH_NAME"
    ;;
  worktrees)
    path="worktrees/$BRANCH_NAME"
    ;;
  ~/.config/superpowers/worktrees/*)
    path="$HOME/.config/superpowers/worktrees/$project/$BRANCH_NAME"
    ;;
esac

# Create worktree with new branch
git worktree add "$path" -b "$BRANCH_NAME"

# Navigate to the new worktree
cd "$path"
```

### Step 6: Run Project Setup

Auto-detect the project type and run appropriate setup commands:

**Node.js projects:**
```bash
if [ -f package.json ]; then
  npm install
fi
```

**Rust projects:**
```bash
if [ -f Cargo.toml ]; then
  cargo build
fi
```

**Python projects:**
```bash
# Using requirements.txt
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

# Using Poetry
if [ -f pyproject.toml ]; then
  poetry install
fi
```

**Go projects:**
```bash
if [ -f go.mod ]; then
  go mod download
fi
```

Run all applicable setup commands for detected project types.

### Step 7: Verify Clean Baseline

**CRITICAL:** Run tests to ensure the worktree starts in a clean state. This is essential for distinguishing new bugs from pre-existing issues.

```bash
# Examples - use project-appropriate command
npm test           # Node.js
cargo test         # Rust
pytest             # Python
go test ./...      # Go
```

**If tests fail:**
- Report the failures clearly
- Ask user: "Baseline tests are failing. Should I proceed anyway or investigate first?"
- Wait for explicit permission to proceed

**If tests pass:**
- Report success with test count
- Proceed to final step

### Step 8: Report Completion

Provide a clear summary:

```
Worktree ready at <full-path>
Tests passing (<N> tests, 0 failures)
Ready to implement <feature-name>
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.worktrees/` exists | Use it (verify ignored) |
| `worktrees/` exists | Use it (verify ignored) |
| Both exist | Use `.worktrees/` |
| Neither exists | Check CLAUDE.md/AGENTS.md → Ask user |
| Directory not ignored | Add to .gitignore + commit immediately |
| Tests fail during baseline | Report failures + ask before proceeding |
| No package.json/Cargo.toml | Skip dependency install |

## Common Issues and Troubleshooting

### Issue: Directory not ignored
**Symptom:** `git check-ignore` returns non-zero exit code

**Fix:** 
1. Add directory to `.gitignore`
2. Commit the change
3. Never proceed without fixing this

**Why:** Prevents worktree contents from polluting the repository

### Issue: Tests fail during baseline verification
**Symptom:** Test command exits with failures

**Fix:**
1. Report failures clearly to user
2. Ask whether to investigate or proceed
3. Never proceed without explicit permission

**Why:** Can't distinguish new bugs from pre-existing issues if baseline isn't clean

### Issue: Setup command fails
**Symptom:** `npm install` or similar fails

**Fix:**
1. Report the error
2. Check for missing dependencies or system requirements
3. Ask user for guidance if resolution isn't obvious

### Issue: Wrong directory location assumed
**Symptom:** Creating worktree in unexpected location

**Fix:** Always follow priority order:
1. Existing directories
2. CLAUDE.md/AGENTS.md preference
3. Ask user

**Why:** Maintains consistency with project conventions

## Safety Rules

**Never:**
- Create project-local worktree without verifying it's ignored
- Skip baseline test verification
- Proceed with failing tests without explicit user permission
- Assume directory location when ambiguous
- Skip CLAUDE.md/AGENTS.md check

**Always:**
- Follow directory priority: existing → config → ask
- Verify directory is ignored for project-local locations
- Auto-detect and run project setup
- Verify clean test baseline before reporting ready
- Report full path and test results

## Integration with Other Workflows

This workflow pairs well with:
- **Brainstorming workflows** - Use after design approval before implementation
- **Finishing development branches** - Required for cleanup after work complete
- **Code review workflows** - Work happens in the isolated worktree

## Notes

- Worktrees share git history but have independent working directories
- Each worktree can be on a different branch
- Changes in one worktree don't affect others
- Use `git worktree list` to see all active worktrees
- Use `git worktree remove <path>` to clean up when done
