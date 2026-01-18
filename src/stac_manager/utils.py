import asyncio
import time
import logging
from typing import Any, Callable, TypeVar

T = TypeVar("T")

class RateLimiter:
    """Token bucket style rate limiter."""
    def __init__(self, requests_per_second: float):
        self.interval = 1.0 / requests_per_second
        self.last_check = 0.0
        self.lock = asyncio.Lock()
    
    async def __aenter__(self):
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_check
            wait = self.interval - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
            self.last_check = time.monotonic()

    async def __aexit__(self, exc_type, exc, tb):
        pass

async def retry_with_backoff(
    func: Callable[[], Any],
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
) -> Any:
    """Retry async function with exponential backoff."""
    for attempt in range(1, max_attempts + 1):
        try:
            return await func()
        except Exception as e:
            if attempt == max_attempts:
                raise e
            
            delay = min(base_delay * (exponential_base ** (attempt - 1)), max_delay)
            # Log warning here in real code
            await asyncio.sleep(delay)
