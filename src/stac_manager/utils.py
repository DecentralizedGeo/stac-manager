import asyncio
import time
from typing import Any, Callable, TypeVar
import os
import re
import sys
from pathlib import Path
from stac_manager.exceptions import ConfigurationError


T = TypeVar("T")

class RateLimiter:
    """Token bucket style rate limiter."""
    def __init__(self, requests_per_second: float):
        self.interval = 1.0 / requests_per_second
        self.last_check = 0.0
        self.lock = asyncio.Lock()
    
    async def __aenter__(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_check
            wait = self.interval - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
            self.last_check = time.monotonic()

    async def __aexit__(self, exc_type, exc, tb):
        pass

async def retry_with_backoff(
    func: Callable[[], Any],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> Any:
    """Retry async function with exponential backoff."""
    for attempt in range(1, max_attempts + 1):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts:
                raise e
            
            delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
            # Log warning here in real code
            await asyncio.sleep(delay)

import shapely.geometry

def ensure_bbox(geometry: dict | None) -> list[float] | None:
    if not geometry:
        return None
    try:
        shape = shapely.geometry.shape(geometry)
        return list(shape.bounds)
    except Exception:
        return None

def substitute_env_vars(config: dict) -> dict:
    """Recursively replace ${VAR} with env vars."""
    
    def replace_str(s: str):
        pattern = re.compile(r'\$\{([^}]+)\}')
        matches = pattern.findall(s)
        for var in matches:
            val = os.getenv(var)
            if val is None:
                raise ConfigurationError(f"Missing environment variable: {var}")
            s = s.replace(f"${{{var}}}", val)
        return s

    def recurse(obj):
        if isinstance(obj, dict):
            return {k: recurse(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [recurse(v) for v in obj]
        elif isinstance(obj, str):
            return replace_str(obj)
        else:
            return obj
            
            return obj
            
    return recurse(config)

def validate_workflow_config(config: dict) -> list[str]:
    errors = []
    
    # Check basics
    if 'name' not in config:
        errors.append("Missing required field: name")
    if 'steps' not in config or not isinstance(config['steps'], list):
        errors.append("Missing or invalid field: steps")
        return errors # Cannot proceed
        
    # Check steps
    step_ids = set()
    dependencies = {}
    
    for step in config['steps']:
        sid = step.get('id')
        if not sid:
            errors.append("Step missing id")
            continue
        if sid in step_ids:
            errors.append(f"Duplicate step id: {sid}")
        step_ids.add(sid)
        
        deps = step.get('depends_on', [])
        dependencies[sid] = deps
        
    # Check dependency existence
    for sid, deps in dependencies.items():
        for dep in deps:
            if dep not in step_ids:
                errors.append(f"Step {sid} depends on unknown step: {dep}")
                
    # Detect Cycles (DFS)
    visited = set()
    path = set()
    
    def visit(node):
        if node in path:
            return True # Cycle
        if node in visited:
            return False
            
        visited.add(node)
        path.add(node)
        
        for neighbor in dependencies.get(node, []):
            if neighbor in step_ids: # Only traverse known
                if visit(neighbor):
                    return True
        
        path.remove(node)
        return False
        
    for sid in step_ids:
        if visit(sid):
            errors.append(f"Circular dependency detected involving {sid}")
            break # One cycle report is enough
            
    for sid in step_ids:
        if visit(sid):
            errors.append(f"Circular dependency detected involving {sid}")
            break # One cycle report is enough
            
    return errors

from stac_manager.failures import FailureCollector

def generate_processing_summary(workflow_result: dict, failure_collector: FailureCollector) -> str:
    lines = []
    lines.append("=== Workflow Processing Summary ===")
    lines.append(f"Workflow: {workflow_result.get('name', 'start')}")
    # Add stats if available in result
    if 'success_count' in workflow_result:
        lines.append(f"Success: {workflow_result['success_count']}")
    if 'failure_count' in workflow_result:
        lines.append(f"Failed: {workflow_result['failure_count']}")
    
    lines.append("")
    lines.append("=== Failure Breakdown ===")
    lines.append(f"Total Failures: {failure_collector.count()}")
    
    # Group failures by step
    counts = {}
    # Assuming get_all() returns list of FailureRecord objects/dicts
    for f in failure_collector.get_all():
        step = getattr(f, 'step_id', 'unknown')
        counts[step] = counts.get(step, 0) + 1
        
    for step, count in counts.items():
        lines.append(f"{step}: {count} failures")
        
    return "\n".join(lines)
