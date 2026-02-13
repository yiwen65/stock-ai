# backend/app/core/profiler.py

import time
import logging
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)


def profile(threshold: float = 1.0):
    """
    Performance profiling decorator

    Args:
        threshold: Log warning if execution time exceeds this value (seconds)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time

                if elapsed > threshold:
                    logger.warning(
                        f"Slow function: {func.__module__}.{func.__name__} "
                        f"took {elapsed:.2f}s (threshold: {threshold}s)"
                    )
                else:
                    logger.debug(
                        f"Function {func.__name__} completed in {elapsed:.3f}s"
                    )

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time

                if elapsed > threshold:
                    logger.warning(
                        f"Slow function: {func.__module__}.{func.__name__} "
                        f"took {elapsed:.2f}s (threshold: {threshold}s)"
                    )
                else:
                    logger.debug(
                        f"Function {func.__name__} completed in {elapsed:.3f}s"
                    )

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


class PerformanceTracker:
    """Track performance metrics for operations"""

    def __init__(self):
        self.metrics = {}

    def record(self, operation: str, duration: float):
        """Record operation duration"""
        if operation not in self.metrics:
            self.metrics[operation] = {
                "count": 0,
                "total_time": 0.0,
                "min_time": float('inf'),
                "max_time": 0.0
            }

        metric = self.metrics[operation]
        metric["count"] += 1
        metric["total_time"] += duration
        metric["min_time"] = min(metric["min_time"], duration)
        metric["max_time"] = max(metric["max_time"], duration)

    def get_stats(self, operation: str = None) -> dict:
        """Get performance statistics"""
        if operation:
            if operation not in self.metrics:
                return {}

            metric = self.metrics[operation]
            avg_time = metric["total_time"] / metric["count"] if metric["count"] > 0 else 0

            return {
                "operation": operation,
                "count": metric["count"],
                "avg_time": round(avg_time, 3),
                "min_time": round(metric["min_time"], 3),
                "max_time": round(metric["max_time"], 3),
                "total_time": round(metric["total_time"], 3)
            }
        else:
            # Return all metrics
            return {
                op: self.get_stats(op)
                for op in self.metrics.keys()
            }

    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()


# Global performance tracker instance
performance_tracker = PerformanceTracker()


def get_performance_tracker():
    """Get global performance tracker instance"""
    return performance_tracker
