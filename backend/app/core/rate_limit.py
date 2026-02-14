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
    """限流依赖 — 已登录用户按 user_id 限流，否则按 IP"""
    # 尝试从 Authorization header 提取 user_id
    user_key = None
    auth = request.headers.get("authorization", "")
    if auth.startswith("Bearer "):
        try:
            from app.core.security import decode_access_token
            payload = decode_access_token(auth[7:])
            if payload and payload.get("sub"):
                user_key = f"rate_limit:user:{payload['sub']}"
        except Exception:
            pass

    if not user_key:
        client_ip = request.client.host
        user_key = f"rate_limit:ip:{client_ip}"

    if not await rate_limiter.check_rate_limit(user_key):
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please try again later."
        )
