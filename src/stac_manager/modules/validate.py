from pydantic import BaseModel, HttpUrl
from typing import List
from stac_validator import stac_validator
from stac_manager.context import WorkflowContext

class ValidateConfig(BaseModel):
    strict: bool = False
    extension_schemas: List[HttpUrl] = []

class ValidateModule:
    """Validates STAC items using stac-validator."""
    
    def __init__(self, config: dict):
        self.config = ValidateConfig(**config)
        self.validator = stac_validator.StacValidate()
        
    def modify(self, item: dict, context: WorkflowContext) -> dict | None:
        # validate_dict returns True if valid, False otherwise
        # Note: stac-validator API might differ slightly by version, 
        # but usage generally involves instantiating and calling validate_dict or similar.
        # Based on v3.3.0:
        context.logger.debug(f"Validating item {item.get('id')}")
        is_valid = self.validator.validate_dict(item)
        
        if is_valid:
            return item
        else:
            # Log failure
            msg = getattr(self.validator, 'message', "Validation failed")
            context.logger.warning(f"Validation failed for item {item.get('id')}: {msg}. Strict: {self.config.strict}")
            context.failure_collector.add(item.get('id', 'unknown'), str(msg), step_id='validate')
            
            if self.config.strict:
                return None
            
            # If not strict, warn but pass through
            # Could optionally attach validation error to item properties
            return item
