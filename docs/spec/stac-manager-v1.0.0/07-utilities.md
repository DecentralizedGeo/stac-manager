# Utilities & Shared Components
## STAC Manager v1.0

**Related Documents**:
- [Protocols](./06-protocols.md)
- [Pipeline Management](./01-pipeline-management.md)

---

## Overview

This document defines shared utility components used across multiple modules. These are **conceptual specifications** - they describe requirements and behavior without prescribing exact implementation.

---

## 1. Rate Limiting

### 1.1 Purpose
Coordinate concurrent async requests to respect API rate limits and avoid overwhelming external services.

### 1.2 Requirements

**Configuration**:
- `requests_per_second`: Maximum request rate (float)
- `max_concurrent`: Maximum parallel requests (int)

**Behavior**:
- Block requests when rate limit would be exceeded
- Distribute requests evenly over time
- Handle API 429 (rate limit) responses gracefully

### 1.3 Public Interface

```python
class RateLimiter:
    """Rate limiter for async HTTP requests."""
    
    def __init__(
        self,
        requests_per_second: float,
        max_concurrent: int = 10
    ) -> None:
        """
        Initialize rate limiter.
        
        Args:
            requests_per_second: Maximum request rate
            max_concurrent: Maximum parallel requests
        """
        ...
    
    async def execute(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute function with rate limiting.
        
        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func
        
        Returns:
            Result from func()
        
        Behavior:
            - Waits if rate limit would be exceeded
            - Blocks if max_concurrent limit reached
        """
        ...
```

### 1.4 Implementation Strategy

**Approach**: Use `asyncio` primitives (Semaphore for concurrency, sleep for rate)

**Mechanism**:
- Semaphore to limit concurrent requests
- Token bucket or sliding window for rate limiting
- Track minimum interval between requests

**Pseudocode (Rate Limiting Algo)**:
```python
async def acquire_slot(self):
    # 1. Enforce Concurrency
    await self.semaphore.acquire()
    
    # 2. Enforce Rate (Token Bucket)
    current_time = now()
    if (current_time - self.last_request) < self.min_interval:
        sleep_duration = self.min_interval - (current_time - self.last_request)
        await sleep(sleep_duration)
        
    self.last_request = now()
    
    try:
        yield # Execute the request
    finally:
        self.semaphore.release()
```

**Usage Pattern**:
```python
# In IngestModule
limiter = RateLimiter(requests_per_second=10.0, max_concurrent=5)

async def fetch_item(url):
    return await limiter.execute(fetch_from_api, url)
```

---

## 2. Retry Logic with Exponential Backoff

### 2.1 Purpose
Handle transient network failures by retrying with increasing delays.

### 2.2 Requirements

**Configuration**:
- `max_attempts`: Maximum retry attempts (default: 3)
- `base_delay`: Initial delay in seconds (default: 1.0)
- `max_delay`: Maximum delay in seconds (default: 60.0)
- `exponential_base`: Backoff multiplier (default: 2.0)

**Behavior**:
- Retry on network errors, timeouts, 429/500/502/503 responses
- Increase delay exponentially: delay = base_delay * (exponential_base ^ attempt)
- Cap delay at max_delay
- Respect `Retry-After` header if present

### 2.3 Public Interface

```python
async def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry (no arguments)
        max_attempts: Maximum retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        exponential_base: Backoff multiplier
    
    Returns:
        Result from successful function call
    
    Raises:
        Last exception if all retries fail
    
    Behavior:
        - Attempt 1: immediate
        - Attempt 2: wait base_delay
        - Attempt 3: wait base_delay * exponential_base
        - Attempt N: wait min(base_delay * exponential_base^(N-2), max_delay)
    """
    ...
```

### 2.4 Usage Pattern

```python
# In IngestModule
async def fetch_page():
    async with session.get(url) as response:
        response.raise_for_status()
        return await response.json()

# Retry on failure
data = await retry_with_backoff(fetch_page, max_attempts=3)
```

---

## 3. Async Integration Patterns

### 3.1 Purpose
Run synchronous libraries (like `pystac-client`) in async workflows without blocking the event loop.

### 3.2 When to Use Executor vs Native Async

|  Scenario | Approach |
|-----------|----------|
| **Sync library with no async version** | Use `run_in_executor()` (Strategy A) |
| **I/O-bound with async support** (e.g. Ingest) | Use native async (`aiohttp`) (Strategy B) |
| **CPU-bound computation** | Use `run_in_executor()` with ProcessPoolExecutor |
| **Quick sync operation (\<10ms)** | Just call it synchronously |


### 3.3 Pattern: Executor Wrapper (Strategy A)

**Problem**: `pystac-client` is synchronous, but modules must be async

**Solution**: Run blocking operations in a thread pool

