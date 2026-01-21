# Update Module
## STAC Manager v1.0

**Role**: `Modifier` (Processor)

---

## 1. Purpose
Modifies existing STAC Items passing through the stream. It supports both **Global Updates** (applied to all items) and **Item-Specific Patches** (applied to specific IDs).

Common uses:
- Adding a global license or provider.
- Patching specific bad metadata fields for a list of items.
- Removing deprecated fields.
- Updating the `updated` timestamp.

## 2. Architecture

### 2.1 Modification Logic
The module applies changes in the following order for each item:
1.  **Global Removals**: Delete fields specified in `removes`.
2.  **Global Updates**: Apply key-value pairs from `updates` to all items.
3.  **Item-Specific Patches**: If a `patch_file` is loaded, look up the item's ID and apply those specific updates.
4.  **Timestamp**: If `auto_update_timestamp` is True, set `properties.updated` to the current UTC time.

### 2.2 Path Syntax
- Uses **Simple Dot Notation** (e.g., `properties.eo:cloud_cover`, `assets.thumbnail.href`).
- **Not JMESPath**: Unlike the Transform module (which uses JMESPath for *querying* complex source data), the Update module uses simple path setters for *modification*.

### 2.3 Structural Integrity (`create_missing_paths`)
- When setting `properties.foo.bar = "value"`:
    - If `properties` exists but `foo` does not:
        - `create_missing_paths=True`: Creates `foo` as a dict, then sets `bar`.
        - `create_missing_paths=False`: Raises an error (Target path not found).

## 3. Configuration Schema

```python
from pydantic import BaseModel
from typing import Dict, Any, List, Optional, Literal

class UpdateConfig(BaseModel):
    # --- Global Modifications (All Items) ---
    updates: Optional[Dict[str, Any]] = None
    """
    Global key-value pairs to set. 
    Key: Dot-notation path (e.g. "properties.license").
    Value: The value to set.
    """
    
    removes: Optional[List[str]] = None
    """
    List of dot-notation paths to remove from the item.
    """

    # --- Item-Specific Modifications ---
    patch_file: Optional[str] = None
    """
    Path to a JSON file mapping Item IDs to update dictionaries.
    Format: {"item_id_1": {"properties.cloud_cover": 50}, ...}
    
    > [!WARNING]
    > In V1.0, this file is loaded entirely into memory. 
    > Be cautious with very large patch files (>100MB).
    """

    # --- Behavior ---
    mode: Literal['merge', 'replace'] = 'merge'
    """
    Merge strategy for dictionary values. Lists are always replaced.
    """
    
    create_missing_paths: bool = True
    """
    If True, creates missing nested dictionaries when setting a value.
    Example: Setting 'properties.new_ext.field' will create 'new_ext' dict if missing.
    """
    
    auto_update_timestamp: bool = True
    """
    If True, sets/overwrites 'properties.updated' with current UTC timestamp.
    """
```

### 3.1 Example Usage (YAML)

```yaml
- id: patch_metadata
  module: UpdateModule
  config:
    # 1. Global: Set license for everyone
    updates:
      "properties.license": "CC-BY-4.0"
      "properties.providers": 
        - name: "My Corp"
          roles: ["processor"]

    # 2. Global: Remove old field
    removes:
      - "properties.deprecated_field"

    # 3. Specific: Fix cloud cover for specific items from file
    patch_file: "./patches/manual_fixes.json"

    # 4. Behavior
    auto_update_timestamp: true
    create_missing_paths: true
```

**Example `manual_fixes.json`**:
```json
{
  "LC08_L1TP_001002_20220101": {
    "properties.eo:cloud_cover": 12.5
  },
  "LC08_L1TP_001002_20220102": {
    "properties.sun_azimuth": 145.2
  }
}
```

## 4. I/O Contract

**Input (Workflow Context)**:
- Stream of STAC Items (`context.data`).

**Output**:
- Stream of **Modified** STAC Items.

```python
def modify(self, item: dict, context: WorkflowContext) -> dict:
    """
    Applies removals, global updates, and patch-file updates to the item.
    Returns the modified item dict.
    """
    ...
```

## 5. Error Handling
- **Path Not Found**: If `create_missing_paths=False` and path is missing, fail the item.
- **Removes**: If removing a non-existent path, ignore (idempotent).
- **Patch File**: If `patch_file` is specified but missing/invalid, fail validation at startup.
