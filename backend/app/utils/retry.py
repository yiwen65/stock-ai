# backend/app/utils/retry.py

from functools import wraps
import time
import logging
from typing import Callable, TypeVar, Any

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_on_failure(max_retries: int = 3, delay: float = 1, backoff: float = 2):
    """
    重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟时间的倍增因子
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            retries = 0
            current_delay = delay

            while retries < max_retries:
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    retries += 1
                    if retries >= max_retries:
                        logger.error(
                            f"Function {func.__name__} failed after {max_retries} retries: {e}",
                            exc_info=True
                        )
                        raise

                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} after {current_delay}s: {e}"
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff

            return None  # type: ignore

        return wrapper
    return decorator
