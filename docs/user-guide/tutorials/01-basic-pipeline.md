# Tutorial 01: Basic Pipeline - Fetching from a Live STAC API

Learn how to fetch real STAC data from a public catalog and validate it.

---

## Overview

This tutorial builds on the [Quickstart Guide](../quickstart.md) by introducing **API-based ingestion** - fetching live STAC data from a remote catalog instead of using local files.

**What you'll learn:**
- How to configure the IngestModule for API mode
- Spatial and temporal filtering of STAC items
- Real-world workflow patterns

**Time required:** ~10 minutes

---

## Prerequisites

- STAC Manager installed ([Installation Guide](../installation.md))
- Completed the [Quickstart Guide](../quickstart.md)
- Internet connection (to fetch from Planetary Computer)

---

## The Workflow

Open `samples/sentinel-2-l2a-api/workflows/01-basic-pipeline.yaml`:

```yaml
name: basic-pipeline

steps:
  - id: ingest
    module: IngestModule
    config:
      mode: api                    # ← Fetch from API instead of file
      source: https://planetarycomputer.microsoft.com/api/stac/v1
      collection_id: sentinel-2-l2a
      max_items: 50
      bbox: [-122.5, 37.5, -122.0, 38.0]    # ← Spatial filter
      datetime: 2024-01-01/2024-01-31       # ← Temporal filter

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
      collection_id: sentinel-2-l2a-tutorial-01
```

### Key Differences from Quickstart

| Aspect | Quickstart (00) | Tutorial 01 |
|--------|-----------------|-----------|
| **Mode** | `file` (local) | `api` (remote) |
| **Data Source** | Pre-generated sample data | Live Planetary Computer |
| **Filtering** | None | Bbox + datetime |
| **Network** | Offline | Requires internet |
| **Items Fetched** | Fixed (20) | Dynamic (up to 50) |

---

## Running the Workflow

Execute the tutorial workflow:

```bash
stac-manager run-workflow samples/sentinel-2-l2a-api/workflows/01-basic-pipeline.yaml
```

**Expected output:**

```
Starting workflow: basic-pipeline
[ingest] Querying API: sentinel-2-l2a collection
[ingest] Applying filters: bbox=[-122.5,37.5,-122.0,38.0], datetime=2024-01-01/2024-01-31
[ingest] Loaded 42 items from API
[validate] Validated 42 items (0 errors)
[output] Wrote 42 items to ./outputs/sentinel-2-l2a-tutorial-01
✓ Workflow completed successfully
```

**Time**: ~15-30 seconds (depending on network and API response time)

---

## Understanding the Components

### IngestModule in API Mode

When `mode: api`, the IngestModule performs these steps:

1. **Connect to Catalog**: Establishes connection to STAC API server
2. **Search**: Queries the catalog with filters
   - `collection_id`: Which dataset to search
   - `bbox`: Bounding box [west, south, east, north] in WGS84
   - `datetime`: ISO8601 date range (e.g., `2024-01-01/2024-01-31`)
   - `max_items`: Limit number of results
3. **Stream Items**: Returns matching items as a stream

### Spatial Filtering

The `bbox` parameter limits results to a geographic area:

```yaml
bbox: [-122.5, 37.5, -122.0, 38.0]
#      west   south  east   north
```

This is the **San Francisco Bay Area**. Try different coordinates to explore other regions:

```yaml
# New York City area
bbox: [-74.3, 40.5, -73.7, 40.9]

# London area
bbox: [-0.3, 51.4, 0.0, 51.7]

# Singapore
bbox: [103.6, 1.2, 103.9, 1.4]
```

### Temporal Filtering

The `datetime` parameter limits results to a date range:

```yaml
datetime: 2024-01-01/2024-01-31
#         start       end
```

**Supported formats:**

```yaml
# Full date range
datetime: 2024-01-01/2024-12-31

# Single date (specific day)
datetime: 2024-06-15

# Open-ended ranges
datetime: 2024-01-01/..     # From date forward
datetime: ../2024-12-31     # Up to date
datetime: ..                # Any date
```

