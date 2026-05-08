from discord import Object
import pytest
from unittest.mock import AsyncMock, MagicMock

from tests.factories.discord_factories import make_guild, make_text_channel
from tests.factories.db_factories import make_user, make_challenge, make_feedback, make_submission, make_track, make_track_with_no_feedback, make_vote, make_winner
from bot.registry.channel_registry import ChannelRegistry
from bot.types.common import ChallengeDurationData, ChallengeEmbedData
from datetime import datetime, timedelta
from bot.config import Config
from bot.utils.extract_attachment_data import MessageExtractor
from bot.types.tests.user import UserCollection
@pytest.fixture
def mock_guild():
    return make_guild()


@pytest.fixture
async def seeded_users(
    make_user
) -> UserCollection:
    submission_author1 = await make_user(user_id=999, username="submission_author1", display_name="submission_author_display_name1")
    submission_author2 = await make_user(user_id=998, username="submission_author2", display_name="submission_author_display_name2")
    submission_author3 = await make_user(user_id=997, username="submission_author3", display_name="submission_author_display_name3")

    track_author1 = await make_user(user_id=899, username="track_author1", display_name="track_display_name1")
    track_author2 = await make_user(user_id=898, username="track_author2", display_name="track_display_name2")
    track_author3 = await make_user(user_id=897, username="track_author3", display_name="track_display_name3")

    voter1 = await make_user(user_id=799, username="voter1", display_name="voter_display_name1")
    voter2 = await make_user(user_id=798, username="voter2", display_name="voter_display_name2")
    voter3 = await make_user(user_id=797, username="voter3", display_name="voter_display_name3")
    voter4 = await make_user(user_id=796, username="voter4", display_name="voter_display_name4")

    feedback_author1 = await make_user(user_id=699, username="fb_author1", display_name="fb_author_display_name1")
    feedback_author2 = await make_user(user_id=698, username="fb_author2", display_name="fb_author_display_name2")
    feedback_author3 = await make_user(user_id=697, username="fb_author3", display_name="fb_author_display_name3")

    
    
    return UserCollection(
        submission_author1=submission_author1,
        submission_author2=submission_author2,
        submission_author3=submission_author3,

        track_author1=track_author1,
        track_author2=track_author2,
        track_author3=track_author3,

        voter1=voter1,
        voter2=voter2,
        voter3=voter3,
        voter4=voter4,

        fb_author1=feedback_author1,
        fb_author2=feedback_author2,
        fb_author3=feedback_author3
    )


@pytest.fixture
def test_config():
    return Config(
        discord_token="fake",
        dc_webhook="fake",
        spotify_api_client_id="fake",
        spotify_api_client_secret="fake",
        db_url="postgresql+asyncpg://test:test@localhost/testdb",
        db_mig_url="postgresql+psycopg2://test:test@localhost/testdb",
        db_health_url="postgresql://test:test@localhost/testdb",
        db_host="localhost",
        db_name="testdb",
        db_password="test",
        db_port="5432",
        db_user="test",
        fb_channel_ids="1007,2007,3007,1009,2009,3009",
        link_channel_ids="1008",
        attachment_channel_ids="1009, 2009, 3009",
        submission_channels="1004,1005",
        challenge_info_channel_id=1003,
        leaderboards_channel_id=1001,
        commands_channel_id=229422,

        developer_id=34534372632456,

        challenge_role_three_id=12432424124,
        challenge_role_ten_id=124123423324345,
        challenge_role_thirty_id=3243245342,
        challenge_role_fifty_id=324324325345,
        challenge_role_hundred_id=23432534534634,

        feedback_role_fifteen_id=654654745,
        feedback_role_thirty_id=456456456456,
        feedback_role_fifty_id=435346457657,
        feedback_role_hundred_id=54645645746,
        feedback_role_thousand_id=345234364566,



        official_submission_channel_id=1004,
        rules_channel_id=1010,
        rules_message_id=1011,
        tiny_submission_channel_id=1005,
        winners_hall_channel_id=1002,
        tracks_no_feedback_channel_id=1006,
        guild_id=999,
        dyno_id=155149108183695360,
        admin_id=396238425558351872,
        bot_id=123456,
    )





