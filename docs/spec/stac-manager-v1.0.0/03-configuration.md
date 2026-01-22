# Configuration
## STAC Manager v1.0

**Related Documents**:
- [Pipeline Management](./01-pipeline-management.md)

---

## 1. Overview
Configuration is primarily handled via YAML files. There are two types of config:
1.  **Workflow Config**: Defines the steps and logic (see [Pipeline Management](./01-pipeline-management.md)).
2.  **Global/Environment Config**: Handles secrets, logging defaults, and runtime environment settings.

## 2. Root Configuration Schema (`WorkflowDefinition`)

The configuration file defines the entire workflow: metadata, global settings, and execution steps.

```python
from typing import List, Optional
from pydantic import BaseModel, Field

# ... (LoggingConfig, DefaultConcurrencyConfig, SecretsConfig defined below) ...

class SettingsConfig(BaseModel):
    """Global runtime settings."""
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    default_concurrency: DefaultConcurrencyConfig = Field(default_factory=DefaultConcurrencyConfig)
    input_secrets: SecretsConfig = Field(default_factory=SecretsConfig)

class StrategyConfig(BaseModel):
    """Execution strategy configuration."""
    matrix: Optional[List[Dict[str, Any]]] = None 
    """
    List of input parameters to spawn parallel pipelines.
    Each dict is injected into the context.data of a child pipeline.
    Example: [{"collection_id": "C1"}, {"collection_id": "C2"}]
    """

class StepConfig(BaseModel):
    """Defines a single workflow step."""
    id: str
    module: str
    config: dict
    depends_on: list[str] = []  # Step IDs this step depends on

class WorkflowDefinition(BaseModel):
    """
    ROOT schema for the workflow YAML file.
    """
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    
    settings: SettingsConfig = Field(default_factory=SettingsConfig)
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    steps: List[StepConfig]
```

This schema applies to the root level of the configuration or a separate base config file.

```python
from pystac_client.client import Client
from typing import Literal, Optional
from pydantic import BaseModel, Field

class LoggingConfig(BaseModel):
    level: Literal['DEBUG', 'INFO', 'WARNING', 'ERROR'] = 'INFO'
    file: Optional[str] = None
    format: Literal['json', 'text'] = 'text'

class DefaultConcurrencyConfig(BaseModel):
    concurrency: int = Field(default=5, ge=1)
    rate_limit: float = Field(default=10.0, gt=0)
    retry_max_attempts: int = Field(default=3, ge=0)
    retry_backoff_base: float = Field(default=2.0, ge=1.0)

class SecretsConfig(BaseModel):
    dotenv_path: Optional[str] = None
```

### 2.1 Example Configuration (YAML)

The following YAML demonstrates how to populate the configuration file:

```yaml
name: "production-ingest"
description: "Ingest Landsat C2 to Parquet"

settings:
  logging:
    level: INFO
    file: "/var/log/stac-manager.log"
  
  default_concurrency:
    concurrency: 10
    rate_limit: 50.0
    retry_max_attempts: 3
    retry_backoff_base: 2.0

  input_secrets:
    dotenv_path: "/etc/stac-manager/secrets.env"

strategy:
  matrix:
    - collection_id: "landsat-c2-l2"
      catalog_url: "https://cmr.earthdata.nasa.gov/stac/v1"

steps:
  - id: ingest
    module: IngestModule
    config:
       ...
```

> [!NOTE]
> **Multiple Workflows**: Currently, each YAML file defines a single workflow. To run different workflows, use separate YAML files and specify via `--config` flag. Future versions may support multiple workflow definitions in a single file with workflow selection.

## 3. Secret Management
Sensitive values (API tokens, database credentials) **MUST NOT** be hardcoded in YAML files.
The configuration loader supports environment variable substitution.

**Usage in YAML**:
```yaml
config:
  catalog_url: "https://api.example.com"
  headers:
    Authorization: "Bearer ${STAC_API_TOKEN}"
```

The system will attempt to resolve `${VAR_NAME}` from the process environment variables at runtime. If the variable is missing, validation will fail.
> [!IMPORTANT]
> **Substitution Timing**: Variable substitution happens **BEFORE** module instantiation. This ensures that Pydantic models in module constructors (`__init__`) receive fully resolved values (e.g., `year: "2023"` becomes `year: 2023` integer), preventing validation errors on template strings.

### 3.1 Matrix Variable Substitution
Variables defined in `strategy.matrix` are also available for substitution within the `config` blocks of steps.
- **Priority**: Matrix Variables > Environment Variables.
- **Scope**: Matrix variables are only available within the specific pipeline instance spawned for that matrix entry.

**Example**:

