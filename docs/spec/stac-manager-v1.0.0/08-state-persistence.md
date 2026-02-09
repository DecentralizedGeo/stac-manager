# State Persistence & Recovery
## STAC Manager v1.0

**Related Documents**:
- [Utilities](./07-utilities.md)
- [Pipeline Management](./01-pipeline-management.md)

---

## 1. Overview

STAC Manager workflows often process millions of items and run for hours. Hardware failures (OOM, preemption, network cut) are inevitable. This document defines the **Checkpoint System** that enables workflows to resume execution without re-processing successfully handled items.

## 2. Architecture

The persistence model relies on **local state files** that track the set of unique identifiers (IDs) that have been successfully processed.

### 2.1 Design Principles

1.  **Crash-Only Design**: The system assumes it could crash at any moment. State is only considered "saved" when it is atomically committed to disk.
2.  **Idempotency**: Resuming start-up loads the state and treats the "processed" set as an ignore-list.
3.  **Efficiency**: Using **Parquet** for state storage allows efficient I/O and compression for millions of records (vs. JSON or SQLite).

---

## 3. Data Schema

Checkpoint files are Parquet tables storing the unique keys of processed items.

### 3.1 Checkpoint File Schema

| Column | Type | Description |
| :--- | :--- | :--- |
| `item_id` | string | Unique STAC Item ID |
| `step_id` | string | The workflow step that completed this item |
| `timestamp` | string | ISO 8601 timestamp (e.g. `2024-01-01T12:00:00Z`) |
| `status` | string | `success` or `failure` |

**Path Convention**:
`./checkpoints/{workflow_id}/{step_id}.parquet`

---

## 4. CheckpointManager

The `CheckpointManager` handles the reading and writing of state. It abstracts the Parquet I/O and atomic file operations.

### 4.1 Interface

```python
from pathlib import Path
from typing import TypedDict

class CheckpointRecord(TypedDict):
    item_id: str
    step_id: str
    timestamp: str      # ISO 8601 string
    status: str

class CheckpointManager:
    """
    Manages persistence of processing state using Parquet files.
    
    The StacManager creates one instance per step, passing the step_id.
    Path convention: {directory}/{workflow_id}/{step_id}/
    """

    def __init__(self, directory: Path, workflow_id: str, step_id: str | None = None):
        """
        Initialize manager and load existing checkpoint state.
        
        Args:
            directory: Base checkpoint directory
            workflow_id: Unique workflow identifier
            step_id: Step identifier (optional for global checkpoint manager)
            
        Behavior:
            - Creates checkpoint directory if missing
            - Loads all `*.parquet` files from checkpoint path
            - Builds in-memory set of processed `item_id` values for O(1) lookup
            - Deduplicates item_ids if found in multiple partition files
        """
        ...

    def contains(self, item_id: str) -> bool:
        """
        Check if an item has already been processed.
        
        Args:
            item_id: STAC Item ID to check
            
        Returns:
            True if item_id exists in the checkpoint state (O(1) lookup)
        """
        ...

    def save(self, new_records: list[CheckpointRecord]) -> None:
        """
        Atomically append new records to the checkpoint using partitioned writes.
        
        Args:
            new_records: List of CheckpointRecord dicts to persist
            
        Implementation Pattern (Atomic Write):
            1. Generate unique filename: `checkpoint_{timestamp}_{uuid}.parquet`
            2. Write records to temporary file: `.tmp/{filename}`
            3. Move temp file to checkpoint directory atomically
            4. Update in-memory processed set with new item_ids
            
        Note:
            Uses partitioned batches to avoid rewriting large files.
            Each call creates a new partition file in the checkpoint directory.
        """
        ...
    
    def get_checkpoint_path(self) -> Path:
        """
        Return full path to checkpoint directory for this workflow/step.
        
        Returns:
            Path object: {directory}/{workflow_id}/{step_id or "global"}/
        """
        ...
```

---

## 5. Atomic Write Strategy

To prevent data corruption during a crash while writing, we strictly use the **Write-Rename** pattern. Since Parquet files are immutable/block-based, we either:
1.  **Append** (if supported by engine and safe)
2.  **Rewrite** (simplest for small-medium batches)
3.  **Partition** (write `part-{timestamp}.parquet` for each batch)

**Selected Strategy for v1.0**: **Partitioned Batches**

Instead of rewriting one giant file, we write small batch files. This completely eliminates the risk of corrupting the main index and makes writes O(1).

### 5.1 Partitioned Implementation

**Directory**: `./checkpoints/{workflow_id}/{step_id}/`

**Write Process**:
1.  `IngestModule` processes a batch of 100 items.
2.  `CheckpointManager.save(batch)` is called.
3.  Create filename: `checkpoint_{timestamp}_{uuid}.parquet`
4.  Write dataframe to temporary path: `.tmp/checkpoint_....parquet`
5.  Move temporary file to target directory.

**Read Process**:
1.  Glob all `*.parquet` files in directory.
2.  Read and concatenate (`pd.read_parquet(dir)` supports this natively).
3.  Deduplicate IDs.

---

## 6. Integration & Ownership

### 6.1 Orchestrator (StacManager) Ownership
The `StacManager` is responsible for the lifecycle of state persistence:
1.  **Instantiation**: It creates a `CheckpointManager` instance for each step in the pipeline.
2.  **Context Injection**: It attaches this instance to the `WorkflowContext.checkpoints`.

### 6.2 The "Auto-Skip" Pattern (Modifiers)
To keep module logic pure, the **`StacManager`** (not the module) should handle the primary "skip" check for Modifiers:

```python
# Inside StacManager loop
async for item_dict in stream:
    # 1. Automatic Resume Check
    if context.checkpoints.contains(item_dict['id']):
        context.logger.debug(f"Skipping {item_dict['id']} (already processed)")
        continue
    
    # 2. Execute Modifier Logic
    result = modifier.modify(item_dict, context)
    
    # 3. Auto-Save (Optional/Configurable)
    if result:
        context.checkpoints.save([{'item_id': result['id'], ...}])
```

### 6.3 Explicit Handling (Fetchers & Bundlers)
- **Fetchers**: May access `context.checkpoints` to perform optimized API-side skipping (e.g., skipping whole pages).
- **Bundlers**: Call `context.checkpoints.save(batch)` after successfully writing data to disk/storage.

---

## 7. Performance Considerations

- **Memory**: A set of 10M item IDs (~20 chars each) takes ~1-2 GB RAM. This is acceptable for modern processing nodes.
- **I/O Efficiency**: Partitioned Parquet writing is O(1) and eliminates large rewriting costs during long-running jobs.
