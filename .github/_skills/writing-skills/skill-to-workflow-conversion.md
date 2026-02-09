---
name: Skill-to-Workflow-Conversion
description: Reference guide for converting Claude Code skills into Antigravity workflow format, including format requirements, structural adaptations, and conversion patterns
---

# Converting Claude Skills to Antigravity Workflows

Reference material for adapting skills from Claude Code superpowers repository (or similar sources) into Antigravity-compatible workflows.

## Core Concept

**Skills are conceptual, workflows are procedural.**

- **Skills** teach patterns and principles
- **Workflows** execute specific tasks step-by-step

## Format Comparison

| Aspect | Claude Skills | Antigravity Workflows |
|--------|---------------|----------------------|
| **Purpose** | Reference materials, reusable knowledge | Step-by-step procedural guides |
| **Format** | Educational, conceptual, includes theory | Actionable instructions with clear steps |
| **Structure** | Overview → Pattern → Examples → Mistakes | YAML frontmatter + numbered steps |
| **Usage** | Referenced for understanding | Invoked via `/workflow-name` |
| **Location** | `.agent/skills/skill-name/SKILL.md` | `.agent/workflows/workflow-name.md` |
| **Organization** | Directory with multiple files | Single markdown file |
| **Size limit** | No hard limit | 12,000 characters maximum |
| **Invocation** | Read for context | Executed procedurally |

## Antigravity Workflow Requirements

### 1. YAML Frontmatter (Mandatory)

```yaml
---
description: Brief description of what the workflow does
---
```

**Guidelines:**
- Under 100 characters ideal
- Focus on what it accomplishes, not how
- Use action verbs: "Create", "Review", "Debug", "Deploy"
- Appears in workflow list for discovery

### 2. Standard Structure

```markdown
# Workflow Title

Overview paragraph

## When to Use
- Triggering scenario 1
- Triggering scenario 2

## Prerequisites (optional)
- Requirement 1
- Requirement 2

## Workflow Steps

### Step 1: Action Name
Procedural instructions...

### Step 2: Another Action
More instructions...

## Quick Reference (optional)
Table or decision matrix

## Common Issues (optional)
Troubleshooting guide

## Safety Rules (optional)
Never/Always lists
```

### 3. Turbo Annotations

Mark safe-to-auto-run commands with `// turbo`:

```markdown
// turbo
```bash
git status
ls -la
```
```

**Safe**: Read-only operations, checks, tests that don't modify state  
**Unsafe**: Writes, installs, commits, destructive operations

## Mapping Strategy

### Conceptual → Procedural Translation

| Skill Section | Maps To | Transformation |
|---------------|---------|----------------|
| Overview (principle) | Overview (what it does) | From "why pattern works" → "what workflow accomplishes" |
| When to Use (symptoms) | When to Use (scenarios) | From "recognize this pattern" → "invoke when X happens" |
| Core Pattern (theory) | Workflow Steps (actions) | From "understand approach" → "execute these steps" |
| Quick Reference | Quick Reference | Keep as-is (tables work well) |
| Common Mistakes | Common Issues | From "avoid X" → "if X happens, do Y" |
| Red Flags | Safety Rules | From warnings → Never/Always rules |
| Integration | Integration | Keep as-is (workflow relationships) |

### Key Transformations

#### 1. Decision Trees → Priority Steps

**Skill (conceptual):**
```markdown
Follow priority: existing → config → ask
```

**Workflow (procedural):**
```markdown
### Step 2: Determine Location

**Priority 1: Check existing directories**
// turbo
```bash
ls -d .worktrees 2>/dev/null
```
- If found → use it (proceed to Step 3)
- If not found → Priority 2

**Priority 2: Check configuration**
// turbo
```bash
grep "worktree" AGENTS.md
```
- If found → use it (proceed to Step 3)
- If not found → Priority 3

**Priority 3: Ask user**
Ask: "Where should I create worktrees?"
```

#### 2. Principles → Concrete Commands

**Skill (abstract):**
```markdown
Verify directory is ignored by git
```

