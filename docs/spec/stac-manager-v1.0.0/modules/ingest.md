# Ingest Module
## STAC Manager v1.0

**Role**: `Fetcher` (Source)

---

## 1. Purpose
The Ingest Module fetches STAC Items for a **single collection** (or target). It enables high-throughput fetching by leveraging internal parallelism.

> [!IMPORTANT]
> **Matrix Execution**: In v1.0, the StacManager spawn *parallel pipelines* based on the global `strategy.matrix` configuration.
> Therefore, this module instance is responsible for fetching items for **one** matrix entry (e.g., one `collection_id`) injected into its context.

## 2. Architecture

### 2.1 Fetcher Logic
- **Responsibility**: Fetch items from the source defined in the context/config.
- **Context Awareness**: Reads `context.data` to determine its target (e.g., `collection_id`, `catalog_url`).
- **Modes**:
    1.  **API Mode**: Uses `pystac-client` and non-blocking HTTP to crawl an API.
    2.  **File Mode**: Reads from a local file (Parquet/JSON) if `source_file` is set.

#### Fetch Loop Pseudocode (Tier 2)

```python
async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
    """
    Orchestrates fetching logic based on mode (API vs File).
    """
    # 1. Resolve Target
    # Priority: Config > Context (injected by Matrix)
    collection_id = self.config.collection_id or context.data.get('collection_id')
    
    if not collection_id and not self.config.source_file:
         raise ConfigurationError("Ingest target (collection_id or source_file) not defined")

    # 2. File Mode
    if self.config.source_file:
         async for item in self._read_file(self.config.source_file):
             yield item
         return

    # 3. API Mode (Parallel)
    # Use RequestSplitter to break big jobs into small chunks
    splitter = RequestSplitter(self.config)
    chunks = splitter.generate_chunks(self.config.filters.datetime)
    
    # Spawn workers to fetch chunks in parallel
    # Yields items as they arrive
    async for item in self._fetch_chunks_parallel(chunks, context):
        yield item
```

### 2.1 Internal Parallelism (`RequestSplitter`)
To allow high-throughput fetching from APIs without timeouts:
- **Problem**: Fetching 1M items linearly (offset + limit) is slow and flaky.
- **Solution**: The module internally splits the time range into chunks and fetches them in parallel.
- **Component**: `RequestSplitter` (Worker Pool).

#### Delegation to Utility
 
 The module delegates temporal splitting to the shared utility `stac_manager.utils.query.temporal_split_search`.
 
 ```python
 # Pseudo-implementation
 async for items in temporal_split_search(
     client=self.client, 
     filters=self.filters, 
     limit=self.config.concurrency.chunk_size
 ):
     yield items
 ```

### 2.3 HTTP Strategy (Tier 3)
- **Requirement**: Must use a **Non-blocking HTTP Client** (e.g., `httpx` or `aiohttp`) for item fetching to ensure the main event loop is not blocked by I/O.
- **Pattern**:
    - `pystac-client` (Sync/Threaded): Used for metadata discovery and split planning.
    - `httpx/aiohttp` (Async): Used for high-volume item fetching.

## 3. Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class IngestFilters(BaseModel):
    """
    Common filters supported by STAC APIs.
    """
    bbox: Optional[List[float]] = None
    datetime: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    ids: Optional[List[str]] = None
    collections: Optional[List[str]] = None

class IngestConfig(BaseModel):
    # If provided in config, overrides Matrix context.
    collection_id: Optional[str] = None 
    
    # Mode switch
    source_file: Optional[str] = None
    """
    Path to a local file or glob pattern (e.g. "./data/*.json").
    Supports: Parquet, JSON (FeatureCollection), or generic JSON files.
    """
    
    # Internal Parallelism
    concurrency: int = Field(default=10, ge=1)
    
    # Filters applied to the API search
    filters: Optional[IngestFilters] = None 
```

## 4. I/O Contract

**Input (Workflow Context)**:
- `context.data` (injected by Matrix Strategy):
  ```python
  {
      "collection_id": "landsat-c2-l2",
      "catalog_url": "https://..."
  }
  ```

**Output**:
```python
AsyncIterator[dict] 
# Yields a single interleaved stream of raw STAC Item dictionaries.
```

## 5. Error Handling
- **429 (Rate Limit)**: Must implement exponential backoff.
- **5xx (Server Error)**: Retry N times, then fail chunk.
- **Partial Failure**: A failed chunk should be logged to `FailureCollector` but should not crash the entire pipeline (functionality allowing).