**Implementation Pattern**:
```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

class IngestModule:
    def __init__(self, config: dict):
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.catalog_url = config['catalog_url']
    
    async def execute(self, context: WorkflowContext):
        """Run sync pystac-client in thread pool."""
        loop = asyncio.get_event_loop()
        
        # Execute blocking function in thread pool
        pages = await loop.run_in_executor(
            self.executor,
            self._search_sync,  # Sync function
            self.catalog_url
        )
        
        return pages
    
    def _search_sync(self, catalog_url: str) -> list:
        """Synchronous search (runs in thread)."""
        from pystac_client import Client
        
        client = Client.open(catalog_url)
        return list(client.search(max_items=100).items())
```

### 3.4 Pattern: Native Async Search (Strategy B)

**Problem**: `pystac-client` is blocking. For high-throughput ingest (>100 items/sec), threads scale poorly.

**Solution**: Use `aiohttp` for raw JSON fetching, `pystac` only for parsing.

**Pattern**:
```python
async def search_native(url, params, semaphore):
    """
    High-performance native async search.
    
    1. Fetch raw JSON pages concurrently (aiohttp)
    2. Yield dicts immediately
    3. Parse to pystac.Item only when needed (lazy)
    """
    async with semaphore:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{url}/search", json=params) as resp:
                data = await resp.json()
                for feat in data['features']:
                    yield pystac.Item.from_dict(feat)
```

---

## 4. Query Utilities

### 4.1 Temporal Request Splitting

**Purpose**: recursively split large time ranges to avoid deep pagination and server timeouts.

**Algorithm**:
1. Query with `limit=0` to get count.
2. If count > `threshold` (e.g., 10,000):
   - Split time range in half (midpoint).
   - Recursively process both halves.
3. If count <= `threshold`:
   - Proceed with standard pagination.

**Function Signature**:
```python
async def temporal_split_search(
    client: Client,
    collection_id: str,
    time_range: Optional[tuple[datetime, datetime]] = None,
    bbox: Optional[list[float]] = None,
    limit: int = 10000
):
    """
    Generator that yields STAC items from a search, splitting by time if needed.
    Used by IngestModule to handle large result sets without timeouts.
    """
    # Implementation logic...
```

---

## 5. Geometry Utilities

### 5.1 Bbox Calculation

**Purpose**: Ensure STAC Items have valid bounding boxes

**Function Signature**:
```python
def ensure_bbox(geometry: dict | None) -> list[float] | None:
    """
    Calculate bounding box from GeoJSON geometry.
    
    Args:
        geometry: GeoJSON geometry dict or None
    
    Returns:
        Bounding box [minx, miny, maxx, maxy] or None if geometry is None
    
    Implementation:
        Uses shapely.geometry.shape(geometry).bounds
    """
    ...
```

**Usage**:
```python
# In SeedModule
bbox = ensure_bbox(transformed_data['geometry'])
```

### 5.2 Geometry Validation and Repair

**Purpose**: Fix common geometry issues (unclosed polygons, invalid coordinates)

**Function Signature**:
```python
def validate_and_repair_geometry(geometry: dict) -> tuple[dict | None, list[str]]:
    """
    Validate and attempt to repair GeoJSON geometry.
    
    Args:
        geometry: GeoJSON geometry dict
    
    Returns:
        Tuple of (repaired_geometry, warnings)
        - repaired_geometry: Valid geometry or None if unrepairable
        - warnings: List of issues found/fixed
    
    Implementation:
        1. Check `shapely.is_valid`.
        2. If invalid, attempt `shapely.make_valid` (GEOS >= 3.8).
        3. Fallback: `geometry.buffer(0)` check.
        4. If still invalid, return None (unrepairable).
    """
    ...
```

---

## 6. State Persistence (Checkpointing)

### 6.1 Purpose
Allow long-running async workflows to resume from where they left off after a crash or interruption.

### 6.2 Detailed Specification
See [State Persistence & Recovery](./08-state-persistence.md) for the complete architecture, data schema, and API definition.