@pytest.fixture
def mock_channel_registery(test_config):
    channels = MagicMock(spec=ChannelRegistry)
    channels.leaderboards = make_text_channel(id=test_config.leaderboards_channel_id, name="leaderboards")
    channels.winners_hall = make_text_channel(id=test_config.winners_hall_channel_id, name="winners-hall")
    channels.challenge_info = make_text_channel(id=test_config.challenge_info_channel_id, name="challenge-info")
    channels.official_submission = make_text_channel(id=test_config.official_submission_channel_id, name="official-submission")
    channels.tiny_submission = make_text_channel(id=test_config.tiny_submission_channel_id, name="tiny-submission")
    channels.tracks_no_feedback = make_text_channel(id=test_config.tracks_no_feedback_channel_id, name="tracks-no-feedback")
    channels.feedback = [make_text_channel(id=test_config.feedback_channel_ids, name="feedback-general")]

    return channels


@pytest.fixture
def mock_challenge_validator(test_config):
    def validate(message, challenge):
        if challenge.type == "community" and message.channel.id == test_config.official_submission_channel_id:
            return False
    
        if challenge.type == "official" and message.channel.id == test_config.tiny_submission_channel_id:
            return False
        
        if message.channel.id not in test_config.submission_channel_ids:
            return False
        
        if message.created_at > challenge.ends_at:
            return False
        
        return True

    challenge_validator = MagicMock()
    challenge_validator.validate = MagicMock(side_effect=validate)
    return challenge_validator


@pytest.fixture
def mock_event_handler():
    event_handler = MagicMock()
    event_handler.emit_async = AsyncMock()

    return event_handler


@pytest.fixture
def mock_track_extractor():
    extractor = MagicMock()
    extractor.extract_title = AsyncMock(return_value=("test_title", "test_platform"))


    return extractor


@pytest.fixture
def mock_extractor(mock_bot, test_config):
    async def mock_extract_embed_data(message_id:int, embed:MagicMock):
        return ChallengeEmbedData(
                title=embed.title,
                description=embed.description,
                field_names= [],
                field_values=[],
                id=message_id,
                is_active=embed.is_active,
                is_ongoing_voting=embed.is_ongoing_voting,
                type=embed.type,
                duration=ChallengeDurationData(
                    starts_at=embed.starts_at,
                    ends_at=embed.ends_at,
                    voting_ends_at=embed.ends_at + timedelta(days=1)
                )
            )

    async def mock_get_submission_data(challenge, message) -> dict:
        return {
        "id":message.id,
        "channel_id":message.channel.id,
        "title":message.title,
        "challenge_id":challenge.id, 
        "author_id":message.author.id,
        "created_at":message.created_at,
        "edited_at":message.edited_at}

        

    extractor = MessageExtractor(bot=mock_bot, config=test_config, track_extractor=AsyncMock())
    extractor.get_submission_title = AsyncMock(return_value="test_title")
    extractor.get_submission_data = AsyncMock(side_effect=mock_get_submission_data)
    extractor.extract_track_message_title = AsyncMock(return_value=("test_track_title", "test_platform"))
    extractor.extract_embed_data = AsyncMock(side_effect=mock_extract_embed_data)

    return extractor

def mock_safe_fetch_messages(
        channel,
        operation: str,
        limit:int | None = None,
        after:Object | datetime | None = None,
        before:Object | datetime | None = None,
        oldest_first: bool = False,
        default=[]
    ):
        async def _fetch(
        channel,
        operation: str,
        limit:int | None = None,
        after:Object | datetime | None = None,
        before:Object | datetime | None = None,
        oldest_first: bool = False,
        default=[]
        ):
            try:
                messages = [message async for message in channel.history(limit=limit, after=after, before=before, oldest_first=oldest_first)]
                return messages
            except:
                return default
        
        return _fetch(
            channel,
            operation,
            limit,
            after,
            before,
            oldest_first,
            default
        )



