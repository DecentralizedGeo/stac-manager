"""Failure collection and reporting."""
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TypedDict


class FailureContext(TypedDict, total=False):
    """Context for failure debugging."""
    source_file: str
    line_number: int
    field_name: str
    url: str
    http_status: int
    retry_attempt: int


@dataclass
class FailureRecord:
    """Single failure record."""
    step_id: str
    item_id: str
    error_type: str
    message: str
    timestamp: str
    context: FailureContext | None = None


class FailureCollector:
    """Collects non-critical failures for reporting."""
    
    def __init__(self):
        self._failures: list[FailureRecord] = []
    
    def add(
        self,
        item_id: str,
        error: str | Exception,
        step_id: str = 'unknown',
        error_context: FailureContext | None = None
    ) -> None:
        """Add a failure record."""
        if isinstance(error, Exception):
            error_type = type(error).__name__
            message = str(error)
        else:
            error_type = "str"
            message = error
        
        record = FailureRecord(
            step_id=step_id,
            item_id=item_id,
            error_type=error_type,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat(),
            context=error_context
        )
        self._failures.append(record)
    
    def get_all(self) -> list[FailureRecord]:
        """Get all collected failures."""
        return self._failures.copy()
