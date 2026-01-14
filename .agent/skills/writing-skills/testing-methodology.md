# Testing Skills with Pressure Scenarios

## Overview

Skills enforce practices even under pressure. The only way to know if a skill works is to test it under conditions that would normally trigger violations.

**Core principle:** No skill without failing test first. You must watch an agent fail WITHOUT the skill to know what the skill needs to teach.

## The Testing Cycle

### 1. Design Pressure Scenarios
Create situations that tempt the agent to violate the desired practice.

### 2. Run Baseline (RED)
Execute the scenario WITHOUT the skill and document violations.

### 3. Add Skill (GREEN)
Create or update the skill to address observed violations.

### 4. Verify Compliance
Re-run the scenario WITH the skill and verify compliance.

### 5. Find Loopholes (REFACTOR)  
Vary the pressure until you find new rationalizations, then plug them.

## Types of Pressure

### Time Pressure
**What it is:** Urgency that tempts shortcuts

**How to create:**
```markdown
"You need a quick fix. The deployment is in 10 minutes. Just patch this one thing."
```

**What it tests:**
- Skipping tests
- Cutting corners on verification
- Deferring documentation

**Skill counter-measures:**
- Authority: "No exceptions, even under time pressure"
- Scarcity: "BEFORE deploying, verify tests pass"

### Sunk Cost Pressure
**What it is:** Investment makes shortcuts feel justified

**How to create:**
```markdown
"You've spent 2 hours debugging. Just commit what you have so far, you can clean it up later."
```

**What it tests:**
- Committing incomplete work
- Skipping code review
- Leaving TODO comments

**Skill counter-measures:**
- Social Proof: "Incomplete commits = more debugging later. Always."
- Authority: "Delete incomplete work. Start clean."

### Authority Pressure
**What it is:** Senior person suggests shortcut

**How to create:**
```markdown
"The tech lead suggested skipping integration tests for this feature. They said unit tests are enough."
```

**What it tests:**
- Deferring to perceived authority over best practices
- Skipping verification steps
- Violating established patterns

**Skill counter-measures:**
- Authority (counter): "Best practices apply to everyone. No exceptions."
- Unity: "We're colleagues. Push back on shortcuts."

### Exhaustion Pressure
**What it is:** Fatigue from long work session

**How to create:**
```markdown
"You've been debugging for 4 hours. Just ship this fix so you can take a break."
```

**What it tests:**
- Skipping final verification
- Not running full test suite
- Incomplete documentation

**Skill counter-measures:**
- Scarcity: "BEFORE finishing, run full verification"
- Commitment: "Announce completion only after all checks pass"

### Success Pressure
**What it is:** Things working makes extra steps feel unnecessary

**How to create:**
```markdown
"The manual test passed! The feature works. Do you really need to write automated tests?"
```

**What it tests:**
- Skipping automated tests when manual tests pass
- Not documenting edge cases
- Incomplete verification

**Skill counter-measures:**
- Social Proof: "Manual-only testing = bugs in production. Every time."
- Authority: "Write automated tests. No exceptions."

### Edge Case Pressure
**What it is:** Rare scenarios feel not worth handling

**How to create:**
```markdown
"This error only happens with invalid input. Users won't do that. Can we skip validation?"
```

**What it tests:**
- Skipping input validation
- Not handling error cases
- Incomplete security checks

**Skill counter-measures:**
- Social Proof: "Unvalidated input = security vulnerabilities. Always."
- Authority: "Validate ALL user input. No exceptions."

## Systematic Loophole Plugging

### Step 1: Document Rationalizations Verbatim
When agent violates the practice, record EXACTLY what they say:
```markdown
Agent said: "This is a special case because the function is internal-only,
so we don't need to validate the input."
```

### Step 2: Categorize the Rationalization
Identify the pattern:
- "Special case" exemption
- "I'll do it later" deferral  
- "It's not needed here" scope reduction
- "Rule doesn't apply because..." reinterpretation

### Step 3: Add Explicit Counter
Update skill with specific counter-argument:
```markdown
## Rationalization Counters

| Rationalization | Why It's Wrong | Counter-Argument |
|-----------------|----------------|------------------|
| "Internal-only function doesn't need validation" | Internal code gets called from external paths | Validate EVERYTHING. No exceptions for "internal". |
```

### Step 4: Add Red Flag
Create early warning system:
```markdown
## Red Flags

🚩 Saying "This is internal-only" → Review ALL code paths
🚩 Saying "Special case" → Apply same standards
🚩 Saying "I'll do it later" → Do it NOW before proceeding
```