---

## Exploring the Results

After running the workflow, inspect the output:

```bash
# View the collection metadata
cat outputs/sentinel-2-l2a-tutorial-01/collection.json

# Count the number of items
ls outputs/sentinel-2-l2a-tutorial-01/items/ | wc -l

# Inspect the first item
cat outputs/sentinel-2-l2a-tutorial-01/items/S2A_*.json | head -n 50
```

---

## Common Patterns

### Pattern 1: Recent Cloud-Free Images

Search for recent images with low cloud cover:

```yaml
- id: ingest
  module: IngestModule
  config:
    mode: api
    source: https://planetarycomputer.microsoft.com/api/stac/v1
    collection_id: sentinel-2-l2a
    max_items: 100
    bbox: [your_west, your_south, your_east, your_north]
    datetime: 2024-12-01/2024-12-31    # Recent month
    # Note: Cloud filtering would require a modifier step (see Tutorial 02)
```

### Pattern 2: Seasonal Analysis

Compare data across seasons:

```yaml
steps:
  - id: ingest_winter
    module: IngestModule
    config:
      mode: api
      collection_id: sentinel-2-l2a
      datetime: 2024-01-01/2024-02-29    # Winter
      # ...

  - id: ingest_summer
    module: IngestModule
    config:
      mode: api
      collection_id: sentinel-2-l2a
      datetime: 2024-07-01/2024-08-31    # Summer
      # ...
```

### Pattern 3: Multi-Region Comparison

Fetch data from multiple areas:

```yaml
steps:
  - id: ingest_north
    module: IngestModule
    config:
      mode: api
      collection_id: sentinel-2-l2a
      bbox: [-122.5, 40.0, -121.5, 41.0]    # North
      # ...

  - id: ingest_south
    module: IngestModule
    config:
      mode: api
      collection_id: sentinel-2-l2a
      bbox: [-122.5, 37.0, -121.5, 38.0]    # South
      # ...
```

---

## Troubleshooting

### API Connection Failed

**Error**: `Connection refused` or `Failed to connect to Planetary Computer`

**Cause**: Internet connection issue or API server down

**Solution**:
```bash
# Check connectivity
ping planetarycomputer.microsoft.com

# Try with a shorter timeout or different API
# For EASIER Data:
url: https://api.easierdata.com/stac/v1
```

### No Items Found

**Error**: `[ingest] Loaded 0 items from API`

**Cause**: Spatial/temporal filters too restrictive or no data in that area/time

**Solution**:
```yaml
# Relax spatial filter
bbox: [-180, -90, 180, 90]    # Whole world

# Extend temporal range
datetime: 2020-01-01/2024-12-31

# Increase max items
max_items: 1000
```

### API Rate Limiting

**Error**: `429 Too Many Requests` or timeout

**Cause**: Too many rapid requests

**Solution**: Add delays between requests or reduce `max_items`

---

## Next Steps

- 🔧 **[Tutorial 02: Update Pipeline](02-update-pipeline.md)** - Filter and modify items in-flight
- 📚 **[Tutorial 03: Extension Pipeline](03-extension-pipeline.md)** - Add extensions and enrich data
- 💡 **[Concepts Guide](../concepts.md)** - Deep dive into architecture

---

## Key Takeaways

✅ API mode fetches **live data** from remote catalogs  
✅ `bbox` and `datetime` filters **reduce data transfer**  
✅ Streams enable **processing without loading all data** into memory  
✅ ValidateModule ensures data **quality and consistency**  

---

## API Endpoints

| Catalog | URL | Collection Examples |
|---------|-----|-------------------|
| Planetary Computer | `https://planetarycomputer.microsoft.com/api/stac/v1` | `sentinel-2-l2a`, `landsat-c2-l2` |
| EASIER Data | `https://api.easierdata.com/stac/v1` | `HLSS30_2.0` |
| OpenSearch.org | `https://stac.collection.org/api/v1` | Various |

Query available collections:

```bash
curl https://planetarycomputer.microsoft.com/api/stac/v1/collections | jq '.collections[].id'
```
