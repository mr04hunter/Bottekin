from datetime import UTC, datetime
from discord import File
import pytest
from bot.commands.commands import CommandsCog
from unittest.mock import MagicMock, AsyncMock

from tests.factories.discord_factories import make_member, make_message, make_text_channel

class TestMainCommands:
    @pytest.fixture
    async def commands(self, mock_bot, mock_services, test_config):
        scheduler = MagicMock()
        scheduler.add_miq_rate_limit = MagicMock()
        scheduler.reset_miq_rate_limit = MagicMock()
        miq_gen = MagicMock()
        miq_gen.create_quote = AsyncMock(return_value=MagicMock(id=55, spec=File))
        return CommandsCog(bot=mock_bot, services=mock_services, scheduler=scheduler, miq_gen=miq_gen, config=test_config)
    

    async def test_miq(self, commands):
        interaction = MagicMock(
            user=MagicMock(id=12345),response=MagicMock(send_message=AsyncMock(),defer=AsyncMock(return_value=None),
            delete_original_response = AsyncMock()), channel=make_text_channel())

        message = make_message(content="normal test message not exceeding 500", author=MagicMock(id=12345))
    

        await commands.make_it_quote(interaction, message)

        kwargs = interaction.channel.send.call_args.kwargs

        view_data = kwargs.get("view")

        assert view_data is not None

        assert view_data.message == message
        assert view_data.text_display.content == f"[Jump to the original message]({message.jump_url})"

    
    async def test_miq_more_than_500_chars(self, commands):
        interaction = MagicMock(
            user=MagicMock(id=12345),response = MagicMock(send_message=AsyncMock(),
            defer=AsyncMock(return_value=None), delete_original_response = AsyncMock()), channel=make_text_channel())

        message = make_message(content="".join([str(n) for n in range(500)]), author=MagicMock(id=12345))
    

        await commands.make_it_quote(interaction, message)

        interaction.channel.send.assert_not_called()
        interaction.response.send_message.assert_called_once_with(content="Bruh, this is an essay :x:")

    async def test_miq_less_than_5_chars(self, commands):
        interaction = MagicMock(
            user=MagicMock(id=12345),response = MagicMock(send_message=AsyncMock(),defer=AsyncMock(return_value=None),
            delete_original_response = AsyncMock()), channel=make_text_channel())


        message = make_message(content="test", author=MagicMock(id=12345))
    

        await commands.make_it_quote(interaction, message)

        interaction.channel.send.assert_not_called()
        interaction.response.send_message.assert_called_once_with(content="More than 5 character required :x:")
        

    async def test_miq_rate_limited(self, commands):
        interaction = MagicMock(
            user=MagicMock(id=12345),response = MagicMock(send_message=AsyncMock(),
            defer=AsyncMock(return_value=None), delete_original_response = AsyncMock()), channel=make_text_channel())

        message = make_message(content="test content message", author=MagicMock(id=12345))
        

        next_available = datetime(year=2026, day=1, month=1, tzinfo=UTC)
        commands.services.miq.is_limited = MagicMock(return_value=True)
        commands.scheduler.next_available_miq_time = MagicMock(return_value=next_available)

        await commands.make_it_quote(interaction, message)

        interaction.channel.send.assert_not_called()
        interaction.response.send_message.assert_called_once_with(f"You cannot make more quotes!\nWait until <t:{int(next_available.timestamp())}>")



    async def test_stats(self, commands):
        interaction = MagicMock(
            user=MagicMock(id=12345),response = MagicMock(send_message=AsyncMock(),
            defer=AsyncMock(return_value=None), guild=MagicMock(id=123456789),
            delete_original_response = AsyncMock()), channel=make_text_channel(),
            followup=MagicMock(send=AsyncMock()), client=MagicMock(id=99999))
        
        stats_user = MagicMock(id=12345)
        commands.main_group.services.user.get_with_stats = AsyncMock(return_value=stats_user)
        await commands.main_group.stats.callback(commands.main_group, interaction=interaction, member=None)

        commands.main_group.services.stats.fetch_music_stats.assert_called_once_with(guild=interaction.guild, user=stats_user, display_name="You")
        commands.main_group.services.stats.fetch_feedback_stats.assert_called_once_with(
            guild=interaction.guild, client=interaction.client, user=stats_user, display_name="You")
        commands.main_group.services.stats.fetch_challenge_stats.assert_called_once_with(
            guild=interaction.guild, client=interaction.client, user=stats_user, display_name="You")
        

    async def test_stats_member(self, commands):
        interaction = MagicMock(
            user=MagicMock(id=12345),response = MagicMock(send_message=AsyncMock(),
            defer=AsyncMock(return_value=None), guild=MagicMock(id=123456789),
            delete_original_response = AsyncMock()), channel=make_text_channel(),
            followup=MagicMock(send=AsyncMock()), client=MagicMock(id=99999))
        
        member = make_member(id=123123, display_name="test_display_name")

        stats_user = MagicMock(id=12345)
        commands.main_group.services.user.get_with_stats = AsyncMock(return_value=stats_user)
        await commands.main_group.stats.callback(commands.main_group, interaction=interaction, member=member)

        commands.main_group.services.stats.fetch_music_stats.assert_called_once_with(guild=interaction.guild, user=stats_user, display_name="test_display_name")
        commands.main_group.services.stats.fetch_feedback_stats.assert_called_once_with(
            guild=interaction.guild, client=interaction.client, user=stats_user, display_name="test_display_name")
        commands.main_group.services.stats.fetch_challenge_stats.assert_called_once_with(
            guild=interaction.guild, client=interaction.client, user=stats_user, display_name="test_display_name")
        

 
