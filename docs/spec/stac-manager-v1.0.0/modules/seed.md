# Seed Module
## STAC Manager v1.0

**Role**: `Fetcher` (Source)

---

## 1. Purpose
The Seed Module acts as a **Generator Source**, yielding "skeleton" or "seed" STAC Items to be fleshed out by downstream modules (like `ExtensionModule`).

It is primarily used for:
1.  **Zero-to-One Scaffolding**: Creating a new collection where no metadata exists, just a list of IDs.
2.  **Testing**: Injecting mock data into the pipeline.
3.  **Reprocessing**: Reading a simple list of IDs or partial items to trigger re-runs.

## 2. Architecture
- **Mechanism**: Iterates over a configured list of items or loads them from a source file.
- **Async Strategy**: Yields items asynchronously to satisfy the `Fetcher` workflow protocol.
- **Context Integration**: Can populate item fields from `context.data` (e.g., Matrix variables).

## 3. Configuration Schema

```python
from pydantic import BaseModel
from typing import List, Dict, Any, Union, Optional

class SeedConfig(BaseModel):
    items: Optional[List[Union[str, Dict[str, Any]]]] = None
    """
    List of items to yield. Can be:
    - Strings: Treated as item IDs.
    - Dicts: Partial STAC items.
    Example: ["item_01", {"id": "item_02", "datetime": "2023-01-01"}]
    """

    source_file: Optional[str] = None
    """
    Path to an external JSON file containing the list of items.
    Accepts implicit absolute paths or paths relative to CWD.
    File content must be a JSON Array of strings or objects.
    """

    defaults: Optional[Dict[str, Any]] = None
    """
    Default values to apply to all generated items (e.g. valid timestamps, geometries).
    Merges with item-specific data (Item data takes precedence).
    """
```

### 3.1 Example Usage (YAML)

```yaml
- id: seed_items
  module: SeedModule
  config:
    items:
      - "LC08_L1TP_001002_20220101"
      - id: "LC08_L1TP_001002_20220102"
        properties: 
          cloud_cover: 0.0
    defaults:
      collection: "landsat-c2-l2"
      properties:
        instrument: "OLI_TIRS"
```

## 4. I/O Contract

**Input (Workflow Context)**:
- `config` (Module Configuration):
  - `items`: Explicit list.
  - `source_file`: External source.
- `context.data` (injected by Matrix Strategy):
  - `collection_id`: Populates item `collection` field if not set in item or defaults.

**Output**:
```python
AsyncIterator[dict] 
# Yields the items defined in config, normalized to dicts.
```

## 5. Error Handling
- **Config Error**: Raised if neither `items` nor `source_file` is provided, or if `source_file` format is invalid.
- **File Error**: Raised if `source_file` cannot be read.

## 6. Logic (Pseudocode)

```python
async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
    """
    Yields items from config or source file.
    """
    items_list = []

    # 1. Load Items
    if self.config.source_file:
        # Load JSON array from file
        file_items = load_json(self.config.source_file)
        if not isinstance(file_items, list):
            raise ConfigError("source_file must contain a JSON array")
        items_list.extend(file_items)

    if self.config.items:
        items_list.extend(self.config.items)

    if not items_list:
        context.logger.warning("SeedModule: No items to yield.")
        return

    # 2. Iterate and Yield
    for item_entry in items_list:
        item_dict = {}

        # Normalize to dict
        if isinstance(item_entry, str):
            item_dict = {"id": item_entry}
        elif isinstance(item_entry, dict):
            item_dict = item_entry.copy()
        else:
            raise ValueError(f"Invalid item format: {type(item_entry)}")

        # 3. Apply Defaults
        # Defaults are the base, Item data overrides them
        if self.config.defaults:
            # Note: Deep merge might be preferred for properties, 
            # but simple update is standard for top-level fields.
            # Here we assume a shallow merge for simplicity unless specified otherwise.
            final_item = self.config.defaults.copy()
            final_item.update(item_dict)
            item_dict = final_item

        # 4. Context Enrichment
        # If 'collection' is missing, try to get from context (Matrix Strategy)
        if "collection" not in item_dict and "collection_id" in context.data:
            item_dict["collection"] = context.data["collection_id"]

        yield item_dict
```