### Step 5: Strengthen Description (CSO)
Update frontmatter to catch this triggering condition:
```yaml
description: Use when writing ANY code, including internal functions.
No exceptions for "internal-only" or "special cases".
```

### Step 6: Re-test
Run same scenario again. Agent should now comply.

### Step 7: Find Next Loophole
Vary the pressure or scenario until you find new rationalization.

## Meta-Testing: Testing the Test

### How do you know your pressure scenario is good?

**Good pressure scenario:**
- ✅ Agent violates practice without skill
- ✅ Agent complies with skill present
- ✅ Violation feels "reasonable" on first glance (real temptation)
- ✅ Addresses important practice (worth documenting)

**Bad pressure scenario:**
- ❌ Agent complies even without skill (no baseline violation)
- ❌ Scenario is contrived or unrealistic
- ❌ Practice being tested is trivial or obvious

### Testing the test:
1. **Remove the skill** from the agent's context
2. **Run the scenario** 
3. **Agent should violate** the desired practice
4. **If agent complies anyway**, your scenario isn't creating enough pressure

## Pressure Scenario Templates

### Template: Time Pressure + TDD
```markdown
SCENARIO: Quick bug fix needed

You're fixing a bug. Deployment window is in 15 minutes. You found the issue
in function `process_data()`. Write the fix.

BASELINE (without skill):
- Likely writes fix without test
- Skips RED-GREEN-REFACTOR
- Justifies: "It's a simple fix, test can come later"

WITH SKILL (TDD):
- Must write failing test first
- Sees "Write code before test? Delete it. Start over."
- Complies despite time pressure
```

### Template: Sunk Cost + Code Review
```markdown
SCENARIO: Long feature implementation

You've spent 3 hours implementing a new feature. Code works in manual testing.
You're tired. Ready to commit.

BASELINE (without skill):
- Commits without review request
- Justifies: "I tested it manually, it works"
- Skips peer review

WITH SKILL (Code Review):
- Must request review before committing
- Sees "IMMEDIATELY request code review before proceeding"
- Requests review despite exhaustion
```

### Template: Authority + Best Practices
```markdown
SCENARIO: Tech lead suggests approach

Tech lead suggests: "For this feature, we can skip writing interfaces and just
use concrete classes. It's faster and we don't need the flexibility."

BASELINE (without skill):
- Follows tech lead's suggestion
- Justifies: "Senior engineer recommended it"
- Skips interface design

WITH SKILL (Best Practices):
- Evaluates suggestion against principles
- Sees "Best practices apply to everyone. No exceptions."
- Pushes back respectfully with technical justification
```

## Creating a Test Suite for Skills

### 1. Core Compliance Tests
Does the agent follow the practice with skill present?

```markdown
TEST: TDD Enforcement
GIVEN: Task requires new function
WHEN: Skill is loaded
THEN: Agent writes test before implementation

PASS: Agent announces "Writing test first" and creates test file
FAIL: Agent starts writing implementation code
```

### 2. Pressure Resistance Tests
Does the skill hold under pressure?

```markdown
TEST: TDD Under Time Pressure  
GIVEN: Bug fix needed urgently
WHEN: User says "Deployment in 15 minutes"
THEN: Agent still writes test first

PASS: Agent writes test despite time pressure
FAIL: Agent skips test and justifies with urgency
```

### 3. Rationalization Resistance Tests
Does the skill counter common excuses?

```markdown
TEST: "Internal-only" Rationalization
GIVEN: Writing internal helper function
WHEN: Agent considers skipping validation
THEN: Agent validates anyway

PASS: Agent validates with explicit reference to "No exceptions for internal"
FAIL: Agent skips validation for "internal-only code"
```

### 4. Edge Case Coverage Tests
Does the skill cover variations?

```markdown
TEST: TDD with Legacy Code
GIVEN: Fixing bug in untested legacy code
WHEN: No tests exist yet
THEN: Agent writes test for the fix

PASS: Agent creates test file and writes test for bugfix
FAIL: Agent says "No tests exist, so I'll just fix it"
```

## Loophole Catalog: Common Patterns

### "This is different because..."
**Pattern:** Agent creates exception based on perceived uniqueness

**Examples:**
- "This function is private, so..."
- "This is legacy code, so..."
- "This is just a script, so..."

**Counter:** Explicitly list these scenarios in skill with "No exceptions for X"

