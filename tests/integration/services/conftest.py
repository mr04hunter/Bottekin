from datetime import UTC, datetime
import pytest
from bot.types.tests.track import TrackCollection, TrackWithNoFeedbackCollection
from bot.types.tests.feedback import FeedbackCollection
from bot.types.tests.challenge import SubmissionCollection, VoteCollection, WinnerCollection





    
@pytest.fixture
async def seeded_submissions(
    seeded_challenge, seeded_users, make_submission
):
    submission1 = await make_submission(
        submission_id=12345, author_id=seeded_users.submission_author1.id,
        challenge_id=seeded_challenge.id, channel_id=111,
        title="submission_title1",created_at=datetime.now(UTC))

    submission2 = await make_submission(
        submission_id=123456, author_id=seeded_users.submission_author2.id,
        challenge_id=seeded_challenge.id, channel_id=111,
        title="submission_title2",created_at=datetime.now(UTC))
    
    submission3 = await make_submission(
        submission_id=1234567, author_id=seeded_users.submission_author3.id,
        challenge_id=seeded_challenge.id, channel_id=111,
        title="submission_title3",created_at=datetime.now(UTC))


    return SubmissionCollection(
        submission1=submission1,
        submission2=submission2,
        submission3=submission3
    )

@pytest.fixture
async def seeded_votes(
    seeded_users, seeded_challenge, seeded_submissions, make_vote
):
    vote1 = await make_vote(voter_id=seeded_users.voter1.id, submission_id=seeded_submissions.submission1.id, challenge_id=seeded_challenge.id)
    vote2 = await make_vote(voter_id=seeded_users.voter2.id, submission_id=seeded_submissions.submission2.id, challenge_id=seeded_challenge.id)
    vote3 = await make_vote(voter_id=seeded_users.voter3.id, submission_id=seeded_submissions.submission3.id, challenge_id=seeded_challenge.id)
    vote4 = await make_vote(voter_id=seeded_users.voter4.id, submission_id=seeded_submissions.submission1.id, challenge_id=seeded_challenge.id)


    return VoteCollection(
        vote1=vote1,
        vote2=vote2,
        vote3=vote3,
        vote4=vote4
    )


@pytest.fixture
async def seeded_winners(
    seeded_users, seeded_challenge, seeded_submissions, make_winner
):
    winner1 = await make_winner(
        winner_id=seeded_users.submission_author1.id,
        submission_id=seeded_submissions.submission1.id, 
        challenge_id=seeded_challenge.id)
    winner2 = await make_winner(
        winner_id=seeded_users.submission_author2.id,
        submission_id=seeded_submissions.submission2.id,
        challenge_id=seeded_challenge.id)
    winner3 = await make_winner(
        winner_id=seeded_users.submission_author3.id,
        submission_id=seeded_submissions.submission3.id, 
        challenge_id=seeded_challenge.id)

    return WinnerCollection(
        winner1=winner1,
        winner2=winner2,
        winner3=winner3
    )


@pytest.fixture
async def seeded_challenge(
    make_challenge
):
    

    challenge = await make_challenge(id=1000, title="test_active_challenge")

    return challenge


@pytest.fixture
async def seeded_challenge2(
    make_challenge
):
    

    challenge = await make_challenge(id=10000, title="test_active_challenge2")

    return challenge



@pytest.fixture
async def seeded_challenge3(
    make_challenge
):
    

    challenge = await make_challenge(id=100000, title="test_active_challenge3")

    return challenge


@pytest.fixture
async def seeded_tracks(
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
        created_at=datetime(year=2026, month=3, day=5, tzinfo=UTC)
    )

    track2 = await make_track(
        id=554,
        author_id=seeded_users.track_author2.id,
        thread_id=554,
        channel_id=111,
        title="track2",
        platform="test platform",
        total_feedbacks=0,
        created_at=datetime(year=2026, month=3, day=10, tzinfo=UTC)
    )

    track3 = await make_track(
        id=553,
        author_id=seeded_users.track_author3.id,
        thread_id=553,
        channel_id=111,
        title="track3",
        platform="test platform",
        total_feedbacks=0,
        created_at=datetime(year=2026, month=3, day=30, tzinfo=UTC)
    )

    return TrackCollection(
        track1=track1,
        track2=track2,
        track3=track3
    )



@pytest.fixture
async def seeded_feedbacks(
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
        created_at=datetime(year=2026, month=3, day=30, tzinfo=UTC)
    )
    feedback2 = await make_feedback(
        id=554,
        author_id=seeded_users.fb_author2.id,
        track_id=seeded_tracks.track2.id,
        thread_id=seeded_tracks.track2.id,
        channel_id=111,
        content="nice track i liked it second",
        word_count=6,
        created_at=datetime(year=2026, month=3, day=30, tzinfo=UTC)
    )
    feedback3 = await make_feedback(
        id=553,
        author_id=seeded_users.fb_author3.id,
        track_id=seeded_tracks.track3.id,
        thread_id=seeded_tracks.track3.id,
        channel_id=111,
        content="nice track i liked it third",
        word_count=6,
        created_at=datetime(year=2026, month=3, day=30, tzinfo=UTC)
    )

    feedback4 = await make_feedback(
        id=552,
        author_id=seeded_users.fb_author1.id,
        track_id=seeded_tracks.track2.id,
        thread_id=seeded_tracks.track2.id,
        channel_id=111,
        content="nice track i liked it third",
        word_count=6,
        created_at=datetime(year=2026, month=3, day=30, tzinfo=UTC)
    )

    feedback5 = await make_feedback(
        id=551,
        author_id=seeded_users.fb_author1.id,
        track_id=seeded_tracks.track3.id,
        thread_id=seeded_tracks.track3.id,
        channel_id=111,
        content="nice track i liked it third",
        word_count=6,
        created_at=datetime(year=2026, month=3, day=30, tzinfo=UTC)
    )


    feedback6 = await make_feedback(
        id=505,
        author_id=seeded_users.fb_author3.id,
        track_id=seeded_tracks.track1.id,
        thread_id=seeded_tracks.track1.id,
        channel_id=111,
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
        feedback6=feedback6,
        author_most_feedback_sent=seeded_users.fb_author1
    )


@pytest.fixture
async def seeded_tracks_with_no_feedback(
    seeded_tracks, make_track_with_no_feedback
):
    track_wn_feedback1 = await make_track_with_no_feedback(
        seeded_tracks.track1.id, 123, "message_url1", seeded_tracks.track1.created_at
    )
    track_wn_feedback2 = await make_track_with_no_feedback(
        seeded_tracks.track2.id, 124, "message_url2", seeded_tracks.track2.created_at
    )
    track_wn_feedback3 = await make_track_with_no_feedback(
        seeded_tracks.track3.id, 125, "message_url3", seeded_tracks.track3.created_at
    )

    return TrackWithNoFeedbackCollection(
        track_wn_feedback1=track_wn_feedback1,
        track_wn_feedback2=track_wn_feedback2,
        track_wn_feedback3=track_wn_feedback3
    )
