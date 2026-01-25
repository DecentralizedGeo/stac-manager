"""Workflow configuration models."""
from typing import Any
from pydantic import BaseModel, Field


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
