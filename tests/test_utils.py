import pytest
import asyncio
import time
from stac_manager.utils import RateLimiter, retry_with_backoff

@pytest.mark.asyncio
async def test_rate_limiter():
    # Allow 10 requests per second
    limiter = RateLimiter(requests_per_second=10.0)
    start = time.time()
    for _ in range(5):
        async with limiter:
            pass
    duration = time.time() - start
    # Should be fast (approx 0.5s total if spacing is 0.1s)
    # Actually if we just burst 5 with rate 10/s, first is free, next 4 take 0.1s each = 0.4s
    assert duration < 1.0

@pytest.mark.asyncio
async def test_retry_success():
    count = 0
    async def flakey():
        nonlocal count
        count += 1
        if count < 3:
            raise ValueError("Fail")
        return "Success"
    
    res = await retry_with_backoff(flakey, max_attempts=5, base_delay=0.01)
    assert res == "Success"
    assert count == 3
