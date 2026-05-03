from datetime import UTC, datetime
import pytest
from bot.types.tests.feedback import FeedbackCollection

@pytest.fixture
async def seeded_feedbacks_to_delete(
    seeded_tracks, seeded_users, make_feedback
):
    feedback1 = await make_feedback(
        id=555,
        author_id=seeded_users.fb_author1.id,
        track_id=seeded_tracks.track1.id,
        thread_id=seeded_tracks.track1.id,
        channel_id=111,
        content="nice track i liked it",
        word_count=5,
        created_at=datetime(year=2026, month=3, day=2, tzinfo=UTC)
    )
    feedback2 = await make_feedback(
        id=554,
        author_id=seeded_users.fb_author2.id,
        track_id=seeded_tracks.track1.id,
        thread_id=seeded_tracks.track1.id,
        channel_id=111,
        content="nice track i liked it second",
        word_count=6,
        created_at=datetime(year=2026, month=3, day=2, tzinfo=UTC)
    )
    feedback3 = await make_feedback(
        id=553,
        author_id=seeded_users.fb_author3.id,
        track_id=seeded_tracks.track1.id,
        thread_id=seeded_tracks.track1.id,
        channel_id=111,
        content="nice track i liked it third",
        word_count=6,
        created_at=datetime(year=2026, month=3, day=30, tzinfo=UTC)
    )


    feedback4 = await make_feedback(
        id=552135,
        author_id=seeded_users.fb_author1.id,
        track_id=seeded_tracks.track2.id,
        thread_id=seeded_tracks.track2.id,
        channel_id=222,
        content="nice track i liked it",
        word_count=5,
        created_at=datetime(year=2026, month=3, day=2, tzinfo=UTC)
    )
    feedback5 = await make_feedback(
        id=532454,
        author_id=seeded_users.fb_author2.id,
        track_id=seeded_tracks.track2.id,
        thread_id=seeded_tracks.track2.id,
        channel_id=222,
        content="nice track i liked it second",
        word_count=6,
        created_at=datetime(year=2026, month=3, day=2, tzinfo=UTC)
    )
    feedback6 = await make_feedback(
        id=553213,
        author_id=seeded_users.fb_author3.id,
        track_id=seeded_tracks.track2.id,
        thread_id=seeded_tracks.track2.id,
        channel_id=222,
        content="nice track i liked it third",
        word_count=6,
        created_at=datetime(year=2026, month=3, day=30, tzinfo=UTC)
    )


    return FeedbackCollection(
        feedback1=feedback1,
        feedback2=feedback2,
        feedback3=feedback3,
        feedback4=feedback4,
        feedback5=feedback5,
        feedback6=feedback6
    )