# Seed Module
## STAC Manager v1.0

**Role**: `Fetcher` (Source)

---

## 1. Purpose
The Seed Module acts as a **Generator Source**, yielding "skeleton" or "seed" STAC Items (often just IDs) to be fleshed out by downstream modules (like `ExtensionModule`).

It is primarily used for:
1.  **Zero-to-One Scaffolding**: Creating a new collection where no metadata exists, just a list of IDs.
2.  **Testing**: Injecting mock data into the pipeline.

## 2. Architecture
- **Mechanism**: Iterates over a configured list of item definitions.
- **Async Strategy**: Yields items asynchronously to satisfy the `Fetcher` workflow protocol.

## 3. Configuration Schema

```python
from pydantic import BaseModel
from typing import List, Dict, Any

class SeedConfig(BaseModel):
    items: Optional[List[str]] = None
    """
    List of Item IDs to yield. 
    Example: ["item_01", "item_02"]
    """

    source_file: Optional[str] = None
    """
    Path to an external JSON file containing the list of items.
    """

    defaults: Optional[Dict[str, Any]] = None
    """
    Default values to apply to all generated items (e.g. valid timestamps, geometries).
    Merges with item-specific data.
    """
```

### 3.1 Example Usage (YAML)

```yaml
- id: seed_items
  module: SeedModule
  config:
    items:
      - "LC08_L1TP_001002_20220101"
      - "LC08_L1TP_001002_20220102"
    defaults:
        collection: "landsat-c2-l2"
```

## 4. I/O Contract

**Input (Workflow Context)**:
- `config` (Module Configuration):
  - `items`: List of explicit IDs.
  - `source_file`: Path to external list.
- `context.data` (injected by Matrix Strategy):
  - `collection_id`: Populates item `collection` field if not set in defaults.
  - Matrix Variables: Available for string interpolation.

**Output**:
```python
AsyncIterator[dict] 
# Yields the items defined in config, with 'collection' populated.
```

## 5. Error Handling
- **Config Error**: Config validation ensures `items` is a list.
