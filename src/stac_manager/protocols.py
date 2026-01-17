from typing import Protocol, AsyncIterator, Any, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from stac_manager.context import WorkflowContext

@runtime_checkable
class Fetcher(Protocol):
    """Retrieves items from an external or local source."""
    
    def __init__(self, config: dict) -> None: ...
        
    async def fetch(self, context: 'WorkflowContext') -> AsyncIterator[dict]: ...

@runtime_checkable
class Modifier(Protocol):
    """Transforms or validates a single item."""
    
    def __init__(self, config: dict) -> None: ...
        
    def modify(self, item: dict, context: 'WorkflowContext') -> dict | None: ...

@runtime_checkable
class Bundler(Protocol):
    """Finalizes and writes items to storage."""
    
    def __init__(self, config: dict) -> None: ...
        
    def bundle(self, item: dict, context: 'WorkflowContext') -> None: ...
        
    def finalize(self, context: 'WorkflowContext') -> dict: ...
