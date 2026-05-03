import pytest
from bot.database.models import TrackWithNoFeedback, Winner, Challenge, Track, Submission, Feedback
from datetime import UTC, datetime, timedelta
import pytest
from bot.database.models import Challenge, Submission, Vote, Winner, User
from bot.types.common import  ChallengeEmbedData, ChallengeDurationData



@pytest.fixture
def make_feedback(uow):
    async def _make(
            id:int,
            author_id:int,
            track_id:int,
            thread_id:int,
            channel_id:int,
            content:str,
            word_count:int,
            created_at: datetime = datetime.now(UTC)

    ):

        

        feedback = Feedback(
            id=id,
            author_id=author_id,
            track_id=track_id,
            thread_id=thread_id,
            channel_id=channel_id,
            content=content,
            word_count=word_count,
            created_at=created_at
        )

        async with uow._session_factory() as session:
            session.add(feedback)
            await session.commit()

        return feedback
    return _make



@pytest.fixture
def make_track(uow):
    async def _make(
        id: int,
        author_id:int,
        thread_id: int,
        channel_id: int,
        title: str,
        platform: str,
        total_feedbacks: int = 0,
        created_at: datetime = datetime.now(UTC)
        ):



        track = Track(
            id=id,
            author_id=author_id,
            thread_id=thread_id,
            channel_id=channel_id,
            title=title,
            platform=platform,
            total_feedbacks=total_feedbacks,
            created_at=created_at
        )

        async with uow._session_factory() as session:
            session.add(track)
            await session.commit()

        return track
    return _make    



@pytest.fixture
def make_track_with_no_feedback(uow):
    async def _make(
            track_id:int,
            message_id:int,
            message_url:str,
            created_at:datetime

    ):
        track_wn_feedback = TrackWithNoFeedback(
            track_id=track_id,
            message_id=message_id, 
            message_url=message_url, 
            created_at=created_at
        )

        async with uow._session_factory() as session:
            session.add(track_wn_feedback)
            await session.commit()
            
        return track_wn_feedback
    
    return _make


@pytest.fixture
def make_user(uow):
    async def _make(
            user_id: int,
            username: str,
            display_name: str,
            is_purge_data: bool = True,
            total_feedbacks_given:int = 0,
            total_feedback_words:int = 0,
            total_submissions:int = 0,
            total_challenges_won:int = 0,
            created_at: datetime = datetime.now(UTC)
    ):

        
        user = User(
            id=user_id,
            username=username,
            display_name=display_name,
            is_purge_data=is_purge_data,
            total_feedback_words=total_feedback_words,
            total_feedbacks_given=total_feedbacks_given,
            total_challenges_won=total_challenges_won,
            total_submissions=total_submissions,
            created_at=created_at
        )

        async with uow._session_factory() as session:
            session.add(user)
            await session.commit()
        
        return user

    return _make
    


@pytest.fixture
def make_challenge(uow):
    async def _make(
        id: int = 1000,
        title: str = "Test Challenge",
        description: str = "test_description",
        type: str = "official",
        is_active: bool = True,
        is_ongoing_voting: bool = True,
        ends_at: datetime | None = None,
        voting_ends_at: datetime | None = None,
    ) -> Challenge:
        now = datetime.now(tz=UTC)
        field_names = ["title", "description", "challenge duration"]
        field_values = ["title", "description", "challenge duration"]
        challenge_duration = ChallengeDurationData(
        starts_at=now - timedelta(days=1),
        ends_at=ends_at or (now + timedelta(days=6) if is_active else now - timedelta(days=1)),
        voting_ends_at=voting_ends_at or (now + timedelta(days=7) if is_ongoing_voting else now - timedelta(hours=1)))
        challenge_data = ChallengeEmbedData(
            id=id,
            title=title,
            description=description,
            type=type,
            is_active=is_active,
            is_ongoing_voting=is_ongoing_voting,
            field_names=field_names,
            field_values=field_values,
            duration=challenge_duration)
        
        await uow.challenges.create_or_update(challenge_data)
        challenge = await uow.challenges.get_current()
        return challenge
    return _make

@pytest.fixture
def make_vote(
    uow
):
    async def _make(
            voter_id:int,
            submission_id: int,
            challenge_id: int
    ):
 

        vote = Vote(
            voter_id=voter_id,
            submission_id=submission_id,
            challenge_id=challenge_id
        )
        async with uow._session_factory() as session:
            session.add(vote)
            await session.commit()
        
        return vote
    return _make


@pytest.fixture
def make_submission(
    uow
):
    
    async def _make(
          submission_id:int,
          author_id: int,
          challenge_id: int,
          channel_id:int,
          title:str,
          created_at: datetime  
    ):


        submission = Submission(
            id=submission_id,
            author_id=author_id,
            channel_id=channel_id,
            challenge_id=challenge_id,
            title=title,
            created_at=created_at
        )

        async with uow._session_factory() as session:
            session.add(submission)
            await session.commit()
        
        return submission
    
    return _make

@pytest.fixture
def make_winner(
    uow
):
    async def _make(
            winner_id:int,
            submission_id:int,
            challenge_id: int
    ):

        winner = Winner(
            winner_id=winner_id,
            submission_id=submission_id,
            challenge_id=challenge_id
        )
        async with uow._session_factory() as session:
            session.add(winner)
            await session.commit()
        return winner
    
    return _make
