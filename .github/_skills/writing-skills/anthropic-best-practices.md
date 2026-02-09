# Anthropic Best Practices for Skill Authoring

> Official guidance from Anthropic on writing effective Skills that agents can discover and use successfully.

## Core Principles

### Concise is Key

The context window is a public good shared between:
- System prompt
- Conversation history  
- Other skills' metadata
- Your actual request

**Default assumption:** The agent is already very smart.

Only add context the agent doesn't already have. Challenge each piece of information:
- "Does the agent really need this explanation?"
- "Can I assume the agent knows this?"
- "Does this paragraph justify its token cost?"

**Good example (concise):**
````markdown
## Extract PDF text

Use pdfplumber for text extraction:

```python
import pdfplumber

with pdfplumber.open("file.pdf") as pdf:
    text = pdf.pages[0].extract_text()
```
````

**Bad example (verbose):**
```markdown
## Extract PDF text

PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available for PDF processing, but we
recommend pdfplumber because it's easy to use and handles most cases well.
First, you'll need to install it using pip. Then you can use the code below...
```

### Set Appropriate Degrees of Freedom

Match the level of specificity to the task's fragility and variability.

#### High Freedom (text-based instructions)
Use when multiple approaches are valid, decisions depend on context, or heuristics guide the approach.

```markdown
## Code review process

1. Analyze the code structure and organization
2. Check for potential bugs or edge cases
3. Suggest improvements for readability and maintainability
4. Verify adherence to project conventions
```

#### Medium Freedom (pseudocode with parameters)
Use when a preferred pattern exists, some variation is acceptable, or configuration affects behavior.

````markdown
## Generate report

Use this template and customize as needed:

```python
def generate_report(data, format="markdown", include_charts=True):
    # Process data
    # Generate output in specified format
    # Optionally include visualizations
```
````

#### Low Freedom (specific scripts)
Use when operations are fragile and error-prone, consistency is critical, or a specific sequence must be followed.

````markdown
## Database migration

Run exactly this script:

```bash
python scripts/migrate.py --verify --backup
```

Do not modify the command or add additional flags.
````

**Analogy:** Think of the agent as a robot exploring a path:
- **Narrow bridge with cliffs:** Only one safe way forward → Provide specific guardrails (low freedom)
- **Open field, no hazards:** Many paths lead to success → Give general direction (high freedom)

### Test with All Models

Skills act as additions to models, so effectiveness depends on the underlying model.

**Testing considerations:**
- **Haiku** (fast, economical): Does the skill provide enough guidance?
- **Sonnet** (balanced): Is the skill clear and efficient?
- **Opus** (powerful): Does the skill avoid over-explaining?

## Skill Structure

### Naming Conventions

**File naming:**
- Use descriptive, searchable names
- Avoid generic terms like "helper" or "utils"
- Use hyphens for multi-word names: `code-review-checklist`

**Frontmatter naming (YAML):**
- `name`: Letters, numbers, and hyphens only (no special characters)
- Keep it concise but descriptive

### Writing Effective Descriptions

The description field is CRITICAL for discovery.

**Focus on triggering conditions:**
```yaml
# ✅ Good - describes WHEN to use
description: Use when tests are failing intermittently and you need to identify root cause

# ❌ Bad - describes WHAT it does
description: This skill teaches you how to debug tests
```

**Include specific symptoms:**
```yaml
# ✅ Good - concrete symptoms
description: Use when seeing "connection refused" errors in CI but tests pass locally

# ❌ Bad - too generic
description: Use for debugging connection issues
```

**Keep it under 500 characters** for token efficiency.

### Progressive Disclosure Patterns

Structure information from high-level to detailed:

```markdown
# Skill Name

## Quick Start
[Minimal example to get started immediately]

## Common Use Cases
[Bullets for typical scenarios]

## Detailed Guide
[Deep dive for complex cases]

## Advanced Options
[Edge cases and special configurations]
```

**Avoid deeply nested references.** If you need extensive reference material (100+ lines), create a separate file.

**Use table of contents for longer files:**
```markdown
# API Reference

## Contents
- [Authentication](#authentication)
- [Endpoints](#endpoints)
- [Error Handling](#error-handling)

## Authentication
...
```

## Workflows and Feedback Loops

### Use Workflows for Complex Tasks

Break multi-step processes into clear phases:

```markdown
## Deployment Workflow

### Phase 1: Pre-deployment Checks
1. Run full test suite
2. Verify build passes
3. Check for breaking changes

### Phase 2: Deployment
1. Deploy to staging
2. Run smoke tests
3. Deploy to production

### Phase 3: Post-deployment
1. Monitor error rates
2. Verify key metrics
3. Update changelog
```

### Implement Feedback Loops

Build verification steps into processes:

```markdown
## Code Review Process

1. Submit code for review
2. **WAIT for review feedback**
3. Address all comments
4. **Request re-review if changes substantial**
5. Only merge after approval
```

## Content Guidelines

### Avoid Time-Sensitive Information

Don't include information that will become outdated:
```markdown
# ❌ Bad - will become outdated
As of 2024, the current version is 3.2

# ✅ Good - timeless
Check the official docs for the latest version
```

### Use Consistent Terminology

Pick terms and stick with them throughout the skill:
```markdown
# ❌ Bad - inconsistent
Submit your code for review...
After the PR is approved...
When your changes are merged...

# ✅ Good - consistent
Submit your pull request for review...
After the pull request is approved...
When your pull request is merged...
```

## Common Patterns

### Template Pattern

Provide reusable templates:

````markdown
## Bug Report Template

```markdown
## Description
[What's the bug?]

## Steps to Reproduce
1. 
2. 
3. 

## Expected Behavior
[What should happen?]

## Actual Behavior
[What actually happens?]

## Environment
- OS: 
- Version: 
```
````

