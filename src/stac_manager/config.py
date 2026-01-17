from typing import List, Optional, Literal
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

class SettingsConfig(BaseModel):
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    default_concurrency: DefaultConcurrencyConfig = Field(default_factory=DefaultConcurrencyConfig)
    input_secrets: SecretsConfig = Field(default_factory=SecretsConfig)

class StepConfig(BaseModel):
    id: str
    module: str
    config: dict
    depends_on: List[str] = Field(default_factory=list)

class WorkflowDefinition(BaseModel):
    name: str
    description: Optional[str] = None
    version: str = "1.0"
    settings: SettingsConfig = Field(default_factory=SettingsConfig)
    steps: List[StepConfig]
