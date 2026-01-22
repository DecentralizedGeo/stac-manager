# Transform Module
## STAC Manager v1.0

**Role**: `Modifier` (Processor)

---

## 1. Purpose
Transforms **"Dirty" or Non-STAC** raw data (e.g. raw JSON, CSV) into STAC-compatible intermediate structures. 

> [!NOTE]
> **When NOT to use this module**: If your raw data has already been transformed into valid STAC (e.g. Items fetched during Ingest or Seed step), do not use the Transform module. Use the `Update` module instead to modify existing STAC items. 

**Enrichment Mode**: This module is primarily designed for **Enrichment**. It joins "Sidecar" data (from CSV/JSON/Parquet) to items passing through the pipeline, using the Item `id` as the join key.

## 2. Architecture
The module is decomposed into specific sub-components to handle complexity:

### 2.1 SchemaLoader
- **Responsibility**: Loads and validates transformation schema from YAML/JSON.
- **Failure Mode**: Fails fast if the schema is invalid.

### 2.2 Lifecycle & Optimization
The module operates in two distinct phases to ensure performance:

1.  **Setup Phase (Once per Workflow)**:
    - Loads the `input_file` (Sidecar) into memory.
    - Builds an optimized index `{ sidecar_id: record }` for O(1) lookups.
2.  **Execution Phase (Per Item)**:
    - Streams items from the pipeline.
    - Performs a dictionary lookup using the Item's `id`.
    - Applies transformation/enrichment.

### 2.3 Sidecar Indexing & Join Logic
- **Join Keys**:
    - **Stream Side**: Always the STAC Item `id`.
    - **Sidecar Side**: Configured via `sidecar_id_path` (JMESPath).
- **Indexing Logic**:
    1. **Pre-processing**: If `data_path` is set, extract the subset of data (e.g. `raw_data = jmespath.search(data_path, raw_file)`).
    2. **Dict Input**: Assumes keys are IDs.
    3. **List Input**: Iterates the list and uses `sidecar_id_path` to extract the ID.
       - Index Structure: `{ extracted_id: record_dict }`
       - **Constraint**: If multiple records have the same ID, **Last Record Wins**.
- **Join Strategies** (Configurable):
    - `merge` (Default): Overwrites existing keys and **adds new keys** from sidecar data.
    - `update`: Overwrites existing keys only. **Ignores new keys** that don't exist in the Item.

### 2.4 FieldMapper
- **Responsibility**: Maps source fields to target STAC properties.
- **Standard**: Uses **JMESPath** for querying source data and **Dot Notation** for setting target values.
- **Logic**:
    - **Extraction**: `jmespath.search(rule.source_field, source)`
    - **Application**: Uses simple dot notation (e.g. `properties.eo:cloud_cover`) to construct nested dictionaries automatically if they don't exist.

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

### 2.5 TypeConverter
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
    """
    strategy: Literal['merge', 'update'] = 'merge'
    """
    Join strategy:
    - 'merge': Overwrite existing + Add new fields.
    - 'update': Overwrite existing only.
    """
    sidecar_id_path: str = "id"
    """
    JMESPath query to extract the unique ID from sidecar records.
    Used to build the lookup index when input_file is a LIST.
    """
    data_path: Optional[str] = None
    """
    Optional JMESPath to locate the list/dict of records within the input file.
    Useful if the data is wrapped (e.g. "response.results").
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
    input_file: "./data/raw_metadata.csv"
    strategy: "merge"
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

**Input (Workflow Context)**:
- `config` (Module Configuration):
  - `input_file`: Sidecar data source.
  - `schema`: Mapping rules.
- `context.data` (injected by Matrix Strategy):
  - Matrix Variables: Available for string interpolation in config.
- **Stream**: `Iterator[dict]` (Standard STAC Items or Skeleton Items)

**Output**:
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
