from datetime import UTC, datetime
from unittest.mock import MagicMock
import pytest
from bot.types.tests.user import UserCollection
from bot.types.tests.track import TrackCollection
from bot.types.tests.feedback import FeedbackCollection
import random
random.seed(5)




@pytest.fixture
async def seeded_15_users(make_user):
    user1 = await make_user(user_id=999, username="user1", display_name="submission_author_display_name1")
    user2 = await make_user(user_id=998, username="user2", display_name="submission_author_display_name2")
    user3 = await make_user(user_id=997, username="user3", display_name="submission_author_display_name3")

    user4 = await make_user(user_id=996, username="user4", display_name="track_display_name1")
    user5 = await make_user(user_id=995, username="user5", display_name="track_display_name2")
    user6 = await make_user(user_id=994, username="user6", display_name="track_display_name3")

    user7 = await make_user(user_id=993, username="user7", display_name="voter_display_name1")
    user8 = await make_user(user_id=992, username="user8", display_name="voter_display_name2")
    user9 = await make_user(user_id=991, username="user9", display_name="voter_display_name3")
    user10 = await make_user(user_id=990, username="user10", display_name="voter_display_name4")

    user11 = await make_user(user_id=989, username="user11", display_name="fb_author_display_name1")
    user12 = await make_user(user_id=988, username="user12", display_name="fb_author_display_name2")
    user13 = await make_user(user_id=987, username="user13", display_name="fb_author_display_name3")

    user14 = await make_user(user_id=986, username="user14", display_name="fb_author_display_name3")

    user15 = await make_user(user_id=985, username="user15", display_name="fb_author_display_name3")

    return UserCollection(
        user1=user1,
        user2=user2,
        user3=user3,
        user4=user4,
        user5=user5,
        user6=user6,
        user7=user7,
        user8=user8,
        user9=user9,
        user10=user10,
        user11=user11,
        user12=user12,
        user13=user13,
        user14=user14,
        user15=user15
    )


@pytest.fixture
async def more_than_10_submissions(uow, seeded_challenge, seeded_15_users):
    for user in seeded_15_users.all:
        await uow.challenges.create_or_update_submission(data={
            "id":user.id+3,
            "challenge_id":seeded_challenge.id,
            "author_id":user.id,
            "channel_id":111,
            "total_votes":random.randint(1,100),
            "title":f"{user.id}'s submission"
        })


@pytest.fixture
async def update_total_feedbacks(uow, seeded_15_users):


    for user in seeded_15_users.all:
        await uow.users.update(user_id=user.id, data={"total_feedbacks_given":random.randint(1, 1000)})



@pytest.fixture
async def update_total_submissions(uow, seeded_15_users):
 

    for user in seeded_15_users.all:
        await uow.users.update(user_id=user.id, data={"total_submissions":random.randint(1, 1000)})       
    

@pytest.fixture
async def update_total_challenges_won(uow, seeded_15_users):


    for user in seeded_15_users.all:
        await uow.users.update(user_id=user.id, data={"total_challenges_won":random.randint(1, 1000)})





@pytest.fixture
def make_activity_tracks(uow):
    random.seed(5)
    async def _make(
            members: list[MagicMock],
            n:int,
            channel_id: int,
            dates: list[datetime],
            used_ids: set | None = None,
            
    ):
        
        choices = random.choices(members, k=n)
        used_ids = used_ids or set()
        tracks = []

        for member in choices:
            s_id = random.randint(100_000_000, 999_999_999)
            while s_id in used_ids:
                s_id = random.randint(100_000_000, 999_999_999)

            created_at = random.choice(dates)
            track = {
                "id":s_id,
                "title":"test_title",
                "channel_id":channel_id,
                "thread_id":s_id,
                "author_id":member.id,
                "created_at":created_at
            }

            used_ids.add(s_id)
            tracks.append(track)
        
        db_tracks = await uow.tracks.bulk_insert_track(tracks)

        track_data = {f"track{i}":track for i,track in enumerate(db_tracks)}

        return TrackCollection(**track_data)
    
    return _make

        




@pytest.fixture
def make_activity_feedbacks(uow):
    async def _make(
            members: list[MagicMock],
            tracks: list[MagicMock],
            dates: list[datetime],
            channel_id: int,
            used_ids: set | None = None
    ):
        
        valid_pairs = [
            (member.id, track.id)
            for member in members
            for track in tracks if track.author_id!=member
        ]
        used_ids = used_ids or set()
        used_pairs = set()
        feedbacks = []

        for member_id,track_id in valid_pairs:
            if (member_id, track_id) in used_pairs:
                continue
            s_id = random.randint(100_000_000, 999_999_999)
            while s_id in used_ids:
                s_id = random.randint(100_000_000, 999_999_999)

            created_at = random.choice(dates)
            feedback = {
                "id":s_id,
                "content":"test content",
                "channel_id":channel_id,
                "thread_id":s_id,
                "author_id":member_id,
                "created_at":created_at,
                "word_count":2
            }

            used_ids.add(s_id)
            feedbacks.append(feedback)
        
        db_feedbacks = await uow.feedback.bulk_insert_feedback(feedbacks)
        feedback_data = {f"feedback{i}":feedback for i,feedback in enumerate(db_feedbacks)}

        return FeedbackCollection(**feedback_data)
    
    return _make



