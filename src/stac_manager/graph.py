from typing import List, Dict
from stac_manager.config import StepConfig
from stac_manager.exceptions import WorkflowConfigError

def build_execution_levels(steps: List[StepConfig]) -> List[List[str]]:
    """
    Builds topologically sorted execution levels (Kahn's Algorithm).
    Returns list of lists of step IDs.
    """
    step_map = {s.id: s for s in steps}
    step_ids = set(step_map.keys())
    
    # 1. Calculate in-degrees and build dependency graph
    in_degree = {sid: 0 for sid in step_ids}
    graph = {sid: [] for sid in step_ids}
    
    for step in steps:
        for dep in step.depends_on:
            if dep not in step_ids:
                raise WorkflowConfigError(f"Step '{step.id}' depends on unknown step '{dep}'")
            graph[dep].append(step.id)
            in_degree[step.id] += 1
            
    # 2. Find Level 0
    queue = [sid for sid, degree in in_degree.items() if degree == 0]
    levels = []
    processed_count = 0
    
    # 3. Process BFS
    while queue:
        # Sort queue for deterministic levels (optional but good for debugging)
        queue.sort() 
        levels.append(queue)
        processed_count += len(queue)
        next_queue = []
        
        for current_id in queue:
            for neighbor in graph[current_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_queue.append(neighbor)
        
        queue = next_queue
        
    # 4. Cycle Check
    if processed_count < len(steps):
        raise WorkflowConfigError("Cycle detected in step dependencies")
        
    return levels
