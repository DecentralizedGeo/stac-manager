"""Workflow configuration models."""
from pathlib import Path
from typing import Any
import yaml
from pydantic import BaseModel, Field, ValidationError
from stac_manager.exceptions import ConfigurationError


class StepConfig(BaseModel):
    """Defines a single workflow step."""
    id: str
    module: str
    config: dict[str, Any]
    depends_on: list[str] = Field(default_factory=list)


class StrategyConfig(BaseModel):
    """Execution strategy configuration."""
    matrix: list[dict[str, Any]] | None = None


class WorkflowDefinition(BaseModel):
    """Root schema for workflow YAML configuration."""
    name: str
    description: str | None = None
    version: str = "1.0"
    
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    steps: list[StepConfig]


def load_workflow_from_yaml(path: Path) -> WorkflowDefinition:
    """
    Load and validate workflow configuration from YAML file.
    
    Args:
        path: Path to YAML configuration file
        
    Returns:
        Validated WorkflowDefinition
        
    Raises:
        ConfigurationError: If file not found or validation fails
    """
    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}")
    
    try:
        with open(path, 'r') as f:
            config_dict = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML syntax: {e}")
    
    try:
        return WorkflowDefinition(**config_dict)
    except ValidationError as e:
        raise ConfigurationError(f"Invalid workflow configuration: {e}")
