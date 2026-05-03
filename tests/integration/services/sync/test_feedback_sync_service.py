import pytest
from bot.services.sync_services.feedback import FeedbackSyncService
from unittest.mock import AsyncMock, MagicMock
from tests.factories.discord_factories import make_text_channel

class TestFeedbackSyncService:
    @pytest.fixture
    async def service(
        self, uow, mock_bot):
        mock_bot.guild = MagicMock()
        mock_bot.guild.fetch_members = AsyncMock()

        return FeedbackSyncService(uow=uow, bot=mock_bot, event_handler=AsyncMock())
    
    async def test_feedback_sync(
            self, service, uow,seeded_members, seeded_track_messages, seeded_threads, make_feedback_messages
    ):
        feedback_messages = make_feedback_messages(seeded_members.all, seeded_track_messages.all)
        threads = seeded_threads(
            feedback_messages=feedback_messages,
            track_messages=seeded_track_messages.all
        )
        channel = make_text_channel(id=111, messages=seeded_track_messages.all, threads=threads.all)
        await service.sync_channel(channel=channel, author_track_ids=seeded_track_messages.author_track_ids, existing_user_ids=seeded_members.all_ids)
        total_feedbacks = await uow.feedback.get_total_feedbacks()
        assert total_feedbacks == threads.get_total_feedbacks()
        for feedback_message in threads.get_all_feedbacks():
            feedback = await uow.feedback.get(feedback_message.id)
            assert feedback is not None
            assert feedback.id == feedback_message.id
            assert feedback.content == feedback_message.content
            assert feedback.channel_id == 111
            assert feedback.thread_id == feedback_message.channel.id

    async def test_duplicate_feedback_sync(
            self, service, uow,seeded_members, seeded_track_messages, seeded_threads, make_feedback_messages
    ):
        feedback_messages = make_feedback_messages(seeded_members.all, seeded_track_messages.all)
        threads = seeded_threads(
            feedback_messages=feedback_messages,
            track_messages=seeded_track_messages.all
        )
        channel = make_text_channel(id=111, messages=seeded_track_messages.all, threads=threads.all)
        await service.sync_channel(channel=channel, author_track_ids=seeded_track_messages.author_track_ids, existing_user_ids=seeded_members.all_ids)
        await service.sync_channel(channel=channel, author_track_ids=seeded_track_messages.author_track_ids, existing_user_ids=seeded_members.all_ids)
        total_feedbacks = await uow.feedback.get_total_feedbacks()
        assert total_feedbacks == threads.get_total_feedbacks()
        for feedback_message in threads.get_all_feedbacks():
            feedback = await uow.feedback.get(feedback_message.id)
            assert feedback is not None
            assert feedback.id == feedback_message.id
            assert feedback.content == feedback_message.content
            assert feedback.channel_id == 111
            assert feedback.thread_id == feedback_message.channel.id

    async def test_sync_cleanup(
        self, service, uow,
        seeded_members, seeded_track_messages,
        seeded_feedback_messages
    ):
        channel = make_text_channel(id=111, messages=seeded_track_messages.all)
        await service.sync_channel(channel=channel, author_track_ids=seeded_track_messages.author_track_ids, existing_user_ids=seeded_members.all_ids)

        assert await uow.feedback.get_total_feedbacks() == 0     

    async def test_sync_partial_cleanup(
            self, service, uow,
            seeded_members, seeded_track_messages, seeded_threads, make_feedback_messages
    ):  
        feedback_messages = make_feedback_messages(seeded_members.all, seeded_track_messages.all)
        threads = seeded_threads(
            feedback_messages=feedback_messages,
            track_messages=seeded_track_messages.all
        )
        
        channel = make_text_channel(threads=[thread for thread in threads.all])
        author_track_ids = {track.id:track.author.id for track in seeded_track_messages.all}
        await service.sync_channel(channel, author_track_ids, seeded_members.all_ids)

        total_feedbacks_before = await uow.feedback.get_total_feedbacks()


        threads.thread1.messages = []
        channel = make_text_channel(threads=[thread for thread in threads])
        await service.sync_channel(channel, author_track_ids, seeded_members.all_ids)

        total_feedbacks_after = await uow.feedback.get_total_feedbacks()

        assert total_feedbacks_after < total_feedbacks_before

        assert total_feedbacks_after == threads.get_total_feedbacks()


    async def test_sync_partial_cleanup_with_pagination(
            self, service, uow,
            seeded_members, seeded_track_messages, seeded_threads, make_feedback_messages
    ):  
        feedback_messages = make_feedback_messages(seeded_members.all, seeded_track_messages.all)
        threads = seeded_threads(
            feedback_messages=feedback_messages,
            track_messages=seeded_track_messages.all,
            page_size=1
        )
        
        channel = make_text_channel(threads=[thread for thread in threads.all])
        author_track_ids = {track.id:track.author.id for track in seeded_track_messages.all}
        await service.sync_channel(channel, author_track_ids, seeded_members.all_ids)

        total_feedbacks_before = await uow.feedback.get_total_feedbacks()


        threads.thread1.messages = []
        channel = make_text_channel(threads=[thread for thread in threads])
        await service.sync_channel(channel, author_track_ids, seeded_members.all_ids)

        total_feedbacks_after = await uow.feedback.get_total_feedbacks()

        assert total_feedbacks_after < total_feedbacks_before

        assert total_feedbacks_after == threads.get_total_feedbacks()

    async def test_nonexistent_fb_author_skipped(
            self, service, uow, seeded_members,seeded_track_messages, seeded_threads, make_feedback_messages
    ):
        feedback_messages = make_feedback_messages(seeded_members.all, seeded_track_messages.all)
        threads = seeded_threads(
            feedback_messages=feedback_messages,
            track_messages=seeded_track_messages.all
        )

        fb_author = threads.select_random_fb_author()
        await uow.users.delete(fb_author.id)

        channel = make_text_channel(threads=[thread for thread in threads.all])
        author_track_ids = {thread.id:thread.owner_id for thread in threads.all if thread.owner_id != fb_author.id}
        existing_user_ids = seeded_members.all_ids
        existing_user_ids.remove(fb_author.id)

        await service.sync_channel(channel, author_track_ids, existing_user_ids)

        skipped_feedbacks = threads.get_feedbacks_of_user(fb_author.id)
        

        for feedback in skipped_feedbacks:
           assert await uow.feedback.get(feedback.id) is None

        total_feedbacks = await uow.feedback.get_total_feedbacks()

        assert total_feedbacks == threads.get_total_feedbacks() - len(skipped_feedbacks)



    async def test_sync_more_than_one_page(
            self, service, uow,seeded_members, seeded_track_messages, make_feedback_messages, seeded_threads
    ):
        feedback_messages = make_feedback_messages(seeded_members.all, seeded_track_messages.all)

        threads = seeded_threads(
            feedback_messages=feedback_messages,
            track_messages=seeded_track_messages.all,
            page_size=1
        )

        channel = make_text_channel(id=111, messages=seeded_track_messages.all, threads=threads.all, page_size=3)
        await service.sync_channel(channel=channel, author_track_ids=seeded_track_messages.author_track_ids, existing_user_ids=seeded_members.all_ids)
        total_feedbacks = await uow.feedback.get_total_feedbacks()
        assert total_feedbacks == threads.get_total_feedbacks()
        for feedback_message in threads.get_all_feedbacks():
            feedback = await uow.feedback.get(feedback_message.id)
            assert feedback is not None
            assert feedback.id == feedback_message.id
            assert feedback.content == feedback_message.content
            assert feedback.channel_id == 111
            assert feedback.thread_id == feedback_message.channel.id
        
    
    async def test_stale_feedbacks_across_pages_are_deleted(
        self, service, uow, seeded_members, seeded_track_messages, seeded_threads, make_feedback_messages
    ):
        stale1 = {
                "id":12345,
                "thread_id":seeded_track_messages.track1.id,
                "track_id":seeded_track_messages.track1.id,
                "author_id":seeded_members.user1.id,
                "channel_id":111,
                "content": "test content",
                "word_count": 2
            }
        stale2 = {
                "id":123456,
                "thread_id":seeded_track_messages.track2.id,
                "track_id":seeded_track_messages.track2.id,
                "author_id":seeded_members.user2.id,
                "channel_id":111,
                "content": "test content",
                "word_count": 2
            }
        
        await uow.feedback.bulk_insert_feedback([stale1, stale2])

        assert await uow.feedback.exists(12345) == True
        assert await uow.feedback.exists(123456) == True

        feedback_messages = make_feedback_messages(seeded_members.all, seeded_track_messages.all)
        threads = seeded_threads(
            feedback_messages=feedback_messages,
            track_messages=seeded_track_messages.all
        )
        channel = make_text_channel(id=111, messages=seeded_track_messages.all, threads=threads.all)
        await service.sync_channel(channel=channel, author_track_ids=seeded_track_messages.author_track_ids, existing_user_ids=seeded_members.all_ids)
        total_feedbacks = await uow.feedback.get_total_feedbacks()
        assert total_feedbacks == threads.get_total_feedbacks()
        
        assert await uow.feedback.exists(12345) == False
        assert await uow.feedback.exists(123456) == False

    async def test_invalid_feedbacks_are_skipped(
            self, service, uow,seeded_members, seeded_track_messages, seeded_threads, make_feedback_messages
    ):
        feedback_messages = make_feedback_messages(seeded_members.all, seeded_track_messages.all, all_valid=False)
        threads = seeded_threads(
            feedback_messages=feedback_messages,
            track_messages=seeded_track_messages.all
        )
        channel = make_text_channel(id=111, messages=seeded_track_messages.all, threads=threads.all)
        await service.sync_channel(channel=channel, author_track_ids=seeded_track_messages.author_track_ids, existing_user_ids=seeded_members.all_ids)
        total_feedbacks = await uow.feedback.get_total_feedbacks()
        assert total_feedbacks == 0
        for feedback_message in threads.get_all_feedbacks():
            assert await uow.feedback.get(feedback_message.id) is None

 