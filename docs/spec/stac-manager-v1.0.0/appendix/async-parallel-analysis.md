# Deep Analysis: Async and Parallel Processing with pystac-client

## 1. Executive Summary

[pystac-client](https://pystac-client.readthedocs.io/) is a synchronous library built on [requests](https://requests.readthedocs.io/). [PySTAC](https://pystac.readthedocs.io/) handles data modeling and I/O via [`StacIO`](https://pystac.readthedocs.io/en/stable/concepts.html#io-in-pystac). Neither supports native `async/await`.

**Key Finding**: ~90% of time is spent on network I/O ([source](https://nbviewer.org/gist/TomAugspurger/ceadc4b2f8b7e4263ff172ee1ea76dbb)). Async is beneficial for network requests; parallelization (threads) is beneficial for CPU-bound serialization and file I/O.

**Community Recommendation**: "If folks want to do async work, they should write their own IO and just use the PySTAC data structures." ([Issue #690](https://github.com/stac-utils/pystac/issues/690#issuecomment-1608082909))

---

## 2. When to Use Async vs Sync vs Parallel

| Scenario | Recommended Pattern | Rationale |
|:---------|:--------------------|:----------|
| **Fetching from STAC API** | `aiohttp` / `httpx` (Async) | 90% time is I/O wait. Async maximizes throughput on single thread. |
| **Parsing JSON → pystac.Item** | Sync (inline) | Fast (~1ms/item). GIL limits thread benefit. |
| **Saving Items to disk** | `ThreadPoolExecutor` (Parallel) | File I/O releases GIL. Parallelism helps significantly. |
| **`Item.to_dict()` with links** | Call `item.clear_links()` first | Link resolution triggers sync HTTP. 1s → 200µs after clearing ([#546](https://github.com/stac-utils/pystac/issues/546)). |
| **Serialization (50k+ items)** | `ProcessPoolExecutor` (Parallel) | Serialization adds ~25s overhead. CPU-bound. Parallelize across processes. |

---

## 3. Performance Benchmarks (Community Data)

### 3.1 Search & Fetch
- **50s for 300 items**: `item_collection()` with sync requests ([#659](https://github.com/stac-utils/pystac-client/issues/659)).
- **Limit Parameter**: Higher `limit=` reduces round-trips but increases memory per page. Default is 100.

### 3.2 Saving
| Items | Collections | Save Time | Notes |
|------:|------------:|----------:|:------|
| 2,000 | 1 | ~6s | ([#1207](https://github.com/stac-utils/pystac/issues/1207)) |
| 10,000 | 1 | ~100s | Exponential growth due to link recalculation |
| 10,000 | 5 (2k each) | ~25s | **4x faster** when sharded into smaller collections |
| 100,000 | 1 | Hours | Profile shows `normalize_hrefs` dominates |

**Top Offenders** ([#1207](https://github.com/stac-utils/pystac/issues/1207#issuecomment-2405500286)):
1. `normalize_hrefs()` - O(n²) link resolution
2. `to_dict()` with attached links

### 3.3 Memory
- **100MB/min/worker**: Long-lived processes grow memory from `ResolvedObjectCache` ([#842](https://github.com/stac-utils/pystac-client/issues/842)).
- **Mitigation**: Periodically nuke client or use short-lived subprocesses.

---

## 4. Async I/O Architecture

### 4.1 The StacIO Interface
PySTAC delegates all I/O through `pystac.StacIO`. This is **pluggable** but **synchronous-only** as of v1.x.

```python
# Custom StacIO for cloud storage (sync, from docs)
class GCSStacIO(DefaultStacIO):
    def __init__(self):
        self.fs = gcsfs.GCSFileSystem()
    
    def read_text(self, source, *args, **kwargs):
        with self.fs.open(source) as f:
            return f.read()
```

For async, bypass StacIO entirely and use raw HTTP clients.

### 4.2 Native Async Pattern (Recommended for IngestModule)

```python
import aiohttp
import pystac

async def search_items_async(url, params, semaphore):
    """Fetch items using native async, parse with pystac."""
    async with semaphore:  # Concurrency control
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{url}/search", json=params) as resp:
                data = await resp.json()
                for feat in data['features']:
                    yield pystac.Item.from_dict(feat)
```

### 4.3 stac-asset Pattern
[stac-asset](https://github.com/stac-utils/stac-asset) uses `async/await` for asset downloads:

```python
# From stac-asset source
async def download(item: pystac.Item, directory: Path) -> pystac.Item:
    async with aiohttp.ClientSession() as session:
        # ...async download logic...
```

---

## 5. Parallelization Patterns

### 5.1 Parallel Saving (File I/O)

```python
from concurrent.futures import ThreadPoolExecutor
import pystac

def save_item(item: pystac.Item, path: str):
    with open(path, 'w') as f:
        f.write(json.dumps(item.to_dict()))

# Parallel execution
with ThreadPoolExecutor(max_workers=10) as pool:
    futures = [pool.submit(save_item, item, f"./items/{item.id}.json")
               for item in items]
    for f in futures:
        f.result()  # Raises exceptions
```

### 5.2 Avoid: Parallel `to_dict()` with Links
`to_dict()` can trigger sync HTTP for link resolution. Always call `clear_links()` first or ensure items are "orphaned" (no parent/root).

### 5.3 When to Use ProcessPoolExecutor
For CPU-bound serialization of 50k+ items, processes bypass GIL:

```python
from concurrent.futures import ProcessPoolExecutor

def serialize_batch(items: list) -> list[dict]:
    return [item.to_dict() for item in items]

with ProcessPoolExecutor(max_workers=4) as pool:
    batches = chunk(all_items, 1000)
    results = list(pool.map(serialize_batch, batches))
```

---

## 6. Memory Management Strategies

### 6.1 The ResolvedObjectCache Problem
PySTAC caches resolved objects (parents, children) indefinitely. In long-lived processes:
- Memory grows **100MB/min** per worker ([#842](https://github.com/stac-utils/pystac-client/issues/842)).
- The cache has **no eviction policy**.

### 6.2 Mitigations
1. **Short-lived workers**: Spawn subprocesses periodically.
2. **Orphan items**: Set `root=None` when deserializing to skip caching.
3. **Explicit cleanup**: Manually delete references after batch processing.

```python
# Process search results without caching
for page in search.pages():
    for item_dict in page['features']:
        item = pystac.Item.from_dict(item_dict)
        item.set_root(None)  # Prevent cache attachment
        yield item
```

---

## 7. Recommendations for STAC Manager

| Module | Pattern | Notes |
|:-------|:--------|:------|
| **IngestModule** | Async (`aiohttp`) | 90% I/O bound. Use semaphores for concurrency control. |
| **TransformModule** | Sync | CPU-bound mapping. Fast enough inline. |
| **OutputModule** | Parallel (ThreadPool) | File I/O benefits from threads. Use atomic writes. |
| **ValidateModule** | Sync or ProcessPool | `jsonschema` is CPU-bound. Benchmark before optimizing. |

### 7.1 Key Takeaways
1. **Async for network, threads for file I/O, processes for heavy CPU.**
2. **Beware `to_dict()` with links** - clears_links() mandatory in pipelines.
3. **Shard large collections** - Save time is O(n²) within a single collection.
4. **Memory leaks from caching** - Use short-lived processes or orphan items.

---

## 8. References

### Core Documentation
- [PySTAC I/O Concepts](https://pystac.readthedocs.io/en/stable/concepts.html#io-in-pystac)
- [pystac-client Documentation](https://pystac-client.readthedocs.io/)
- [stac-asset API](https://github.com/stac-utils/stac-asset?tab=readme-ov-file#api)

### Performance Issues
- [#546: Slowness in `Item.to_dict()`](https://github.com/stac-utils/pystac/issues/546)
- [#659: Efficiency of `item_collection()`](https://github.com/stac-utils/pystac-client/issues/659)
- [#690: Write Items in parallel](https://github.com/stac-utils/pystac/issues/690)
- [#1207: Save time exponential with item count](https://github.com/stac-utils/pystac/issues/1207)
- [#1545: Async StacIO proposal](https://github.com/stac-utils/pystac/issues/1545)

### Memory & Long-Lived Processes
- [#842: Memory management in long-lived processes](https://github.com/stac-utils/pystac-client/issues/842)

### Benchmarks
- [Tom Augspurger: STAC Query Perf Notebook](https://nbviewer.org/gist/TomAugspurger/ceadc4b2f8b7e4263ff172ee1ea76dbb)
- [Tom Augspurger: Async pystac-client Notebook](https://gist.github.com/TomAugspurger/50c3573d39213a2cb450d02074e4db01)
