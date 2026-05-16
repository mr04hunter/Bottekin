from datetime import UTC, datetime

class TestTrackRepository:
    async def test_get_for_user(
            self, uow, seeded_tracks
    ):
        tracks = await uow.tracks.get_for_user(seeded_tracks.track1.author_id)

        assert len(tracks) == 1
        assert tracks[0].id == seeded_tracks.track1.id

    async def test_get_for_nonexistent_user(
            self, uow
    ):
        tracks = await uow.tracks.get_for_user(123123)

        assert tracks == []


    async def test_bulk_insert_tracks(
            self, uow, seeded_users
    ):
        created_at = datetime(year=2026, month=1, day=12, tzinfo=UTC)
        track1 = {
            "id":555,
            "author_id":seeded_users.track_author1.id,
            "thread_id":555,
            "channel_id":111,
            "title":"title1",
            "platform":"platform1",
            "created_at":created_at}
        
        track2 = {
            "id":554,
            "author_id":seeded_users.track_author1.id,
            "thread_id":554,
            "channel_id":111,
            "title":"title1",
            "platform":"platform1",
            "created_at":created_at}
        
        track3 = {
            "id":553,
            "author_id":seeded_users.track_author1.id,
            "thread_id":553,
            "channel_id":111,
            "title":"title1",
            "platform":"platform1",
            "created_at":created_at}
        
        
        await uow.tracks.bulk_insert_track([track1, track2, track3])

        exists = await uow.tracks.exists(555)
        assert exists == True

        exists2 = await uow.tracks.exists(554)
        assert exists2 == True

        exists3 = await uow.tracks.exists(553)
        assert exists3 == True

        updated = {
            "id":555, 
            "author_id":seeded_users.track_author1.id, 
            "thread_id":555,
            "channel_id":111,
            "title":"updated_title", 
            "platform":"updated_platform"}
        
        await uow.tracks.bulk_insert_track([updated])

        updated_track = await uow.tracks.get(555)

        assert updated_track.title == "updated_title"
        assert updated_track.platform == "updated_platform"



    async def test_bulk_insert_tracks_integrity_error_retry(
            self, uow, seeded_users
    ):
        created_at = datetime(year=2026, month=1, day=12, tzinfo=UTC)
        track1 = {
            "id":555,
            "author_id":seeded_users.track_author1.id,
            "thread_id":555,
            "channel_id":111,
            "title":"title1",
            "platform":"platform1",
            "created_at":created_at}
        
        track2 = {
            "id":554,
            "author_id":seeded_users.track_author1.id,
            "thread_id":554,
            "channel_id":111,
            "title":"title1",
            "platform":"platform1",
            "created_at":created_at}
        
        track3 = {
            "id":553,
            "author_id":seeded_users.track_author1.id,
            "thread_id":553,
            "channel_id":111,
            "title":"title1",
            "platform":"platform1",
            "created_at":created_at}
        
        track4 = {
            "id":552,
            "author_id":324535346345345,
            "thread_id":553,
            "channel_id":111,
            "title":"title1",
            "platform":"platform1",
            "created_at":created_at}
        
        
        await uow.tracks.bulk_insert_track([track1, track2, track3, track4])

        exists = await uow.tracks.exists(555)
        assert exists == True

        exists2 = await uow.tracks.exists(554)
        assert exists2 == True

        exists3 = await uow.tracks.exists(553)
        assert exists3 == True

        exists4 = await uow.tracks.exists(552)
        assert exists4 == False
        


    async def test_cleanup_tracks(
            self, uow, seeded_tracks
    ):
        #assert no track is deleted
        await uow.tracks.cleanup_tracks(111, {seeded_tracks.track1.id,seeded_tracks.track2.id,seeded_tracks.track3.id}, None, None)

        assert await uow.tracks.exists(seeded_tracks.track1.id) == True
        assert await uow.tracks.exists(seeded_tracks.track2.id) == True
        assert await uow.tracks.exists(seeded_tracks.track3.id) == True



    async def test_cleanup_tracks_clean_all(
            self, uow, seeded_tracks
    ):

        #assert all cleaned
        await uow.tracks.cleanup_tracks(111, {}, None, None)

        assert await uow.tracks.exists(seeded_tracks.track1.id) == False
        assert await uow.tracks.exists(seeded_tracks.track2.id) == False
        assert await uow.tracks.exists(seeded_tracks.track3.id) == False

    async def test_cleanup_tracks_after(
            self, uow, seeded_tracks_to_delete
    ):


        #assert the track created after the after date gets deleted and the ones before the after date remains  
        await uow.tracks.cleanup_tracks(111, {}, datetime(year=2026, month=1, day=13, tzinfo=UTC), None)

        assert await uow.tracks.exists(seeded_tracks_to_delete.track1.id) == True
        assert await uow.tracks.exists(seeded_tracks_to_delete.track2.id) == True
        assert await uow.tracks.exists(seeded_tracks_to_delete.track3.id) == False

    async def test_cleanup_tracks_before(
            self, uow, seeded_tracks_to_delete
    ):


        #assert the track created before the before date gets deleted and the ones after the before date remains  
        await uow.tracks.cleanup_tracks(111, {}, None, datetime(year=2026, month=1, day=13, tzinfo=UTC))

        assert await uow.tracks.exists(seeded_tracks_to_delete.track1.id) == False
        assert await uow.tracks.exists(seeded_tracks_to_delete.track2.id) == False
        assert await uow.tracks.exists(seeded_tracks_to_delete.track3.id) == True


    



    
    async def test_make_track_with_no_feedback(
            self, uow, seeded_tracks
    ):
        await uow.tracks.create_track_with_no_feedback(
            seeded_tracks.track1.id, 123, "message_url", datetime.now(tz=UTC)
        )

        track_with_no_feedback = await uow.tracks.get_track_with_no_feedback(seeded_tracks.track1.id)

        assert track_with_no_feedback.message_id == 123
        assert track_with_no_feedback.message_url == "message_url"
        assert track_with_no_feedback.track_id == seeded_tracks.track1.id

    async def test_create_and_delete_track_with_no_feedback(
            self, uow, seeded_tracks
    ):
        await uow.tracks.create_track_with_no_feedback(
            seeded_tracks.track1.id, 123, "message_url", datetime.now(tz=UTC)
        )

        await uow.tracks.delete_track_with_no_feedback(seeded_tracks.track1.id)
        track_with_no_feedback = await uow.tracks.get_track_with_no_feedback(seeded_tracks.track1.id)

        assert track_with_no_feedback == None

    async def test_create_existing_track_with_no_feedback_updates(
            self, uow, seeded_tracks_with_no_feedback
    ):
        await uow.tracks.create_track_with_no_feedback(
            seeded_tracks_with_no_feedback.track_wn_feedback1.track_id, 128, "message_url_updated", datetime.now(tz=UTC)
        )

        track_with_no_feedback = await uow.tracks.get_track_with_no_feedback(seeded_tracks_with_no_feedback.track_wn_feedback1.track_id)

        assert track_with_no_feedback.message_id == 128
        assert track_with_no_feedback.message_url == "message_url_updated"



    async def test_cleanup_tracks_with_no_feedback(
            self, uow, seeded_tracks_with_no_feedback
    ):
        
        #no cleanup should be made

        await uow.tracks.cleanup_track_with_no_feedback(datetime(2025, month=1, day=1))

        track_with_no_feedback1 = await uow.tracks.get_track_with_no_feedback(555)
        assert track_with_no_feedback1 is not None

        track_with_no_feedback2 = await uow.tracks.get_track_with_no_feedback(554)
        assert track_with_no_feedback2 is not None

        track_with_no_feedback3 = await uow.tracks.get_track_with_no_feedback(553)
        assert track_with_no_feedback3 is not None

    async def test_cleanup_old_tracks_with_no_feedback(
            self, uow, seeded_tracks_with_no_feedback
    ):
        
        #all should be deleted (created_at more than 2 weeks ago)

        await uow.tracks.cleanup_track_with_no_feedback(datetime(year=2027, month=1, day=1))

        track_with_no_feedback1 = await uow.tracks.get_track_with_no_feedback(seeded_tracks_with_no_feedback.track_wn_feedback1.track_id)
        assert track_with_no_feedback1 is None

        track_with_no_feedback2 = await uow.tracks.get_track_with_no_feedback(seeded_tracks_with_no_feedback.track_wn_feedback2.track_id)
        assert track_with_no_feedback2 is None

        track_with_no_feedback3 = await uow.tracks.get_track_with_no_feedback(seeded_tracks_with_no_feedback.track_wn_feedback3.track_id)
        assert track_with_no_feedback3 is None

    
    async def test_cleanup_track_with_no_feedback_more_than_3_feedback(
            self, uow, seeded_tracks_with_no_feedback
    ):

        track_data = {
            "total_feedbacks":3}
        
        await uow.tracks.update(seeded_tracks_with_no_feedback.track_wn_feedback1.track_id,track_data)

        await uow.tracks.cleanup_track_with_no_feedback(datetime(2025, month=1, day=1))

        deleted_track_with_no_feedback = await uow.tracks.get_track_with_no_feedback(seeded_tracks_with_no_feedback.track_wn_feedback1.track_id)
        assert deleted_track_with_no_feedback is None

        assert await uow.tracks.get_track_with_no_feedback(seeded_tracks_with_no_feedback.track_wn_feedback2.track_id) is not None
        assert await uow.tracks.get_track_with_no_feedback(seeded_tracks_with_no_feedback.track_wn_feedback3.track_id) is not None