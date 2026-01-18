from typing import List, Optional, Literal, Any
from pydantic import BaseModel
import jmespath
from stac_manager.context import WorkflowContext

class MappingRule(BaseModel):
    source_field: str
    target_field: str
    type: Literal['string', 'int', 'float', 'datetime', 'geometry']
    format: Optional[str] = None
    required: bool = False

class TransformConfig(BaseModel):
    mappings: List[MappingRule]
    strategy: Literal['new', 'merge'] = 'new'

class TransformModule:
    """Transforms raw dicts to STAC-like structure using JMESPath."""
    
    def __init__(self, config: dict):
        # Allow nested config under 'config' key if passed from orchestrator, 
        # but here we assume direct dict match for simplicity or flattened.
        self.config = TransformConfig(**config)
        self.compiled_rules = [
            (jmespath.compile(r.source_field), r) for r in self.config.mappings
        ]
    
    def modify(self, item: dict, context: WorkflowContext) -> dict | None:
        if self.config.strategy == 'merge':
            import copy
            result = copy.deepcopy(item)
            if "properties" not in result:
                result["properties"] = {}
        else:
            result = {"properties": {}} # Minimal init
        
        for expression, rule in self.compiled_rules:
            value = expression.search(item)
            
            if value is None:
                if rule.required:
                    # Log failure in context (omitted for brevity)
                    return None
                continue
            
            # Simple assignment logic
            self._set_nested(result, rule.target_field, value)
            
        return result

    def _set_nested(self, d: dict, path: str, value: Any):
        keys = path.split('.')
        current = d
        for k in keys[:-1]:
            current = current.setdefault(k, {})
        current[keys[-1]] = value
