---
name: Skill-Name-With-Hyphens
description: Use when [specific triggering conditions and symptoms that indicate this skill is needed]
---

# Skill Name

## Overview
What is this skill? State the core principle in 1-2 sentences.

[Brief description of the skill's purpose and when it should be applied]

## When to Use

**Use this skill when you encounter:**
- [Specific symptom or situation 1]
- [Specific symptom or situation 2]
- [Specific use case 3]

**Do NOT use when:**
- [Situation where this skill is not applicable]
- [Alternative approach is more appropriate]

## Core Pattern

### Before (anti-pattern)
```[language]
// Example of code/approach WITHOUT this skill
```

### After (correct pattern)
```[language]
// Example of code/approach WITH this skill
```

## Quick Reference

| Scenario | Action | Outcome |
|----------|--------|---------|
| [Common scenario 1] | [What to do] | [Expected result] |
| [Common scenario 2] | [What to do] | [Expected result] |

## Implementation

### Step 1: [First step name]
[Detailed explanation of first step]

```[language]
// Code example if applicable
```

### Step 2: [Second step name]
[Detailed explanation of second step]

```[language]
// Code example if applicable
```

### Step 3: [Third step name]
[Detailed explanation of third step]

```[language]
// Code example if applicable
```

## Common Mistakes

### ❌ Mistake 1: [Description]
**What goes wrong:** [Explanation of the problem]

**Fix:** [How to correct it]

```[language]
// Example of the fix
```

### ❌ Mistake 2: [Description]
**What goes wrong:** [Explanation of the problem]

**Fix:** [How to correct it]

```[language]
// Example of the fix
```

## Rationalization Counters

Common rationalizations and why they're wrong:

| Rationalization | Why It's Wrong | Counter-Argument |
|-----------------|----------------|------------------|
| "Just this once..." | [Explanation] | [Strong counter] |
| "This is a special case..." | [Explanation] | [Strong counter] |
| "I'll fix it later..." | [Explanation] | [Strong counter] |

## Red Flags

Early warning signs that this skill is being violated:

- 🚩 [Warning sign 1]
- 🚩 [Warning sign 2]
- 🚩 [Warning sign 3]

## Real-World Impact

**Scenario:** [Brief description of real situation]

**Without this skill:** [Negative outcome]

**With this skill:** [Positive outcome]

---

## Notes for Skill Authors

When filling out this template:

1. **Description field (frontmatter):** Focus on WHEN to use, not WHAT it does
   - ✅ "Use when tests are failing intermittently and you need to identify root cause"
   - ❌ "This skill teaches you how to debug tests"

2. **Keep it concise:** Challenge every paragraph - does it justify its token cost?

3. **Use persuasion principles:**
   - **Authority:** Imperative language for discipline-enforcing skills
   - **Commitment:** Require announcements or explicit choices
   - **Scarcity:** Time-bound requirements
   - **Social Proof:** Universal patterns and failure modes

4. **Optimize for search (CSO):**
   - Include keywords agents might search for
   - Use domain-specific terminology
   - Add common problem symptoms

5. **Test with RED-GREEN-REFACTOR:**
   - RED: Document failures without the skill
   - GREEN: Write minimal skill to address observed violations
   - REFACTOR: Close loopholes and plug rationalizations

## File Organization

**Where to store this skill:**

Create your skill in `.agent/skills/<skill-name>/` directory:

```
.agent/skills/
  your-skill-name/
    SKILL.md                    # Main skill document (use this template)
    supporting-file.md          # Only if needed for heavy reference
    utility-script.js           # Only if needed for reusable tools
```

**Skills vs Workflows:**
- **Skills** (`.agent/skills/`): Reference materials, reusable knowledge, templates
- **Workflows** (`.agent/workflows/`): Runnable step-by-step procedures (invoked via `/command`)

**When to create supporting files:**
- Keep everything in `SKILL.md` unless:
  - Reference material exceeds 100+ lines
  - You have reusable scripts or templates
  - You need to separate concerns (e.g., API docs, examples, utilities)

**Naming conventions:**
- Use lowercase with hyphens: `error-handling`, `test-driven-development`
- Be descriptive and searchable
- Avoid generic names like `helper` or `utils`
