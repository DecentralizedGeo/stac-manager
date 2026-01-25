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


def build_execution_order(steps: list[StepConfig]) -> list[str]:
    """
    Build execution order using topological sort (Kahn's algorithm).
    
    Args:
        steps: List of step configurations
        
    Returns:
        List of step IDs in execution order
        
    Raises:
        ConfigurationError: If cycle detected or missing dependency
    """
    # Build graph structures
    step_map = {step.id: step for step in steps}
    in_degree = {step.id: 0 for step in steps}
    adjacency = {step.id: [] for step in steps}
    
    # Calculate in-degrees and build adjacency list
    for step in steps:
        for dep_id in step.depends_on:
            if dep_id not in step_map:
                raise ConfigurationError(
                    f"Step '{step.id}' depends on unknown step '{dep_id}'"
                )
            adjacency[dep_id].append(step.id)
            in_degree[step.id] += 1
    
    # Kahn's algorithm: Start with nodes that have no dependencies
    queue = [step_id for step_id, degree in in_degree.items() if degree == 0]
    execution_order = []
    
    while queue:
        # Sort for deterministic ordering within same level
        queue.sort()
        current = queue.pop(0)
        execution_order.append(current)
        
        # Reduce in-degree for dependent steps
        for neighbor in adjacency[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # Verify all steps processed (no cycles)
    if len(execution_order) != len(steps):
        # Find cycle for better error message (simplified detection)
        raise ConfigurationError("Circular dependency detected in workflow steps")
    
    return execution_order
