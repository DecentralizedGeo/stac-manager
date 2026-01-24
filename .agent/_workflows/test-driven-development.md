---
description: RED-GREEN-REFACTOR cycle for test-driven development
---

# Test-Driven Development (TDD) Workflow

## The Iron Law
**NEVER write code before writing a failing test for it.**

If you wrote code before the test, DELETE IT and start over.

## The RED-GREEN-REFACTOR Cycle

### Step 1: RED - Write Failing Test
// turbo
1. Write ONE test for the NEXT small piece of functionality
2. Make it as simple and focused as possible
3. Commit: `git commit -m "test: add failing test for [feature]"`

### Step 2: Verify RED - Watch It Fail
// turbo
4. Run the test and VERIFY it fails
5. Read the failure message to confirm it's failing for the RIGHT reason
6. If it passes unexpectedly, investigate why

### Step 3: GREEN - Minimal Code
// turbo
7. Write the MINIMUM code to make the test pass
8. Don't add extra features or "nice to haves"
9. It's okay if the code is ugly at this stage

### Step 4: Verify GREEN - Watch It Pass
// turbo
10. Run the test and VERIFY it passes
11. Run ALL tests to ensure no regressions
12. If it fails, debug until it passes

### Step 5: REFACTOR - Clean Up
// turbo
13. Now improve the code quality WITHOUT changing behavior
14. Run tests after each refactoring step
15. Commit: `git commit -m "feat: implement [feature]"`

### Step 6: Repeat
16. Go back to Step 1 for the next piece of functionality

## Red Flags - STOP and Start Over

If you find yourself:
- Writing implementation code without a test
- Writing multiple tests before any implementation
- Skipping the "watch it fail" step
- Adding features not covered by tests
- Rationalizing why TDD doesn't apply "in this case"

**STOP. Delete the code. Start over with a test.**

## When to Use

- [ ] Adding new functionality
- [ ] Fixing bugs (write test that reproduces bug first)
- [ ] Refactoring existing code
- [ ] Implementing API endpoints or business logic

## Verification Checklist

After completing TDD cycle:
- [ ] Every line of new code is covered by a test
- [ ] All tests pass
- [ ] Each commit has either a failing test OR passing implementation
- [ ] No speculative features were added
