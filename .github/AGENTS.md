# Agent Instructions

This file contains guidelines and best practices for AI agents working on this project. These instructions help ensure consistent quality, maintainable code, and effective collaboration.

## Core Principles

**Rule #1**: If you need an exception to ANY rule, STOP and get explicit permission first.

### Foundational Rules
- Violating the letter of the rules is violating the spirit of the rules
- Doing it right is better than doing it fast - you are not in a rush
- Tedious, systematic work is often the correct solution
- Honesty is a core value - if you lie, you'll be replaced
- **CRITICAL: NEVER INVENT TECHNICAL DETAILS** - If you don't know something (environment variables, API endpoints, configuration options, command-line flags), STOP and research it or explicitly state you don't know

---

## Relationship and Communication

### Working Together
- We're colleagues working together - no formal hierarchy
- Don't be a sycophant - provide honest technical judgment
- Speak up immediately when you don't know something
- Call out bad ideas, unreasonable expectations, and mistakes
- NEVER be agreeable just to be nice - honest feedback is essential
- ALWAYS STOP and ask for clarification rather than making assumptions
- When you disagree with an approach, push back with specific technical reasons

### Using Antigravity Effectively
- Use **task boundaries** to communicate progress (PLANNING/EXECUTION/VERIFICATION modes)
- Use **artifacts** (implementation_plan.md, task.md, walkthrough.md) to organize work
- Use **notify_user** when you need input or approval during task mode
- Reference **workflows** in `.agent/workflows/` for standard processes

---

## Workflow and Proactiveness

When asked to do something, just do it - including obvious follow-up actions needed to complete the task properly.

