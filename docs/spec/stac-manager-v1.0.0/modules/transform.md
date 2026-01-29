# Transform Module
## STAC Manager v1.0

**Role**: `Modifier` (Processor)

---

## 1. Purpose
Transforms **"Dirty" or Non-STAC** raw data (e.g. raw JSON, CSV) into STAC-compatible intermediate structures. 

> [!NOTE]
> **When NOT to use this module**: If your raw data has already been transformed into valid STAC (e.g. Items fetched during Ingest or Seed step), do not use the Transform module. Use the `Update` module instead to modify existing STAC items. 

**Enrichment Mode**: This module is primarily designed for **Enrichment**. It joins **Input Data** (from CSV/JSON/Parquet) to items passing through the pipeline, using the Item `id` as the join key.

## 2. Architecture
The module is decomposed into specific sub-components to handle complexity:

### 2.1 SchemaLoader
- **Responsibility**: Loads and validates transformation schema from YAML/JSON.
- **Failure Mode**: Fails fast if the schema is invalid.

### 2.2 Lifecycle & Optimization
The module operates in two distinct phases to ensure performance:

1.  **Setup Phase (Once per Workflow)**:
    - Loads the `input_file` into memory.
    - Builds an optimized index `{ input_join_key: record }` for O(1) lookups.
2.  **Execution Phase (Per Item)**:
    - Streams items from the pipeline.
    - Performs a dictionary lookup using the Item's `id`.
    - Applies transformation/enrichment.

### 2.3 Input Indexing & Join Logic
- **Supported Formats**:
    - **JSON**: Standard `json` load.
    - **CSV**: Uses `pyarrow` for type inference (Int/Float/Timestamp).
- **Join Keys**:
    - **Stream Side**: Always the STAC Item `id`.
    - **Input Side**: Configured via `input_join_key` (Default: "id").
    - **Type Safety**: For CSVs, `input_join_key` column is forced to String type to ensure robust joining with STAC IDs.
- **Indexing Logic**:
    1. **CSV**: Read via PyArrow -> force ID column to string -> Convert to `{ id: row_dict }`.
    2. **JSON**: Read via Stdlib -> Apply `data_path` (if set) -> Convert to `{ id: row_dict }`.
    
### 2.4 Field Mapping Strategy
- **Requirement**: `field_mapping` is **REQUIRED**. Implicit merging is not supported.
- **Extraction (Source)**: "Hybrid" Strategy.
    - **Simple Key**: Direct lookup (e.g. `"Cloud Cover %"`). Supports spaces/symbols.
    - **JMESPath**: Complex query (e.g. `"telemetry.sensors[0].gain"`).
- **Injection (Target)**:
    - **Dot Notation**: `properties.eo:cloud_cover`.
    - **Auto-Creation**: Creates missing intermediate dictionaries (e.g. `properties.sensors` created as dict for `properties.sensors.gain`).
    - **Overwrite**: Sets/Overwrites the value at the target path. 

## 3. Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Literal

class TransformConfig(BaseModel):
    input_file: str = Field(description="Path to input data file (CSV/JSON/Parquet)")
    """
    Path to input data. PyArrow used for CSV to infer types.
    """
    
    input_join_key: str = Field(default="id", description="Field in input file to join on")
    """
    Column/Key in input data that contains the Item ID.
    """
    
    data_path: Optional[str] = Field(default=None, description="JMESPath to records list (JSON only)")
    """
    Optional JMESPath to locate list of records in JSON. Not used for CSV.
    """
    
    field_mapping: Dict[str, str] = Field(description="Map target_field -> source_field")
    """
    REQUIRED. Map of Target Path (Item) -> Source Path (Input).
    Target: Dot-notation (e.g. "properties.eo:cloud_cover").
    Source: Simple Key or JMESPath.
    """
    
    handle_missing: Literal['ignore', 'warn', 'error'] = 'ignore'
    strategy: Literal['merge', 'update'] = 'merge'
```

### 3.1 Example Usage (YAML)

```yaml
- id: transform
  module: TransformModule
  config:
    input_file: "./data/raw_metadata.csv"
    input_join_key: "Image_ID"
    field_mapping:
      "properties.datetime": "Acquisition_Date"
      "properties.eo:cloud_cover": "Cloud Cover %"  # Spaces allowed in simple keys
      "id": "Image_ID"
```

## 4. I/O Contract

**Input (Workflow Context)**:
- `config` (Module Configuration):
  - `input_file`: Input data source.
  - `field_mapping`: Transformation rules.
- `context.data` (injected by Matrix Strategy):
  - Matrix Variables: Available for string interpolation in config.
- **Stream**: `Iterator[dict]` (Standard STAC Items or Skeleton Items)

**Output**:
**Output**:
- **Stream**: `Iterator[dict]` (Enriched STAC Items)

```python
def modify(self, item: dict, context: WorkflowContext) -> dict | None:
    """
    Transforms a single raw dictionary into an enriched STAC Item dict.
    Returns None if the item is invalid and should be dropped.
    """
```

## 5. Error Handling
- **Missing Input Item**: Controlled by `handle_missing` (`ignore`, `warn`, `error`).
- **Missing Source Field**: If a configured source field is missing in the input data, the target field is skipped (not set).
- **JMESPath Failure**: If a complex JMESPath query returns `null`, the target field is skipped.