### Examples Pattern

Show concrete examples for each major use case:

````markdown
## String Formatting

### Simple variable insertion
```python
name = "Alice"
greeting = f"Hello, {name}!"
```

### Multiple variables
```python
age = 30
message = f"{name} is {age} years old"
```

### Formatting numbers
```python
price = 19.99
formatted = f"Price: ${price:.2f}"
```
````

### Conditional Workflow Pattern

Provide decision trees for choosing approaches:

```markdown
## Choosing a Data Structure

**Use a list when:**
- Order matters
- You need to iterate sequentially
- Duplicates are allowed

**Use a set when:**
- You need fast membership testing
- Duplicates should be removed
- Order doesn't matter

**Use a dict when:**
- You need key-value associations
- Fast lookups by key are important
```

## Evaluation and Iteration

### Build Evaluations First

Before finalizing a skill, create test scenarios:

```markdown
## Test Scenarios for TDD Skill

Scenario 1: Agent receives simple feature request
Expected: Writes test before implementation

Scenario 2: Agent needs to fix bug urgently
Expected: Still writes test first despite pressure

Scenario 3: Agent working with legacy code  
Expected: Creates test infrastructure if needed
```

### Develop Skills Iteratively

1. **Start minimal:** Core guidance only
2. **Test with real usage:** Apply skill to actual tasks
3. **Identify gaps:** Where does agent still struggle?
4. **Add specificity:** Address observed failures
5. **Remove redundancy:** Cut what isn't helping

### Observe How Agents Navigate Skills

Pay attention to:
- Which sections get referenced most?
- Where does agent seem confused?
- What information is never used?
- When does agent violate the guidance?

## Anti-Patterns to Avoid

### ❌ Avoid Windows-Style Paths

Use forward slashes for cross-platform compatibility:
```markdown
# ✅ Good
path/to/file.py

# ❌ Bad
path\to\file.py
```

### ❌ Avoid Offering Too Many Options

Decision fatigue reduces compliance:
```markdown
# ❌ Bad - too many choices
You could use approach A, or B, or C, or D. Each has pros and cons...

# ✅ Good - clear recommendation with escape hatch
Use approach A for most cases. Use B only if you need [specific feature].
```

## Advanced: Skills with Executable Code

### Solve, Don't Punt

Provide working code, not just guidance:

````markdown
# ❌ Bad - punts to agent
You'll need to parse the JSON and extract the fields

# ✅ Good - provides solution
```python
import json

def extract_fields(json_str, fields):
    data = json.loads(json_str)
    return {field: data.get(field) for field in fields}
```
````

### Provide Utility Scripts

Include complete, runnable scripts:

````markdown
## Batch Image Resize

```python
# resize_images.py
from PIL import Image
import sys
from pathlib import Path

def resize_image(input_path, output_path, max_width=800):
    img = Image.open(input_path)
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    img.save(output_path)

if __name__ == "__main__":
    input_dir = Path(sys.argv[1])
    output_dir = Path(sys.argv[2])
    output_dir.mkdir(exist_ok=True)
    
    for img_path in input_dir.glob("*.jpg"):
        resize_image(img_path, output_dir / img_path.name)
```

Usage:
```bash
python resize_images.py ./input ./output
```
````

### Create Verifiable Intermediate Outputs

Build checkpoints into workflows:

```markdown
## Data Pipeline

1. **Extract data**
   ```bash
   python extract.py > raw_data.json
   ```
   ✓ Verify: File should contain JSON array with > 0 items

2. **Transform data**
   ```bash
   python transform.py raw_data.json > clean_data.json
   ```
   ✓ Verify: All required fields present in each record

3. **Load data**
   ```bash
   python load.py clean_data.json
   ```
   ✓ Verify: Database row count increased by expected amount
```

### Package Dependencies

Specify runtime requirements clearly:

```markdown
## Requirements

This skill requires:
- Python 3.8+
- PIL/Pillow library: `pip install Pillow`

Verify installation:
```bash
python -c "from PIL import Image; print('OK')"
```
```

### Avoid Assuming Tools Are Installed

Check for dependencies and provide install instructions:

```markdown
## Setup

Check if jq is installed:
```bash
which jq
```

If not found, install:
```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt-get install jq

# Windows
choco install jq
```
```

## Checklist for Effective Skills

### Core Quality
- [ ] Description focuses on WHEN to use (triggering conditions)
- [ ] Every paragraph justifies its token cost
- [ ] Appropriate degree of freedom for task type
- [ ] Consistent terminology throughout
- [ ] No time-sensitive information
- [ ] Progressive disclosure (simple → complex)

### Code and Scripts
- [ ] Code examples are complete and runnable
- [ ] Dependencies clearly specified
- [ ] Installation instructions provided
- [ ] Verification steps included
- [ ] No Windows-specific paths

### Testing
- [ ] Tested with all target models (Haiku/Sonnet/Opus)
- [ ] Test scenarios documented
- [ ] Verified agent can discover skill when needed
- [ ] Confirmed agent follows guidance under pressure
- [ ] Iterated based on observed usage

## Next Steps

After creating your skill:

1. **Test thoroughly** - Use the testing methodology in `testing-methodology.md`
2. **Apply persuasion principles** - See `persuasion-principles.md` for compliance techniques
3. **Iterate based on usage** - Observe where agents struggle and refine
4. **Keep it current** - Update as tools and practices evolve (but avoid time-sensitive content)

---

**Source:** Adapted from [Anthropic's official skill authoring documentation](https://docs.anthropic.com/en/docs/agents-and-tools/agent-skills)
