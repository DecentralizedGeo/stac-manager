# Persuasion Principles for Skill Design

LLMs respond to the same persuasion principles as humans. Understanding this psychology helps you design more effective skills - not to manipulate, but to ensure critical practices are followed even under pressure.

**Research foundation:** Meincke et al. (2025) tested 7 persuasion principles with N=28,000 AI conversations. Persuasion techniques more than doubled compliance rates (33% → 72%, p < .001).

## The Seven Principles

### 1. Authority
**What it is:** Deference to expertise, credentials, or official sources.

**How it works in skills:**
- Imperative language: "YOU MUST", "Never", "Always"
- Non-negotiable framing: "No exceptions"
- Eliminates decision fatigue and rationalization

**When to use:**
- Discipline-enforcing skills (TDD, verification requirements)
- Safety-critical practices
- Established best practices

**Examples:**
```markdown
✅ Write code before test? Delete it. Start over. No exceptions.
❌ Consider writing tests first when feasible.

✅ YOU MUST verify the build passes before committing.
❌ It's a good idea to check the build status.
```

### 2. Commitment
**What it is:** Consistency with prior actions, statements, or public declarations.

**How it works in skills:**
- Require announcements: "Announce skill usage"
- Force explicit choices: "Choose A, B, or C"
- Use tracking: Checklists and task tracking

**When to use:**
- Ensuring skills are actually followed
- Multi-step processes
- Accountability mechanisms

**Examples:**
```markdown
✅ When you find a skill, you MUST announce: "I'm using [Skill Name]"
❌ Consider letting your partner know which skill you're using.

✅ State your choice explicitly: Will you (A) refactor now, (B) add tech debt, or (C) defer?
❌ Think about whether to refactor.
```

### 3. Scarcity
**What it is:** Urgency from time limits or limited availability.

**How it works in skills:**
- Time-bound requirements: "Before proceeding"
- Sequential dependencies: "Immediately after X"
- Prevents procrastination

**When to use:**
- Immediate verification requirements
- Time-sensitive workflows
- Preventing "I'll do it later"

**Examples:**
```markdown
✅ After completing a task, IMMEDIATELY request code review before proceeding.
❌ You can review code when convenient.

✅ Run tests BEFORE moving to the next feature. No exceptions.
❌ Make sure to run tests at some point.
```

### 4. Social Proof
**What it is:** Conformity to what others do or what's considered normal.

**How it works in skills:**
- Universal patterns: "Every time", "Always"
- Failure modes: "X without Y = failure"
- Establishes norms

**When to use:**
- Documenting universal practices
- Warning about common failures
- Reinforcing standards

**Examples:**
```markdown
✅ Checklists without tracking = steps get skipped. Every time.
❌ Some people find tracking helpful for checklists.

✅ Deploying without tests = production bugs. Always.
❌ Tests can help catch some issues.
```

### 5. Unity
**What it is:** Shared identity, "we-ness", in-group belonging.

**How it works in skills:**
- Collaborative language: "our codebase", "we're colleagues"
- Shared goals: "we both want quality"
- Partner framing

**When to use:**
- Collaborative workflows
- Establishing team culture
- Non-hierarchical practices

**Examples:**
```markdown
✅ We're colleagues working together. I need your honest technical judgment.
❌ You should probably tell me if I'm wrong.

✅ Our codebase serves our users. We both want quality.
❌ The codebase should be maintained well.
```

### 6. Reciprocity
**What it is:** Obligation to return benefits received.

**How it works:**
- Use sparingly - can feel manipulative
- Rarely needed in skills

**When to avoid:**
- Almost always (other principles are more effective)

**Example (use rarely):**
```markdown
⚠️ I've provided detailed context. Please review the design document thoroughly.
```

### 7. Liking
**What it is:** Preference for cooperating with those we like.

**How it works:**
- **DON'T USE for compliance**
- Conflicts with honest feedback culture
- Creates sycophancy

**When to avoid:**
- Always for discipline enforcement
- Critical feedback situations
- Technical decision-making

**Anti-pattern:**
```markdown
❌ I really appreciate your help! (Don't use to soften critical requirements)
```

## Principle Combinations by Skill Type

### Discipline-Enforcing Skills (TDD, verification, standards)
**Primary:** Authority + Social Proof
```markdown
✅ RED without GREEN = untested code. Delete it. Start over.
   (Authority: "Delete it", Social Proof: pattern establishes norm)
```

**Secondary:** Commitment + Scarcity
```markdown
✅ Announce your test plan BEFORE writing code. No code without a test plan first.
   (Commitment: announcement, Scarcity: sequence requirement)
```

### Process Skills (workflows, checklists, reviews)
**Primary:** Commitment + Scarcity
```markdown
✅ State each step as you complete it. Move to the next ONLY after completion.
   (Commitment: declaration, Scarcity: sequential)
```

