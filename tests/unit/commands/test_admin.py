import pytest
from bot.commands.admin import AdminCommandCog
from unittest.mock import MagicMock, AsyncMock

from tests.factories.discord_factories import make_member, make_text_channel


class TestAdminCommands:
    @pytest.fixture
    async def commands(self, mock_bot, mock_services, test_config):
        return AdminCommandCog(bot=mock_bot, services=mock_services, config=test_config)
    

    async def test_change_stats(self, commands):
        interaction = MagicMock(
        user=MagicMock(id=12345),response=MagicMock(send_message=AsyncMock(),defer=AsyncMock(return_value=None),
        delete_original_response = AsyncMock()), channel=make_text_channel(),
        followup=MagicMock(send=AsyncMock()))

        stats_user = make_member(id=123)

        await commands.admin_group.increment_stats.callback(commands.admin_group, interaction=interaction, user=stats_user, stats="total_challenges_won", count=5)

        commands.admin_group.services.user.change_stats.assert_called_once_with(user_id=stats_user.id, field="total_challenges_won", count=5)
        interaction.followup.send.assert_called_once_with(
            f"User: {stats_user.mention}\n" f"Affected stat: {"total_challenges_won"}\n" f"{"Incremented" if 5 > 0 else "Decremented"} by {5}",
            ephemeral=True)
        

    async def test_change_stats_invalid_stat_name(self, commands):
        interaction = MagicMock(
        user=MagicMock(id=12345),response=MagicMock(send_message=AsyncMock(),defer=AsyncMock(return_value=None),
        delete_original_response = AsyncMock()), channel=make_text_channel(),
        followup=MagicMock(send=AsyncMock()))

        stats_user = make_member(id=123)

        await commands.admin_group.increment_stats.callback(commands.admin_group, interaction=interaction, user=stats_user, stats="invalid_field_name", count=5)

        interaction.response.send_message.assert_called_once_with(content="Please select a valid stat name")

        commands.admin_group.services.user.change_stats.assert_not_called()