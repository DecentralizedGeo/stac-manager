import pytest
import asyncio
from stac_manager.utils.streaming import chunk_stream, limit_stream


@pytest.mark.asyncio
async def test_chunk_stream():
    """chunk_stream yields items in chunks."""
    async def source():
        for i in range(5):
            yield i
            
    chunks = []
    async for chunk in chunk_stream(source(), size=2):
        chunks.append(chunk)
        
    assert chunks == [[0, 1], [2, 3], [4]]


@pytest.mark.asyncio
async def test_limit_stream():
    """limit_stream stops after count."""
    async def source():
        for i in range(10):
            yield i
            
    results = []
    async for item in limit_stream(source(), limit=3):
        results.append(item)
        
    assert results == [0, 1, 2]