def mock_safe_reaction_users(
    reaction,
    operation: str,
    limit:int | None = None,
    after:Object | datetime | None = None,
    before:Object | datetime | None = None,
    oldest_first: bool = False,
    default=[]
    ):
        async def _fetch(
        reaction,
        operation: str,
        limit:int | None = None,
        after:Object | datetime | None = None,
        before:Object | datetime | None = None,
        oldest_first: bool = False,
        default=[]
        ):
            try:
                users = [user async for user in reaction.users(limit=limit, after=after) if not user.bot]
                return users
            except Exception as e:
                return default
        
        return _fetch(
            reaction,
            operation,
            limit,
            after,
            before,
            oldest_first,
            default
        )



def mock_safe_fetch_members(
        guild,
        operation: str,
        limit:int | None = None,
        after:Object | datetime | None = None,
        before:Object | datetime | None = None,
        oldest_first: bool = False,
        default=[]
    ):
        async def _fetch(
        guild,
        operation: str,
        limit:int | None = None,
        after:Object | datetime | None = None,
        before:Object | datetime | None = None,
        oldest_first: bool = False,
        default=[]
        ):
            try:
                members = [member async for member in guild.fetch_members(limit=limit, after=after)]
                return members
            except:
                return default
        
        return _fetch(
            guild,
            operation,
            limit,
            after,
            before,
            oldest_first,
            default
        )
    

def mock_safe_fetch_threads(
    channel,
    operation: str,
    limit:int | None = None,
    after:Object | datetime | None = None,
    before:Object | datetime | None = None,
    oldest_first: bool = False,
    default=[]
    ):
        async def _fetch(
        channel,
        operation: str,
        limit:int | None = None,
        after:Object | datetime | None = None,
        before:Object | datetime | None = None,
        oldest_first: bool = False,
        default=[]
        ):
            threads = [user async for user in channel.archived_threads(limit=limit)]
            return threads
        return _fetch(
            channel,
            operation,
            limit,
            after,
            before,
            oldest_first,
            default
        )


@pytest.fixture
def mock_client():
    def mock_safe_call(coro, operation, default=None):
        async def _call(coro, operation, default):
            try:
                return await coro()
            except:
                
                return default
        return _call(coro, operation, default)
    
    def mock_safe_write_call(coro, operation, default=None):
        async def _call(coro, operation, default):
            try:
                return await coro()
            except:
                return default
        return _call(coro, operation, default)

    client = MagicMock()
    client.safe_discord_call = MagicMock(side_effect=mock_safe_call)
    client.safe_fetch_messages = MagicMock(side_effect=mock_safe_fetch_messages)
    client.safe_fetch_members = MagicMock(side_effect=mock_safe_fetch_members)
    client.safe_fetch_reaction_users = MagicMock(side_effect=mock_safe_reaction_users)
    client.safe_fetch_threads = MagicMock(side_effect=mock_safe_fetch_threads)
    client.safe_discord_write_call = MagicMock(side_effect=mock_safe_write_call)

    return client


@pytest.fixture
def mock_bot(
    mock_guild,
    test_config,
    mock_channel_registery,
    mock_client
    ):
    bot = MagicMock()
    bot.guild = mock_guild
    bot.guild.fetch_member = AsyncMock()
    bot.config = test_config
    bot.client = mock_client
    bot.channels = mock_channel_registery
    
    return bot

@pytest.fixture
def mock_uow():
    uow = MagicMock()
    uow.users = MagicMock()
    uow.tracks = MagicMock()
    uow.feedback = MagicMock()
    uow.challenges = MagicMock()
    uow.leaderboards = MagicMock()

    for repo in [uow.users, uow.tracks, uow.feedback, uow.challenges, uow.leaderboards]:
        for attr in dir(repo):
            if not attr.startswith("_"):
                setattr(repo, attr, AsyncMock())

    tx = MagicMock()
    tx.users = MagicMock()
    tx.tracks = MagicMock()
    tx.feedback = MagicMock()
    tx.challenges = MagicMock()
    for repo in [tx.users, tx.tracks, tx.feedback, tx.challenges]:
        for attr in dir(repo):
            if not attr.startswith("_"):
                setattr(repo, attr, AsyncMock())

    uow.transaction = MagicMock()
    uow.transaction.return_value.__aenter__ = AsyncMock(return_value=tx)
    uow.transaction.return_value.__aexit__ = AsyncMock(return_value=False)
    uow._tx = tx 
    return uow