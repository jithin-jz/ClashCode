"""
Redis-backed rate limiter for the chat service.

Uses Redis for rate limiting to ensure limits work correctly
across multiple container instances (horizontal scaling).
"""

from typing import Optional

import redis.asyncio as redis


class RateLimiter:
    """
    Async Redis-backed rate limiter using the sliding window counter algorithm.

    Usage:
        limiter = RateLimiter(redis_client)
        if await limiter.check_connection_rate(user_id):
            # Allow connection
        else:
            # Reject - rate limited
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """
        Check if a request is allowed under the rate limit.

        Uses Redis INCR with EXPIRE for simple sliding window.

        Args:
            key: Unique identifier for this rate limit (e.g., "ratelimit:ws:connect:123")
            max_requests: Maximum number of requests allowed in the window
            window_seconds: Time window in seconds

        Returns:
            True if request is allowed, False if rate limited
        """
        current = await self.redis.incr(key)

        if current == 1:
            # First request in this window, set expiry
            await self.redis.expire(key, window_seconds)

        return current <= max_requests

    async def get_remaining(self, key: str, max_requests: int) -> int:
        """Get remaining requests in the current window."""
        current = await self.redis.get(key)
        if current is None:
            return max_requests
        return max(0, max_requests - int(current))

    async def get_reset_time(self, key: str) -> Optional[int]:
        """Get seconds until the rate limit resets."""
        ttl = await self.redis.ttl(key)
        return ttl if ttl > 0 else None

    # ===== Convenience Methods for Chat Service =====

    async def check_connection_rate(self, user_id: int) -> bool:
        """
        Check if user can establish a new WebSocket connection.

        Limit: 5 new connections per minute per user.
        Prevents connection spam attacks.
        """
        key = f"ratelimit:ws:connect:{user_id}"
        return await self.is_allowed(key, max_requests=5, window_seconds=60)

    async def check_message_rate(self, user_id: int) -> bool:
        """
        Check if user can send a new message.

        Limit: 30 messages per minute per user.
        Prevents chat spam.
        """
        key = f"ratelimit:ws:message:{user_id}"
        return await self.is_allowed(key, max_requests=30, window_seconds=60)

    async def check_burst_rate(self, user_id: int) -> bool:
        """
        Check short burst rate to prevent rapid-fire messages.

        Limit: 5 messages per 5 seconds.
        Prevents flooding chat.
        """
        key = f"ratelimit:ws:burst:{user_id}"
        return await self.is_allowed(key, max_requests=5, window_seconds=5)
