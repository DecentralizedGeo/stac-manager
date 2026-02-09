"""Validation utilities for STAC items and configuration."""
from typing import Any, Tuple, List
import jsonschema
from stac_validator import stac_validator


def validate_stac_item(item: dict) -> Tuple[bool, List[str]]:
    """
    Validate STAC item using stac-validator.
    
    Args:
        item: STAC item dict
        
    Returns:
        (is_valid, list_of_errors)
    """
    validator = stac_validator.StacValidate()
    # validate_dict returns True if valid
    is_valid = validator.validate_dict(item)
    
    errors = []
    if not is_valid:
        # stac-validator stores results in a message attribute
        # which can contain error details
        msg = getattr(validator, 'message', [])
        if isinstance(msg, list):
            # The message is often a list of dicts/strings
            errors = [str(m) for m in msg]
        elif isinstance(msg, dict):
            # Sometimes it's a dict with 'error' or 'path' keys
            errors = [str(msg.get('error', msg))]
        else:
            errors = [str(msg)]
            
    return is_valid, errors



def validate_schema(data: Any, schema: dict) -> Tuple[bool, List[str]]:
    """
    Validate data against JSON schema.
    
    Args:
        data: Data to validate
        schema: JSON schema dict
        
    Returns:
        (is_valid, list_of_errors)
    """
    errors = []
    try:
        jsonschema.validate(instance=data, schema=schema)
        return True, []
    except jsonschema.ValidationError as e:
        # Simplified error message
        errors.append(f"{e.message} at {'.'.join(str(p) for p in e.path)}")
        return False, errors
    except Exception as e:
        errors.append(str(e))
        return False, errors
