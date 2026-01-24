---
description: Review completed work against plan and quality standards
---

# Code Review Workflow

Use this workflow after completing a major project step to review implementation against the plan.

## Step 1: Load Planning Documents
// turbo
1. Look for planning documents in artifacts directory (e.g., `implementation_plan.md`, `plan.md`, or similar)
2. Load the relevant planning document
3. Identify which step or component was completed

## Step 2: Plan Alignment Check
// turbo
3. Compare implementation against planned approach and requirements
4. Identify any deviations from the plan
5. Assess if deviations are justified improvements or problematic
6. Verify all planned functionality is implemented

## Step 3: Code Quality Review
// turbo
7. Review code for established patterns and conventions
8. Check error handling, type safety, and defensive programming
9. Evaluate naming, organization, and maintainability
10. Assess test coverage and quality
11. Look for security vulnerabilities or performance issues

## Step 4: Architecture Review
// turbo
12. Ensure SOLID principles and architectural patterns are followed
13. Check separation of concerns and loose coupling
14. Verify integration with existing systems
15. Assess scalability and extensibility

## Step 5: Documentation Review
// turbo
16. Verify code includes appropriate comments and documentation
17. Check file headers, function docs, and inline comments
18. Ensure adherence to project coding standards

## Step 6: Categorize Issues
// turbo
19. Categorize findings as:
    - **Critical**: Must fix before proceeding
    - **Important**: Should fix soon
    - **Suggestions**: Nice to have

20. For each issue provide:
    - Specific code examples
    - Actionable recommendations
    - Code samples when helpful

## Step 7: Create Review Report
21. Create review report in `walkthrough.md` with sections:
    - **Summary**: Overall assessment
    - **What Went Well**: Positive aspects (start here)
    - **Critical Issues**: Must-fix items
    - **Important Issues**: Should-fix items
    - **Suggestions**: Optional improvements
    - **Plan Deviations**: Assessment of changes

22. Use `notify_user` to share results

## Communication Guidelines
- Always acknowledge what was done well first
- For significant plan deviations, request confirmation
- For plan issues, recommend updates
- Be thorough but concise
- Provide constructive feedback

## Review Checklist
- [ ] All planned functionality implemented
- [ ] Code follows established patterns
- [ ] Error handling is robust
- [ ] Type safety maintained
- [ ] Tests are comprehensive
- [ ] Security considered
- [ ] Performance assessed
- [ ] Documentation complete
- [ ] SOLID principles followed
- [ ] Code is maintainable
