from unittest.mock import AsyncMock

import pytest
from rate_limiter import RateLimiter


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def limiter(mock_redis):
    return RateLimiter(mock_redis)


@pytest.mark.asyncio
async def test_is_allowed_first_request(limiter, mock_redis):
    # Mock INCR to return 1 (first request)
    mock_redis.incr.return_value = 1

    allowed = await limiter.is_allowed("test_key", max_requests=5, window_seconds=60)

    assert allowed is True
    mock_redis.incr.assert_called_with("test_key")
    mock_redis.expire.assert_called_with("test_key", 60)


@pytest.mark.asyncio
async def test_is_allowed_at_limit(limiter, mock_redis):
    # Mock INCR to return 5
    mock_redis.incr.return_value = 5

    allowed = await limiter.is_allowed("test_key", max_requests=5, window_seconds=60)

    assert allowed is True
    # Should not call expire because current > 1
    mock_redis.expire.assert_not_called()


@pytest.mark.asyncio
async def test_is_allowed_over_limit(limiter, mock_redis):
    # Mock INCR to return 6
    mock_redis.incr.return_value = 6

    allowed = await limiter.is_allowed("test_key", max_requests=5, window_seconds=60)

    assert allowed is False
    mock_redis.expire.assert_not_called()


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
