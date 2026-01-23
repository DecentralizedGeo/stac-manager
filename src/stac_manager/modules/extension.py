"""Extension Module - STAC extension scaffolding."""
import requests
from stac_manager.modules.config import ExtensionConfig
from stac_manager.core.context import WorkflowContext
from stac_manager.exceptions import ConfigurationError


class ExtensionModule:
    """Applies STAC extensions via schema scaffolding."""
    
    def __init__(self, config: dict) -> None:
        """Initialize and fetch schema."""
        self.config = ExtensionConfig(**config)
        
        # Fetch schema
        try:
            response = requests.get(self.config.schema_uri, timeout=10)
            response.raise_for_status()
            self.schema = response.json()
        except requests.RequestException as e:
            raise ConfigurationError(f"Failed to fetch schema from {self.config.schema_uri}: {e}")
