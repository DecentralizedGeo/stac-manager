# Quickstart Guide

Get started with STAC Manager in 5 minutes by running your first pipeline.

---

## Goal

Run a simple workflow that:
1. Fetches STAC items from a local file
2. Validates them against the STAC schema
3. Outputs them to a structured directory

---

## Prerequisites

- STAC Manager installed ([Installation Guide](installation.md))
- Sample data available (generate with `scripts/generate_sample_data.py`)

---

## Step 1: Verify Installation

First, confirm STAC Manager is installed:

```bash
stac-manager --version
```

Expected output: `stac-manager, version 1.0.0`

---

## Step 2: Review the Workflow Configuration

Open `samples/sentinel-2-l2a-api/workflows/00-quickstart.yaml` to see the workflow definition:

```yaml
name: quickstart-pipeline

steps:
  - id: ingest
    module: IngestModule
    config:
      mode: file
      source: samples/sentinel-2-l2a-api/data/items.json
      collection_id: sentinel-2-l2a

  - id: validate
    module: ValidateModule
    depends_on: [ingest]
    config:
      strict: true

  - id: output
    module: OutputModule
    depends_on: [validate]
    config:
      base_dir: ./outputs
      format: json
      collection_id: sentinel-2-l2a
```

**What this does:**

- **IngestModule**: Reads STAC items from a local JSON file (Sentinel-2 L2A collection)
- **ValidateModule**: Checks each item against STAC schema (strict mode)
- **OutputModule**: Writes validated items to `./outputs/sentinel-2-l2a/`

---

## Step 3: Run the Workflow

Execute the workflow using the CLI:

```bash
stac-manager run-workflow samples/sentinel-2-l2a-api/workflows/00-quickstart.yaml
```

**Expected output:**

```
Starting workflow: quickstart-pipeline
[ingest] Loaded N items from file
[validate] Validated N items (0 errors)
[output] Wrote N items to ./outputs/sentinel-2-l2a
✓ Workflow completed successfully
```

**Time**: ~5-10 seconds

---

## Step 4: Inspect the Output

Check the output directory:

```bash
ls -R outputs/sentinel-2-l2a
```

**You should see:**

```
outputs/sentinel-2-l2a/
├── collection.json          # Collection metadata
└── items/
    ├── item_1.json
    ├── item_2.json
    └── ... (more items)
```

**View a single item:**

```bash
cat outputs/sentinel-2-l2a/items/item_1.json | head -n 30
```

---

## What Just Happened?

### The Pipeline

STAC Manager executed three modules in sequence:

1. **IngestModule (Fetcher)**
   - Role: Source of STAC items
   - Action: Read items from `items.json` file
   - Output: Stream of STAC item dictionaries

2. **ValidateModule (Modifier)**
   - Role: Transform/validate items in-flight
   - Action: Check each item against STAC JSON schema
   - Output: Only valid items pass through

3. **OutputModule (Bundler)**
   - Role: Sink for processed items
   - Action: Write items to disk in self-contained collection structure
   - Output: `collection.json` + individual item files

### The Architecture

This follows the **Pipes and Filters** pattern:
- **Fetchers** → generate items (IngestModule)
- **Modifiers** → process items (ValidateModule)
- **Bundlers** → consume items (OutputModule)

Data flows through the pipeline as an **async stream**, meaning STAC Manager can process millions of items without loading everything into memory.

---

## Common Issues

### "Workflow validation failed"

**Cause**: Invalid YAML syntax or missing required fields.

**Fix**: Use the validation command to check your config:

```bash
stac-manager validate-workflow your-workflow.yaml
```

### "Module 'IngestModule' not found"

**Cause**: STAC Manager not installed correctly.

**Fix**: Reinstall:

```bash
pip install --upgrade stac-manager
```

### Permission denied writing to outputs/

**Cause**: Insufficient write permissions.

**Fix**: Use a different output directory:

```yaml
config:
  base_dir: ~/my-outputs  # User home directory
```

---

## Next Steps

### Try Using a Real STAC API

Modify the `ingest` step to fetch from Microsoft Planetary Computer:

```yaml
- id: ingest
  module: IngestModule
  config:
    mode: api
    source: https://planetarycomputer.microsoft.com/api/stac/v1
    collection_id: sentinel-2-l2a
    max_items: 10
    bbox: [-122.5, 37.5, -122.0, 38.0]  # San Francisco Bay Area
```

Run the workflow again:

```bash
stac-manager run-workflow samples/sentinel-2-l2a-api/workflows/00-quickstart.yaml
```

### Learn More

- 📚 **[System Architecture](../spec/stac-manager-v1.0.0/00-system-overview.md)** - Understand Pipes and Filters design
- 🔧 **[Module Reference](../spec/stac-manager-v1.0.0/)** - Complete module documentation
- *📖 **Tutorials** - Coming in Phase C (Basic, Update, and Extension pipelines)*

---

## Python API Alternative

You can also run workflows programmatically:

```python
from stac_manager import StacManager
from pathlib import Path

# Load workflow
workflow_path = Path("samples/sentinel-2-l2a-api/workflows/00-quickstart.yaml")
manager = StacManager.from_yaml(workflow_path)

# Execute
result = await manager.run()

print(f"Processed {result.items_processed} items")
print(f"Failures: {result.failure_count}")
```

See [Python API Documentation](../spec/stac-manager-v1.0.0/04-python-library-api.md) for details.
