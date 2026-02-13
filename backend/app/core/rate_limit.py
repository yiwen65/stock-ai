# backend/app/core/rate_limit.py

import time
from fastapi import Request, HTTPException
from app.core.cache import get_redis

class RateLimiter:
    def __init__(self, requests: int = 100, window: int = 60):
        """
        Args:
            requests: 时间窗口内允许的请求数
            window: 时间窗口（秒）
        """
        self.requests = requests
        self.window = window

    async def check_rate_limit(self, key: str) -> bool:
        """检查是否超过限流"""
        redis = get_redis()
        current = int(time.time())
        window_start = current - self.window

        # 使用 Redis Sorted Set 存储请求时间戳
        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # 删除过期记录
        pipe.zadd(key, {str(current): current})  # 添加当前请求
        pipe.zcount(key, window_start, current)  # 统计窗口内请求数
        pipe.expire(key, self.window)  # 设置过期时间

        results = pipe.execute()
        request_count = results[2]

        return request_count <= self.requests

# 创建限流器实例
rate_limiter = RateLimiter(requests=100, window=60)

async def rate_limit_dependency(request: Request):
    """限流依赖"""
    # 使用 IP 地址作为限流 Key
    client_ip = request.client.host
    key = f"rate_limit:{client_ip}"

    if not await rate_limiter.check_rate_limit(key):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )
