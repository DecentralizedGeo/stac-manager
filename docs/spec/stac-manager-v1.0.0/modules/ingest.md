# Ingest Module
## STAC Manager v1.0

**Role**: `Fetcher` (Source)

---

## 1. Purpose
The Ingest Module fetches STAC Items from a Collection with support for pagination, concurrency, and rate limiting. It handles the "crawling" aspect of the pipeline.

It supports two modes:
1.  **API Crawl**: Fetch items from a remote STAC API.
2.  **File Read**: Load items from a local file (JSON/Parquet), enabling the **Parquet Cache Strategy**.

## 2. Architecture
Fetching data from APIs at scale requires careful resource management.

### 2.1 ItemFetcher
- **Responsibility**: High-throughput data fetching.
- **Context**: Consumes **Task Contexts** (containing `ItemSearch` objects) yielded by the Discovery module.
- **Strategy**: **Native Async Search** (Strategy B).
  - Use **Non-blocking HTTP Client** (e.g., `aiohttp`) for raw JSON fetching (non-blocking I/O).
  - Use `pystac` only for parsing (CPU-bound).
  - **Avoid**: Blocking calls (like `pystac_client.Client.search()`) in the hot path.

### 2.2 Hybrid Fetching Strategy
To optimize both logic ("splitting") and throughput ("fetching"):

1.  **Control Plane (Sync/Threaded)**: Use `pystac-client` to Query Metadata.
    - Specifically checking `search(...).matched()` counts.
    - Used by `RequestSplitter` to verify if a range is safe to fetch.
    - Runs in `ThreadPoolExecutor` to avoid blocking the loop.
3.  **Data Plane (Native Async)**: Use **Non-blocking I/O** for Item Pages.
    - Once a time-range is deemed "safe" (count < limit), fetch it using native async.
    - Yields raw STAC Item **dictionaries** immediately to the pipeline.
- **Responsibility**: Manages cursor/page tracking and query sharding.
- **Strategy**: **Temporal Request Splitting**.
  - Recursively split time ranges when item counts exceed threshold (e.g., 10k).
  - Prevents deep pagination server timeouts (offset > 10k).

#### RequestSplitter Pseudocode
```python
class RequestSplitter:
    """Handles temporal splitting for deep pagination."""
    
    def split_range(self, time_range: tuple[datetime, datetime]) -> Iterator[tuple[datetime, datetime]]:
        """
        Recursively split time range until count < limit.
        """
        # Control Plane: Use pystac-client (threaded) to get count
        count = self.get_count_via_pystac_client(time_range)
        
        if count < self.max_items_per_request:
            yield time_range
            return

        # Split in half
        mid_point = time_range[0] + (time_range[1] - time_range[0]) / 2
        
        # Recurse left
        yield from self.split_range((time_range[0], mid_point))
        
        # Recurse right
        yield from self.split_range((mid_point, time_range[1]))
```

### 2.3 RateLimiter
- **Responsibility**: Enforces API politeness.
- **Mechanism**: Token bucket/semaphore as defined in [Utilities](../07-utilities.md). Responds to `429 Retry-After` headers.

### 2.4 FileFetcher (Parquet Cache Support)
- **Responsibility**: Read items from a local file instead of an API.
- **Trigger**: Active when `config.source_file` is set.
### 2.4 FileFetcher (Parquet Cache Support)
- **Responsibility**: Read items from a local file instead of an API.
- **Trigger**: Active when `config.source_file` is set.
- **Implementation (Pseudocode)**:

```python
def fetch_from_file(self, path: str) -> Iterator[dict]:
    if path.endswith(".parquet"):
        # Use simple stac-geoparquet reader
        df = stac_geoparquet.read(path)
        yield from df.to_dicts()
    else:
        # JSON / GeoJSON
        with open(path) as f:
            data = json.load(f)
            
        if isinstance(data, dict):
            if data.get("type") == "FeatureCollection":
                yield from data.get("features", [])
            else:
                yield data # Single item
        elif isinstance(data, list):
            yield from data
```

## 3. Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class IngestFilters(BaseModel):
    temporal: Optional[Dict[str, str]] = None # {"start": "...", "end": "..."}
    spatial: Optional[list[float]] = None # [minx, miny, maxx, maxy]
    query: Optional[Dict[str, Any]] = None 
    """
    STAC API Query Extension parameters (JSON body).
    These filters are **applied to** the base ItemSearch object retrieved from WorkflowContext.
    See: [STAC Item Search filter parameter](https://api.stacspec.org/v1.0.0-rc.1/item-search/#tag/Item-Search/operation/postItemSearch)
    """

class IngestConfig(BaseModel):
    collection_id: str
    """
    Single collection ID to ingest.
    The StacManager manages parallelism at the collection level,
    spawning independent pipelines for each collection.
    """
    source_file: Optional[str] = None
    """
    Path to local JSON or Parquet file.
    If set, overrides API fetching mode.
    """
    limit: Optional[int] = Field(None, gt=0)
    concurrency: int = Field(default=5, ge=1)
    rate_limit: float = Field(default=10.0, gt=0)
    filters: IngestFilters = Field(default_factory=IngestFilters)
```

> [!NOTE]
> **ItemSearch Context**: When operating in API Crawl mode, the module expects the upstream Discovery step to have populated `context.data` with the necessary `ItemSearch` context (e.g. valid collection object or connection parameters). The `IngestFilters` are applied on top of this base context.

### 3.1 Example Usage (YAML)

```yaml
- id: ingest
  module: IngestModule
  depends_on: [discover]
  config:
    collection_id: "landsat-c2-l2"
    limit: 1000
    concurrency: 20
    filters:
      spatial: [-180, -90, 180, 90]
      query:
        "eo:cloud_cover": {"lt": 5}
```

## 4. I/O Contract

- stream of **Task Contexts** (from Discovery): 
  ```json
  {
     "type": "collection_search",
     "collection_id": "...",
     "search_object": <pystac_client.ItemSearch>
  }
  ```

**Output (Python)**:
```python
AsyncIterator[dict]  # Yields raw STAC Item dictionaries
```
> **Streaming Requirement**: This module yields items one-by-one or in small batches using `search_object.items_as_dicts()`. It MUST NOT accumulate the entire result set in memory.

## 5. Error Handling
- **Fetch Failure (Single Page/Item)**: Log error to `FailureCollector`, skip, and continue.
- **Rate Limit Exhaustion**: Retry N times, then fail the specific batch.
- **Malformed Item**: Log validation warning, skip.

