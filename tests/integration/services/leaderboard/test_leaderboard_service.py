from datetime import UTC, datetime, timedelta
import discord
import pytest
from bot.services.leaderboard import LeaderboardService
from unittest.mock import AsyncMock, MagicMock

class TestLeaderboardService:
    @pytest.fixture
    async def service(self, uow, mock_bot, test_config):
        mock_bot.convert_users_to_members_data = AsyncMock(
            side_effect=lambda data: [
                (f"<@{user.id}>", val) for user, val in data
            ]
        )

        mock_channel = AsyncMock(spec=discord.TextChannel)
        mock_channel.id = 1001

        sent_message = MagicMock(spec=discord.Message)
        sent_message.id = 99999
        mock_channel.send = AsyncMock(return_value=sent_message)

        fetched_message = MagicMock(spec=discord.Message)
        fetched_message.id = 99999
        fetched_message.edit = AsyncMock()
        mock_channel.fetch_message = AsyncMock(return_value=fetched_message)

        mock_bot.channels = MagicMock()
        mock_bot.channels.leaderboards = mock_channel

        return LeaderboardService(uow=uow, bot=mock_bot, converter=AsyncMock(), config=test_config)
        

    async def test_creates_new_message_when_none_exists(
        self, service, uow):
        mock_embed = MagicMock(spec=discord.Embed)
        channel = service.bot.channels.leaderboards

        await service.create_or_update_leaderboard_message(
            channel=channel,
            embed=mock_embed,
            lb_type="test_lb_type"
        )

        channel.send.assert_called_once_with(embed=mock_embed)

        stored_id = await uow.leaderboards.get_lb_message_id("test_lb_type")
        assert stored_id == 99999

    async def test_edits_existing_message_when_id_stored(
    self, service, uow
    ):
        mock_embed = MagicMock(spec=discord.Embed)
        channel = service.bot.channels.leaderboards


        await service.create_or_update_leaderboard_message(
            channel=channel, embed=mock_embed, lb_type="test_lb_type"
        )
        channel.send.reset_mock()

        await service.create_or_update_leaderboard_message(
            channel=channel, embed=mock_embed, lb_type="test_lb_type"
        )

        channel.send.assert_not_called()
        channel.fetch_message.assert_called_with(99999)
        fetched_message = await channel.fetch_message(99999)
        fetched_message.edit.assert_called_with(embed=mock_embed)


    async def test_creates_new_message_when_fetch_fails(
        self, service, uow
    ):
        mock_embed = MagicMock(spec=discord.Embed)
        channel = service.bot.channels.leaderboards

        await uow.leaderboards.insert_lb_message_id(88888, "test_lb_type")

        channel.fetch_message = AsyncMock(
            side_effect=discord.NotFound(MagicMock(), "message not found")
        )

        new_message = MagicMock(spec=discord.Message)
        new_message.id = 77777
        channel.send = AsyncMock(return_value=new_message)

        await service.create_or_update_leaderboard_message(
            channel=channel, embed=mock_embed, lb_type="test_lb_type"
        )

        channel.send.assert_called_once_with(embed=mock_embed)

        stored_id = await uow.leaderboards.get_lb_message_id("test_lb_type")
        assert stored_id == 77777



    async def test_feedback_leaderboard_sends_embed_with_real_data(
    self, service, uow, seeded_feedbacks, seeded_users
    ):
        await service.create_or_update_feedback_leaderboard()

        channel = service.bot.channels.leaderboards
        channel.send.assert_called_once()
        
        sent_embed = channel.send.call_args.kwargs["embed"]
        assert sent_embed is not None
        assert sent_embed.title == "**FEEDBACK LEADERBOARD**"
        

        assert str(seeded_feedbacks.total_feedbacks) in sent_embed.description


    async def test_submission_leaderboard_sends_embed_with_real_data(
    self, service, uow, seeded_users, seeded_submissions
    ):
        await service.create_or_update_submission_leaderboard()

        channel = service.bot.channels.leaderboards
        channel.send.assert_called_once()
        
        sent_embed = channel.send.call_args.kwargs["embed"]
        assert sent_embed is not None
        assert sent_embed.title == "**MOST ACTIVE CHALLENGERS**"
        

        assert str(len(seeded_submissions.all)) in sent_embed.description

    async def test_all_time_winners_leaderboard_sends_embed_with_real_data(
    self, service, uow, seeded_users,seeded_winners
    ):
        await service.create_or_update_all_time_challenges_won_leaderboard()

        channel = service.bot.channels.leaderboards
        channel.send.assert_called_once()
        
        sent_embed = channel.send.call_args.kwargs["embed"]
        assert sent_embed is not None
        assert sent_embed.title == "**WINNERS LEADERBOARD**"
        

        assert str(len(seeded_winners.all)) in sent_embed.description


    
    async def test_server_activity_board_sends_embed_with_real_data(
    self, service, uow, seeded_users, make_activity_tracks, make_activity_feedbacks
    ):
        dates = [
        datetime.now(UTC)-timedelta(hours=2),
        datetime.now(UTC)-timedelta(days=5),
        datetime.now(UTC)-timedelta(days=25)
        ]
        tracks = await make_activity_tracks(members=seeded_users.all, channel_id=111, n=20, dates=dates)
        feedbacks = await make_activity_feedbacks(members=seeded_users.all, channel_id=111, tracks=tracks, dates=dates)

        sent_embed = await service.server_activity_board()

        
        assert sent_embed is not None
        assert sent_embed.title == f"**SERVER ACTIVITY**"
        
        dict_embed = sent_embed.to_dict()
        fields = dict_embed.get("fields")

        daily,weekly,monthly = fields

        total_tracks_daily = str(len(tracks.get_all_tracks_created_at(dates[0])))
        total_feedbacks_daily = str(len(feedbacks.get_all_feedbacks_created_at(dates[0])))

        total_tracks_weekly = str(len(tracks.get_all_tracks_created_at(dates[1]))+ int(total_tracks_daily))
        total_feedbacks_weekly = str(len(feedbacks.get_all_feedbacks_created_at(dates[1]))+ int(total_feedbacks_daily))

        total_tracks_monthly = str(len(feedbacks.all))
        total_feedbacks_monthly = str(len(tracks.all))

        assert total_tracks_daily in daily.get("value")
        assert total_feedbacks_daily in daily.get("value")

        assert total_tracks_weekly in weekly.get("value")
        assert total_feedbacks_weekly in weekly.get("value")

        assert total_tracks_monthly in monthly.get("value")
        assert total_feedbacks_monthly in monthly.get("value")


    async def test_server_activity_board_excludes_out_of_date_range_posts(
    self, service, uow, seeded_users, make_activity_tracks, make_activity_feedbacks
    ):
        await uow.tracks.add(
            {
                "id":213421,
                "author_id":seeded_users.track_author1.id,
                "title":"test_title",
                "thread_id":213421,
                "channel_id":111,
                "created_at":datetime(year=2024, month=2, day=3, tzinfo=UTC)
            }
        )

        await uow.feedback.add(
            {
                "id":212333421,
                "author_id":seeded_users.fb_author1.id,
                "content":"test_content",
                "track_id":213421,
                "thread_id":213421,
                "channel_id":111,
                "created_at":datetime(year=2024, month=2, day=3, tzinfo=UTC),
                "word_count":2
            }
        )

        dates = [
        datetime.now(UTC)-timedelta(hours=2),
        datetime.now(UTC)-timedelta(days=5),
        datetime.now(UTC)-timedelta(days=25)
        ]
        tracks = await make_activity_tracks(members=seeded_users.all, channel_id=111, n=20, dates=dates)
        feedbacks = await make_activity_feedbacks(members=seeded_users.all, channel_id=111, tracks=tracks, dates=dates)

        sent_embed = await service.server_activity_board()

        
        assert sent_embed is not None
        assert sent_embed.title == f"**SERVER ACTIVITY**"
        
        dict_embed = sent_embed.to_dict()
        fields = dict_embed.get("fields")

        daily,weekly,monthly = fields

        total_tracks_daily = str(len(tracks.get_all_tracks_created_at(dates[0])))
        total_feedbacks_daily = str(len(feedbacks.get_all_feedbacks_created_at(dates[0])))

        total_tracks_weekly = str(len(tracks.get_all_tracks_created_at(dates[1]))+ int(total_tracks_daily))
        total_feedbacks_weekly = str(len(feedbacks.get_all_feedbacks_created_at(dates[1]))+ int(total_feedbacks_daily))

        total_tracks_monthly = str(len(feedbacks.all))
        total_feedbacks_monthly = str(len(tracks.all))

        assert total_tracks_daily in daily.get("value")
        assert total_feedbacks_daily in daily.get("value")

        assert total_tracks_weekly in weekly.get("value")
        assert total_feedbacks_weekly in weekly.get("value")

        assert total_tracks_monthly in monthly.get("value")
        assert total_feedbacks_monthly in monthly.get("value")