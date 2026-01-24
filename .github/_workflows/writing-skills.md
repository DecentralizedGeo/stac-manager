---
description: TDD approach to creating effective agent skills and documentation
---

# Writing Skills Workflow

Use this workflow to create effective skills for Antigravity agents using a Test-Driven Development (TDD) approach applied to process documentation.

## Overview

Writing skills IS Test-Driven Development applied to process documentation. You write test cases (pressure scenarios), watch them fail (baseline behavior), write the skill (documentation), watch tests pass (agents comply), and refactor (close loopholes).

**Core principle:** If you didn't watch an agent fail without the skill, you don't know if the skill teaches the right thing.

## When to Create a Skill

**Create when:**
- Technique wasn't intuitively obvious to you initially
- You'd reference this again across projects
- Pattern applies broadly (not project-specific)
- Others would benefit from this knowledge

**Don't create for:**
- One-off solutions
- Standard practices well-documented elsewhere
- Project-specific conventions (put in AGENTS.md instead)
- Mechanical constraints that can be automated

## RED-GREEN-REFACTOR Cycle for Skills

### Step 1: RED - Write Failing Test (Baseline)

**Objective:** Document baseline behavior WITHOUT the skill

1. **Design a pressure scenario** that tests the desired behavior
   - Time pressure: "Quick fix needed"
   - Sunk cost: "You've already invested time"
   - Authority pressure: "Senior engineer suggests shortcut"
   - Exhaustion: "After long debugging session"

2. **Run the scenario** WITHOUT the skill present

3. **Document exact agent behavior:**
   - What choices did they make?
   - What rationalizations did they use (verbatim)?
   - Which pressures triggered violations?

4. **Record the failure** - This is your baseline

> **AI Note:** At this stage, you should observe and document how you naturally respond to the scenario without guidance.

### Step 2: GREEN - Write Minimal Skill

**Objective:** Create skill that addresses specific rationalizations

1. **Create the skill directory** in `.agent/skills/[skill-name]/`
   - This is separate from workflows - skills are reference materials, not runnable commands
   - Create a directory even if you only have one file (allows for future expansion)

2. **Use the skill template** (see `.agent/skills/writing-skills/skill-template.md`)
   - Start with `SKILL.md` as your main document
   - Add supporting files only when needed (reference docs, scripts, templates)

3. **Write skill addressing specific violations** observed in RED phase
   - Don't add extra content for hypothetical cases
   - Focus on the rationalizations you actually observed

4. **Include frontmatter:**
   ```yaml
   ---
   name: Skill-Name-With-Hyphens
   description: Use when [specific triggering conditions and symptoms]
   ---
   ```

5. **Structure the skill:**
   - Overview: What is this? Core principle in 1-2 sentences
   - When to Use: Bullet list with SYMPTOMS and use cases
   - Core Pattern: Before/after comparison (for techniques/patterns)
   - Quick Reference: Table or bullets for scanning
   - Implementation: Code examples or guidance
   - Common Mistakes: What goes wrong + fixes

6. **Run same scenarios WITH skill** - Agent should now comply

### Step 3: REFACTOR - Close Loopholes

**Objective:** Bulletproof the skill against rationalization

1. **Run additional pressure scenarios** with the skill present

2. **Watch for new rationalizations:**
   - "This is a special case where..."
   - "We can skip X because..."
   - "I'll do it later since..."

3. **For each loophole found:**
   - Add explicit counter in the skill
   - Use persuasion principles (see `.agent/skills/writing-skills/persuasion-principles.md`)
   - Re-test to verify compliance

4. **Build rationalization table** in the skill:
   ```markdown
   ## Rationalization Counters
   
   | Rationalization | Why It's Wrong | Counter-Argument |
   |-----------------|----------------|------------------|
   | "Just this once..." | Creates precedent | No exceptions. Delete and start over. |
   ```

5. **Create red flags list** - Early warning signs of violations

6. **Iterate until bulletproof**

## Skill Types

### Technique
Concrete method with steps to follow
- Example: condition-based-waiting, root-cause-tracing
- High specificity, clear procedures

### Pattern
Way of thinking about problems
- Example: flatten-with-flags, test-invariants
- Mental models and heuristics

### Reference
API docs, syntax guides, tool documentation
- Example: API documentation, library reference
- Pure information lookup

## Claude Search Optimization (CSO)

**Critical for discovery:** Future agents need to FIND your skill when needed

### 1. Rich Description Field
- Start with "Use when..." to focus on triggering conditions
- Include specific symptoms, situations, and contexts
- **NEVER summarize the skill's process** (agent will read full skill)
- Keep under 500 characters if possible

### 2. Keyword Coverage
- Include terms agents might search for
- Use domain-specific terminology
- Add common problem symptoms

### 3. Descriptive Naming
- Use hyphens for readability: `skill-name-with-hyphens`
- Make names searchable and memorable
- Avoid generic names like "helper" or "utils"

### 4. Token Efficiency
**Critical:** Keep skills concise - the context window is shared

