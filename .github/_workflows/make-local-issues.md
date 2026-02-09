---
description: Review code and generate GitHub issues for identified problems
---

# Make Local Issues - Code Review and Issue Generation

Use this workflow to systematically review code and create actionable GitHub issues for any problems found.

## When to Use

- After completing a feature or milestone
- During periodic code quality reviews
- Before creating a pull request
- When asked to audit codebase health
- When you need to document technical debt

## Review Process

### Step 1: Silent Analysis - Think Before Acting

**CRITICAL**: Do NOT write anything yet. Think quietly to yourself about:

1. **Bugs**: Logic errors, potential crashes, edge cases not handled
2. **Design Issues**: Architecture problems, poor separation of concerns, tight coupling
3. **Code Quality**: Duplication, unclear naming, missing error handling
4. **Testing**: Missing tests, inadequate coverage, poor test design
5. **Security**: Potential vulnerabilities, input validation, data exposure
6. **Performance**: Inefficiencies, unnecessary operations, resource leaks
7. **Documentation**: Missing comments, unclear API, outdated docs

### Step 2: Categorize Issues by Severity and Type

**Severity Levels:**
- **Critical**: Bugs that cause crashes, data loss, or security vulnerabilities
- **High**: Significant design flaws or bugs that affect core functionality
- **Medium**: Code quality issues, maintainability problems, medium bugs
- **Low**: Minor improvements, style issues, documentation gaps

**Types:**
- `bug` - Something that doesn't work correctly
- `enhancement` - Missing feature or improvement
- `refactor` - Code quality or design improvement
- `documentation` - Missing or unclear documentation
- `performance` - Performance optimization needed
- `security` - Security concern

### Step 3: Check for Duplicate Issues

Before creating each issue:

// turbo
1. List all existing files in `projects/` directory
2. Read titles and descriptions of existing issues
3. Check if similar issue already exists:
   - Same file and similar problem
   - Similar root cause or symptom
   - Already documented technical debt

**If duplicate found:**
- Skip creating the issue
- Note in summary that issue already tracked

### Step 4: Generate Issue Files

For each unique issue, create a file in `projects/` directory:

**Filename format**: `projects/YYYY-MM-DD-brief-title.md`

**Issue template**:

```markdown
---
title: [Clear, actionable title]
labels: [bug|enhancement|refactor|documentation|performance|security]
severity: [critical|high|medium|low]
created: YYYY-MM-DD
status: open
---

## Description

[Clear description of the issue - what's wrong and why it matters]

## Location

- **File**: `path/to/file.ext`
- **Lines**: L123-L145 (or approximate location)
- **Component**: [if applicable, what component/module]

## Current Behavior

[Describe what's happening now or what the code currently does]

## Expected Behavior / Recommended Fix

[Describe what should happen or how to fix it]

## Example / Code Reference

```language
[relevant code snippet showing the problem]
```

## Impact

[Who is affected? What breaks? How serious is it?]

## Additional Context

- Related files: [list related files if any]
- Dependencies: [list if this blocks other work]
- References: [link to docs, similar issues, etc.]
```

### Step 5: Create Issues

// turbo
For each issue identified:
1. Generate filename with current date and brief title
2. Create file in `projects/` directory
3. Fill in template with specific details
4. Ensure all code references are accurate (NO HALLUCINATIONS)

### Step 6: Report Summary

After creating issues, provide a summary:

```
## Code Review Summary

Reviewed: [files/components reviewed]
Issues created: [number] ([critical], [high], [medium], [low])

### Critical Issues
- [Title and file] - projects/YYYY-MM-DD-title.md

### High Priority Issues
- [Title and file] - projects/YYYY-MM-DD-title.md

### Medium/Low Priority Issues
- [Title and file] - projects/YYYY-MM-DD-title.md

### Skipped (Duplicates)
- [Description of why skipped]

### Overall Assessment
[Brief assessment of code health and recommended next steps]
```

## Best Practices

### Be Specific, Not General
❌ "Error handling could be improved"
✅ "Function `processPayment()` at line 234 doesn't handle `NetworkError` exceptions, which could crash the app when API is unreachable"

### Include Context
- Reference specific lines and files
- Show code snippets
- Explain WHY it's a problem
- Suggest HOW to fix it

### Don't Hallucinate
- Only report issues you can verify in the code
- If unsure about a line number, give approximate location
- If testing behavior, state that you inferred it from code
- When in doubt, be explicit about what you don't know

### Prioritize Accurately
- **Critical**: Production-breaking bugs, security holes
- **High**: Significant design flaws, core feature bugs
- **Medium**: Code quality, maintainability, non-critical bugs
- **Low**: Style, minor improvements, documentation

### Group Related Issues
If multiple issues stem from the same root cause:
- Create ONE issue for the root cause
- Reference all affected locations in that issue
- Don't create separate issues for each symptom

## Example Usage

```
User: "Review the authentication module and create issues"
Agent: "I'll review the authentication code systematically..."

[Agent thinks quietly, identifies issues]
[Checks for duplicates]
[Creates issue files]
[Reports summary]

Code Review Summary:
Reviewed: src/auth/*.ts (5 files)
Issues created: 4 (1 critical, 2 high, 1 medium)

### Critical Issues
- SQL injection vulnerability in login validation - projects/2026-01-12-sql-injection-login.md

### High Priority Issues
- Missing password reset token expiration - projects/2026-01-12-token-expiration.md
- No rate limiting on login endpoint - projects/2026-01-12-rate-limiting.md

### Medium Priority Issues
- Inconsistent error messages expose internal state - projects/2026-01-12-error-messages.md
```

## Red Flags - STOP and Reconsider

If you find yourself:
- Creating vague issues without specific locations
- Guessing about behavior you haven't verified
- Creating issues for every minor style inconsistency
- Duplicating existing issues
- Making issues too broad ("Refactor everything")

**STOP. Be more specific and thorough.**

## Integration with Other Workflows

- Use `/code-review` first for overall quality assessment
- Then use `/make-local-issues` to document specific problems
- Issues can reference the code review walkthrough
- Team can prioritize and assign issues from `projects/` directory
