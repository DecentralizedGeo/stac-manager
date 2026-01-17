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

steps:
  - id: discover
    module: DiscoveryModule
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

---

## 4. Module Instantiation Logic

The `StacManager` uses a factory pattern to instantiate modules based on the `steps` defined in the configuration.

### 4.1 Constructor Injection
For each step in the `WorkflowDefinition`:
1.  The `module` string is resolved to a class (e.g., `discovery.DiscoveryModule`).
2.  The `config` dictionary is passed directly to the module's `__init__` method.

```python
# StacManager Instantiation Logic (Tier 2: Algorithmic Guidance)

def _instantiate_modules(self, workflow: WorkflowDefinition) -> dict[str, ModuleInstance]:
    """
    Create module instances from workflow steps.
    
    Returns:
        Dictionary mapping step_id to instantiated module.
    """
    instances = {}
    
    for step in workflow.steps:
        # 1. Resolve module class from registry
        module_class = MODULE_REGISTRY.get(step.module)
        if not module_class:
            raise WorkflowConfigError(f"Unknown module: {step.module}")
        
        # 2. Inject step config into module constructor
        # The module's __init__ receives the raw config dict and validates
        # it internally using Pydantic (see 4.3 below)
        instance = module_class(config=step.config)
        
        instances[step.id] = instance
    
    return instances
```

### 4.2 Data Ownership
- **StacManager**: Owns the `WorkflowDefinition` and module lifecycle.
- **Module**: Owns the configuration schema for its specific `config` block. This allows modules to define their own specific parameters (e.g., `catalog_url`, `output_path`) without polluting the core schema.

### 4.3 Module Config Validation Pattern

Each module validates its config in `__init__` using its own Pydantic model:

```python
# Example: DiscoveryModule (Tier 2: Algorithmic Guidance)
from pydantic import BaseModel, HttpUrl

class DiscoveryConfig(BaseModel):
    catalog_url: HttpUrl
    collection_ids: list[str] | None = None

class DiscoveryModule:
    def __init__(self, config: dict):
        # Pydantic validates and converts the raw dict
        self.config = DiscoveryConfig(**config)
    
    async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
        # Access validated config
        client = Client.open(str(self.config.catalog_url))
        ...
```

### 4.4 Runtime Data Sharing via WorkflowContext

Modules that need to share runtime data (not static config) use `context.data`.

**Example**: Discovery stores `catalog_url` for downstream modules:

```python
# In DiscoveryModule.fetch()
async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
    # Store for downstream modules (e.g., IngestModule)
    context.data['catalog_url'] = str(self.config.catalog_url)
    
    collections = await self._discover_collections()
    for collection in collections:
        yield collection.to_dict()
```

**Example**: IngestModule reads `catalog_url` from context:

```python
# In IngestModule.fetch()
async def fetch(self, context: WorkflowContext) -> AsyncIterator[dict]:
    # Inherit catalog_url from Discovery step
    catalog_url = context.data.get('catalog_url')
    if not catalog_url:
        raise ModuleException("IngestModule requires 'catalog_url' in context.data")
    
    # Use inherited URL with module-specific collection_id
    async for item in self._fetch_items(catalog_url, self.config.collection_id):
        yield item
```

### 4.5 Per-Collection Pipeline Injection

When the StacManager spawns parallel per-collection pipelines (see [Pipeline Management](./01-pipeline-management.md#82-collection-centric-parallel-execution)), it injects the current `collection_id` into `context.data`:

```python
# StacManager Per-Collection Dispatch (Tier 2: Algorithmic Guidance)

async def _execute_collection_pipelines(self, collections: list[dict], context: WorkflowContext):
    """
    Spawn parallel pipelines for each collection.
    """
    async def process_one_collection(collection_dict: dict):
        # Create a per-collection context with injected collection_id
        collection_id = collection_dict['id']
        context.data['_current_collection_id'] = collection_id
        
        # Execute remaining pipeline steps for this collection
        await self._execute_pipeline_for_collection(collection_id, context)
    
    # Parallel execution across collections
    await asyncio.gather(*[
        process_one_collection(c) for c in collections
    ])
```
