"""Async streaming utilities for STAC items."""
from typing import AsyncIterator, TypeVar, List

T = TypeVar("T")


async def chunk_stream(
    iterator: AsyncIterator[T],
    size: int
) -> AsyncIterator[List[T]]:
    """
    Chunk an async iterator.
    
    Args:
        iterator: Async iterator of items
        size: Maximum chunk size
        
    Yields:
        Lists of items (chunks)
    """
    chunk = []
    async for item in iterator:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


async def limit_stream(
    iterator: AsyncIterator[T],
    limit: int
) -> AsyncIterator[T]:
    """
    Limit number of items from an async iterator.
    
    Args:
        iterator: Async iterator of items
        limit: Maximum items to yield
        
    Yields:
        Items up to limit
    """
    count = 0
    async for item in iterator:
        if count >= limit:
            break
        yield item
        count += 1