**Workflow (concrete):**
```markdown
### Step 3: Verify Gitignore

**CRITICAL:** Verify directory is ignored before proceeding.

// turbo
```bash
git check-ignore -q .worktrees
```

**If command fails (non-zero exit):**
1. Add `.worktrees/` to `.gitignore`
2. Commit the change
3. Proceed to next step
```

#### 3. Mistakes → Troubleshooting

**Skill (warning):**
```markdown
### Skipping verification
**Problem:** Contents get tracked
**Fix:** Always verify first
```

**Workflow (diagnostic):**
```markdown
### Issue: Directory not ignored

**Symptom:** `git check-ignore` returns exit code 1

**Fix:**
1. Add directory to `.gitignore`
2. Run `git add .gitignore`
3. Run `git commit -m "Ignore worktree directory"`
4. Verify with `git check-ignore -q .worktrees`

**Why critical:** Prevents accidental commits of development artifacts
```

## Critical Preservation Points

When converting, you MUST preserve:

### Safety Checks
- All verification steps (gitignore checks, test runs)
- All "MUST" or "CRITICAL" requirements
- All error handling logic

**Example:**
```markdown
**CRITICAL:** If tests fail, ask before proceeding.
```

### Decision Points
- All branching logic (if X then Y else Z)
- All user interaction points
- All conditional paths

**Example:**
```markdown
**If tests pass:**
- Report success
- Proceed to next step

**If tests fail:**
- Report failures
- Ask: "Tests failing. Proceed anyway or investigate?"
```

### Error Handling
- What to do when commands fail
- How to recover from errors
- When to ask user for guidance

## Character Limit Optimization

Workflows limited to 12,000 characters. Strategies:

### Keep
- ✅ All safety-critical checks
- ✅ All decision points with clear logic
- ✅ All concrete commands
- ✅ Error handling for common failures
- ✅ Quick reference tables

### Trim
- ❌ Extended rationale (unless safety-critical)
- ❌ Historical context or background
- ❌ Multiple examples of same pattern
- ❌ Redundant explanations
- ❌ Alternative approaches not part of workflow

### Optimization Techniques
1. Tables instead of prose for reference material
2. Bullet points instead of paragraphs
3. Combine related steps when possible
4. Inline short code examples, separate file if >100 lines
5. Assume intelligent agent - avoid over-explaining

**Check character count:**
```bash
# PowerShell
Get-Content "path/to/workflow.md" | Measure-Object -Character

# Unix/Linux
wc -c path/to/workflow.md
```

## Common Patterns

### Pattern: Multi-Option Selection

**Skill approach:**
```markdown
Choose based on project type
```

**Workflow approach:**
```markdown
### Step 4: Run Project Setup

Detect project type and run appropriate setup:

**Node.js** (if `package.json` exists):
```bash
npm install
```

**Python** (if `requirements.txt` exists):
```bash
pip install -r requirements.txt
```

**Rust** (if `Cargo.toml` exists):
```bash
cargo build
```

Run all applicable commands for detected types.
```

### Pattern: Safety Verification

**Skill approach:**
```markdown
Ensure baseline is clean before starting
```

**Workflow approach:**
```markdown
### Step 7: Verify Clean Baseline

Run tests to ensure worktree starts clean:

```bash
npm test  # or appropriate test command
```

**If tests fail:**
- Report failures clearly
- Ask: "Baseline tests failing. Proceed or investigate?"
- Wait for explicit permission

**If tests pass:**
- Report: "✓ N tests passing"
- Proceed to Step 8

**Why critical:** Can't distinguish new bugs from pre-existing issues without clean baseline
```

### Pattern: Systematic Process

**Skill approach:**
```markdown
Follow systematic directory selection
```

**Workflow approach:**
```markdown
### Step 2: Determine Directory Location

Follow this priority order **in sequence**:

1. **Check existing** → if found, use it
2. **Check config** → if specified, use it  
3. **Ask user** → get preference

Do NOT skip steps. Do NOT assume location.
```

