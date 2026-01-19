# Discovery Module
## STAC Manager v1.0

**Role**: `Fetcher` (Source)

---

## 1. Purpose
The Discovery Module is responsible for querying STAC API endpoints to find available Collections and their metadata. It acts as the primary **entry point** for most API-based workflows.

It manages the process of establishing a valid `pystac_client` connection by:
1.  **Verifying Existence**: Calls `client.get_collection("your-collection-id")` to confirm the collection exists.
2.  **Creating Search Tasks**: If valid, it constructs a complete `pystac_client.Search` object (initially configured with those collection parameters and any filters) and packages it into a **Task Context**.
3.  **Handoff**: It yields these "Search Tasks" to effectively "queue up" work for the downstream Ingest module.

## 2. Architecture
- **Role**: `Fetcher` (Source).
- **Wrapper**: Wraps `pystac_client.Client` for standard STAC API interactions.
- **Async Strategy**: **Executor Wrapper** (Strategy A).
  - Since discovery is low-volume (collections, not items), run blocking `pystac-client` calls in a `ThreadPoolExecutor`.
  - Avoids blocking the main loop without needing complex native async logic.
- **Filtering**: Filtered by specific collection IDs provided in config.
- **Output**: Yields STAC Collections as **dictionary objects** to the pipeline.

## 3. Configuration Schema

```python
from pydantic import BaseModel, HttpUrl, Field
from typing import Optional

class DiscoveryFilters(BaseModel):
    temporal: Optional[dict] = None
    spatial: Optional[list[float]] = None # [minx, miny, maxx, maxy]

class DiscoveryConfig(BaseModel):
    catalog_url: HttpUrl
    collection_ids: Optional[list[str]] = None # List of exact collection IDs to fetch
    filters: DiscoveryFilters = Field(default_factory=DiscoveryFilters)
```

### 3.1 Example Usage (YAML)

```yaml
- id: discover
  module: DiscoveryModule
  config:
    catalog_url: "https://cmr.earthdata.nasa.gov/stac/v1"
    collection_ids: ["C12345-DAAC"]
    filters:
      temporal:
        start: "2024-01-01T00:00:00Z"
        end: "2024-01-31T23:59:59Z"
```

## 4. I/O Contract

**Input (Workflow Context)**:
- None (First step trigger) or previous step data (ignored).

**Side Effects (Workflow Context)**:
- Populates `context.data['catalog_url']` and `context.data['discovery_filters']` for downstream reference.

**Output (Python)**:
```python
AsyncIterator[dict] 
# Yields "Task Contexts" to the pipeline:
# {
#    "type": "collection_search",
#    "collection_id": "...", 
#    "search_object": pystac_client.ItemSearch(...)
# }
```

## 5. Error Handling
- **Network Errors**: Log and fail fast (usually critical for discovery).
- **Invalid URL**: Fail fast.
- **Empty Result**: Log warning ("No collections found matching criteria") but return empty list.
