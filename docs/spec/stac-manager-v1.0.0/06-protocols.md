# Protocols & Type Contracts
## STAC Manager v1.0

**Related Documents**:
- [System Overview](./00-system-overview.md)
- [Pipeline Management](./01-pipeline-management.md)

---

## Overview

This document defines the **type-safe contracts** that all modules must implement. These are Protocol-based interfaces that ensure consistency, enable type checking, and provide clear implementation requirements.

---

## 1. Pipeline Roles (Protocols)

The STAC Manager architecture follows a **Pipes and Filters** pattern. Components implement one of three specialized protocols based on their role in the pipeline.

### 1.1 Fetcher (Source)
Responsible for finding or retrieving metadata and originating the item stream.

```python
from typing import Protocol, AsyncIterator, Any
from dataclasses import dataclass
import logging

class Fetcher(Protocol):
    """Retrieves items from an external (API) or local (File) source."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with step-specific configuration."""
        ...
        
    async def fetch(self, context: 'WorkflowContext') -> AsyncIterator[dict]:
        """
        Originate a stream of STAC Items or Collections.
        
        Note:
            API Fetchers use native async (Non-blocking I/O). 
            File Fetchers use threads (via run_in_executor) to yield items asynchronously.
        """
        ...
```

### 1.2 Modifier (Processor)
Responsible for transforming, validating, or enriching individual items in-stream.

```python
class Modifier(Protocol):
    """Transforms or validates a single STAC Item/Collection."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with step-specific configuration."""
        ...
        
    def modify(self, item: dict, context: 'WorkflowContext') -> dict | None:
        """
        Process a single item.
        
        Returns:
            - The modified dict
            - None if the item should be filtered out (dropped)
            
        Note:
            Modifiers are SYNC. StacManager handles the async pipeline loop.
        """
        ...
```

### 1.3 Bundler (Sink)
Responsible for aggregating and persisting the finalized items.

```python
class Bundler(Protocol):
    """Finalizes and writes items to storage (Parquet, JSON, etc)."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with step-specific configuration."""
        ...
        
    async def bundle(self, item: dict, context: 'WorkflowContext') -> None:
        """
        Add an item to the current bundle/buffer.
        
        Note:
            **ASYNC**: This method MUST be non-blocking. 
            Implementations should buffer items and use `run_in_executor` 
            (or async libraries like aiohttp) when flushing to disk/network.
        """
        ...
        
    async def finalize(self, context: 'WorkflowContext') -> dict:
        """
        Commit any remaining buffers and return an execution manifest.
        
        Returns:
            OutputResult-compatible dict containing files_written, etc.
        """
        ...
```

---

## 2. Shared Context

### 2.1 WorkflowContext (Shared Singleton)

The `WorkflowContext` is a **shared singleton** object instantiated by the `StacManager` and passed into every `fetch`, `modify`, and `bundle` call. It provides access to cross-cutting infrastructure.

```python
from dataclasses import dataclass
from typing import Any
import logging

@dataclass
class WorkflowContext:
    """Shared state passed to all components during execution."""
    workflow_id: str                      # Unique execution identifier
    config: dict                          # Global workflow configuration (WorkflowDefinition)
    logger: logging.Logger                # Structured logger instance
    failure_collector: 'FailureCollector' # Error aggregator
    checkpoints: 'CheckpointManager'      # Manager for state persistence
    data: dict[str, Any]                  # Inter-step ephemeral data store
```

### 2.2 Role Assignments

| Module | Role | Protocol Implementation |
|:-------|:-----|:------------------------|
| **IngestModule** | Fetcher | `async def fetch(...) -> AsyncIterator[dict]` |
| **SeedModule** | Fetcher | `async def fetch(...) -> AsyncIterator[dict]` |
| **TransformModule** | Modifier | `def modify(...) -> dict | None` |
| **ExtensionModule** | Modifier | `def modify(...) -> dict | None` |
| **ValidateModule** | Modifier | `def modify(...) -> dict | None` |
| **UpdateModule** | Modifier | `def modify(...) -> dict | None` |
| **OutputModule** | Bundler | `async def bundle(...)` + `async def finalize(...)` |

---

## 3. Implementation Guidelines

- **Statelessness**: Components should not store mutable state that affects independent items (except for Bundlers managing buffers).
- **Fetcher Concurrency**: Fetchers should use semaphores to honor concurrency limits.
- **Modifier Simplicity**: Keep Modifiers sync for easier unit testing and implementation of business logic.

### 3.1 Bundler Async I/O
Bundlers **MUST** implement buffering and non-blocking I/O.
- **Good**: Buffer 100 items -> `await loop.run_in_executor(None, write_batch, batch)`
- **Bad**: `with open(...)` inside `bundle()` (Blocks the entire pipeline)

### 3.2 Bundler Atomic Writes
 Bundlers should implement a crash-only design (write-then-rename).
 
---

## 4. Data Transfer Objects

Data transfer objects used in the pipeline are defined centrally in [Data Contracts](./05-data-contracts.md).

### 4.1 Use of Dicts
All modules communicate using the standard Python `dict` as the primary data structure, aligning with the "Wire Format" definition in Data Contracts.

### 4.2 OutputResult

See [Data Contracts - Output Result Schema](./05-data-contracts.md#6-output-result-schema).

---

## 5. Protocol Compliance

### 5.1 Type Checking

Protocols enable static type checking with tools like `mypy`:

```bash
# Run type checker
mypy stac_manager/
```

### 5.2 Runtime Verification

Protocol compliance can be verified at runtime:

```python
from typing import runtime_checkable

@runtime_checkable
class Fetcher(Protocol):
    ...

# Check if object implements protocol
def verify_fetcher(obj: Any) -> bool:
    if not isinstance(obj, Fetcher):
        raise TypeError(f"{obj} does not implement Fetcher protocol")
    return True
```

---

## 6. Summary

The STAC Manager v1.0 architecture uses a strictly decoupled **Pipes and Filters** model:

1.  **Fetcher/Modifier/Bundler**: Specialized interfaces for clear roles.
2.  **Shared Context**: `WorkflowContext` provides infrastructure (logging, errors, checkpoints).
3.  **Wire Format**: `dict` is the standard data exchange format across the pipe for performance and interoperability.

This ensures the system is high-performance, easy to test, and ready for implementation.

