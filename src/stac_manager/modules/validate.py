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
        is_valid = self.validator.validate_dict(item)
        
        if is_valid:
            return item
        else:
            # Log failure
            # stac-validator usually stores messages in .message attribute list/dict
            msg = getattr(self.validator, 'message', "Validation failed")
            context.failure_collector.add(item.get('id', 'unknown'), str(msg), step_id='validate')
            return None
