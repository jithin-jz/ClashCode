import os

import redis.asyncio as redis
from rate_limiter import RateLimiter

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)
rate_limiter = RateLimiter(redis_client)


def channel_key(room: str) -> str:
    return f"chat:room:{room}"
