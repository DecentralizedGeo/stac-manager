"""Validate Module - STAC schema validation."""
from stac_manager.modules.config import ValidateConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import DataProcessingError
from stac_validator import stac_validator


class ValidateModule:
    """Validates STAC Items against schema."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = ValidateConfig(**config)
        # Initialize validator once
        self.validator = stac_validator.StacValidate()
    
    def modify(self, item: dict, context: WorkflowContext) -> dict | None:
        """
        Validate item against STAC schema.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Item if valid, None if invalid (permissive mode)
        
        Raises:
            DataProcessingError: If strict=True and validation fails
        """
        # Validate item
        is_valid = self.validator.validate_dict(item)
        
        if not is_valid:
            # validator.message is a list of dicts with error details
            if hasattr(self.validator, 'message') and self.validator.message:
                errors = [str(msg) for msg in self.validator.message]
                error_msg = "; ".join(errors)
            else:
                error_msg = "Validation failed"
            
            if self.config.strict:
                raise DataProcessingError(f"STAC validation failed: {error_msg}")
            
            context.failure_collector.add(
                item_id=item.get("id", "unknown"),
                error=f"STAC validation failed: {error_msg}",
                step_id="validate"
            )
            
            return None  # Drop invalid item
        
        return item
