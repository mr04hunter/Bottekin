import pytest
from bot.services.feedback import FeedbackService
from bot.types.common import FeedbackData, UserData
from unittest.mock import AsyncMock, MagicMock




class TestFeedbackServiceIntegration:

    @pytest.fixture
    async def service(self, uow, mock_bot):
        mock_bot.services = MagicMock()
        mock_bot.services.sync_service = MagicMock()
        mock_bot.services.sync_service.sync_track_with_no_feedback = AsyncMock()
        event_handler = AsyncMock()
        return FeedbackService(uow=uow, event_handler=event_handler, bot=mock_bot)

    
    


    async def test_add_feedback_actually_persists_to_db(
        self, service, uow, seeded_users, seeded_tracks
    ):
        data = FeedbackData(
            id=555,
            track_id=seeded_tracks.track1.id,
            author=UserData(id=seeded_users.fb_author1.id, username=seeded_users.fb_author1.username, display_name=seeded_users.fb_author1.display_name),
            channel_id=111,
            content="This track has a really solid mix and great melody throughout",
            word_count=12,
        )

        await service.add_feedback(data)

        feedback = await uow.feedback.exists(555)
        assert feedback is True


    async def test_add_feedback_triggers_fire_correctly(
        self, service, uow, seeded_users, seeded_tracks
    ):
        data = FeedbackData(
            id=555,
            track_id=seeded_tracks.track1.id,
            author=UserData(id=seeded_users.fb_author1.id,
                            username=seeded_users.fb_author1.username,
                            display_name=seeded_users.fb_author1.display_name),
            channel_id=111,
            content="This track has a really solid mix and great melody throughout",
            word_count=12,
        )

        await service.add_feedback(data)

        reviewer_in_db = await uow.users.get_by_id(seeded_users.fb_author1.id)
        assert reviewer_in_db.total_feedbacks_given == 1
        assert reviewer_in_db.total_feedback_words == 12

        author_in_db = await uow.users.get_by_id(seeded_tracks.track1.author_id)
        assert author_in_db.total_feedbacks_received == 1

    async def test_add_feedback_creates_new_user_automatically(
        self, service, uow, seeded_users, seeded_tracks
    ):
        data = FeedbackData(
            id=555, track_id=seeded_tracks.track1.id,
            author=UserData(id=456, username="new_user", display_name="New User"),
            channel_id=111,
            content="Really enjoyed this track great production quality",
            word_count=7,
        )

        assert await uow.users.exists(456) is False

        await service.add_feedback(data)

        assert await uow.users.exists(456) is True
        new_user = await uow.users.get_by_id(456)
        assert new_user.username == "new_user"


    async def test_update_feedback(
            self, service, seeded_feedbacks
    ):
        
        feedback_data = {
            "word_count":3,
            "content":"nice work man"
        }
        await service.update_feedback(seeded_feedbacks.feedback1.id, feedback_data)

        feedback = await service.uow.feedback.get(seeded_feedbacks.feedback1.id)
        
        assert feedback.content == "nice work man"
        assert feedback.word_count == 3
    

    async def test_add_feedback_then_delete_leaves_db_consistent(
        self, service, seeded_users, seeded_tracks
    ):
        reviewer = UserData(id=seeded_users.fb_author1.id,
                            username=seeded_users.fb_author1.username,
                            display_name=seeded_users.fb_author1.display_name)
        data = FeedbackData(
            id=555, track_id=seeded_tracks.track1.id, author=reviewer, channel_id=111,
            content="Great track with solid production and nice melodies",
            word_count=8,
        )

        await service.add_feedback(data)
        await service.delete_feedback(thread_id=seeded_tracks.track1.id, feedback_id=555)

        reviewer_in_db = await service.uow.users.get_by_id(seeded_users.fb_author1.id)
        assert reviewer_in_db.total_feedbacks_given == 0
        assert reviewer_in_db.total_feedback_words == 0

        author_in_db = await service.uow.users.get_by_id(seeded_tracks.track1.author_id)
        assert author_in_db.total_feedbacks_received == 0


    async def test_duplicate_feedback_is_rejected_by_validator(
        self, service, seeded_users, seeded_tracks, seeded_feedbacks
    ):
        

        from bot.services.feedback_validator import FeedbackValidator
        validator = FeedbackValidator(uow=service.uow)
        is_valid, reason = await validator.validate(
            author_id=seeded_users.fb_author1.id,
            thread_id=seeded_tracks.track1.id,
            content="Different content this time",
            word_count=4,
        )

        assert is_valid is False
        assert reason == "already_exists"
 

    async def test_delete_feedback_nonexistent_does_nothing(
        self, service, seeded_users, seeded_tracks
    ):

        await service.delete_feedback(thread_id=seeded_tracks.track1.id, feedback_id=99999)
        # no exception = pass

    async def test_update_feedback_nonexistent_does_nothing(
        self, service
    ):
        await service.update_feedback(
            feedback_id=99999,
            feedback_data={"content": "new", "word_count": 2}
        )
        # no exception = pass

    async def test_update_feedback_word_count_trigger_fires(
        self, service, uow, seeded_users, seeded_tracks, seeded_feedbacks
    ):
        

        reviewer_in_db = await uow.users.get_by_id(seeded_users.fb_author1.id)
        assert reviewer_in_db.total_feedback_words == seeded_feedbacks.get_total_fb_words_of_user(seeded_users.fb_author1.id)
        seeded_feedbacks.feedback1.word_count = 1
        await service.update_feedback(555, {"content": "short", "word_count": 1})


        reviewer_in_db = await uow.users.get_by_id(seeded_users.fb_author1.id)
        assert reviewer_in_db.total_feedback_words == seeded_feedbacks.get_total_fb_words_of_user(seeded_users.fb_author1.id)