# Extension Module
## STAC Manager v1.0

**Role**: `Modifier` (Processor)

---

## 1. Purpose
Applies STAC extensions to **Items or Collections** using a configuration-driven approach. It automatically "scaffolds" the item structure based on the extension's JSON Schema and applies user-defined default values.

> [!NOTE]
> This module is designed for **Scaffolding** (structural extension) and **Defaults**. It does not perform complex per-item calculations (like computing centroids). Use `TransformModule` for complex data mapping.

## 2. Architecture
The module uses an "Auto-Scaffolding" strategy to minimize user effort.

### 2.1 Initialization Phase (Startup)
Performed once when the module loads.

1.  **Fetch Schema**: Downloads the JSON Schema from `schema_uri`.
2.  **Parse & Build Template**:
    *   Identifies properties defined in the schema.
    *   Constructs a "Template Dictionary" representing the structure of the extension.
    *   Populates fields with `null` (or schema defaults if available).
3.  **Merge Defaults**: Overlays user-provided `defaults` from configuration onto the template.
4.  **Cache**: Stores the ready-to-merge template in memory.

### 2.2 Execution Phase (Per Item)
Performed for every item in the stream.

1.  **Tagging**: Appends `schema_uri` to the item's `stac_extensions` list (if missing).
2.  **Merging**: Deep-merges the cached "Template Dictionary" into the Item.
    *   Existing values in the Item are **preserved** (unless overridden by explicit `defaults`).
    *   New values from the template are added.

### 2.3 Logic (Pseudocode)

```python
class ExtensionModule:
    """
    Tier 2: Logic Flow
    """
    def __init__(self, config: dict) -> None:
        # Tier 1: Strict Pydantic parsing
        self.config = ExtensionConfig(**config)
        
        # 1. Fetch Schema Definition
        self.schema_def = fetch_json(str(self.config.schema_uri))
        
        # 2. Parse & Build Template (One-time cost)
        self.template = self._build_template(self.schema_def)
        
        # 3. Apply Config Defaults (Override Template)
        if self.config.defaults:
             self.template = deep_merge(self.template, self.config.defaults)

    def _build_template(self, schema: dict) -> dict:
        """
        Parses JSON Schema to build a scaffolding template.
        Strategies:
        1. 'properties': Direct mapping.
        2. 'oneOf': Heuristic search for 'type': 'Feature' (STAC Item).
        3. '$ref': (Simplified) Assumed resolved or ignored for V1.
        """
        template = {"properties": {}}
        
        # 1. Identify Property Source
        target_properties = {}
        
        if "properties" in schema:
             target_properties = schema["properties"]
        elif "oneOf" in schema:
             # Heuristic: Find the variant that looks like a STAC Item
             for variant in schema["oneOf"]:
                 if variant.get("properties", {}).get("type", {}).get("const") == "Feature":
                     # Found STAC Item definition
                     target_properties = variant.get("properties", {}).get("properties", {})
                     # If it's a $ref, we assume it's resolved or we skip complex resolution for V1
                     if "$ref" in target_properties:
                         # For V1: We might need a real JSON-Schema resolver library here
                         pass 
                     break
        
        # 2. Build Scaffolding
        for key, field_def in target_properties.items():
            if key == "stac_extensions":
                continue # Handled by tagging
            
            # Extract default if present
            # Note: If no default, we explicitly set to None (null) to ensure key existence
            default_val = field_def.get("default", None)
            template["properties"][key] = default_val
            
        return template
             
    def modify(self, item: dict, context: WorkflowContext) -> dict:
        # 1. Tag
        extensions = item.setdefault("stac_extensions", [])
        if self.config.schema_uri not in extensions:
            extensions.append(self.config.schema_uri)
            
        # 2. Merge Template (Scaffold)
        # Strategy: "Keep Existing". 
        # Only add keys that are missing. Do NOT overwrite existing data.
        item = deep_merge(item, self.template, strategy="keep_existing")
        
        # 3. Validation (Optional)
        if self.config.validate:
             # Implementation detail: generic validator logic
             pass
        
        return item
```

## 3. Configuration Schema

```python
from pydantic import BaseModel
from typing import Dict, Any, Optional

class ExtensionConfig(BaseModel):
    schema_uri: str 
    """
    URL to the JSON Schema. Required.
    Used to fetch definitions and auto-scaffold the item structure.
    """
    
    defaults: Optional[Dict[str, Any]] = None
    """
    Optional Key-Value pairs to set as defaults.
    Keys can use Simple Dot Notation (e.g. 'properties.dgeo:licensing').
    Values here OVERRIDE the auto-generated nulls from the schema.
    """
    
    validate: bool = False
    """
    If True, validates the item against the schema AFTER application.
    """
```

### 3.1 Example Usage (YAML)

```yaml
- id: apply_dgeo
  module: ExtensionModule
  config:
    # 1. Source of Truth
    schema_uri: "https://example.com/schemas/dgeo.json"
    
    # 2. Static Overrides
    defaults:
      "properties.dgeo:ownership.type": "individual"
      "properties.dgeo:provenance": "unknown"
      
    # 3. Validation
    validate: true
```

## 4. I/O Contract

**Input (Workflow Context)**:
- `config` (Module Configuration): `schema_uri`, `defaults`.
- Stream of STAC Items (dict).

**Output**:
- Stream of **Extended** STAC Items (dict).
  - Contains new keys from the extension.
  - Contains `schema_uri` in `stac_extensions`.

## 5. Error Handling
- **Fetch Error**: If `schema_uri` is unreachable at startup -> Raise `ConfigurationError` (abort workflow).
- **Parse Error**: If schema is invalid JSON or non-standard -> Raise `ConfigurationError`.
- **Merge Conflict**: If `defaults` specify a path that conflicts with schema structure (e.g. treating a string field as a dict) -> Raise `ConfigurationError`.
- **Validation Error**: If `validate: true` and item fails schema check -> Raise `ExtensionError` (logged to FailureCollector).
