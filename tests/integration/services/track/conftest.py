import pytest
from datetime import datetime, UTC
from bot.types.tests.track import TrackCollection

@pytest.fixture
async def seeded_tracks_to_delete(
    seeded_users, make_track
):
    track1 = await make_track(
        id=555,
        author_id=seeded_users.track_author1.id,
        thread_id=555,
        channel_id=111,
        title="track1",
        platform="test platform",
        total_feedbacks=0,
        created_at=datetime(year=2026, month=1, day=2, tzinfo=UTC)
    )

    track2 = await make_track(
        id=554,
        author_id=seeded_users.track_author2.id,
        thread_id=554,
        channel_id=111,
        title="track2",
        platform="test platform",
        total_feedbacks=0,
        created_at=datetime(year=2026, month=1, day=3, tzinfo=UTC)
    )

    track3 = await make_track(
        id=553,
        author_id=seeded_users.track_author3.id,
        thread_id=553,
        channel_id=111,
        title="track3",
        platform="test platform",
        total_feedbacks=0,
        created_at=datetime(year=2026, month=1, day=15, tzinfo=UTC)
    )

    return TrackCollection(
        track1=track1,
        track2=track2,
        track3=track3
    )

