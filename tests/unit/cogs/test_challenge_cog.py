from datetime import UTC, datetime, timedelta
import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.cogs.challenge import ChallengeCog
from tests.factories.discord_factories import make_message, make_text_channel
from discord import RawMessageDeleteEvent, RawReactionActionEvent, RawMessageUpdateEvent


class TestChallengeCog:
    @pytest.fixture
    async def cog(self, mock_bot, test_config, mock_extractor, mock_services):
        return ChallengeCog(
            bot=mock_bot, config=test_config, extractor=mock_extractor, services=mock_services)
    
    async def test_is_challenge_info_message(self, cog, test_config):
        message = make_message(id=123, author=MagicMock(id=test_config.dyno_id), embeds=[MagicMock()])
        channel = make_text_channel(id=test_config.challenge_info_channel_id)
        message.channel = channel
        assert cog._is_challenge_info_message(message=message) == True

    async def test_is_challenge_info_message_not_dyno(self, cog, test_config):
        message = make_message(id=123, author=MagicMock(id=32424), embeds=[MagicMock()])
        channel = make_text_channel(id=test_config.challenge_info_channel_id)
        message.channel = channel
        assert cog._is_challenge_info_message(message=message) == False

    async def test_is_challenge_info_message_not_info_channel(self, cog, test_config):
        message = make_message(id=123, author=MagicMock(id=test_config.dyno_id), embeds=[MagicMock()])
        channel = make_text_channel(id=123123)
        message.channel = channel
        assert cog._is_challenge_info_message(message=message) == False

    async def test_is_challenge_info_message_no_embed(self, cog, test_config):
        message = make_message(id=123, author=MagicMock(id=test_config.dyno_id), embeds=[])
        channel = make_text_channel(id=test_config.challenge_info_channel_id)
        message.channel = channel
        assert cog._is_challenge_info_message(message=message) == False


    async def test_on_message_create_challenge(self, cog, test_config):
        embed = MagicMock(
            title="test_challenge_title", description="test_description", type="official",
            is_active=True, is_onoing_voting=True, starts_at=datetime(year=2026, month=1, day=1, tzinfo=UTC),
            ends_at=datetime(year=2026, month=1, day=8, tzinfo=UTC))
        message = make_message(id=123, author=MagicMock(id=test_config.dyno_id), embeds=[embed])
        channel = make_text_channel(id=test_config.challenge_info_channel_id)
        message.channel = channel

        await cog.on_message(message=message)

        cog.services.challenge.create_or_update_challenge.assert_called()
        kwargs = cog.services.challenge.create_or_update_challenge.call_args.kwargs
        data = kwargs["data"]

        assert data.title == embed.title
        assert data.description == embed.description
        assert data.id == message.id
        assert data.is_active == embed.is_active
        assert data.is_ongoing_voting == embed.is_ongoing_voting
        assert data.type == embed.type
        assert data.duration.starts_at == embed.starts_at
        assert data.duration.ends_at == embed.ends_at
        assert data.duration.voting_ends_at == embed.ends_at + timedelta(days=1)

    async def test_on_message_return_null_embed(self, cog, test_config):
        embed = MagicMock(
            title="test_challenge_title", description="test_description", type="official",
            is_active=True, is_onoing_voting=True, starts_at=datetime(year=2026, month=1, day=1, tzinfo=UTC),
            ends_at=datetime(year=2026, month=1, day=8, tzinfo=UTC))
        message = make_message(id=123, author=MagicMock(id=test_config.dyno_id), embeds=[embed])
        channel = make_text_channel(id=test_config.challenge_info_channel_id)
        message.channel = channel
        cog.extractor.extract_embed_data = AsyncMock(return_value=None)
        await cog.on_message(message=message)

        cog.services.challenge.create_or_update_challenge.assert_not_called()


    async def test_on_message_create_submission(self, cog, test_config):
        message = make_message(id=123, author=MagicMock(id=143124324))
        channel = make_text_channel(id=test_config.submission_channel_ids[0])
        message.channel = channel

        await cog.on_message(message=message)

        cog.services.challenge.add_submission.assert_called_once_with(message=message)

    
    async def test_on_message_author_bot(self, cog, test_config):
        message = make_message(id=123, author=MagicMock(id=test_config.bot_id))
        channel = make_text_channel(id=test_config.submission_channel_ids[0])
        message.channel = channel

        await cog.on_message(message=message)

        cog.services.challenge.add_submission.assert_not_called()

    async def test_on_raw_message_delete(self, cog, test_config):
        payload = MagicMock(RawMessageDeleteEvent)
        payload.channel_id = test_config.submission_channel_ids[0]
        payload.message_id = 12345
        await cog.on_raw_message_delete(payload=payload)

        cog.services.challenge.delete_submission.assert_called_once_with(payload.message_id)

    async def test_on_raw_message_delete_unrelated_channel(self, cog, test_config):
        payload = MagicMock(RawMessageDeleteEvent)
        payload.channel_id = 345345345
        payload.message_id = 12345
        await cog.on_raw_message_delete(payload=payload)

        cog.services.challenge.delete_submission.assert_not_called()


    async def test_on_raw_message_edit_challenge_update(self, cog, test_config):
        embed = MagicMock(
            title="test_challenge_title", description="test_description", type="official",
            is_active=True, is_onoing_voting=True, starts_at=datetime(year=2026, month=1, day=1, tzinfo=UTC),
            ends_at=datetime(year=2026, month=1, day=8, tzinfo=UTC))
        message = make_message(id=123, author=MagicMock(id=test_config.dyno_id), embeds=[embed])
        channel = make_text_channel(id=test_config.challenge_info_channel_id)
        message.channel = channel

        payload = MagicMock(RawMessageUpdateEvent)
        payload.message = message
        payload.channel_id = test_config.challenge_info_channel_id
        payload.message_id = 123

        await cog.on_raw_message_edit(payload=payload)

        cog.services.challenge.create_or_update_challenge.assert_called()
        kwargs = cog.services.challenge.create_or_update_challenge.call_args.kwargs
        data = kwargs["data"]

        assert data.title == embed.title
        assert data.description == embed.description
        assert data.id == message.id
        assert data.is_active == embed.is_active
        assert data.is_ongoing_voting == embed.is_ongoing_voting
        assert data.type == embed.type
        assert data.duration.starts_at == embed.starts_at
        assert data.duration.ends_at == embed.ends_at
        assert data.duration.voting_ends_at == embed.ends_at + timedelta(days=1)

    
    async def test_on_raw_message_edit_submision_update(self, cog, test_config):
        message = make_message(id=123, author=MagicMock(id=143124324))
        channel = make_text_channel(id=test_config.submission_channel_ids[0])
        message.channel = channel

        payload = MagicMock(RawMessageUpdateEvent)
        payload.message = message
        payload.channel_id = channel.id
        payload.message_id = message.id
        await cog.on_raw_message_edit(payload=payload)

        cog.services.challenge.update_submission.assert_called_once_with(message=message)
        

    async def test_on_raw_reaction_add_author_votes_for_themselves(self, cog, test_config):
        payload = MagicMock(RawReactionActionEvent)
        payload.user_id = 123
        payload.message_author_id = 123
        payload.emoji = "👍"

        await cog.on_raw_reaction_add(payload=payload)

        cog.services.challenge.vote.assert_not_called()
        cog.services.challenge.set_chosen_winner.assert_not_called()


    async def test_on_raw_reaction_add_vote(self, cog, test_config):
        payload = MagicMock(RawReactionActionEvent)
        payload.user_id = 123
        payload.message_id = 123243
        payload.message_author_id = 12345
        payload.emoji = "👍"
        payload.channel_id = test_config.submission_channel_ids[0]

        await cog.on_raw_reaction_add(payload=payload)

        cog.services.challenge.vote.assert_called_once_with(submission_id=payload.message_id, voter_id=payload.user_id)
        cog.services.challenge.set_chosen_winner.assert_not_called()

    
    async def test_on_raw_reaction_set_chosen_winner(self, cog, test_config):
        payload = MagicMock(RawReactionActionEvent)
        payload.user_id = test_config.admin_id
        payload.message_id = 123243
        payload.message_author_id = 12345
        payload.emoji = "🏆"
        payload.channel_id = test_config.submission_channel_ids[0]

        await cog.on_raw_reaction_add(payload=payload)

        cog.services.challenge.vote.assert_not_called()
        cog.services.challenge.set_chosen_winner.assert_called_once_with(user_id=payload.message_author_id, submission_id=payload.message_id)

    async def test_on_raw_reaction_unrelated_channel_returns(self, cog, test_config):
        payload = MagicMock(RawReactionActionEvent)
        payload.user_id = test_config.admin_id
        payload.message_id = 123243
        payload.message_author_id = 12345
        payload.emoji = "🏆"
        payload.channel_id = 1232345345142423

        await cog.on_raw_reaction_add(payload=payload)

        cog.services.challenge.vote.assert_not_called()
        cog.services.challenge.set_chosen_winner.assert_not_called()

    
    async def test_on_raw_reaction_admin_adds_vote(self, cog, test_config):
        payload = MagicMock(RawReactionActionEvent)
        payload.user_id = test_config.admin_id
        payload.message_id = 123243
        payload.message_author_id = 12345
        payload.emoji = "👍"
        payload.channel_id = test_config.submission_channel_ids[0]

        await cog.on_raw_reaction_add(payload=payload)

        cog.services.challenge.vote.assert_called_once_with(submission_id=payload.message_id, voter_id=payload.user_id)
        cog.services.challenge.set_chosen_winner.assert_not_called()


    async def test_on_reaction_remove_vote(self, cog, test_config):
        payload = MagicMock(RawMessageDeleteEvent)
        payload.channel_id = test_config.submission_channel_ids[0]
        payload.emoji = "👍"
        payload.message_id = 1234132
        payload.user_id = 1234234

        await cog.on_raw_reaction_remove(payload=payload)

        cog.services.challenge.remove_vote.assert_called_once_with(submission_id=payload.message_id, voter_id=payload.user_id)
        cog.services.challenge.remove_chosen_winner.assert_not_called()


    async def test_on_reaction_remove_winner(self, cog, test_config):
        payload = MagicMock(RawMessageDeleteEvent)
        payload.channel_id = test_config.submission_channel_ids[0]
        payload.emoji = "🏆"
        payload.message_id = 1234132
        payload.user_id = test_config.admin_id
        submission_message = make_message(id=123123213, author=MagicMock(id=12332123132))
        official_submission_channel = MagicMock()
        official_submission_channel.fetch_message = AsyncMock(return_value=submission_message)
        cog.bot.channels.official_submission = official_submission_channel
        await cog.on_raw_reaction_remove(payload=payload)

        cog.services.challenge.remove_vote.assert_not_called()
        cog.services.challenge.remove_chosen_winner.assert_called_once_with(user_id=submission_message.author.id, submission_id=submission_message.id)


    async def test_on_reaction_remove_unrelated_channel(self, cog, test_config):
        payload = MagicMock(RawMessageDeleteEvent)
        payload.channel_id = 23423423432
        payload.emoji = "👍"
        payload.message_id = 1234132
        payload.user_id = 1234234

        await cog.on_raw_reaction_remove(payload=payload)

        cog.services.challenge.remove_vote.assert_not_called()
        cog.services.challenge.remove_chosen_winner.assert_not_called()