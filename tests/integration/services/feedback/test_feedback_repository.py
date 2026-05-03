from datetime import UTC, datetime





class TestFeedbackServiceIntegration:


    async def test_bulk_insert_feedback(
                self, uow, seeded_users, seeded_tracks
        ):
            now = datetime.now(tz=UTC)
            feedback1 = {
                "id":555,
                "author_id":seeded_users.fb_author1.id,
                "track_id":seeded_tracks.track1.id,
                "thread_id":seeded_tracks.track1.id,
                "channel_id":111,
                "content":"nice track man",
                "word_count":3,
                "created_at":now}
            
            
            feedback2 = {
                "id":554,
                "author_id":seeded_users.fb_author2.id,
                "track_id":seeded_tracks.track1.id,
                "thread_id":seeded_tracks.track1.id,
                "channel_id":111,
                "content":"nice track man second",
                "word_count":4,
                "created_at":now}

            feedback3 = {
                "id":553,
                "author_id":seeded_users.fb_author3.id,
                "track_id":seeded_tracks.track1.id,
                "thread_id":seeded_tracks.track1.id,
                "channel_id":111,
                "content":"nice track man third",
                "word_count":4,
                "created_at":now}
            
            await uow.feedback.bulk_insert_feedback([feedback1, feedback2, feedback3])

            assert await uow.feedback.exists(555) == True
            assert await uow.feedback.exists(554) == True
            assert await uow.feedback.exists(553) == True

    async def test_bulk_insert_updates_feedback(
            self, uow, seeded_users, seeded_tracks, seeded_feedbacks
    ):
        updated = [
        {
            "id": 555, "track_id": seeded_tracks.track1.id, "author_id": seeded_users.fb_author1.id,
            "channel_id": 111, "thread_id": seeded_tracks.track1.id,
            "content": "updated content for feedback 555",
            "word_count": 5, "created_at": datetime.now(UTC),
        },
        ]
        await uow.feedback.bulk_insert_feedback(updated)

        feedback = await uow.feedback.get(555)
        assert feedback.content == "updated content for feedback 555"


    async def test_cleanup_feedback(
            self, uow, seeded_tracks, seeded_feedbacks_to_delete
    ):

        #assert no feedback is deleted
        await uow.feedback.cleanup_feedbacks_on_thread(seeded_tracks.track1.id, {555,554,553}, None, None)

        assert await uow.feedback.exists(555) == True
        assert await uow.feedback.exists(554) == True
        assert await uow.feedback.exists(553) == True

    async def test_cleanup_feedbacks_on_thread_all_cleaned(
            self, uow, seeded_tracks, seeded_feedbacks_to_delete
    ):
        #assert all cleaned
        await uow.feedback.cleanup_feedbacks_on_thread(seeded_tracks.track1.id, {}, None, None)

        assert await uow.feedback.exists(555) == False
        assert await uow.feedback.exists(554) == False
        assert await uow.feedback.exists(553) == False

    async def test_cleanup_feedback_after(
            self, uow, seeded_users, seeded_tracks, seeded_feedbacks_to_delete
    ):


        #assert the feedback created after the after date gets deleted and the ones before the after date remains  
        await uow.feedback.cleanup_feedbacks_on_thread(seeded_tracks.track1.id, {}, datetime(year=2026, month=3, day=3, tzinfo=UTC), None)

        assert await uow.feedback.exists(555) == True #feedback1
        assert await uow.feedback.exists(554) == True #feedback2
        assert await uow.feedback.exists(553) == False #feedback3

    async def test_cleanup_feedback_before(
            self, uow, seeded_tracks, seeded_feedbacks_to_delete
    ):


        #assert the feedback created before the before date gets deleted and the ones after the before date remains  
        await uow.feedback.cleanup_feedbacks_on_thread(seeded_tracks.track1.id, {}, None, datetime(year=2026, month=3, day=3, tzinfo=UTC))

        assert await uow.feedback.exists(555) == False
        assert await uow.feedback.exists(554) == False
        assert await uow.feedback.exists(553) == True

    async def test_cleanup_feedbacks_with_stale_thread(
              self, uow, seeded_tracks, seeded_feedbacks_to_delete
    ):
        await uow.feedback.cleanup_feedbacks(thread_ids={}, channel_id=111)

        assert await uow.feedback.exists(seeded_feedbacks_to_delete.feedback1.id) == False
        assert await uow.feedback.exists(seeded_feedbacks_to_delete.feedback2.id) == False
        assert await uow.feedback.exists(seeded_feedbacks_to_delete.feedback3.id) == False


    async def test_cleanup_feedbacks_with_stale_thread_doesnt_delete_unrelated_feedbacks(
              self, uow, seeded_tracks, seeded_feedbacks_to_delete
    ):
        await uow.feedback.cleanup_feedbacks(thread_ids={}, channel_id=111)

        assert await uow.feedback.exists(seeded_feedbacks_to_delete.feedback4.id) == True
        assert await uow.feedback.exists(seeded_feedbacks_to_delete.feedback5.id) == True
        assert await uow.feedback.exists(seeded_feedbacks_to_delete.feedback6.id) == True


    async def test_cleanup_feedbacks_with_stale_thread_skips_valid(
              self, uow, seeded_tracks, seeded_feedbacks_to_delete
    ):
        await uow.feedback.cleanup_feedbacks(thread_ids={seeded_tracks.track1.id}, channel_id=111)

        assert await uow.feedback.exists(seeded_feedbacks_to_delete.feedback1.id) == True
        assert await uow.feedback.exists(seeded_feedbacks_to_delete.feedback2.id) == True
        assert await uow.feedback.exists(seeded_feedbacks_to_delete.feedback3.id) == True