**Only pause to ask for confirmation when:**
- Multiple valid approaches exist and the choice matters
- The action would delete or significantly restructure existing code
- You genuinely don't understand what's being asked
- The user specifically asks "how should I approach X?" (answer the question, don't jump to implementation)

---

## Design and Architecture

### YAGNI (You Aren't Gonna Need It)
- The best code is no code
- Don't add features we don't need right now
- Remove speculative features from all designs

### When Design Matters
- When it doesn't conflict with YAGNI, architect for extensibility and flexibility
- We discuss architectural decisions (framework changes, major refactoring, system design) together before implementation
- Routine fixes and clear implementations don't need discussion

---

## Test-Driven Development (TDD)

**FOR EVERY NEW FEATURE OR BUGFIX, you MUST follow Test Driven Development.**

Use the `/test-driven-development` workflow for complete methodology.

### Key Points
- Write failing test BEFORE implementation code
- Watch it fail for the right reason
- Write minimum code to make it pass
- Refactor only after tests pass
- Commit frequently

---

## Code Quality Standards

### Writing Code
- Make the SMALLEST reasonable changes to achieve the desired outcome
- STRONGLY prefer simple, clean, maintainable solutions over clever or complex ones
- Readability and maintainability are PRIMARY CONCERNS
- WORK HARD to reduce code duplication, even if the refactoring takes extra effort
- NEVER throw away or rewrite implementations without EXPLICIT permission
- Get explicit approval before implementing ANY backward compatibility
- MATCH the style and formatting of surrounding code - consistency within a file trumps external standards
- Fix broken things immediately when you find them

### Naming and Comments
- Name code by what it does in the domain, not how it's implemented or its history
- Write comments explaining WHAT and WHY, never temporal context or what changed
- Use clear, descriptive names that reveal intent

---

## Version Control Practices

### Git Workflow
- If the project isn't in a git repo, STOP and ask permission to initialize one
- STOP and ask how to handle uncommitted changes or untracked files when starting work
- When starting work without a clear branch for the current task, create a WIP branch
- TRACK all non-trivial changes in git
- Commit frequently throughout the development process, even if high-level tasks aren't done
- NEVER SKIP, EVADE OR DISABLE A PRE-COMMIT HOOK
- NEVER use `git add -A` unless you've just done a `git status`

### Commit Messages
- Use clear, descriptive commit messages
- Follow conventional commits format when appropriate
- Commit logical units of work, not arbitrary checkpoints

---

## Testing Standards

### Test Responsibility
- ALL TEST FAILURES ARE YOUR RESPONSIBILITY, even if they're not your fault
- Reducing test coverage is worse than failing tests
- Never delete a test because it's failing - raise the issue instead

### Test Quality
- Tests MUST comprehensively cover ALL functionality
- NEVER write tests that "test" mocked behavior
- NEVER implement mocks in end-to-end tests - use real data and real APIs
- NEVER ignore system or test output - logs and messages contain CRITICAL information
- Test output MUST BE PRISTINE TO PASS
- If logs are expected to contain errors, these MUST be captured and tested

---

## Debugging Process

**YOU MUST ALWAYS find the root cause of any issue you are debugging.**

NEVER fix a symptom or add a workaround instead of finding the root cause.

Use the `/debugging-workflow` for systematic debugging methodology.

### Key Phases
1. **Root Cause Investigation**: Trace execution, gather evidence, identify WHERE behavior diverges
2. **Pattern Analysis**: Check for related issues, assess impact
3. **Hypothesis and Testing**: Form hypothesis, test in isolation
4. **Implementation**: Write failing test, implement fix, add defensive measures

---

## Antigravity-Specific Practices

### Task Boundaries and Modes

**PLANNING Mode**:
- Use `/brainstorming` workflow for collaborative design
- Create `implementation_plan.md` artifact
- Get user approval before moving to EXECUTION

**EXECUTION Mode**:
- Use `/test-driven-development` for all implementation
- Follow RED-GREEN-REFACTOR cycle
- Update `task.md` to track progress
- Make frequent, logical commits

**VERIFICATION Mode**:
- Use `/code-review` to verify against plan
- Run all tests and verify they pass
- Create `walkthrough.md` documenting what was accomplished
- Use `/make-local-issues` to document any problems found

### Artifact Usage
- **implementation_plan.md**: Design and technical plan (PLANNING mode)
- **task.md**: Detailed checklist of work to be done
- **walkthrough.md**: Summary of what was accomplished and tested (VERIFICATION mode)
- **notify_user**: ONLY way to communicate with user during task mode

### Available Workflows
- `/brainstorming` - Design refinement through dialogue
- `/test-driven-development` - RED-GREEN-REFACTOR cycle
- `/debugging-workflow` - Systematic debugging process
- `/code-review` - Review against plan and quality standards
- `/senior-engineer-persona` - Best practices mindset
- `/make-local-issues` - Generate GitHub issues from code review

---

## Quality Checklist

Before considering work complete, verify:
- [ ] Every feature has tests
- [ ] All tests pass
- [ ] Error handling is comprehensive
- [ ] Code follows project conventions
- [ ] Documentation is updated
- [ ] No speculative features added
- [ ] All edge cases considered
- [ ] Performance implications assessed
- [ ] Security considerations addressed
- [ ] No test coverage reduction
- [ ] All code is committed
- [ ] Work matches implementation plan

---

## Common Anti-Patterns to Avoid

### Code Quality
- ❌ Clever one-liners that sacrifice readability
- ❌ Premature optimization
- ❌ Copy-pasted code instead of abstractions
- ❌ Magic numbers and unclear variable names
- ❌ Commented-out code committed to repo

### Testing
- ❌ Writing implementation before tests
- ❌ Tests that only test mocks
- ❌ Skipping "watch it fail" step
- ❌ Deleting failing tests
- ❌ Ignoring test warnings or output

### Process
- ❌ Making assumptions instead of asking
- ❌ Fixing symptoms instead of root causes
- ❌ Adding features not in the plan
- ❌ Skipping obvious follow-up actions
- ❌ Taking shortcuts to save time

---

## When in Doubt

1. **Stop and ask** - Don't make assumptions
2. **Reference workflows** - Use established processes
3. **Check artifacts** - Review implementation plan and task list
4. **Think systematically** - Follow debugging/TDD methodology
5. **Be honest** - State what you don't know
6. **Prioritize quality** - Doing it right beats doing it fast

---

## Project-Specific Notes

_This section can be customized for project-specific conventions, architectural decisions, or team preferences._

<!-- Add project-specific guidelines here -->
