import pytest
from bot.services.track import TrackService
from unittest.mock import AsyncMock, MagicMock

class TestTrackService:
    @pytest.fixture
    async def service(
        self, uow, mock_bot):
        mock_bot.services = MagicMock()
        mock_bot.services.sync_service = MagicMock()
        mock_bot.services.sync_service.sync_track_with_no_feedback = AsyncMock()
        event_handler = AsyncMock()
        return TrackService(uow=uow, event_handler=event_handler, bot=mock_bot)
    
    async def test_create_track(
            self, service, uow, seeded_users
    ):
        await service.add_track(
            555, seeded_users.track_author1.id, 555, 111, "test track", "youtube"
        )

        exists = await uow.tracks.exists(555)
        assert exists == True


    async def test_create_track_with_nonexistent_user(
            self, service, uow
    ):
        await service.add_track(
            555, 7876, 555, 111, "test track", "youtube"
        )
        assert await uow.tracks.exists(555) is False

    
    async def test_update_track(
            self, service,uow, seeded_tracks
    ):
        await service.update_track(
            seeded_tracks.track1.id, {"total_feedbacks":5}
        )

        track = await uow.tracks.get(seeded_tracks.track1.id)

        assert track.total_feedbacks == 5

    async def test_update_non_existent_track(
            self, service
    ):
        await service.update_track(
            555, {"total_feedbacks":5}
        )

        #no exception pass
        

    async def test_add_track_then_delete(
            self, service, uow, seeded_users
    ):
        await service.add_track(
            555, seeded_users.track_author1.id, 555, 111, "test track", "youtube"
        )
        await service.delete_track(555)

        exists = await uow.tracks.exists(555)

        assert exists == False


    async def test_delete_nonexistent_track(
            self, service, uow
    ):
        await service.delete_track(123)



    async def test_increment_track_reaction(
            self, service, uow, seeded_tracks
    ):

        await service.increment_track_reaction(seeded_tracks.track1.id)

        track = await uow.tracks.get(seeded_tracks.track1.id)

        assert track.total_reactions == 1

    async def test_decrement_track_reaction(
            self, service, uow, seeded_tracks
    ):

        await service.increment_track_reaction(seeded_tracks.track1.id)
        track = await uow.tracks.get(seeded_tracks.track1.id)
        assert track.total_reactions == 1

        await service.decrement_track_reaction(seeded_tracks.track1.id)
        track = await uow.tracks.get(seeded_tracks.track1.id)
        assert track.total_reactions == 0


    async def test_increment_nonexistent_track_reaction(
            self, service, uow
    ):

        await service.increment_track_reaction(555)
        #no exception pass

    async def test_decrement_nonexistent_track_reaction(
            self, service, uow
    ):

        await service.decrement_track_reaction(555)

        #no exception pass