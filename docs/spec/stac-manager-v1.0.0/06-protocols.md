# Protocols & Type Contracts
## STAC Manager v1.0

**Related Documents**:
- [System Overview](./00-system-overview.md)
- [Pipeline Management](./01-pipeline-management.md)

---

## Overview

This document defines the **type-safe contracts** that all modules and extensions must implement. These are Protocol-based interfaces that ensure consistency, enable type checking, and provide clear implementation requirements.

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
            API Fetchers use native async (aiohttp). 
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
        
    def bundle(self, item: dict, context: 'WorkflowContext') -> None:
        """Add an item to the current bundle/buffer."""
        ...
        
    def finalize(self, context: 'WorkflowContext') -> dict:
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
| **DiscoveryModule** | Fetcher | `async def fetch(...) -> AsyncIterator[dict]` |
| **IngestModule** | Fetcher | `async def fetch(...) -> AsyncIterator[dict]` |
| **TransformModule** | Modifier | `def modify(...) -> dict | None` |
| **ScaffoldModule** | Modifier | `def modify(...) -> dict | None` |
| **ExtensionModule** | Modifier | `def modify(...) -> dict | None` |
| **ValidateModule** | Modifier | `def modify(...) -> dict | None` |
| **UpdateModule** | Modifier | `def modify(...) -> dict | None` |
| **OutputModule** | Bundler | `def bundle(...)` + `def finalize(...)` |

---

## 3. Implementation Guidelines

- **Statelessness**: Components should not store mutable state that affects independent items (except for Bundlers managing buffers).
- **Fetcher Concurrency**: Fetchers should use semaphores to honor concurrency limits.
- **Modifier Simplicity**: Keep Modifiers sync for easier unit testing and implementation of business logic.
- **Bundler Atomic Writes**: Bundlers should implement a crash-only design (write-then-rename).


---

## 2. Extension Protocol

Custom STAC extensions **MUST** implement this protocol to be compatible with the ExtensionModule.

### 2.1 Protocol Definition

```python
from typing import Protocol
import pystac

class Extension(Protocol):
    """
    Protocol for STAC extension implementations.
    
    Extensions add domain-specific fields to STAC Items or Collections.
    They must provide schema validation and field application logic.
    """
    
    # Class-level attributes (must be defined)
    extension_name: str      # Short name (e.g., "dgeo", "eo", "custom")
    schema_url: str          # URL to JSON Schema for this extension
    
    def apply(
        self,
        item: pystac.Item | pystac.Collection,
        config: dict
    ) -> pystac.Item | pystac.Collection:
        """
        Apply extension fields to a STAC object.
        
        Args:
            item: STAC Item or Collection to extend
            config: Extension-specific configuration from workflow YAML
        
        Returns:
            The same STAC object with extension fields added and
            schema_url added to stac_extensions array
        
        Raises:
            ExtensionError: If extension cannot be applied
        
        Note:
            **Mutability**: This method modifies the input object in-place AND returns it.
            Returning the object enables method chaining and consistent patterns.
            **Required Action**: It MUST add the extension's schema_url to item.stac_extensions.
        """
        ...
    
    def validate(
        self,
        item: pystac.Item | pystac.Collection
    ) -> tuple[bool, list[str]]:
        """
        Validate extension fields against the extension's JSON schema.
        
        Args:
            item: STAC Item or Collection with extension fields
        
        Returns:
            Tuple of (is_valid, error_messages)
            - is_valid: True if all extension fields are valid
            - error_messages: List of validation errors (empty if valid)
        
        Note:
            This method typically delegates to stac-validator with
            the extension's schema_url.
        """
        ...
```

### 2.2 Implementation Example

```python
import pystac
from stac_validator import stac_validator

class DgeoExtension:
    """DecentralizedGeo STAC Extension for ownership and licensing."""
    
    extension_name = "dgeo"
    schema_url = "https://raw.githubusercontent.com/DecentralizedGeo/dgeo-asset/refs/heads/pgstac-variant/json-schema/schema.json"
    
    def apply(
        self,
        item: pystac.Item,
        config: dict
    ) -> pystac.Item:
        """Apply dgeo extension fields."""
        
        # Add extension to stac_extensions array
        if self.schema_url not in item.stac_extensions:
            item.stac_extensions.append(self.schema_url)
        
        # Add dgeo-specific properties
        if 'ownership' in config:
            item.properties['dgeo:ownership'] = config['ownership']
        
        if 'licensing' in config:
            item.properties['dgeo:licensing'] = config['licensing']
        
        if 'provenance' in config:
            item.properties['dgeo:provenance'] = config['provenance']
        
        return item
    
    def validate(self, item: pystac.Item) -> tuple[bool, list[str]]:
        """Validate dgeo fields against schema."""
        
        validator = stac_validator.StacValidator()
        is_valid = validator.validate_dict(
            item.to_dict(),
            custom_schema=self.schema_url
        )
        
        errors = []
        if not is_valid:
            errors = validator.message if isinstance(validator.message, list) else [validator.message]
        
        return is_valid, errors
```

### 2.3 Extension Registration

Extensions can be referenced in workflows by:

1. **Short name** (if built-in): `extension: "dgeo"`
2. **Full module path** (if custom): `extension: "my_package.extensions.MyExtension"`

**Built-in Registry** (in ExtensionModule):
```python
BUILTIN_EXTENSIONS = {
    'dgeo': 'stac_manager.extensions.dgeo.DgeoExtension',
    'alternate-assets': 'stac_manager.extensions.alternate_assets.AlternateAssetsExtension',
}
```

### 2.4 Key Requirements

- **Schema URL**: Must be a publicly accessible JSON Schema
- **Idempotent**: Calling `apply()` multiple times should be safe
- **Immutability**: Don't modify `config`, only read from it
- **Validation**: Use `stac-validator` library for schema checking

---

## 3. Data Transfer Objects

Data transfer objects used in the pipeline are defined centrally in [Data Contracts](./05-data-contracts.md).

### 3.1 TransformedItem

See [Data Contracts - Intermediate Data Schema](./05-data-contracts.md#2-intermediate-data-schema).

### 3.2 OutputResult

See [Data Contracts - Output Result Schema](./05-data-contracts.md#6-output-result-schema).

---

## 4. Protocol Compliance

### 4.1 Type Checking

Protocols enable static type checking with tools like `mypy`:

```bash
# Run type checker
mypy stac_manager/
```

### 4.2 Runtime Verification

Protocol compliance can be verified at runtime:

```python
from typing import runtime_checkable

@runtime_checkable
class Extension(Protocol):
    ...

# Check if object implements protocol
def verify_extension(ext: Any) -> bool:
    if not isinstance(ext, Extension):
        raise TypeError(f"{ext} does not implement Extension protocol")
    
    # Check required attributes
    if not hasattr(ext, 'extension_name'):
        raise AttributeError("Extension missing 'extension_name'")
    
    return True
```

---

## 5. Summary

The STAC Manager v1.0 architecture uses a strictly decoupled **Pipes and Filters** model:

1.  **Fetcher/Modifier/Bundler**: Specialized interfaces for clear roles.
2.  **Shared Context**: `WorkflowContext` provides infrastructure (logging, errors, checkpoints).
3.  **Wire Format**: `dict` is the standard data exchange format across the pipe for performance and interoperability.
4.  **Plugin Strategy**: The `Extension` protocol allows for modular STAC enhancements.

This ensures the system is high-performance, easy to test, and ready for implementation.
