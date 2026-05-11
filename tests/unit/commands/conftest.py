from discord import Embed
import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.services.rate_limiter import RateLimiter


@pytest.fixture
def mock_services(mock_bot, mock_uow, mock_redis_client):
    services = MagicMock()
    
    stats = MagicMock()
    stats.fetch_music_stats = AsyncMock(return_value=MagicMock(id=111,spec=Embed))
    stats.fetch_feedback_stats = AsyncMock(return_value=MagicMock(id=222,spec=Embed))
    stats.fetch_challenge_stats = AsyncMock(return_value=MagicMock(id=333,spec=Embed))

    user = MagicMock()
    user.get_with_stats = AsyncMock(return_value=MagicMock(id=222))
    user.change_stats = AsyncMock()

    scheduler = MagicMock()
    scheduler.add_miq_rate_limit = MagicMock()
    scheduler.reset_miq_rate_limit = MagicMock()

    rate_limiter = RateLimiter(redis_client=mock_redis_client,uow=mock_uow, bot=mock_bot, scheduler=scheduler)

    services.rate_limiter = rate_limiter
    services.stats = stats
    services.user = user

    return services