```yaml
strategy:
  matrix:
    - region: "us-west"
      year: 2023
    - region: "us-east"
      year: 2024
steps:
  - id: ingest
    module: IngestModule
    config:
      # Interpolates to "s3://bucket/us-west/2023/data.json"
      # Run another process in parallel "s3://bucket/us-east/2024/data.json"
      source_file: "s3://bucket/${region}/${year}/data.json"
```

---

## 4. Module Instantiation Logic

The `StacManager` uses a factory pattern to instantiate modules based on the `steps` defined in the configuration.

### 4.1 Constructor Injection
For each step in the `WorkflowDefinition`:
1.  The `module` string is resolved to a class (e.g., `ingest.IngestModule`).
2.  The `config` dictionary is passed directly to the module's `__init__` method.

```python
# StacManager Instantiation Logic (Tier 2: Algorithmic Guidance)

def _instantiate_step(self, step_config: StepConfig, context: WorkflowContext) -> ModuleInstance:
    """
    Instantiate a single module step with Context-aware substitution.
    """
    # 1. Substitute Variables (Env + Matrix + Context)
    # Recursively replace ${var} in step_config.config
    resolved_config = self.variable_substitutor.resolve(
        step_config.config, 
        context.data  # Matrix variables are in context.data
    )
    
    # 2. Resolve module class from registry
    module_class = MODULE_REGISTRY.get(step_config.module)
    if not module_class:
        raise WorkflowConfigError(f"Unknown module: {step_config.module}")
    
    # 3. Instantiate with validated config
    # Pydantic validation happens here inside the module's __init__
    return module_class(config=resolved_config)
    
def _build_pipeline_instances(self, steps: List[StepConfig], context: WorkflowContext) -> dict[str, Any]:
    """
    Builds the pipeline components for THIS specific execution context.
    """
    instances = {}
    for step in steps:
        instances[step.id] = self._instantiate_step(step, context)
    return instances
```

### 4.2 Data Ownership
- **StacManager**: Owns the `WorkflowDefinition` and module lifecycle.
- **Module**: Owns the configuration schema for its specific `config` block. This allows modules to define their own specific parameters (e.g., `catalog_url`, `output_path`) without polluting the core schema.

### 4.3 Module Config Validation Pattern

Each module validates its config in `__init__` using its own Pydantic model:

```python
# Example: IngestModule (Tier 2: Algorithmic Guidance)
from pydantic import BaseModel, HttpUrl

class IngestConfig(BaseModel):
    catalog_url: HttpUrl
    collection_ids: list[str] | None = None

class IngestModule:
    def __init__(self, config: dict):
        # Pydantic validates and converts the raw dict
        self.config = IngestConfig(**config)
    
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        # Access validated config
        client = Client.open(str(self.config.catalog_url))
        ...
```

### 4.4 Runtime Data Sharing via WorkflowContext

Modules that need to share runtime data (not static config) use `context.data`.

**Example**: SeedModule stores collection_id for downstream modules:

```python
# In SeedModule.fetch()
async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
    # Store for downstream modules
    if self.config.defaults and 'collection' in self.config.defaults:
        context.data['collection_id'] = self.config.defaults['collection']
    
    for item in items:
        yield item
```

**Example**: IngestModule reads `catalog_url` from context:

```python
# In IngestModule.fetch()
async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
    # Inherit collection_id from Matrix Strategy or Config
    collection_id = context.data.get('collection_id')
    if not collection_id and not self.config.collection_id:
        raise ModuleException("IngestModule requires 'collection_id'")
    
    # Use inherited URL with module-specific collection_id
    async for item in self._fetch_items(catalog_url, self.config.collection_id):
        yield item
```

### 4.5 Per-Collection Pipeline Injection

When the StacManager spawns parallel per-collection pipelines (see [Pipeline Management](./01-pipeline-management.md#82-collection-centric-parallel-execution)), it injects the current `collection_id` into `context.data`:

```python
# StacManager Matrix Execution (Tier 2: Algorithmic Guidance)

async def _execute_matrix(self, workflow: WorkflowDefinition, context: WorkflowContext):
    """
    Spawn parallel pipelines for each matrix entry.
    """
    matrix: List[dict] = workflow.strategy.matrix
    
    async def process_entry(entry: dict):
        # 1. Fork Context & Inject Data
        # 'entry' contains variables like {"collection_id": "C1"}
        child_context = context.fork(data=entry)
        
        # 2. "Late Binding" Instantiation
        # Instantiate modules specifically for THIS child context
        # This allows ${collection_id} to be resolved before __init__
        pipeline_instances = self._build_pipeline_instances(workflow.steps, child_context)
        
        # 3. Execute Pipeline
        await self._execute_pipeline(pipeline_instances, child_context)

    # Parallel execution
    await asyncio.gather(*[process_entry(row) for row in matrix])
```
