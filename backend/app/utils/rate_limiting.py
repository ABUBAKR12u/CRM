import math
import time
from datetime import timedelta

from fastapi import HTTPException, Request, status
from redis.asyncio import Redis

from app.utils.config import settings

MAX_BUCKETS = 10_000


class RateLimiter:
    def __init__(self, name: str, limit: int, window: timedelta, redis: Redis | None = None):
        self.name = name
        self.limit = limit
        self.window = int(window.total_seconds())
        self.redis = redis
        self.buckets: dict[str, tuple[int, float]] = {}

    def redis_key(self, key: str) -> str:
        return f"rate:{self.name}:{key}"

    async def retry_after(self, key: str) -> int:
        if self.redis:
            count = await self.redis.get(self.redis_key(key))
            if count is None or int(count) < self.limit:
                return 0
            return max(await self.redis.ttl(self.redis_key(key)), 1)

        count, reset_at = self.buckets.get(key, (0, 0.0))
        remaining = reset_at - time.monotonic()
        return math.ceil(remaining) if count >= self.limit and remaining > 0 else 0

    async def hit(self, key: str) -> None:
        if self.redis:
            redis_key = self.redis_key(key)
            await self.redis.pipeline().incr(redis_key).expire(redis_key, self.window, nx=True).execute()
            return

        now = time.monotonic()
        if len(self.buckets) > MAX_BUCKETS:
            self.buckets = {k: v for k, v in self.buckets.items() if v[1] > now}
        count, reset_at = self.buckets.get(key, (0, 0.0))
        if reset_at <= now:
            count, reset_at = 0, now + self.window
        self.buckets[key] = (count + 1, reset_at)

    async def reset(self, key: str) -> None:
        if self.redis:
            await self.redis.delete(self.redis_key(key))
            return
        self.buckets.pop(key, None)


async def ensure_not_limited(*checks: tuple[RateLimiter, str]) -> None:
    retry_after = max([await limiter.retry_after(key) for limiter, key in checks])
    if retry_after:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "rate_limited", headers={"Retry-After": str(retry_after)}
        )


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


redis = Redis.from_url(settings.REDIS_URL, decode_responses=True) if settings.REDIS_URL else None

login_ip_limiter = RateLimiter("login-ip", 20, timedelta(minutes=15), redis)
login_account_limiter = RateLimiter("login-account", 5, timedelta(minutes=15), redis)
forgot_limiter = RateLimiter("forgot", 5, timedelta(minutes=15), redis)
reset_limiter = RateLimiter("reset", 10, timedelta(minutes=15), redis)

LIMITERS = (login_ip_limiter, login_account_limiter, forgot_limiter, reset_limiter)
