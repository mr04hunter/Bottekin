from discord import Embed
import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.services.make_it_quote_service import MakeItQuoteService


@pytest.fixture
def mock_services(mock_bot, mock_uow):
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

    miq = MakeItQuoteService(uow=mock_uow, bot=mock_bot, scheduler=scheduler)

    services.miq = miq
    services.stats = stats
    services.user = user

    return services

