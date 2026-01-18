# Research: Memory Management & Caching Strategy

**Status**: Accepted Strategy
**Related Components**: `IngestModule`, `OutputModule`, `WorkflowOrchestrator`, `TransformModule`
**NOTE**: This document is a research artifact that will be applied in version 1.1.

---

## 1. Executive Summary

To handle processing scales of 1M+ items without OOM (Out-Of-Memory) crashes, STAC Manager adopts a **3-Tiered Memory Strategy**:

1.  **Strict Streaming (Level 1)**: All modules communicate via `AsyncIterator[Item]`. No lists of Items are ever instantiated by default.
2.  **Micro-Batching (Level 2)**: Operations requiring vectorization (validation, writing) accumulate small buffers (e.g., 500 items) and flush immediately.
3.  **Parquet Spill (Level 3)**: Workflows requiring global operations (e.g., "Sort by Date", "Deduplicate Global") must materialize the entire dataset to a temporary Parquet file on disk, then stream from that file.

---

## 2. Memory Profiling & Constraints

### 2.1 The Cost of `pystac.Item`
A standard `pystac.Item` is significantly heavier than its JSON representation due to Python object overhead and validation logic.

-   **Raw JSON**: ~2-5 KB
-   **pystac.Item (in-memory)**: ~30-50 KB (depending on link count)
-   **TransformedItem (TypedDict)**: ~10-15 KB

**Implication**:
-   **100k Items in List**: ~5 GB RAM (Danger Zone)
-   **1M Items in List**: ~50 GB RAM (Guaranteed OOM on standard workers)

### 2.2 Bottlenecks
1.  **Link Resolution**: `pystac` attempts to resolve links. If `root` or `parent` links are traversed, the entire catalog tree can be inadvertently loaded.
2.  **Accumulators**: `results = [await step(i) for i in items]` is an anti-pattern.
3.  **Async Concurrency**: Too many concurrent tasks (e.g., `asyncio.gather(*[process(i) for i in 100000_items])`) will create 100k coroutines, blowing up the event loop and memory.

---

## 3. Detailed Strategy

### 3.1 Tier 1: Strict Generator Pipelines
All modules must implement `execute` as a generator, yielding items as soon as they are ready.

**Pattern**:
```python
# GOOD
async def execute(self, context):
    async for item in previous_step:
        result = process(item)
        yield result

# BAD
async def execute(self, context):
    items = [i async for i in previous_step]  # OOM Risk
    return process_all(items)
```

**Concurrency Control**:
Use `asyncio.Semaphore` or `asyncio.Queue` to limit active processing tasks, rather than unbounded `gather`.

### 3.2 Tier 2: Micro-Batching (The "Chunk" Pattern)
For components that *need* to see multiple items (e.g., `stac-geoparquet` writing row groups, or efficient validation), we use **Micro-Batching**.

**Configuration**:
-   `batch_size`: Default `500` Items.

**Mechanism**:
Accumulate `batch_size` items in a list, then process/write/flush. This bounds memory usage to `500 * 50KB = 25MB`, which is safe.

```python
batch = []
async for item in source:
    batch.append(item)
    if len(batch) >= CONFIG.BATCH_SIZE:
        await process_batch(batch)
        batch = []
if batch:
    await process_batch(batch)
```

### 3.3 Tier 3: The "Parquet Spill" (Global Operations)
Some operations cannot be streamed (e.g., Global Deduplication, Global Time Sorting, Tiling).

**Trigger**: Users must explicitly configure a "Blocking" step or the Orchestrator detects a "Global" requirement.

**Implementation**:
1.  **Spill**: The step reads the *entire* input stream and writes it to a temporary Parquet dataset (`.tmp/workflow_id/step_id/buffer.parquet`).
2.  **Process**: The operation `duckdb` or `pyarrow` to perform the sort/dedup on the Parquet files (Out-of-Core processing).
3.  **Resume**: The step yields a generator reading from the processed Parquet files.

This turns O(N) RAM usage into O(1) RAM usage, effectively effectively utilizing disk (NVMe preferred) as extended memory.

---

## 4. Component-Specific Strategies

### 4.1 IngestModule (Producer)
-   **Strategy**: Pure Generator.
-   **Memory**: Minimal.
-   **Constraint**: Must handle API pagination lazily. Never fetch all pages before yielding.

### 4.2 TransformModule (Processor)
-   **Strategy**: Semaphore-controlled Concurrency.
-   **Data Structure**: Convert `pystac.Item` to `TransformedItem` (dict) ASAP if the transformation logic allows, to reduce overhead.
-   **Link Management**: Explicitly `item.clear_links()` if retaining the item object generally, though ideally we simply drop the reference.

### 4.3 OutputModule (Consumer)
-   **Strategy**: Buffered Writer.
-   **Format**: `stac-geoparquet`.
-   **Buffer**: Accumulate items until `chunk_size` (e.g., 200MB) or `item_count` (e.g., 10k) is reached.
-   **Flush**: Write a Parquet **Row Group**.
-   **Memory Cap**: If the buffer exceeds 75% of assigned memory, force flush.

---

## 5. Configuration Options

To support this strategy, the `WorkflowContext` config will include:

| Key | Default | Description |
| :--- | :--- | :--- |
| `execution.batch_size` | `100` | Number of items to process in vectorized steps |
| `execution.max_concurrency` | `10` | Max concurrent async tasks per worker |
| `execution.spill_threshold_mb` | `512` | (Future) RAM usage trigger to force disk spill |

## 6. Garbage Collection (GC)
Python's GC is generally sufficient for acyclic graphs. However, `pystac` can create cycles (Item <-> Collection).
-   **Action**: `WorkflowOrchestrator` typically effectively cleans up between steps by design (stateless modules).
-   **Safety**: If memory leaks are observed, insert explicit `gc.collect()` calls after major batch flushes in the `OutputModule`.
