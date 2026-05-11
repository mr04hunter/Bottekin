import pytest
import fakeredis.aioredis
from unittest.mock import MagicMock, AsyncMock
from bot.services.rate_limiter import RateLimiter, MIQ_RATE_LIMIT, STATS_RATE_LIMIT


class TestRateLimiter:

    @pytest.fixture
    def redis_client(self):
        return fakeredis.aioredis.FakeRedis(decode_responses=True)

    @pytest.fixture
    def service(self, mock_uow, mock_bot, redis_client):
        scheduler = MagicMock()
        return RateLimiter(
            uow=mock_uow,
            bot=mock_bot,
            scheduler=scheduler,
            redis_client=redis_client 
        )

    # --- MIQ tests ---

    @pytest.mark.asyncio
    async def test_miq_increment_usage(self, service):
        await service.miq_increment_usage(user_id=123)
        await service.miq_increment_usage(user_id=123)
        await service.miq_increment_usage(user_id=123)
        assert await service.miq_is_limited(123) is False

    @pytest.mark.asyncio
    async def test_miq_rate_limited_after_max_usage(self, service):
        for _ in range(MIQ_RATE_LIMIT.max_usage):
            await service.miq_increment_usage(user_id=123)
        assert await service.miq_is_limited(123) is True

    @pytest.mark.asyncio
    async def test_miq_increment_usage_returns_true_when_limited(self, service):
        for _ in range(MIQ_RATE_LIMIT.max_usage - 1):
            result = await service.miq_increment_usage(user_id=123)
            assert result is False
        result = await service.miq_increment_usage(user_id=123)
        assert result is True

    @pytest.mark.asyncio
    async def test_miq_usage_key_deleted_after_rate_limit(self, service, redis_client):
        for _ in range(MIQ_RATE_LIMIT.max_usage):
            await service.miq_increment_usage(user_id=123)
        assert await redis_client.exists("miq:usage:123") == 0

    @pytest.mark.asyncio
    async def test_miq_remove_limited_user(self, service):
        for _ in range(MIQ_RATE_LIMIT.max_usage):
            await service.miq_increment_usage(user_id=123)
        await service.remove_limited_user("miq", 123)
        assert await service.miq_is_limited(123) is False

    @pytest.mark.asyncio
    async def test_miq_remove_nonexistent_limited_user(self, service):
        await service.remove_limited_user("miq", 123)  # no crash

    @pytest.mark.asyncio
    async def test_miq_cleanup_usage(self, service, redis_client):
        await service.miq_increment_usage(user_id=123)
        await service.miq_increment_usage(user_id=123)
        await service.cleanup_usage("miq", 123)
        assert await redis_client.exists("miq:usage:123") == 0

    @pytest.mark.asyncio
    async def test_miq_cleanup_nonexistent_user(self, service):
        await service.cleanup_usage("miq", 123)  # no crash

    @pytest.mark.asyncio
    async def test_next_available_miq_time_when_limited(self, service):
        for _ in range(MIQ_RATE_LIMIT.max_usage):
            await service.miq_increment_usage(user_id=123)
        result = await service.next_available_miq_time(123)
        assert result is not None

    @pytest.mark.asyncio
    async def test_next_available_miq_time_when_not_limited(self, service):
        result = await service.next_available_miq_time(123)
        assert result is None

    # --- Stats tests ---

    @pytest.mark.asyncio
    async def test_stats_increment_usage(self, service):
        await service.stats_increment_usage(user_id=123)
        await service.stats_increment_usage(user_id=123)
        assert await service.stats_is_limited(123) is False

    @pytest.mark.asyncio
    async def test_stats_rate_limited_after_max_usage(self, service):
        for _ in range(STATS_RATE_LIMIT.max_usage):
            await service.stats_increment_usage(user_id=123)
        assert await service.stats_is_limited(123) is True

    @pytest.mark.asyncio
    async def test_stats_increment_usage_returns_true_when_limited(self, service):
        for _ in range(STATS_RATE_LIMIT.max_usage - 1):
            result = await service.stats_increment_usage(user_id=123)
            assert result is False
        result = await service.stats_increment_usage(user_id=123)
        assert result is True

    @pytest.mark.asyncio
    async def test_stats_namespaced_separately_from_miq(self, service):
        """Hitting MIQ limit should not affect stats and vice versa"""
        for _ in range(MIQ_RATE_LIMIT.max_usage):
            await service.miq_increment_usage(user_id=123)
        assert await service.stats_is_limited(123) is False

    @pytest.mark.asyncio
    async def test_next_available_stats_time_when_limited(self, service):
        for _ in range(STATS_RATE_LIMIT.max_usage):
            await service.stats_increment_usage(user_id=123)
        result = await service.next_available_stats_time(123)
        assert result is not None

    @pytest.mark.asyncio
    async def test_next_available_stats_time_when_not_limited(self, service):
        result = await service.next_available_stats_time(123)
        assert result is None

    # --- Isolation tests ---

    @pytest.mark.asyncio
    async def test_different_users_are_isolated(self, service):
        for _ in range(MIQ_RATE_LIMIT.max_usage):
            await service.miq_increment_usage(user_id=123)
        assert await service.miq_is_limited(123) is True
        assert await service.miq_is_limited(456) is False