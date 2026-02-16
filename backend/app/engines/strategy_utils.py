# backend/app/engines/strategy_utils.py
"""Utilities for concurrent strategy execution."""
import asyncio
import logging
from typing import Any, Callable, Coroutine, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

DEFAULT_CONCURRENCY = 20
DEFAULT_PER_ITEM_TIMEOUT = 8.0  # seconds


async def batch_fetch(
    items: List[Dict],
    fetch_fn: Callable[[Dict], Coroutine[Any, Any, Optional[T]]],
    concurrency: int = DEFAULT_CONCURRENCY,
    timeout: float = DEFAULT_PER_ITEM_TIMEOUT,
) -> List[T]:
    """Fetch data for multiple items concurrently with per-item timeout.

    Args:
        items: List of stock dicts to process.
        fetch_fn: Async function that takes a stock dict, fetches extra data,
                  applies filtering logic, and returns a result dict if the
                  stock passes, or None to skip.
        concurrency: Max number of concurrent fetch operations.
        timeout: Timeout in seconds for each individual fetch_fn call.

    Returns:
        List of non-None results from fetch_fn.
    """
    semaphore = asyncio.Semaphore(concurrency)
    results: List[Optional[T]] = []

    async def _process(item: Dict) -> Optional[T]:
        async with semaphore:
            try:
                return await asyncio.wait_for(fetch_fn(item), timeout=timeout)
            except asyncio.TimeoutError:
                logger.debug(f"Timeout fetching data for {item.get('stock_code', '?')}")
                return None
            except Exception as e:
                logger.debug(f"Error processing {item.get('stock_code', '?')}: {e}")
                return None

    tasks = [_process(item) for item in items]
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]
