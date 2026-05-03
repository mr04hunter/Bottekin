from datetime import datetime, UTC
from discord import NotFound
import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.services.track_notification_service import TrackNotificationService
from tests.factories.discord_factories import make_message, make_text_channel, make_thread


class TestTrackNotification:
    @pytest.fixture
    async def service(self, uow, mock_bot):
        return TrackNotificationService(bot=mock_bot, uow=uow)
    
    async def test_sync_track_with_no_feedback(self, uow, service, seeded_tracks):
        message = make_message(id=seeded_tracks.track1.id, author=MagicMock(id=seeded_tracks.track1.author_id))
        thread = make_thread(id=seeded_tracks.track1.id, owner_id=seeded_tracks.track1.author_id)

        service.bot.channels.tracks_no_feedback.guild.fetch_channel = AsyncMock(return_value=thread)
        service.bot.channels.tracks_no_feedback.send = AsyncMock(return_value=MagicMock(id=12345, created_at=datetime(year=2026, month=1, day=1, tzinfo=UTC)))

        await service.sync_track_with_no_feedback(message.id, 0)

        service.bot.channels.tracks_no_feedback.guild.fetch_channel.assert_called_once_with(message.id)
        service.bot.channels.tracks_no_feedback.send.assert_called_once_with(f"{thread.jump_url} | Total feedback: {0}")

        track_with_no_feedback = await uow.tracks.get_track_with_no_feedback(track_id=seeded_tracks.track1.id)


        assert track_with_no_feedback is not None
        assert track_with_no_feedback.message_id == 12345
        assert track_with_no_feedback.message_url == thread.jump_url


    async def test_sync_track_with_no_feedback_more_than_three_feedback(self, uow, service, seeded_tracks, seeded_tracks_with_no_feedback):
        message = make_message(id=seeded_tracks_with_no_feedback.track_wn_feedback1.message_id, author=MagicMock(id=seeded_tracks.track1.author_id))
        thread = make_thread(id=seeded_tracks.track1.id, owner_id=seeded_tracks.track1.author_id)

        service.bot.channels.tracks_no_feedback.guild.fetch_channel = AsyncMock(return_value=thread)
        service.bot.channels.tracks_no_feedback.fetch_message = AsyncMock(return_value=message)

        await service.sync_track_with_no_feedback(seeded_tracks_with_no_feedback.track_wn_feedback1.track_id, 3)

        service.bot.channels.tracks_no_feedback.fetch_message.assert_called_once_with(seeded_tracks_with_no_feedback.track_wn_feedback1.message_id)
        message.delete.assert_called_once()

        track_with_no_feedback = await uow.tracks.get_track_with_no_feedback(track_id=seeded_tracks.track1.id)


        assert track_with_no_feedback is None


    async def test_existing_sync_track_with_no_feedback(self, uow, service, seeded_tracks, seeded_tracks_with_no_feedback):
        message = make_message(id=seeded_tracks_with_no_feedback.track_wn_feedback1.message_id, author=MagicMock(id=seeded_tracks.track1.author_id))
        thread = make_thread(id=seeded_tracks.track1.id, owner_id=seeded_tracks.track1.author_id)

        service.bot.channels.tracks_no_feedback.guild.fetch_channel = AsyncMock(return_value=thread)
        service.bot.channels.tracks_no_feedback.fetch_message = AsyncMock(return_value=message)

        await service.sync_track_with_no_feedback(seeded_tracks_with_no_feedback.track_wn_feedback1.track_id, 2)

        service.bot.channels.tracks_no_feedback.fetch_message.assert_called_once_with(seeded_tracks_with_no_feedback.track_wn_feedback1.message_id)
        message.edit.assert_called_once_with(content=f"{thread.jump_url} | Total feedback: {2}")

        track_with_no_feedback = await uow.tracks.get_track_with_no_feedback(track_id=seeded_tracks.track1.id)


        assert track_with_no_feedback is not None
        assert track_with_no_feedback.message_id == seeded_tracks_with_no_feedback.track_wn_feedback1.message_id
        assert track_with_no_feedback.message_url == seeded_tracks_with_no_feedback.track_wn_feedback1.message_url

    async def test_existing_sync_track_with_no_feedback_message_not_found(self, uow, service, seeded_tracks, seeded_tracks_with_no_feedback):
        deleted_message = make_message(id=seeded_tracks_with_no_feedback.track_wn_feedback1.message_id, author=MagicMock(id=seeded_tracks.track1.author_id))
        thread = make_thread(id=seeded_tracks.track1.id, owner_id=seeded_tracks.track1.author_id)

        new_message = make_message(id=123123123, author=MagicMock(id=seeded_tracks.track1.author_id), created_at=datetime(year=2026, month=1, day=1, tzinfo=UTC))

        service.bot.channels.tracks_no_feedback.guild.fetch_channel = AsyncMock(return_value=thread)
        service.bot.channels.tracks_no_feedback.fetch_message = AsyncMock(side_effect=NotFound(response=MagicMock(), message=MagicMock()))
        service.bot.channels.tracks_no_feedback.send = AsyncMock(return_value=new_message)
        await service.sync_track_with_no_feedback(seeded_tracks_with_no_feedback.track_wn_feedback1.track_id, 2)

        service.bot.channels.tracks_no_feedback.fetch_message.assert_called_once_with(seeded_tracks_with_no_feedback.track_wn_feedback1.message_id)
        deleted_message.edit.assert_not_called()
        service.bot.channels.tracks_no_feedback.send.assert_called_once_with(f"{thread.jump_url} | Total feedback: {2}")

        track_with_no_feedback = await uow.tracks.get_track_with_no_feedback(track_id=seeded_tracks.track1.id)


        assert track_with_no_feedback is not None
        assert track_with_no_feedback.message_id == new_message.id
        assert track_with_no_feedback.message_url == thread.jump_url
        assert track_with_no_feedback.created_at == new_message.created_at


    async def test_cleanup_channel_all_deleted(self, uow, service, seeded_tracks_with_no_feedback):
        messages = [make_message(id=tw_no_feedback.message_id) for tw_no_feedback in seeded_tracks_with_no_feedback.all]
        service.bot.channels.tracks_no_feedback.messages = messages

        await service.cleanup_tracks_no_feedback()

        for message in messages:
            message.delete.assert_called_once()

        for tw_no_feedback in seeded_tracks_with_no_feedback.all:
            assert await uow.tracks.get_track_with_no_feedback(track_id=tw_no_feedback.track_id) is None

    async def test_cleanup_channel_valids_remain(self, uow, service, seeded_tracks_with_no_feedback):

        #valid track_with_no_feedback, not older than 2 weeks
        await uow.tracks.create_track_with_no_feedback(
            track_id=seeded_tracks_with_no_feedback.track_wn_feedback1.track_id,
            message_id=seeded_tracks_with_no_feedback.track_wn_feedback1.message_id,
            url="some_url",
            created_at=datetime.now(tz=UTC))
        
        messages = [make_message(id=tw_no_feedback.message_id) for tw_no_feedback in seeded_tracks_with_no_feedback.all]

        service.bot.channels.tracks_no_feedback.messages = messages

        await service.cleanup_tracks_no_feedback()

        for message in messages:
            if message.id == seeded_tracks_with_no_feedback.track_wn_feedback1.message_id:
                message.delete.assert_not_called()
                continue

            message.delete.assert_called_once()


    async def test_cleanup_channel_all_deleted_pagination(self, uow, service, seeded_tracks_with_no_feedback):
        messages = [make_message(id=tw_no_feedback.message_id, created_at=tw_no_feedback.created_at) for tw_no_feedback in seeded_tracks_with_no_feedback.all]
        service.bot.channels.tracks_no_feedback = make_text_channel(messages=messages, page_size=1)

        await service.cleanup_tracks_no_feedback()

        for message in messages:
            message.delete.assert_called_once()

        for tw_no_feedback in seeded_tracks_with_no_feedback.all:
            assert await uow.tracks.get_track_with_no_feedback(track_id=tw_no_feedback.track_id) is None



    async def test_delete_track_with_no_feedback_message(self, service):
        message = make_message(id=1231234)
        service.bot.channels.tracks_no_feedback.fetch_message = AsyncMock(return_value=message)

        await service.delete_track_with_no_feedback_message(message_id=message.id)

        service.bot.channels.tracks_no_feedback.fetch_message.assert_called_once_with(message.id)
        message.delete.assert_called_once()