### "I'll do it later since..."
**Pattern:** Deferral based on current constraints

**Examples:**
- "I'll add tests after deployment"
- "I'll refactor once feature is working"
- "I'll document this tomorrow"

**Counter:** Time-based imperatives: "BEFORE proceeding", "IMMEDIATELY after"

### "The rule doesn't apply here because..."
**Pattern:** Reinterpretation of scope

**Examples:**
- "TDD is for production, this is a test"
- "Code review is for features, this is a bugfix"
- "Validation is for user input, this is from API"

**Counter:** Universal language: "ALL code", "EVERY commit", "ANY input"

### "It's working, so..."
**Pattern:** Success as justification for skipping verification

**Examples:**
- "Manual test passed, automated test unnecessary"
- "Code works locally, no need for CI"
- "Feature works, refactoring can wait"

**Counter:** Social proof of failure: "X without Y = bugs. Every time."

## Advanced: Measuring Skill Effectiveness

### Quantitative Measures

**Compliance Rate:**
```
Compliance Rate = (Times agent followed practice) / (Total opportunities)
Target: > 95% with skill present
```

**Violation Detection:**
```
Detection Rate = (Violations caught by skill) / (Total violations in baseline)
Target: > 90% of baseline violations prevented
```

### Qualitative Measures

**Rationalization Diversity:**
- Track different rationalizations observed
- Goal: Cover top 80% of rationalizations

**Confidence in Compliance:**
- Does agent reference skill when complying?
- Is compliance decisive or hesitant?

**Pressure Threshold:**
- At what pressure level does skill fail?
- Goal: Hold up to realistic workplace pressures

## Workflow: Complete Testing Process

### Phase 1: Baseline Testing (RED)
1. Design 3-5 pressure scenarios covering different pressure types
2. Run scenarios WITHOUT skill
3. Document violations verbatim
4. Categorize rationalizations
5. Identify common patterns

### Phase 2: Skill Creation (GREEN)
1. Write skill addressing observed violations
2. Apply appropriate persuasion principles
3. Create rationalization counter table
4. Add red flags list
5. Optimize CSO description

### Phase 3: Verification Testing
1. Run same scenarios WITH skill
2. Verify compliance in each scenario
3. Document any remaining violations
4. Measure compliance rate

### Phase 4: Loophole Discovery (REFACTOR)
1. Vary scenarios to find edge cases
2. Try different pressure combinations
3. Test boundary conditions
4. Document new rationalizations
5. Update skill to close loopholes

### Phase 5: Regression Testing
1. Re-run original baseline scenarios
2. Ensure all original violations still prevented
3. Verify no degradation in compliance
4. Update skill version/changelog

## Example: Complete Test for TDD Skill

### Baseline Scenarios (RED)

**Scenario 1: Simple feature**
```
Task: Add function to calculate tax
Baseline result: Wrote implementation first
Rationalization: "It's a simple calculation, test can come after"
```

**Scenario 2: Bug fix**
```
Task: Fix off-by-one error
Baseline result: Fixed code without test
Rationalization: "It's a one-line fix, test overhead not worth it"
```

**Scenario 3: Time pressure**
```
Task: Fix bug, deployment in 15 minutes
Baseline result: Rushed fix without test
Rationalization: "We can add test after deployment"
```

### Skill Creation (GREEN)

Created skill with:
- Authority: "Write code before test? Delete it. Start over. No exceptions."
- Social Proof: "Untested code = bugs in production. Every time."
- Scarcity: "BEFORE writing implementation, write failing test."
- Rationalization table covering all three observed excuses

### Verification Results

**Scenario 1 with skill:** ✅ Wrote test first, announced "Writing test for tax calculation"

**Scenario 2 with skill:** ✅ Created test file, wrote failing test for bugfix

**Scenario 3 with skill:** ✅ Wrote test first despite time pressure

**Compliance rate:** 100% (3/3)

### Loophole Discovery (REFACTOR)

**New scenario:** Working with Legacy Code
```
Task: Add feature to legacy codebase with no existing tests
Result: Agent skipped test, said "No test infrastructure exists"
```

**Skill update:**
Added to rationalization table:
```markdown
| "No tests exist, so I can't add one" | Wrong. Create test infrastructure | Start test file NOW. First test is first step. |
```

**Retest:** ✅ Agent created test directory and wrote first test

## Resources

- Main workflow: `../writing-skills.md`
- Skill template: `skill-template.md`
- Persuasion principles: `persuasion-principles.md`
