"""Protocol definitions for pipeline components."""
from typing import Protocol, AsyncIterator, runtime_checkable


@runtime_checkable
class Fetcher(Protocol):
    """Retrieves items from external or local sources."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with step-specific configuration."""
        ...
    
    async def fetch(self, context: 'WorkflowContext') -> AsyncIterator[dict]:
        """
        Originate a stream of STAC Items or Collections.
        
        Yields:
            STAC item dicts
        """
        ...


@runtime_checkable
class Modifier(Protocol):
    """Transforms or validates a single STAC Item/Collection."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with step-specific configuration."""
        ...
    
    def modify(self, item: dict, context: 'WorkflowContext') -> dict | None:
        """
        Process a single item.
        
        Args:
            item: STAC item dict
            context: Workflow context
        
        Returns:
            Modified dict or None to filter out item
        """
        ...


@runtime_checkable
class Bundler(Protocol):
    """Finalizes and writes items to storage."""
    
    def __init__(self, config: dict) -> None:
        """Initialize with step-specific configuration."""
        ...
    
    async def bundle(self, item: dict, context: 'WorkflowContext') -> None:
        """
        Add an item to the current bundle/buffer.
        
        Must be non-blocking async.
        """
        ...
    
    async def finalize(self, context: 'WorkflowContext') -> dict:
        """
        Commit any remaining buffers and return execution manifest.
        
        Returns:
            OutputResult-compatible dict
        """
        ...
