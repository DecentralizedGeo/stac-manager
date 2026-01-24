# Writing Skills - Workflow and Reference Materials

This directory contains a comprehensive workflow and supporting materials for creating effective agent skills using Test-Driven Development (TDD) principles.

## Overview

The Writing Skills workflow applies TDD to process documentation. You test skills with pressure scenarios, document failures, write minimal skills to address violations, and iteratively close loopholes through the RED-GREEN-REFACTOR cycle.

## Files in This Directory

### Main Re Workflow
- **`../workflows/writing-skills.md`** - The primary workflow file (accessible via `/writing-skills`)

### Reference Materials  
All reference materials are in `.agent/skills/writing-skills/`:
- **`skill-template.md`** - Template for creating new skill documents with proper structure
- **`persuasion-principles.md`** - Guide to using psychological principles for ensuring agent compliance
- **`testing-methodology.md`** - Comprehensive guide to testing skills with pressure scenarios
- **`anthropic-best-practices.md`** - Official Anthropic guidance on skill authoring

## Quick Start

1. **Read the main workflow:** Start with `/writing-skills` to understand the TDD approach
2. **Review the template:** Look at `skill-template.md` to see the structure
3. **Learn persuasion principles:** Read `persuasion-principles.md` to understand compliance techniques
4. **Understand testing:** Read `testing-methodology.md` to learn how to test skills under pressure

## Core Concepts

### RED-GREEN-REFACTOR for Skills

**RED:** Run pressure scenarios WITHOUT the skill, document violations
**GREEN:** Write minimal skill addressing observed violations  
**REFACTOR:** Close loopholes by testing variations and adding explicit counters

### Claude Search Optimization (CSO)

Skills must be discoverable. Optimize for agent search by:
- Writing descriptions focused on WHEN to use (triggering conditions)
- Including specific symptoms and scenarios
- Using searchable, descriptive names
- Keeping content token-efficient

### Persuasion Principles

Apply research-backed techniques for compliance:
- **Authority:** Imperative language for discipline-enforcing skills
- **Commitment:** Require announcements or explicit choices
- **Scarcity:** Time-bound requirements
- **Social Proof:** Universal patterns and failure modes

## Usage in Antigravity

These materials have been adapted for Google Antigravity's autonomous Agent mode from the [superpowers repository](https://github.com/obra/superpowers/tree/main/skills/writing-skills).

### Integration Points

**Workflows:** Main workflow at `.agent/workflows/writing-skills.md`  
**Skills:** Reference materials and templates in `.agent/skills/writing-skills/`  
**Agents:** Reference in `.agent/AGENTS.md` for agent-specific configurations  
**Projects:** Use for project-specific conventions and patterns

### Key Adaptations

- Adapted file paths for Antigravity's `.agent/workflows` structure
- Integrated with Antigravity's task and artifact workflow
- Added references to Antigravity-specific tools and concepts
- Maintained compatibility with TDD and testing workflows

## Best Practices

1. **Always test in RED phase first** - Document baseline failures before writing skill
2. **Keep skills concise** - Challenge every paragraph's token cost
3. **Use appropriate persuasion** - Match principle strength to requirement importance
4. **Iterate based on loopholes** - Watch for new rationalizations and plug them
5. **Optimize for discovery** - Focus descriptions on triggering conditions

## Resources

- **Original source:** [obra/superpowers - writing-skills](https://github.com/obra/superpowers/tree/main/skills/writing-skills)
- **Related workflows:** 
  - `/test-driven-development` - TDD workflow for code
  - `/debugging-workflow` - Root cause debugging approach
  - `/code-review` - Code review process

## Creating Your First Skill

1. **Identify a practice** worth enforcing (see "When to Create a Skill" in main workflow)
2. **Design pressure scenarios** that would tempt violations (time, sunk cost, authority, etc.)
3. **Run baseline (RED):** Test without skill, document exact rationalizations
4. **Create skill (GREEN):** Use `skill-template.md`, address observed violations
5. **Test and refactor:** Re-run scenarios, find loopholes, add explicit counters
6. **Verify completeness:** Use checklist in main workflow

## Contributing

When adding new reference materials:
- Place in this `writing-skills/` directory
- Update this README with file description
- Link from main workflow where relevant
- Follow CSO principles in naming and structure

---

**Created:** 2026-01-13  
**Source:** Superpowers repository by @obra  
**Adapted for:** Google Antigravity autonomous Agent mode