## Anti-Patterns

### ❌ Copying Conceptual Content

Don't just copy skill's educational explanations:

```markdown
<!-- Don't do this -->
Git worktrees create isolated workspaces by sharing the same
repository. This is beneficial because it allows concurrent
development without the overhead of multiple clones...
```

### ✅ Write Procedural Instructions

Do provide clear actionable steps:

```markdown
<!-- Do this -->
### Step 1: Create Worktree

```bash
git worktree add .worktrees/feature-name -b feature-name
cd .worktrees/feature-name
```
```

### ❌ Vague Instructions

Don't leave ambiguity:

```markdown
<!-- Don't do this -->
### Step 3: Setup Environment
Configure your environment appropriately
```

### ✅ Concrete Commands

Do specify exact actions:

```markdown
<!-- Do this -->
### Step 3: Install Dependencies

**Node.js projects:**
```bash
npm install
```

**Python projects:**
```bash
pip install -r requirements.txt
```
```

### ❌ Missing Error Handling

Don't ignore failure scenarios:

```markdown
<!-- Don't do this -->
### Step 4: Run Tests
Run the test suite
```

### ✅ Explicit Error Paths

Do define what happens on failure:

```markdown
<!-- Do this -->
### Step 4: Run Tests

```bash
npm test
```

**On success:** Proceed to Step 5  
**On failure:** Report errors, ask "Proceed or investigate?"
```

## Quality Checklist

Before considering conversion complete:

- [ ] YAML frontmatter present with concise description
- [ ] Title (H1) clearly names the workflow
- [ ] Overview explains what workflow does (not how pattern works)
- [ ] All steps are numbered and procedural
- [ ] All safety checks from skill are preserved
- [ ] Code examples are concrete and runnable
- [ ] Decision points have explicit "if X then Y" logic
- [ ] Error handling defined for common failures
- [ ] Character count under 12,000
- [ ] Turbo annotations on safe commands
- [ ] No conceptual explanations (move to skills if needed)
- [ ] Workflow is independently executable

## Example: git-worktrees Conversion

### Source Skill Characteristics
- **Format**: Educational with principles
- **Size**: ~4,000 characters
- **Focus**: Understanding the pattern
- **Structure**: Overview → Process → Mistakes → Integration

### Converted Workflow Characteristics
- **Format**: Step-by-step procedural
- **Size**: 8,039 characters (67% of limit)
- **Focus**: Executing the task
- **Structure**: YAML → Overview → Steps → Reference → Troubleshooting

### Key Adaptations
1. "Directory Selection Process" → Step 2 with priority-ordered actions
2. "Safety Verification" → Explicit mandatory Step 3
3. "Creation Steps" → Steps 4-7 with concrete bash commands
4. "Common Mistakes" → "Troubleshooting" with symptom-fix-why format
5. "Quick Reference" preserved as decision matrix table
6. Added `// turbo` annotations for safe commands

## Relationship to Skills

**Skills and workflows complement each other:**

- **Workflow** (`.agent/workflows/git-worktrees.md`): How to execute the process
- **Skill** (`.agent/skills/using-git-worktrees/`): Why pattern works, when to use it

A workflow can reference a skill for deeper understanding, but must be independently executable without reading the skill.

**When to keep both:**
- Skill teaches the pattern/principle
- Workflow executes a specific instance of that pattern

**When to only create workflow:**
- Skill is purely procedural already
- No underlying pattern to teach
- One-time process unlikely to vary

## Summary

Converting skills to workflows = transform conceptual to procedural:

| Transformation | From (Skill) | To (Workflow) |
|----------------|--------------|---------------|
| **Tone** | Educational | Instructional |
| **Content** | Why it works | How to do it |
| **Structure** | Principles | Steps |
| **Examples** | Illustrative | Executable |
| **Errors** | What to avoid | What to do when it happens |
| **Format** | Flexible | YAML + numbered steps |
| **Invocation** | Reference | Execute |

The goal: Create a workflow an agent can follow step-by-step without needing to interpret conceptual guidance.
