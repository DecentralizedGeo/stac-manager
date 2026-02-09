"""Validate Module - STAC schema validation."""
import logging
from stac_manager.modules.config import ValidateConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import DataProcessingError
from stac_validator import stac_validator


class ValidateModule:
    """Validates STAC Items against schema."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with configuration."""
        self.config = ValidateConfig(**config)
        self.logger = logging.getLogger(__name__)  # Default logger
        # Initialize validator once
        self.validator = stac_validator.StacValidate()
    
    def set_logger(self, logger: logging.Logger) -> None:
        """Set step-specific logger for this module.
        
        Args:
            logger: Logger instance to use for this module
        """
        self.logger = logger
    
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
        item_id = item.get("id", "unknown")
        
        # DEBUG: Validating item
        self.logger.debug(f"Validating item | item: {item_id}")
        
        # Validate item
        is_valid = self.validator.validate_dict(item)
        
        if not is_valid:
            # validator.message is a list of dicts with error details
            if hasattr(self.validator, 'message') and self.validator.message:
                errors = [str(msg) for msg in self.validator.message]
                error_msg = "; ".join(errors)
            else:
                error_msg = "Validation failed"
            
            # WARNING: Validation failed
            self.logger.warning(f"Validation failed | item: {item_id} | errors: {error_msg}")
            
            if self.config.strict:
                raise DataProcessingError(f"STAC validation failed: {error_msg}")
            
            context.failure_collector.add(
                item_id=item_id,
                error=f"STAC validation failed: {error_msg}",
                step_id="validate"
            )
            
            return None  # Drop invalid item
        
        # INFO: Validation passed
        self.logger.info(f"Validated item | item: {item_id} | status: valid")
        
        return item