@pytest.fixture
def seeded_activity_tracks(
   seeded_users, make_track
):
    async def _make(created_at:datetime):

        track1 = await make_track(
            id=12345,
            author_id=seeded_users.track_author1.id,
            thread_id=12345,
            channel_id=111,
            title="track1",
            platform="test platform",
            total_feedbacks=0,
            created_at=created_at
        )

        track2 = await make_track(
            id=123456,
            author_id=seeded_users.track_author2.id,
            thread_id=123456,
            channel_id=111,
            title="track2",
            platform="test platform",
            total_feedbacks=0,
            created_at=created_at
        )

        track3 = await make_track(
            id=1234567,
            author_id=seeded_users.track_author3.id,
            thread_id=1234567,
            channel_id=111,
            title="track3",
            platform="test platform",
            total_feedbacks=0,
            created_at=created_at
        )

        return TrackCollection(
            track1=track1,
            track2=track2,
            track3=track3
        )
    return _make


@pytest.fixture
async def most_active_periods_data(
    seeded_users, make_track, make_feedback
):
    await make_track(
        id=555,
        author_id=seeded_users.track_author1.id,
        thread_id=555,
        channel_id=111,
        title="track1",
        platform="test platform",
        total_feedbacks=0,
        created_at=datetime(year=2026, month=1, day=5, tzinfo=UTC)
    )
    await make_track(
        id=554,
        author_id=seeded_users.track_author1.id,
        thread_id=554,
        channel_id=111,
        title="track1",
        platform="test platform",
        total_feedbacks=0,
        created_at=datetime(year=2026, month=1, day=5, tzinfo=UTC)
    )
    await make_track(
        id=553,
        author_id=seeded_users.track_author1.id,
        thread_id=553,
        channel_id=111,
        title="track1",
        platform="test platform",
        total_feedbacks=0,
        created_at=datetime(year=2026, month=1, day=5, tzinfo=UTC)
    )

    await make_track(
        id=552,
        author_id=seeded_users.track_author1.id,
        thread_id=552,
        channel_id=111,
        title="track1",
        platform="test platform",
        total_feedbacks=0,
        created_at=datetime(year=2026, month=1, day=6, tzinfo=UTC)
    )


    await make_feedback(
        id=888,
        author_id=seeded_users.fb_author1.id,
        track_id=555,
        thread_id=555,
        channel_id=111,
        content="nice track i liked it",
        word_count=5,
        created_at=datetime(year=2026, month=1, day=7, tzinfo=UTC)
    )
    await make_feedback(
        id=887,
        author_id=seeded_users.fb_author2.id,
        track_id=554,
        thread_id=554,
        channel_id=111,
        content="nice track i liked it second",
        word_count=6,
        created_at=datetime(year=2026, month=1, day=5, tzinfo=UTC)
    )
    await make_feedback(
        id=886,
        author_id=seeded_users.fb_author3.id,
        track_id=553,
        thread_id=553,
        channel_id=111,
        content="nice track i liked it third",
        word_count=6,
        created_at=datetime(year=2026, month=1, day=5, tzinfo=UTC)
    )

    await make_feedback(
        id=3242,
        author_id=seeded_users.fb_author1.id,
        track_id=554,
        thread_id=554,
        channel_id=111,
        content="nice track i liked it",
        word_count=5,
        created_at=datetime(year=2026, month=1, day=5, tzinfo=UTC)
    )
    await make_feedback(
        id=324234,
        author_id=seeded_users.fb_author1.id,
        track_id=553,
        thread_id=553,
        channel_id=111,
        content="nice track i liked it",
        word_count=5,
        created_at=datetime(year=2026, month=1, day=5, tzinfo=UTC)
    )
    
@pytest.fixture
def seeded_activity_feedbacks(
    seeded_users, make_feedback
):
    async def _make(created_at: datetime):

        feedback1 = await make_feedback(
            id=555,
            author_id=seeded_users.fb_author1.id,
            track_id=12345,
            thread_id=12345,
            channel_id=111,
            content="nice track i liked it third",
            word_count=6,
            created_at=created_at
        )

        feedback2 = await make_feedback(
            id=554,
            author_id=seeded_users.fb_author1.id,
            track_id=123456,
            thread_id=123456,
            channel_id=111,
            content="nice track i liked it third",
            word_count=6,
            created_at=created_at
        )


        feedback3 = await make_feedback(
            id=553,
            author_id=seeded_users.fb_author3.id,
            track_id=12345,
            thread_id=12345,
            channel_id=111,
            content="nice track i liked it third",
            word_count=6,
            created_at=created_at
        )

        return FeedbackCollection(
            feedback1=feedback1,
            feedback2=feedback2,
            feedback3=feedback3
        )
    return _make