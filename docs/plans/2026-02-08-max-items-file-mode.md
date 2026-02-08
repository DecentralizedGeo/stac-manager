# Max Items for File Ingest Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement `max_items` support for file-based ingestion to limit processed items, ensuring parity with API mode.

**Architecture:** Modify `IngestModule.fetch` to check `max_items` configuration during iteration of file sources (file, directory, collection) and break the loop when the limit is reached. The `limit` parameter will be explicitly ignored in file mode as it is intended for API page sizes.

**Tech Stack:** Python, STAC Manager, Pytest

---

## Phase 1: Implementation

### Task 1: Create and Verify Failing Test

**Files:**
- Create: `tests/unit/modules/test_ingest_limits.py`
- Modify: `src/stac_manager/modules/ingest.py`

**Step 1: Create the failing unit test file**

Create `tests/unit/modules/test_ingest_limits.py` with three test cases:
1.  `test_file_ingest_max_items_limit`: Set `max_items=5` on a 10-item file. Assert 5 items returned.
2.  `test_file_ingest_limit_ignored`: Set `limit=5` on a 10-item file. Assert 10 items returned (limit ignored).
3.  `test_file_ingest_no_limit`: No limits set. Assert 10 items returned.

**Step 2: Run test to verify it fails**

Run: `pytest tests/unit/modules/test_ingest_limits.py`
Expected: 
- `test_file_ingest_max_items_limit`: FAIL (returns 10, expects 5)
- `test_file_ingest_limit_ignored`: PASS (returns 10, expects 10)
- `test_file_ingest_no_limit`: PASS (returns 10, expects 10)

**Step 3: Implement `max_items` logic**

**Files:**
- Modify: `src/stac_manager/modules/ingest.py`

In `IngestModule.fetch`:
- Identify the loop handling file mode ingestion (`if self.config.mode == "file":`).
- Inside the loop, check if `self.config.max_items` is set.
- Maintain a valid count of yielded items (already exists).
- If `count >= max_items`, break the loop.
- Log an info message when the limit is reached.

```python
    # In IngestModule.fetch:
    
    # ... inside the file mode loop ...
    if self.config.mode == "file":
        async for item in self._fetch_from_file():
            # Check limit BEFORE yielding
            if self.config.max_items is not None and count >= self.config.max_items:
                self.logger.info(f"Reached max_items limit: {self.config.max_items}")
                break

            if item is None:
                continue
            
            self.logger.debug(f"Fetched item {item.get('id', 'unknown')}")
            yield item
            count += 1
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/unit/modules/test_ingest_limits.py`
Expected: All tests PASS.

**Step 5: Cleanup and Commit**

- Remove reproduction script `tests/repro_limit.py`.
- Commit changes.

```bash
git add src/stac_manager/modules/ingest.py tests/unit/modules/test_ingest_limits.py
git rm tests/repro_limit.py
git commit -m "feat: implement max_items limit for file ingestion"
```
