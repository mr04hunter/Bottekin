from datetime import UTC, datetime, timedelta
import pytest
from bot.services.challenge import ChallengeService
from bot.types.common import ChallengeEmbedData, ChallengeDurationData, MonthlyChallengeData
from tests.factories.discord_factories import make_submission_message
from unittest.mock import AsyncMock, MagicMock

class TestChallengeService:
    @pytest.fixture
    async def service(
        self, uow, mock_bot, mock_extractor, mock_challenge_validator, test_config):

        scheduler = AsyncMock()
        track_extractor = MagicMock()
        track_extractor.extract_title = AsyncMock(return_value=("test_submission", "test_platform"))
        return ChallengeService(uow=uow, bot=mock_bot,extractor=mock_extractor,
                                scheduler=scheduler, event_handler=AsyncMock(),
                                validator=mock_challenge_validator, config=test_config, track_extractor=track_extractor)
    

    async def test_add_submission(
        self, service, uow, seeded_challenge, seeded_users
    ):
        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id))

        await service.add_submission(message=message)

        submission = await uow.challenges.get_submission(message.id)
        assert submission is not None
        assert submission.author_id == seeded_users.submission_author1.id
        assert submission.challenge_id == seeded_challenge.id
        assert submission.title == "test_submission"

        
    
    async def test_add_monthly_submission(self, service, uow, seeded_monthly_challenge, seeded_users):
        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id))

        await service.add_monthly_submission(message=message)

        submission = await uow.challenges.get_monthly_submission(message.id)
        assert submission is not None
        assert submission.author_id == seeded_users.submission_author1.id
        assert submission.challenge_id == seeded_monthly_challenge.id
        assert submission.title == "test_submission"


    async def test_add_monthly_submission_trigger_fires_correctly(
        self, service, uow, seeded_users, seeded_monthly_challenge
    ):
        challenge = await uow.challenges.get_current_monthly_challenge()

        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id))

        await service.add_monthly_submission(message=message)

        user = await uow.users.get_by_id(seeded_users.submission_author1.id)
        challenge = await uow.challenges.get_current_monthly_challenge()
        assert user.total_submissions == 1
        assert challenge.total_submissions == 1

    async def test_add_submission_trigger_fires_correctly(
        self, service, uow, seeded_users, seeded_challenge
    ):
        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id))

        await service.add_submission(message=message)

        user = await uow.users.get_by_id(seeded_users.submission_author1.id)
        challenge = await uow.challenges.get_current()
        assert user.total_submissions == 1
        assert challenge.total_submissions == 1

    async def test_add_submission_after_end_date(
        self, service, uow, make_challenge, seeded_users
    ):
        challenge = await make_challenge(ends_at=datetime.now(tz=UTC))
        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id), created_at=challenge.ends_at + timedelta(days=1))

        await service.add_submission(message=message)

        submission = await uow.challenges.get_submission(message.id)
        assert submission is None


    async def test_add_monthly_submission_after_end_date(
        self, service, uow, seeded_ended_monthly_challenge, seeded_users
    ):

        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id), created_at=seeded_ended_monthly_challenge.ends_at + timedelta(days=1))

        await service.add_monthly_submission(message=message)

        submission = await uow.challenges.get_monthly_submission(message.id)
        assert submission is None


    async def test_add_submission_without_a_challenge(
        self, service, uow, seeded_users
    ):
        
        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id))

        await service.add_submission(message=message)

        submission = await uow.challenges.get_submission(message.id)
        assert submission is None


    async def test_add_monthly_submission_without_a_challenge(
        self, service, uow, seeded_users
    ):
        
        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id))

        await service.add_monthly_submission(message=message)

        submission = await uow.challenges.get_monthly_submission(message.id)
        assert submission is None


    async def test_add_and_delete_submission_persists_to_db(
        self, service, uow, seeded_challenge, seeded_users
    ):
        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id))

        await service.add_submission(message=message)

        await service.delete_submission(message.id)

        assert await uow.challenges.get_submission(message.id) is None


    async def test_add_and_delete_monthly_submission_persists_to_db(
        self, service, uow, seeded_monthly_challenge, seeded_users
    ):
        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id))

        await service.add_monthly_submission(message=message)

        await service.delete_monthly_submission(message.id)

        assert await uow.challenges.get_monthly_submission(message.id) is None


    async def test_add_and_delete_monthly_submission_triggers_fire_correctly(
        self, service, uow, seeded_monthly_challenge, seeded_users
    ):
       
        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id))

        await service.add_monthly_submission(message=message)

        await service.delete_monthly_submission(message.id)

        challenge = await uow.challenges.get_current_monthly_challenge()
        user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert challenge.total_submissions == 0
        assert user.total_submissions == 0


    async def test_add_and_delete_submission_triggers_fire_correctly(
        self, service, uow, seeded_challenge, seeded_users
    ):
       
        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id))

        await service.add_submission(message=message)

        await service.delete_submission(message.id)

        challenge = await uow.challenges.get_current()
        user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert challenge.total_submissions == 0
        assert user.total_submissions == 0



    async def test_delete_nonexistent_submission(
        self, service, uow
    ):

        await service.delete_submission(213123)


    async def test_delete_nonexistent_monthly_submission(
        self, service, uow
    ):

        await service.delete_monthly_submission(213123)

    async def test_add_and_update_submission_persists_to_db(
        self, service, uow,seeded_users, seeded_challenge
    ):

        message = make_submission_message(id=1234567,author=MagicMock(id=seeded_users.submission_author1.id))
        await service.add_submission(message=message)

        edited_at = datetime.now(tz=UTC) + timedelta(days=3)
        updated_message = make_submission_message(1234567,author=MagicMock(id=seeded_users.submission_author1.id), edited_at=edited_at)
        await service.update_submission(updated_message)

        submission = await uow.challenges.get_submission(1234567)
        assert submission.edited_at == edited_at


    async def test_add_and_update_monthly_submission_persists_to_db(
        self, service, uow,seeded_users, seeded_monthly_challenge
    ):

        message = make_submission_message(id=1234567,author=MagicMock(id=seeded_users.submission_author1.id))
        await service.add_monthly_submission(message=message)

        edited_at = datetime.now(tz=UTC) + timedelta(days=3)
        updated_message = make_submission_message(1234567,author=MagicMock(id=seeded_users.submission_author1.id), edited_at=edited_at)
        await service.add_monthly_submission(updated_message)

        submission = await uow.challenges.get_monthly_submission(1234567)
        assert submission.edited_at == edited_at
        
    
    async def test_update_nonexistent_submission_gets_created(
        self, service, uow, seeded_challenge, seeded_users
    ):
        edited_at = datetime.now(tz=UTC) + timedelta(days=3)
        updated_message = make_submission_message(1234567,author=MagicMock(id=seeded_users.submission_author1.id), edited_at=edited_at)
        await service.update_submission(updated_message)

        assert await uow.challenges.get_submission(1234567) is not None

    async def test_update_nonexistent_submission_not_created_without_challenge(
        self, service, uow, seeded_users
    ):
        
        edited_at = datetime.now(tz=UTC) + timedelta(days=3)
        updated_message = make_submission_message(1234567,author=MagicMock(id=seeded_users.submission_author1.id), edited_at=edited_at)
        await service.update_submission(updated_message)

        assert await uow.challenges.get_submission(1234567) is None



    async def test_create_monthly_challenge(self, service, uow):
        data = MonthlyChallengeData(
        id=111111111,
        title="2026_5",
        is_active=True,
        starts_at=datetime(year=2026, month=5, day=1, tzinfo=UTC),
        ends_at=datetime(year=2026, month=6, day=1, tzinfo=UTC)
        )
        challenge = await service.create_or_update_monthly_challenge(data=data)

        assert challenge.id == 111111111
        assert challenge.title == "2026_5"
        assert challenge.is_active == True
        assert challenge.starts_at == datetime(year=2026, month=5, day=1, tzinfo=UTC)
        assert challenge.ends_at == datetime(year=2026, month=6, day=1, tzinfo=UTC)


    async def test_create_or_update_monthly_challenge_updates_existing_monthly_challenge(
        self,service, uow, seeded_monthly_challenge):

        updated_data = MonthlyChallengeData(
            id=seeded_monthly_challenge.id,
            title="updated_test_monthly_challenge_title",
            is_active=True,
            starts_at=seeded_monthly_challenge.starts_at,
            ends_at=seeded_monthly_challenge.ends_at
        )

        challenge = await service.create_or_update_monthly_challenge(updated_data)

        assert challenge.title == "updated_test_monthly_challenge_title"
    async def test_create_challenge(
            self, service, uow
    ):
        now = datetime.now(tz=UTC)
        starts_at=now - timedelta(days=1)
        ends_at=now + timedelta(days=1)
        voting_ends_at=now + timedelta(days=2)
        field_names = ["title", "description", "challenge duration"]
        field_values = ["title", "description", "challenge duration"]
        challenge_duration = ChallengeDurationData(
        starts_at=starts_at,
        ends_at=ends_at,
        voting_ends_at=voting_ends_at)
        challenge_data = ChallengeEmbedData(
            id=123456,
            title="test",
            description="test_description",
            type="official",
            is_active=True,
            is_ongoing_voting=True,
            field_names=field_names,
            field_values=field_values,
            duration=challenge_duration)
        
        await service.create_or_update_challenge(challenge_data)

        challenge = await uow.challenges.get_current()

        assert challenge.id == challenge_data.id
        assert challenge.title == challenge_data.title
        assert challenge.description == challenge_data.description
        assert challenge.type == challenge_data.type
        assert challenge.is_active == challenge_data.is_active
        assert challenge.is_ongoing_voting == challenge_data.is_ongoing_voting
        assert challenge.ends_at == challenge_data.duration.ends_at
        assert challenge.starts_at == challenge_data.duration.starts_at
        assert challenge.voting_ends_at == challenge_data.duration.voting_ends_at

    async def test_update_challenge(
            self, service, uow, make_challenge
    ):
        await make_challenge(title="test title", type="community")

        now = datetime.now(tz=UTC)
        starts_at=now - timedelta(days=1)
        ends_at=now + timedelta(days=1)
        voting_ends_at=now + timedelta(days=2)
        field_names = ["title", "description", "challenge duration"]
        field_values = ["title", "description", "challenge duration"]
        challenge_duration = ChallengeDurationData(
        starts_at=starts_at,
        ends_at=ends_at,
        voting_ends_at=voting_ends_at)
        challenge_data = ChallengeEmbedData(
            id=1000,
            title="updated",
            description="test_description",
            type="official",
            is_active=True,
            is_ongoing_voting=True,
            field_names=field_names,
            field_values=field_values,
            duration=challenge_duration)
        
        await service.create_or_update_challenge(challenge_data)

        challenge = await uow.challenges.get_current()

        assert challenge.title == "updated"
        assert challenge.type == "official" 
    
    async def test_delete_challenge(
            self, service, uow, seeded_users, seeded_challenge, seeded_submissions, seeded_votes
    ):
        await service.delete_challenge(seeded_challenge.id)
        
        assert await uow.challenges.get_current() is None
        assert await uow.challenges.get_submission(seeded_submissions.submission1.id) is None
        assert await uow.challenges.get_submission(seeded_submissions.submission2.id) is None
        assert await uow.challenges.get_submission(seeded_submissions.submission3.id) is None

        assert await uow.challenges.get_vote(seeded_votes.vote1.voter_id, seeded_votes.vote1.challenge_id, seeded_votes.vote1.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote2.voter_id, seeded_votes.vote2.challenge_id, seeded_votes.vote2.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote3.voter_id, seeded_votes.vote3.challenge_id, seeded_votes.vote3.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote4.voter_id, seeded_votes.vote4.challenge_id, seeded_votes.vote4.submission_id) is None


    async def test_add_vote(
            self, service, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        
        await service.vote(seeded_submissions.submission1.id, seeded_users.voter1.id)

        assert await uow.challenges.get_vote(seeded_users.voter1.id, seeded_challenge.id, seeded_submissions.submission1.id) is not None


    async def test_add_vote_trigger_fires_correctly(
            self, service, uow, seeded_users, seeded_submissions
    ):
        
        await service.vote(seeded_submissions.submission1.id, seeded_users.voter1.id)

        challenge = await uow.challenges.get_current()
        submission = await uow.challenges.get_submission(seeded_submissions.submission1.id)
        voter_user = await uow.users.get_by_id(seeded_users.voter1.id)
        submission_user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert challenge.total_votes == 1
        assert submission.total_votes == 1
        assert voter_user.times_voted == 1
        assert submission_user.total_votes_received == 1


    async def test_add_and_delete_vote(
            self, service, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        
        await service.vote(seeded_submissions.submission1.id, seeded_users.voter1.id)
        await service.remove_vote(seeded_submissions.submission1.id, seeded_users.voter1.id)

        assert await uow.challenges.get_vote(seeded_users.voter1.id, seeded_challenge.id, seeded_submissions.submission1.id) is None


    async def test_add_and_remove_vote_trigger_fires_correctly(
            self, service, uow, seeded_users, seeded_submissions
    ):
        
        
        await service.vote(seeded_submissions.submission1.id, seeded_users.voter1.id)
        await service.remove_vote(seeded_submissions.submission1.id, seeded_users.voter1.id)

        challenge = await uow.challenges.get_current()
        submission = await uow.challenges.get_submission(seeded_submissions.submission1.id)
        voter_user = await uow.users.get_by_id(seeded_users.voter1.id)
        submission_user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert challenge.total_votes == 0
        assert submission.total_votes == 0
        assert voter_user.times_voted == 0
        assert submission_user.total_votes_received == 0


    async def test_add_duplicate_vote(
            self, service, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        
        await service.vote(seeded_submissions.submission1.id, seeded_users.voter1.id)
        await service.vote(seeded_submissions.submission2.id, seeded_users.voter1.id)

        assert await uow.challenges.get_vote(seeded_users.voter1.id, seeded_challenge.id, seeded_submissions.submission1.id) is None


        assert await uow.challenges.get_vote(seeded_users.voter1.id, seeded_challenge.id, seeded_submissions.submission2.id) is not None


        submission1 = await uow.challenges.get_submission(seeded_submissions.submission1.id)
        assert submission1.total_votes == 0

        submission2 = await uow.challenges.get_submission(seeded_submissions.submission2.id)
        assert submission2.total_votes == 1


    async def test_add_vote_without_challenge(
            self, service, seeded_users
    ):
        await service.vote(123141324, seeded_users.voter1.id)
        #no crash: pass


    async def test_vote_after_voting_ended(
            self, service, uow,make_challenge, seeded_users
    ):
        challenge = await make_challenge(is_ongoing_voting=False)

        message = make_submission_message(author=MagicMock(id=seeded_users.submission_author1.id), created_at=challenge.starts_at + timedelta(minutes=5))
        await service.add_submission(message=message)

        await service.vote(message.id, seeded_users.voter1.id)

        assert await uow.challenges.get_vote(seeded_users.voter1.id, challenge.id, message.id) is None

    async def test_add_chosen_winner(
            self, service, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        
        await service.set_chosen_winner(seeded_users.submission_author1.id, seeded_submissions.submission1.id)

        assert await uow.challenges.get_winner(seeded_users.submission_author1.id, seeded_submissions.submission1.id, seeded_challenge.id) is not None


    async def test_add_chosen_winner_duplicate(
            self, service, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        
        await service.set_chosen_winner(seeded_users.submission_author1.id, seeded_submissions.submission1.id)
        submission = await uow.challenges.get_submission(seeded_submissions.submission1.id)
        assert submission.winner_declared == True
        await service.set_chosen_winner(seeded_users.submission_author1.id, seeded_submissions.submission1.id)
        #no crash pass



    async def test_add_chosen_winner_trigger_fires_correctly(
            self, service, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        
        
        await service.set_chosen_winner(seeded_users.submission_author1.id, seeded_submissions.submission1.id)
        submission = await uow.challenges.get_submission(seeded_submissions.submission1.id)
        user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert submission.winner_declared == True
        assert user.total_challenges_won == 1

    async def test_add_and_remove_chosen_winner(
            self, service, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        
        await service.set_chosen_winner(seeded_users.submission_author1.id, seeded_submissions.submission1.id)
        await service.remove_chosen_winner(seeded_users.submission_author1.id, seeded_submissions.submission1.id)
        assert await uow.challenges.get_winner(seeded_users.submission_author1.id, seeded_submissions.submission1.id, seeded_challenge.id) is None

        
    async def test_add_and_remove_chosen_winner_trigger_fires_correctly(
            self, service, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        
        await service.set_chosen_winner(seeded_users.submission_author1.id, seeded_submissions.submission1.id)
        await service.remove_chosen_winner(seeded_users.submission_author1.id, seeded_submissions.submission1.id)
        submission = await uow.challenges.get_submission(seeded_submissions.submission1.id)
        user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert submission.winner_declared == False
        assert user.total_challenges_won == 0

    async def test_add_nonexistent_chosen_winner(
            self, service, uow, seeded_users, seeded_challenge
    ):
        
        await service.set_chosen_winner(seeded_users.submission_author1.id, 123321)
        assert await uow.challenges.get_winner(seeded_users.submission_author1.id, 12313124, seeded_challenge.id) is None

    async def test_remove_nonexistent_chosen_winner(
            self, service, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        await service.remove_chosen_winner(seeded_users.submission_author1.id, seeded_submissions.submission1.id)