### 6.3 Shared Pattern: Atomic Output
(Moved to [08-state-persistence.md](./08-state-persistence.md#5-atomic-write-strategy))

Modules writing files MUST follow the atomic write protocols defined in the State Persistence spec.

---

## 7. Logging Utilities

### 7.1 Logger Setup

**Purpose**: Configure structured logger from workflow config

**Function Signature**:
```python
def setup_logger(config: dict) -> logging.Logger:
    """
    Create configured logger instance.
    
    Args:
        config: Workflow configuration with logging section
    
    Returns:
        Configured logger with console and optional file handlers
    
    Configuration:
        logging:
          level: DEBUG | INFO | WARNING | ERROR
          file: path/to/log/file.log (optional)
          format: json | text (default: text)
    
    Behavior:
        - Always adds console handler (stdout)
        - Adds file handler if 'file' configured
        - Creates log directory if needed
        - Uses structured format with timestamps
    """
    ...
```

### 7.2 Structured Logging Pattern

**Module Logging Convention**:
```python
# In any module
async def execute(self, context: WorkflowContext):
    context.logger.info(f"[{self.__class__.__name__}] Starting execution")
    
    # ... work ...
    
    context.logger.info(
        f"[{self.__class__.__name__}] Completed: {count} items processed"
    )
```

**Log Level Guidelines**:

| Level | Usage |
|-------|-------|
| **DEBUG** | Detailed diagnostic info (field mappings, API responses, intermediate values) |
| **INFO** | Progress updates (step start/completion, item counts, milestones) |
| **WARNING** | Non-critical errors (validation failures, skipped items, retries) |
| **ERROR** | Critical failures (module exceptions, I/O errors, config errors) |

---

## 8. Processing Summary Generator

### 8.1 Purpose
Create human-readable summary of workflow execution results

### 8.2 Function Signature

```python
def generate_processing_summary(
    result: WorkflowResult, 
    context: WorkflowContext
) -> str:
    """
    Generates a human-readable markdown summary of the workflow execution.
    
    Args:
        result: WorkflowResult dict
        context: WorkflowContext object
        
    Returns:
        Formatted summary string for console output
    
    Output Format:
        === Workflow Processing Summary ===
        Workflow: {name}
        Total Steps: {total}
        Successful Steps: {success}
        Failed Steps: {failed}
        
        === Failure Breakdown ===
        Total Failures: {count}
        
        {step_id}: {failure_count} failures
        ...
        
        Detailed failure report: {path}
    """
    ...
```

### 8.3 Usage

```python
# In CLI or StacManager
result = await orchestrator.execute()
summary = generate_processing_summary(result, context.failure_collector)
print(summary)
```

---

## 9. Configuration Validation

### 9.1 Workflow Config Validator

**Purpose**: Validate workflow YAML before execution

**Function Signature**:
```python
def validate_workflow_config(config: dict) -> list[str]:
    """
    Validate workflow configuration structure and requirements.
    
    Args:
        config: Loaded workflow configuration dictionary
    
    Returns:
        List of validation errors (empty if valid)
    
    Checks:
        - Required fields present (workflow.name, workflow.steps)
        - All step IDs are unique
        - All dependencies reference valid step IDs
        - No circular dependencies
        - Each step has required fields (id, module, config)
        - Module names are valid
    """
    ...
```

**Usage**:
```python
# Before executing workflow
errors = validate_workflow_config(config)
if errors:
    for error in errors:
        print(f"Configuration error: {error}")
    sys.exit(1)
```

---

## 10. Environment Variable Substitution

### 10.1 Purpose
Resolve `${VAR_NAME}` placeholders in config from environment variables

### 10.2 Function Signature

```python
def substitute_env_vars(config: dict) -> dict:
    """
    Replace ${VAR} placeholders with environment variable values.
    
    Args:
        config: Configuration dict (may contain ${VAR} strings)
    
    Returns:
        Configuration with placeholders replaced
    
    Raises:
        ConfigurationError: If referenced env var doesn't exist
    
    Example:
        Input:  {"token": "${API_TOKEN}", "url": "https://api.com"}
        Env:    API_TOKEN=secret123
        Output: {"token": "secret123", "url": "https://api.com"}
    """
    ...
```

---

## 11. Implementation Notes

### 11.1 Library Choices

These utilities can be implemented using:

**Async/Concurrency**:
- `asyncio` (stdlib) - Semaphores, sleep, executors
- `aiohttp` - Async HTTP client

**Geometry**:
- `shapely` - Geometry validation and operations
- `pyproj` - Coordinate transformations (if needed)

**Logging**:
- `logging` (stdlib) - Standard Python logging
- Optional: `structlog` for structured JSON logs

### 11.2 Testing Considerations

Utilities should have comprehensive unit tests:
- Rate limiter: Test request spacing, concurrency limits
- Retry logic: Test backoff timing, failure scenarios
- Geometry: Test edge cases (null island, antimeridian, poles)
- Config validation: Test all error conditions

---

## 12. Summary

This document defines:

- **Rate Limiting**: Async request coordination
- **Retry Logic**: Exponential backoff for network failures
- **Async Patterns**: Integrating sync libraries in async workflows
- **Geometry Utilities**: Bbox calculation and validation
- **State Persistence**: Checkpointing and atomic writes
- **Logging Setup**: Structured logger configuration
- **Processing Summary**: Workflow result reporting (StacManager)
- **Config Validation**: Pre-execution checks
- **Env Var Substitution**: Secure credential handling
