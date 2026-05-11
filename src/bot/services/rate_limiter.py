from bot.database.unit_of_work import UnitOfWork
from bot.services.base_service import BaseService
from typing import TYPE_CHECKING
from bot.logging import get_logger
from datetime import datetime, UTC, timedelta
from dataclasses import dataclass

if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider
    from bot.scheduler.scheduler import Scheduler

from redis.asyncio import Redis

logger = get_logger("rate_limiter")

@dataclass(frozen=True)
class RateLimitConfig:
    max_usage: int
    window_seconds: int
    cooldown_seconds: int

MIQ_RATE_LIMIT = RateLimitConfig(
    max_usage=4,
    window_seconds=300,
    cooldown_seconds=86400
)

STATS_RATE_LIMIT = RateLimitConfig(
    max_usage=3,
    window_seconds=60,
    cooldown_seconds=300
)

class RateLimiter(BaseService):
    """
    Records /stats usage and /make_it_quote usage
    """
    def __init__(
        self,
        uow: UnitOfWork,
        bot: "ChannelProvider",
        scheduler: "Scheduler",
        redis_client: Redis,
    ) -> None:
        super().__init__(uow, bot)
        self.scheduler = scheduler
        self.redis = redis_client

    def _usage_key(self, namespace: str, user_id: int) -> str:
        return f"{namespace}:usage:{user_id}"

    def _limited_key(self, namespace: str, user_id: int) -> str:
        return f"{namespace}:limited:{user_id}"

    async def is_limited(self, namespace: str, user_id: int) -> bool:
        return await self.redis.exists(self._limited_key(namespace, user_id)) == 1

    async def increment_usage(self, namespace: str, user_id: int, cfg: RateLimitConfig) -> bool:
        """
        Increments usage counter for the user.
        Returns True if the user just got rate limited, False otherwise.
        """
        usage_key = self._usage_key(namespace, user_id)
        limited_key = self._limited_key(namespace, user_id)

        current_usage = await self.redis.incr(usage_key)

        if current_usage == 1:
            await self.redis.expire(usage_key, cfg.window_seconds)

        if current_usage >= cfg.max_usage:
            await self.redis.set(limited_key, 1, ex=cfg.cooldown_seconds)
            await self.redis.delete(usage_key)
            logger.info(f"{user_id} rate limited on {namespace} for {cfg.cooldown_seconds}s")
            return True

        logger.info(f"{user_id} {namespace} use count: {current_usage}")
        return False

    async def next_available_time(self, namespace: str, user_id: int) -> datetime | None:
        ttl = await self.redis.ttl(self._limited_key(namespace, user_id))
        if ttl <= 0:
            return None
        return datetime.now(tz=UTC) + timedelta(seconds=ttl)

    async def remove_limited_user(self, namespace: str, user_id: int) -> None:
        limited_key = self._limited_key(namespace, user_id)
        existed = await self.redis.delete(limited_key)
        if not existed:
            logger.info(f"User {user_id} is not rate limited on {namespace}")
            return
        logger.info(f"user_id: {user_id} removed rate limit on {namespace}")

    async def cleanup_usage(self, namespace: str, user_id: int) -> None:
        await self.redis.delete(self._usage_key(namespace, user_id))
        logger.info(f"user_id: {user_id} reset usage on {namespace}")

    # --- MIQ helpers ---
    async def miq_is_limited(self, user_id: int) -> bool:
        return await self.is_limited("miq", user_id)

    async def miq_increment_usage(self, user_id: int) -> bool:
        return await self.increment_usage("miq", user_id, MIQ_RATE_LIMIT)

    async def next_available_miq_time(self, user_id: int) -> datetime | None:
        return await self.next_available_time("miq", user_id)

    # --- Stats helpers ---
    async def stats_is_limited(self, user_id: int) -> bool:
        return await self.is_limited("stats", user_id)

    async def stats_increment_usage(self, user_id: int) -> bool:
        return await self.increment_usage("stats", user_id, STATS_RATE_LIMIT)

    async def next_available_stats_time(self, user_id: int) -> datetime | None:
        return await self.next_available_time("stats", user_id)