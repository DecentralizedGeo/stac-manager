
class StacManagerError(Exception):
    """Base exception for all STAC Manager errors."""
    pass

class ConfigurationError(StacManagerError):
    """Configuration validation failed."""
    pass

class ModuleException(StacManagerError):
    """Critical module error."""
    pass

class WorkflowConfigError(StacManagerError):
    """Invalid workflow definition (DAG cycles, etc)."""
    pass

class WorkflowExecutionError(StacManagerError):
    """Workflow execution failed."""
    pass

class DataProcessingError(StacManagerError):
    """Non-critical data error."""
    pass

class ExtensionError(StacManagerError):
    """Extension apply/validate error."""
    pass
