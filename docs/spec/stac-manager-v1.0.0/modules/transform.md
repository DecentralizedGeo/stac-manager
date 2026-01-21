# Transform Module
## STAC Manager v1.0

**Role**: `Modifier` (Processor)

---

## 1. Purpose
Transforms **"Dirty" or Non-STAC** raw data (e.g. raw JSON, CSV) into STAC-compatible intermediate structures. 

> [!NOTE]
> **When NOT to use this module**: If your raw data has already been transformed into valid STAC (e.g. Items fetched during Ingest or Seed step), do not use the Transform module. Use the `Update` module instead to modify existing STAC items. This module is primaryly used to map raw data to their STAC equivalent properties (e.g. map CSV columns to STAC properties). See the [Workflow Patterns](../09-workflow-patterns.md) for use cases.

## 2. Architecture
The module is decomposed into specific sub-components to handle complexity:

### 2.1 SchemaLoader
- **Responsibility**: Loads and validates transformation schema from YAML/JSON.
- **Failure Mode**: Fails fast if the schema is invalid.

### 2.2 FieldMapper
- **Responsibility**: Maps source fields to target STAC properties.
- **Standard**: Uses the **JMESPath query language** for robust querying of nested source structures.
- **Logic**: Handles nested lookups (`source.metadata.date`) and applies defaults if fields are missing.

#### FieldMapper Pseudocode
```python
import jmespath

class FieldMapper:
    def map_field(self, source_data: dict, rule: MappingRule) -> Any:
        """
        Extract value using JMESPath and apply defaults.
        """
        # 1. Extract raw value
        value = jmespath.search(rule.source_field, source_data)
        
        # 2. Check existence
        if value is None:
            if rule.default is not None:
                return rule.default
            if rule.required:
                raise MappingError(f"Missing required field: {rule.source_field}")
            return None
            
        # 3. Return raw value (TypeConverter handles casting later)
        return value
```

### 2.3 TypeConverter
- **Responsibility**: Casts raw values to strict STAC types.
- **Operations**:
    - String to RFC 3339 Datetime.
    - String/Array normalization.
    - Coordinate reprojection (optional future).

## 3. Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, List, Literal

class MappingRule(BaseModel):
    source_field: str
    target_field: str
    type: Literal['string', 'int', 'float', 'datetime', 'geometry']
    format: Optional[str] = None # e.g. "%Y-%m-%d" for datetime
    required: bool = False # If True, fail record if source field is missing

class SchemaConfig(BaseModel):
    mappings: List[MappingRule]

class TransformConfig(BaseModel):
    input_file: Optional[str] = None
    """
    Path to sidecar data file (CSV/JSON/Parquet) for hydration.
    Acts as a lookup table joined to the stream by ID.
    """
    schema_file: Optional[str] = None
    schema_mapping: Optional[SchemaConfig] = Field(alias='schema', default=None)
    """
    Inline schema mapping configuration.
    Aliased to 'schema' in YAML for cleaner syntax.
    """
```

### 3.1 Example Usage (YAML)

```yaml
- id: transform
  module: TransformModule
  config:
    source_file: "./data/raw_metadata.csv"
    schema:
      mappings:
        - source_field: "Acquisition_Date"
          target_field: "properties.datetime"
          type: "datetime"
          format: "%Y-%m-%d"
        - source_field: "Image_ID"
          target_field: "id"
          type: "string"
```

## 4. I/O Contract

### 3.1 Input
 
 - **Stream**: `Iterator[dict]` (Standard STAC Items or Skeleton Items)
 - **Sidecar (Optional)**: `input_file` (Raw Data for hydration)
 
 ### 3.2 Output
 
 - **Stream**: `Iterator[TransformedItem]` (Hydrated/Transformed Items)

```python
def modify(self, item: dict, context: WorkflowContext) -> dict | None:
    """
    Transforms a single raw dictionary into a TransformedItem-compatible dict.
    Returns None if the item is invalid and should be dropped.
    """
```
> [!NOTE]
> `TransformedItem` is defined in [Data Contracts](../05-data-contracts.md).

## 5. Error Handling
- **Missing Source Field**: Check `required` flag in schema. If required, log failure and skip record.
- **Conversion Error**: Log warning, use default if provided, else fail record.
