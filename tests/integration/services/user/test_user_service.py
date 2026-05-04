from unittest.mock import AsyncMock, MagicMock
import pytest
from bot.services.user import UserService
from tests.factories.discord_factories import make_message, make_text_channel

class TestUserService:
    @pytest.fixture
    async def service(self, uow, mock_bot):
        event_handler = MagicMock()
        event_handler.emit_async = AsyncMock()
        event_handler = event_handler
        user_service = UserService(uow=uow, bot=mock_bot, event_handler=event_handler)


        return user_service

    async def test_create_user(
            self, service, uow, make_user
    ):
        await service.create_user(user_id=999, username="username", display_name="display_name", is_purge_data=True)

        user = await uow.users.get_by_id(999)

        assert user is not None
        assert user.id == 999
        assert user.username == "username"
        assert user.display_name == "display_name"
        assert user.is_purge_data == True

    
    async def test_delete_user(
            self,  service, uow, seeded_users
    ):
        await service.delete_user(seeded_users.submission_author1.id)

        assert await uow.users.get_by_id(seeded_users.submission_author1.id) is None


    async def test_change_stats_increment(
            self, service, uow, seeded_users
    ):
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_submissions", count=5)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_feedbacks_given", count=10)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_challenges_won", count=15)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_feedback_words", count=30)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="times_voted", count=3)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_votes_received", count=12)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_feedbacks_received", count=23)
        user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert user.total_submissions == 5
        assert user.total_feedbacks_given == 10
        assert user.total_challenges_won == 15
        assert user.total_feedback_words == 30
        assert user.times_voted == 0 #not in STATS constant
        assert user.total_votes_received == 0 #not in STATS constant
        assert user.total_feedbacks_received == 23


    async def test_change_stats_decrement(
            self, service, uow, seeded_users
    ):
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_submissions", count=5)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_feedbacks_given", count=10)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_challenges_won", count=15)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_feedback_words", count=30)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="times_voted", count=3)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_votes_received", count=12)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_feedbacks_received", count=23)


        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_submissions", count=-2)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_feedbacks_given", count=-5)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_challenges_won", count=-3)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_feedback_words", count=-7)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="times_voted", count=-1)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_votes_received", count=-3)
        await service.change_stats(user_id=seeded_users.submission_author1.id, field="total_feedbacks_received", count=-2)

        user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert user.total_submissions == 3
        assert user.total_feedbacks_given == 5
        assert user.total_challenges_won == 12
        assert user.total_feedback_words == 23
        assert user.times_voted == 0 #not in STATS constant
        assert user.total_votes_received == 0 #not in STATS constant
        assert user.total_feedbacks_received == 21


    async def test_set_purge_data(
            self, service, uow, seeded_users
    ):
        await service.set_purge_data(user_id=seeded_users.submission_author1.id, purge=False)

        user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert user.is_purge_data == False

        await service.set_purge_data(user_id=seeded_users.submission_author1.id, purge=True)

        user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert user.is_purge_data == True

    async def test_get_with_stats(
        self,
        service,
        uow,
        seeded_users,
        seeded_tracks,
        seeded_feedbacks,
        seeded_challenge,
        seeded_submissions,
        seeded_votes,
        seeded_winners
    ):
        submission_author1_with_stats = await service.get_with_stats(user_id=seeded_users.submission_author1.id)
        assert submission_author1_with_stats.total_submissions == seeded_submissions.get_total_of_user(seeded_users.submission_author1.id)
        assert submission_author1_with_stats.total_challenges_won == seeded_winners.get_total_wins(seeded_users.submission_author1.id)
        assert submission_author1_with_stats.total_votes_received == seeded_votes.get_total_votes_received(
            seeded_submissions.get_submission_ids_of_user(seeded_users.submission_author1.id))

        fb_author1_with_stats = await service.get_with_stats(user_id=seeded_users.fb_author1.id)
        assert fb_author1_with_stats.total_feedbacks_given == seeded_feedbacks.get_total_feedbacks_of_user(seeded_users.fb_author1.id)
        assert fb_author1_with_stats.total_feedback_words == seeded_feedbacks.get_total_fb_words_of_user(seeded_users.fb_author1.id)

        voter1_with_stats = await service.get_with_stats(seeded_users.voter1.id)
        assert voter1_with_stats.times_voted == seeded_votes.get_times_voted(seeded_users.voter1.id)


    async def test_handle_member_leave_purges(
            self, service, uow, seeded_users, seeded_tracks
    ):
        service._notify_track_thread = AsyncMock()
        await service.handle_member_leave(seeded_users.track_author1.id)

        user = await uow.users.get_by_id(seeded_users.track_author1.id)
        assert user is None

        total_tracks_of_user = seeded_tracks.get_total_tracks_of_user(seeded_users.track_author1.id)


        assert service._notify_track_thread.call_count == seeded_tracks.get_total_tracks_of_user(seeded_users.track_author1.id)
        

    async def test_handle_member_leave_limit_three(
            self, service, uow,seeded_users, seeded_tracks
    ):
        await service.uow.tracks.add(
            {
                "id":888888,
                "thread_id":888888,
                "author_id":seeded_users.track_author1.id,
                "title":"test_title",
                "channel_id":11123453,
                "platform":"test_platform"
            }
        )

        await service.uow.tracks.add(
            {
                "id":999999,
                "thread_id":999999,
                "author_id":seeded_users.track_author1.id,
                "title":"test_title",
                "channel_id":113453123,
                "platform":"test_platform"
            }
        )

        await service.uow.tracks.add(
            {
                "id":55555,
                "thread_id":55555,
                "author_id":seeded_users.track_author1.id,
                "title":"test_title",
                "channel_id":11345345123,
                "platform":"test_platform"
            }
        )


        channel1 = make_text_channel(id=11123453)
        message1 = make_message(id=888888, thread=MagicMock(id=888888,send=AsyncMock(return_value=MagicMock(id=199999, channel=MagicMock(id=888888)))))
        channel1.fetch_message = AsyncMock(return_value=message1)
        channel2 = make_text_channel(id=113453123)
        message2 = make_message(id=999999, thread=MagicMock(id=999999,send=AsyncMock(return_value=MagicMock(id=188888, channel=MagicMock(id=999999)))))
        channel2.fetch_message = AsyncMock(return_value=message2)
        channel3 = make_text_channel(id=11345345123)
        message3 = make_message(id=55555, thread=MagicMock(id=55555,send=AsyncMock(return_value=MagicMock(id=177777, channel=MagicMock(id=55555)))))
        channel3.fetch_message = AsyncMock(return_value=message3)

        service.bot.guild.get_channel = MagicMock(side_effect=[channel1, channel2, channel3])

        await service.handle_member_leave(seeded_users.track_author1.id)

        user = await uow.users.get_by_id(seeded_users.track_author1.id)
        assert user is None



        user_left_notification_messages = await uow.tracks.get_user_left_notifications(seeded_users.track_author1.id)

        assert len(user_left_notification_messages) == 3

        
        assert user_left_notification_messages[0].user_id == seeded_users.track_author1.id
        assert user_left_notification_messages[0].message_id == 199999
        assert user_left_notification_messages[0].channel_id == 888888

        assert user_left_notification_messages[1].user_id == seeded_users.track_author1.id
        assert user_left_notification_messages[1].message_id == 188888
        assert user_left_notification_messages[1].channel_id == 999999

        assert user_left_notification_messages[2].user_id == seeded_users.track_author1.id
        assert user_left_notification_messages[2].message_id == 177777
        assert user_left_notification_messages[2].channel_id == 55555
    
        
    
    async def test_cleanup_user_notif(self, service, uow, seeded_user_left_notification_messages):
        await service.clean_user_left_messages(user_id=seeded_user_left_notification_messages.notif1.user_id)

        notifs = await uow.tracks.get_user_left_notifications(user_id=seeded_user_left_notification_messages.notif1.user_id)

        assert len(notifs) == 0