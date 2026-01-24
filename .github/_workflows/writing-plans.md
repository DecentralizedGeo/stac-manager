---
description: Create comprehensive implementation plans before coding
---

# Writing Plans Workflow

Use this workflow when you have a specification or requirements for a multi-step task, before touching any code. This ensures you create bite-sized, well-structured plans that follow best practices.

## Overview

Write comprehensive implementation plans assuming the engineer has minimal context for the codebase. Document everything they need to know: which files to touch for each task, complete code examples, testing requirements, documentation to check, and how to verify each step. Give them the whole plan as bite-sized tasks.

**Core Principles:**
- **DRY** (Don't Repeat Yourself)
- **YAGNI** (You Aren't Gonna Need It)
- **TDD** (Test-Driven Development)
- **Frequent commits** after each successful step

**Assumptions:**
- Developer is skilled but knows almost nothing about the toolset or problem domain
- Developer doesn't know good test design very well
- Developer has zero context about this codebase

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`

## Workflow Steps

### Step 1: Announce the Workflow

Before starting, announce that you're using this workflow:

```
I'm using the writing-plans workflow to create the implementation plan.
```

### Step 2: Create the Plan Document Header

Every plan MUST start with this header structure. Adapt the placeholder content to your specific project:

```markdown
# [Feature Name] Implementation Plan

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about the technical approach]

**Tech Stack:** [Key technologies/libraries being used]

---
```

### Step 3: Define Bite-Sized Tasks

Break the implementation into granular tasks where **each step is one action taking 2-5 minutes**.

**Task granularity examples:**
- ✅ "Write the failing test" - one step
- ✅ "Run it to make sure it fails" - one step
- ✅ "Implement the minimal code to make the test pass" - one step
- ✅ "Run the tests and make sure they pass" - one step
- ✅ "Commit" - one step

**NOT granular enough:**
- ❌ "Implement the feature with tests"
- ❌ "Write and test the authentication system"

### Step 4: Structure Each Task

Use this template for every task in the plan:

```markdown
### Task N: [Component Name]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

**Step 1: Write the failing test**

Provide the complete test code:

```python
def test_specific_behavior():
    result = function(input)
    assert result == expected
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

**Step 3: Write minimal implementation**

Provide the complete implementation code:

```python
def function(input):
    return expected
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
```
```

### Step 5: Include Complete Code Examples

**Critical: Never use placeholders or partial code.**

❌ Bad - vague placeholders:
```python
# Add validation here
# Implement the logic
```

✅ Good - complete, runnable code:
```python
def validate_input(data):
    if not isinstance(data, dict):
        raise ValueError("Input must be a dictionary")
    if "required_field" not in data:
        raise ValueError("Missing required_field")
    return True
```

### Step 6: Specify Exact Commands and Expected Output

For every command that needs to be run:

1. **Provide the exact command** (copy-pasteable)
2. **Specify expected output** or behavior

Example:
```markdown
**Run:** `npm test -- --coverage`
**Expected:** All tests pass, coverage above 80%
```

### Step 7: Review the Plan

Before saving, verify your plan includes:

- [ ] **Exact file paths** for every file mentioned
- [ ] **Complete code** in every code block (no "add validation" placeholders)
- [ ] **Exact commands** with expected output for testing/verification
- [ ] **Bite-sized steps** (each 2-5 minutes)
- [ ] **TDD structure** (test first, then implementation)
- [ ] **Commit points** after each logical unit of work

### Step 8: Save the Plan

Save the completed plan to:

```
docs/plans/YYYY-MM-DD-<feature-name>.md
```

Example: `docs/plans/2026-01-13-user-authentication.md`

### Step 9: Handoff for Implementation

After saving the plan, notify that it's ready for implementation:

```
Plan complete and saved to `docs/plans/<filename>.md`. 
The plan is ready for implementation following the step-by-step tasks defined.
```

## Remember: The Golden Rules

1. **Exact file paths always** - Never use relative or vague references
2. **Complete code in plan** - Not "add validation" but the actual validation code
3. **Exact commands with expected output** - Make it copy-pasteable
4. **DRY, YAGNI, TDD** - Follow these principles throughout
5. **Frequent commits** - After each task completion
6. **Assume minimal context** - Explain everything the developer needs to know

## Common Mistakes to Avoid

| Mistake | Why It's Wrong | Correct Approach |
|---------|----------------|------------------|
| "Implement feature X" | Too broad, not actionable | Break into 5-10 specific steps |
| `some/file.py` | Relative path, ambiguous | `/absolute/path/to/file.py` |
| "Add error handling" | Placeholder, not specific | Show the complete try/catch code |
| Single test step | Misses verification loop | Separate: write test → run (fail) → implement → run (pass) |
| No expected output | Developer can't verify | Always specify what success looks like |

## Example Task Breakdown

Here's a complete example of one task following the workflow:

```markdown
### Task 1: User Authentication Model

**Files:**
- Create: `src/models/user.py`
- Create: `tests/models/test_user.py`

**Step 1: Write the failing test**

```python
# tests/models/test_user.py
import pytest
from src.models.user import User

def test_user_password_hashing():
    user = User(username="test", password="plain_password")
    assert user.password != "plain_password"
    assert user.verify_password("plain_password") is True
    assert user.verify_password("wrong_password") is False
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/models/test_user.py::test_user_password_hashing -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'src.models.user'"

**Step 3: Write minimal implementation**

```python
# src/models/user.py
import bcrypt

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = bcrypt.hashpw(
            password.encode('utf-8'), 
            bcrypt.gensalt()
        ).decode('utf-8')
    
    def verify_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password.encode('utf-8')
        )
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/models/test_user.py::test_user_password_hashing -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/models/user.py tests/models/test_user.py
git commit -m "feat: add User model with password hashing"
```
```

This example demonstrates the complete TDD cycle with exact code, commands, and expected outcomes.
