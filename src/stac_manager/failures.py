from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TypedDict, Optional, Any

@dataclass
class FailureContext(TypedDict, total=False):
    source_file: str
    line_number: int
    field_name: str
    url: str
    http_status: int
    retry_attempt: int

@dataclass
class FailureRecord:
    step_id: str
    item_id: str
    error_type: str
    message: str
    timestamp: str
    context: Optional[FailureContext] = None

class FailureCollector:
    def __init__(self):
        self._failures: list[FailureRecord] = []
        
    def add(
        self, 
        item_id: str, 
        error: str | Exception,
        step_id: str = 'unknown',
        error_context: Optional[FailureContext] = None
    ) -> None:
        message = str(error)
        error_type = type(error).__name__ if isinstance(error, Exception) else "Error"
        
        record = FailureRecord(
            step_id=step_id,
            item_id=item_id,
            error_type=error_type,
            message=message,
            timestamp=datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            context=error_context
        )
        self._failures.append(record)
        
    def get_all(self) -> list[FailureRecord]:
        return list(self._failures)
        
    def count(self) -> int:
        return len(self._failures)
        
    def count_by_step(self) -> dict[str, int]:
        counts = {}
        for f in self._failures:
            counts[f.step_id] = counts.get(f.step_id, 0) + 1
        return counts