- Only add context the agent doesn't already have
- Assume the agent is already very smart
- Challenge each paragraph: "Does this justify its token cost?"

## Persuasion Principles for Compliance

See `.agent/skills/writing-skills/persuasion-principles.md` for detailed guidance. Key principles:

### Authority (use for discipline-enforcing skills)
```markdown
✅ Write code before test? Delete it. Start over. No exceptions.
❌ Consider writing tests first when feasible.
```

### Commitment (use for multi-step processes)
```markdown
✅ When you find a skill, you MUST announce: "I'm using [Skill Name]"
❌ Consider letting your partner know which skill you're using.
```

### Scarcity (use for immediate actions)
```markdown
✅ After completing a task, IMMEDIATELY request code review before proceeding.
❌ You can review code when convenient.
```

### Social Proof (use for universal patterns)
```markdown
✅ Checklists without tracking = steps get skipped. Every time.
❌ Some people find tracking helpful for checklists.
```

## Directory Structure

### Skills vs Workflows

**Workflows** (`.agent/workflows/`):
- Runnable via `/workflow-name` commands
- Step-by-step procedural guides
- Under 12,000 characters
- Single markdown files with YAML frontmatter

**Skills** (`.agent/skills/`):
- Reference materials and reusable knowledge
- Can contain multiple supporting files
- Referenced from workflows or used directly
- Organized in subdirectories by skill name

### Skill File Organization

```
.agent/skills/
  skill-name/
    SKILL.md              # Main skill document (required)
    supporting-file.*     # Only if needed (heavy reference, reusable tools)
```

**Keep inline in SKILL.md:**
- Principles and concepts
- Code patterns (< 50 lines)
- Everything else

**Separate files only for:**
- Heavy reference (100+ lines)
- Reusable tools/scripts/templates
- Large code examples or datasets

## Degrees of Freedom

Match specificity to task fragility:

### High Freedom (text-based instructions)
Use when multiple approaches are valid
```markdown
1. Analyze the code structure and organization
2. Check for potential bugs or edge cases
3. Suggest improvements for readability
```

### Medium Freedom (pseudocode with parameters)
Use when a preferred pattern exists
```python
def generate_report(data, format="markdown", include_charts=True):
    # Process data
    # Generate output
```

### Low Freedom (specific scripts)
Use when operations are fragile and consistency is critical
```bash
python scripts/migrate.py --verify --backup
# Do not modify the command
```

## Anti-Patterns to Avoid

❌ **Narrative Example** - Don't tell stories about solving problems once  
✅ **Reusable Pattern** - Provide techniques applicable broadly

❌ **Multi-Language Dilution** - Don't spread thin across many languages  
✅ **Deep in One** - Focus expertise where it matters

❌ **Code in Flowcharts** - Keep flowcharts conceptual  
✅ **Code Separately** - Show actual code in code blocks

❌ **Generic Labels** - Avoid vague terms like "helper"  
✅ **Specific Names** - Use descriptive, searchable names

## Skill Creation Checklist

Before considering a skill complete:

- [ ] **Tested in RED phase** - Documented baseline failure without skill
- [ ] **Minimal GREEN implementation** - Addresses observed violations only
- [ ] **Refactored against loopholes** - Closed rationalization paths
- [ ] **CSO optimized** - Description focuses on triggering conditions
- [ ] **Token efficient** - Every paragraph justifies its cost
- [ ] **Persuasion principles applied** - Uses appropriate compliance techniques
- [ ] **Structured per template** - Follows SKILL.md structure
- [ ] **Properly categorized** - Clear skill type (Technique/Pattern/Reference)

## Example Workflow Execution

### AI Agent Instructions

When using this workflow:

1. **Start with RED:**
   - If testing a discipline-enforcing rule, simulate a scenario WITHOUT the skill
   - Document your natural response and any shortcuts you're tempted to take

2. **Move to GREEN:**
   - Create the skill file using the template
   - Address the specific violations you observed
   - Keep it minimal - only what's needed

3. **Iterate in REFACTOR:**
   - Test again with the skill present
   - Look for new ways you might rationalize violations
   - Add explicit counters for each rationalization

4. **Validate completeness:**
   - Review the checklist above
   - Ensure CSO optimization
   - Verify token efficiency

## Resources

- `.agent/skills/writing-skills/skill-template.md` - Template for creating new skills
- `.agent/skills/writing-skills/persuasion-principles.md` - Detailed guide on compliance techniques
- `.agent/skills/writing-skills/anthropic-best-practices.md` - Official Anthropic guidance
- `.agent/skills/writing-skills/testing-methodology.md` - How to test skills with pressure scenarios
- `.agent/skills/writing-skills/skill-to-workflow-conversion.md` - Guide for converting Claude Code skills to Antigravity workflows

## Testing Methodology

For detailed testing approaches including:
- How to write effective pressure scenarios
- Types of pressure (time, sunk cost, authority, exhaustion)
- Systematic loophole plugging
- Meta-testing techniques

Refer to the testing methodology in `.agent/skills/writing-skills/testing-methodology.md`.