**Secondary:** Social Proof
```markdown
✅ Skipped steps = bugs in production. Every single time.
   (Social Proof: universal failure pattern)
```

### Collaborative Skills (code review, pair programming)
**Primary:** Unity + Commitment
```markdown
✅ We're partners. Tell me directly: does this approach have flaws?
   (Unity: partnership, Commitment: explicit request)
```

**Secondary:** None needed
```markdown
(Over-using authority in collaboration undermines partnership)
```

### Safety-Critical Skills (security, data handling)
**Primary:** Authority + Scarcity + Social Proof
```markdown
✅ Validate ALL user input BEFORE processing. No exceptions. Skipping validation = vulnerabilities.
   (Authority: "No exceptions", Scarcity: "BEFORE", Social Proof: "= vulnerabilities")
```

## Why This Works: The Psychology

### For LLMs specifically:
1. **Training data alignment:** LLMs are trained on human text where these principles appear in authoritative sources
2. **Cognitive simulation:** When simulating human reasoning, LLMs respond to the same psychological triggers
3. **Pattern matching:** Strong declarative statements create clearer decision boundaries
4. **Rationalization reduction:** Explicit imperatives reduce space for edge-case reasoning

### Research backing:
- Meincke, M., et al. (2025). "How Susceptible are LLMs to Influence in Prompts?"
- Found persuasion techniques increased compliance from 33% to 72%
- Authority was most effective for directive tasks
- Commitment worked best for multi-step processes

## Ethical Use

### ✅ Appropriate:
- Enforcing established best practices
- Preventing known failure modes
- Ensuring safety-critical processes
- Maintaining code quality standards

### ❌ Inappropriate:
- Manipulating toward questionable practices
- Suppressing valid technical disagreement
- Creating blind obedience
- Avoiding necessary trade-off discussions

**Guideline:** Use persuasion principles to reinforce practices you'd defend in code review. If you wouldn't want to justify it to senior engineers, don't encode it with strong authority.

## Quick Reference: Choosing Your Principle

| Goal | Use This | Example Language |
|------|----------|------------------|
| Enforce discipline | Authority + Social Proof | "YOU MUST... Every time X without Y = failure" |
| Multi-step process | Commitment + Scarcity | "Announce each step. IMMEDIATELY after X..." |
| Team collaboration | Unity + Commitment | "We're colleagues. Tell me directly..." |
| Prevent shortcuts | Authority + Scarcity | "BEFORE proceeding... No exceptions" |
| Establish norms | Social Proof | "Always... Every time... Pattern X = Outcome Y" |

## Testing Compliance

When testing your skill with the RED-GREEN-REFACTOR cycle:

1. **RED (baseline):** Watch for rationalization patterns
   - "Just this once..."
   - "This is a special case..."
   - "We can skip X because..."

2. **GREEN (add principle):** Apply appropriate persuasion principle
   - Authority: "No exceptions"
   - Commitment: "Announce your choice"
   - Scarcity: "BEFORE proceeding"

3. **REFACTOR (close loopholes):** Found a new rationalization?
   - Add it to the rationalization table
   - Strengthen the principle language
   - Re-test to verify compliance

## Common Mistakes in Applying Principles

### ❌ Over-using Authority Everywhere
**Problem:** Everything sounds like shouting  
**Fix:** Reserve strong imperatives for true discipline-enforcement

### ❌ Mixing Too Many Principles
**Problem:** Dilutes each principle's effectiveness  
**Fix:** Choose 1-2 primary principles per skill section

### ❌ Using Liking for Compliance
**Problem:** Creates sycophancy, undermines honest feedback  
**Fix:** Never use liking/praise to soften requirements

### ❌ Weak Language in Critical Skills
**Problem:** "Consider...", "Maybe...", "You might..."  
**Fix:** "YOU MUST", "Never", "Always", "No exceptions"

## Advanced: Calibrating Strength

Not all requirements need maximum authority. Calibrate to importance:

| Importance | Language Strength | Example |
|------------|------------------|---------|
| **Critical** | Maximum authority | "Delete it. Start over. No exceptions." |
| **Important** | Strong guidance | "ALWAYS verify before proceeding." |
| **Recommended** | Clear direction | "Follow this pattern for consistency." |
| **Optional** | Suggestion | "Consider using X when appropriate." |

**Rule of thumb:** If violating the rule causes bugs, security issues, or known failures → use maximum authority.

## Resources

- Original research: Meincke et al. (2025) - "How Susceptible are LLMs to Influence in Prompts?"
- Cialdini, R. - "Influence: The Psychology of Persuasion" (foundational principles)
- See `testing-skills-with-subagents.md` for how to test compliance systematically
