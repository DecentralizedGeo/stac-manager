"""Exception hierarchy for STAC Manager."""


class StacManagerError(Exception):
    """Base exception for all STAC Manager errors."""
    pass


class ConfigurationError(StacManagerError):
    """Configuration validation failed."""
    pass


class DataProcessingError(StacManagerError):
    """Non-critical data error (item-level)."""
    pass
