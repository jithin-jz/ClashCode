from unittest.mock import AsyncMock, MagicMock

import pytest
from rate_limiter import RateLimiter


@pytest.fixture
def pipe():
    pipe = MagicMock()
    pipe.execute = AsyncMock()
    return pipe


@pytest.fixture
def mock_redis(pipe):
    redis = AsyncMock()
    redis.pipeline = MagicMock(return_value=pipe)
    return redis


@pytest.fixture
def limiter(mock_redis):
    return RateLimiter(mock_redis)


@pytest.mark.asyncio
async def test_is_allowed_first_request(limiter, mock_redis, pipe):
    pipe.execute.return_value = [1, True]

    allowed = await limiter.is_allowed("test_key", max_requests=5, window_seconds=60)

    assert allowed is True
    mock_redis.pipeline.assert_called_with(transaction=True)
    pipe.incr.assert_called_with("test_key")
    # TTL is set atomically with the increment, and only once per window
    pipe.expire.assert_called_with("test_key", 60, nx=True)


@pytest.mark.asyncio
async def test_is_allowed_at_limit(limiter, pipe):
    pipe.execute.return_value = [5, False]
    assert await limiter.is_allowed("test_key", max_requests=5, window_seconds=60) is True


@pytest.mark.asyncio
async def test_is_allowed_over_limit(limiter, pipe):
    pipe.execute.return_value = [6, False]
    assert await limiter.is_allowed("test_key", max_requests=5, window_seconds=60) is False


@pytest.mark.asyncio
async def test_get_remaining(limiter, mock_redis):
    mock_redis.get.return_value = "3"
    remaining = await limiter.get_remaining("test_key", max_requests=5)
    assert remaining == 2

    mock_redis.get.return_value = None
    remaining = await limiter.get_remaining("test_key", max_requests=5)
    assert remaining == 5


@pytest.mark.asyncio
async def test_convenience_methods(limiter, mock_redis):
    # We just want to check they call is_allowed with correct params
    limiter.is_allowed = AsyncMock(return_value=True)

    await limiter.check_connection_rate(123)
    limiter.is_allowed.assert_called_with("ratelimit:ws:connect:123", max_requests=5, window_seconds=60)

    await limiter.check_message_rate(123)
    limiter.is_allowed.assert_called_with("ratelimit:ws:message:123", max_requests=30, window_seconds=60)

    await limiter.check_burst_rate(123)
    limiter.is_allowed.assert_called_with("ratelimit:ws:burst:123", max_requests=5, window_seconds=5)
