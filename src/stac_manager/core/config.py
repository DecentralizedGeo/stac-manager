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
    
    # Checkpoint configuration
    resume_from_checkpoint: bool = Field(
        default=True,
        description="Whether to resume from existing checkpoints. Set to False to ignore and overwrite existing checkpoints."
    )
    
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
        # Find cycle using DFS
        remaining = set(step_map.keys()) - set(execution_order)
        cycle_path = _find_cycle(remaining, step_map)
        raise ConfigurationError(
            f"Circular dependency detected: {' -> '.join(cycle_path)}"
        )
    
    return execution_order


def _find_cycle(remaining_steps: set[str], step_map: dict[str, StepConfig]) -> list[str]:
    """
    Find a cycle in the remaining steps using DFS.
    
    Args:
        remaining_steps: Set of step IDs not yet processed
        step_map: Mapping of step ID to StepConfig
        
    Returns:
        List of step IDs forming a cycle
    """
    visited = set()
    rec_stack = []
    
    def dfs(step_id: str) -> list[str] | None:
        if step_id in rec_stack:
            # Found cycle - return path from cycle start
            cycle_start = rec_stack.index(step_id)
            return rec_stack[cycle_start:] + [step_id]
        
        if step_id in visited:
            return None
        
        visited.add(step_id)
        rec_stack.append(step_id)
        
        # Explore dependencies
        step = step_map[step_id]
        for dep_id in step.depends_on:
            if dep_id in remaining_steps:
                cycle = dfs(dep_id)
                if cycle:
                    return cycle
        
        rec_stack.pop()
        return None
    
    # Start DFS from any remaining step
    for step_id in remaining_steps:
        if step_id not in visited:
            cycle = dfs(step_id)
            if cycle:
                return cycle
    
    return ["unknown"]  # Fallback (should not reach)
