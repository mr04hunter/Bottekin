from datetime import UTC, datetime
import pytest
from bot.database.models import Vote, Winner
from bot.services.challenge import ChallengeService
from unittest.mock import AsyncMock, MagicMock

class TestChallengeRepository:
    @pytest.fixture
    async def service(
        self, uow, mock_bot, mock_extractor, mock_challenge_validator, test_config):
        mock_bot.services = MagicMock()
        mock_bot.services.sync_service = MagicMock()


        
        scheduler = MagicMock()
        scheduler.schedule_challenge_jobs = AsyncMock()
        return ChallengeService(uow=uow, bot=mock_bot,
                    extractor=mock_extractor,event_handler=AsyncMock(),
                    scheduler=scheduler, validator=mock_challenge_validator,
                    config=test_config, track_extractor=AsyncMock())

    async def test_bulk_insert_submissions(
                self, uow, seeded_users, seeded_challenge
        ):
            submission1 = {
                "id":555,
                "author_id":seeded_users.submission_author1.id,
                "channel_id":111,
                "challenge_id":seeded_challenge.id,
                "title":"submission1",
                "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}
            



            submission2 = {
                "id":554,
                "author_id":seeded_users.submission_author2.id,
                "channel_id":111,
                "challenge_id":seeded_challenge.id,
                "title":"submission1",
                "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}
            
            submission3 = {
                "id":553,
                "author_id":seeded_users.submission_author3.id,
                "channel_id":111,
                "challenge_id":seeded_challenge.id,
                "title":"submission1",
                "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}

            await uow.challenges.bulk_insert_submissions([submission1, submission2, submission3])
            assert await uow.challenges.get_submission(555) is not None
            assert await uow.challenges.get_submission(554) is not None
            assert await uow.challenges.get_submission(553) is not None

    async def test_bulk_insert_updates_submissions(
            self, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
    

        updated_submission ={
                "id":seeded_submissions.submission1.id,
                "author_id":seeded_users.submission_author1.id,
                "channel_id":111,
                "challenge_id":seeded_challenge.id,
                "title":"updated_title",
                "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}


        await uow.challenges.bulk_insert_submissions([updated_submission])

        submission = await uow.challenges.get_submission(seeded_submissions.submission1.id)

        assert submission.title == "updated_title"

    async def test_bulk_insert_votes(
            self, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        

        vote1 = {
            "voter_id":seeded_users.voter1.id,
            "submission_id":seeded_submissions.submission1.id,
            "challenge_id":seeded_challenge.id}
        vote2 = {
            "voter_id":seeded_users.voter2.id,
            "submission_id":seeded_submissions.submission2.id,
            "challenge_id":seeded_challenge.id}
        vote3 = {
            "voter_id":seeded_users.voter3.id,
            "submission_id":seeded_submissions.submission3.id,
            "challenge_id":seeded_challenge.id}
        votes = {
            seeded_users.voter1.id: Vote(**vote1),
            seeded_users.voter2.id: Vote(**vote2),
            seeded_users.voter3.id: Vote(**vote3)
        }
        await uow.challenges.bulk_insert_votes(votes, seeded_challenge)

        assert await uow.challenges.get_vote(seeded_users.voter1.id, seeded_challenge.id, seeded_submissions.submission1.id) is not None
        assert await uow.challenges.get_vote(seeded_users.voter2.id, seeded_challenge.id, seeded_submissions.submission2.id) is not None
        assert await uow.challenges.get_vote(seeded_users.voter3.id, seeded_challenge.id, seeded_submissions.submission3.id) is not None

    async def test_bulk_insert_updates_votes(
            self,uow, seeded_users, seeded_challenge, seeded_submissions, seeded_votes,
    ):
        vote1_data = {
            "voter_id":seeded_users.voter1.id,
            "submission_id":seeded_submissions.submission1.id,
            "challenge_id":seeded_challenge.id}
        vote2_data = {
            "voter_id":seeded_users.voter2.id,
            "submission_id":seeded_submissions.submission1.id,
            "challenge_id":seeded_challenge.id}
        vote3_data = {
            "voter_id":seeded_users.voter3.id,
            "submission_id":seeded_submissions.submission1.id,
            "challenge_id":seeded_challenge.id}
        votes = {
            seeded_users.voter1.id: Vote(**vote1_data),
            seeded_users.voter2.id: Vote(**vote2_data),
            seeded_users.voter3.id: Vote(**vote3_data)
        }
        await uow.challenges.bulk_insert_votes(votes, seeded_challenge)

       
        vote1 = await uow.challenges.get_vote(seeded_users.voter1.id, seeded_challenge.id, seeded_submissions.submission1.id)
        assert vote1.submission_id == seeded_submissions.submission1.id
        vote2 = await uow.challenges.get_vote(seeded_users.voter2.id, seeded_challenge.id, seeded_submissions.submission1.id)
        assert vote2.submission_id == seeded_submissions.submission1.id
        vote3 = await uow.challenges.get_vote(seeded_users.voter3.id, seeded_challenge.id, seeded_submissions.submission1.id)
        assert vote3.submission_id == seeded_submissions.submission1.id

    async def test_bulk_insert_winners(
            self, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        


        winner1 =  {
            "winner_id":seeded_users.submission_author1.id,
            "submission_id":seeded_submissions.submission1.id,
            "challenge_id":seeded_challenge.id}
        
        winner2 = {
            "winner_id":seeded_users.submission_author2.id,
            "submission_id":seeded_submissions.submission2.id,
            "challenge_id":seeded_challenge.id}
        winner3 = {
            "winner_id":seeded_users.submission_author3.id,
            "submission_id":seeded_submissions.submission3.id,
            "challenge_id":seeded_challenge.id}
        

        await uow.challenges.bulk_insert_winners({Winner(**winner1), Winner(**winner2), Winner(**winner3)})

        assert await uow.challenges.get_winner(seeded_users.submission_author1.id,seeded_submissions.submission1.id,seeded_challenge.id) is not None
        assert await uow.challenges.get_winner(seeded_users.submission_author2.id,seeded_submissions.submission2.id, seeded_challenge.id) is not None
        assert await uow.challenges.get_winner(seeded_users.submission_author3.id,seeded_submissions.submission3.id, seeded_challenge.id) is not None

    async def test_duplicate_bulk_insert_winners(
            self, uow, seeded_users, seeded_challenge, seeded_submissions
    ):
        winner1 =  {
            "winner_id":seeded_users.submission_author1.id,
            "submission_id":seeded_submissions.submission1.id,
            "challenge_id":seeded_challenge.id}
        
        winner2 = {
            "winner_id":seeded_users.submission_author2.id,
            "submission_id":seeded_submissions.submission2.id,
            "challenge_id":seeded_challenge.id}
        winner3 = {
            "winner_id":seeded_users.submission_author3.id,
            "submission_id":seeded_submissions.submission3.id,
            "challenge_id":seeded_challenge.id}

        await uow.challenges.bulk_insert_winners({Winner(**winner1), Winner(**winner2), Winner(**winner3)})

        #no crash: pass
    

    async def test_cleanup_challenge_data(
            self, uow, seeded_users, seeded_challenge, seeded_submissions, seeded_votes
    ):
        challenge = await uow.challenges.get_current()
        await uow.challenges.cleanup_challenge_data([], [], [], challenge)

        assert await uow.challenges.get_submission(seeded_submissions.submission1.id) is None
        assert await uow.challenges.get_submission(seeded_submissions.submission2.id) is None
        assert await uow.challenges.get_submission(seeded_submissions.submission3.id) is None

        assert await uow.challenges.get_vote(seeded_votes.vote1.voter_id, seeded_votes.vote1.challenge_id, seeded_votes.vote1.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote2.voter_id, seeded_votes.vote2.challenge_id, seeded_votes.vote2.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote3.voter_id, seeded_votes.vote3.challenge_id, seeded_votes.vote3.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote4.voter_id, seeded_votes.vote4.challenge_id, seeded_votes.vote4.submission_id) is None

        assert await uow.challenges.get_winner(seeded_users.submission_author1.id,seeded_submissions.submission1.id,seeded_challenge.id) is None
        assert await uow.challenges.get_winner(seeded_users.submission_author2.id,seeded_submissions.submission2.id, seeded_challenge.id) is None
        assert await uow.challenges.get_winner(seeded_users.submission_author3.id,seeded_submissions.submission3.id, seeded_challenge.id) is None



    async def test_cleanup_submissions(
            self, uow, seeded_users, seeded_challenge, seeded_submissions,seeded_winners, seeded_votes
    ):
        #deleting all submissions should cascade winners, votes
        await uow.challenges.cleanup_challenge_data([], seeded_votes.all, seeded_winners.all, seeded_challenge)
        


        assert await uow.challenges.get_submission(seeded_submissions.submission1.id) is None
        assert await uow.challenges.get_submission(seeded_submissions.submission2.id) is None
        assert await uow.challenges.get_submission(seeded_submissions.submission3.id) is None

        assert await uow.challenges.get_vote(seeded_votes.vote1.voter_id, seeded_votes.vote1.challenge_id, seeded_votes.vote1.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote2.voter_id, seeded_votes.vote2.challenge_id, seeded_votes.vote2.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote3.voter_id, seeded_votes.vote3.challenge_id, seeded_votes.vote3.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote4.voter_id, seeded_votes.vote4.challenge_id, seeded_votes.vote4.submission_id) is None

        assert await uow.challenges.get_winner(seeded_users.submission_author1.id,seeded_submissions.submission1.id,seeded_challenge.id) is None
        assert await uow.challenges.get_winner(seeded_users.submission_author2.id,seeded_submissions.submission2.id, seeded_challenge.id) is None
        assert await uow.challenges.get_winner(seeded_users.submission_author3.id,seeded_submissions.submission3.id, seeded_challenge.id) is None

    async def test_cleanup_partial_submissions(
            self, uow, seeded_users, seeded_challenge, seeded_submissions, seeded_votes, seeded_winners
    ):
        #keep only submission1, rest should cascade
        await uow.challenges.cleanup_challenge_data([seeded_submissions.submission1.id], seeded_votes.all, seeded_winners.all, seeded_challenge)
        


        assert await uow.challenges.get_submission(seeded_submissions.submission1.id) is not None
        assert await uow.challenges.get_submission(seeded_submissions.submission2.id) is None
        assert await uow.challenges.get_submission(seeded_submissions.submission3.id) is None

        assert await uow.challenges.get_vote(seeded_votes.vote1.voter_id, seeded_votes.vote1.challenge_id, seeded_votes.vote1.submission_id) is not None
        assert await uow.challenges.get_vote(seeded_votes.vote2.voter_id, seeded_votes.vote2.challenge_id, seeded_votes.vote2.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote3.voter_id, seeded_votes.vote3.challenge_id, seeded_votes.vote3.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote4.voter_id, seeded_votes.vote4.challenge_id, seeded_votes.vote4.submission_id) is not None

        assert await uow.challenges.get_winner(seeded_users.submission_author1.id,seeded_submissions.submission1.id,seeded_challenge.id) is not None
        assert await uow.challenges.get_winner(seeded_users.submission_author2.id,seeded_submissions.submission2.id, seeded_challenge.id) is None
        assert await uow.challenges.get_winner(seeded_users.submission_author3.id,seeded_submissions.submission3.id, seeded_challenge.id) is None

    async def test_cleanup_votes(
            self, uow, seeded_users, seeded_challenge, seeded_submissions, seeded_votes, seeded_winners
    ):

        await uow.challenges.cleanup_challenge_data(seeded_submissions.submission_ids, [], seeded_winners.all, seeded_challenge)

        assert await uow.challenges.get_submission(seeded_submissions.submission1.id) is not None
        assert await uow.challenges.get_submission(seeded_submissions.submission2.id) is not None
        assert await uow.challenges.get_submission(seeded_submissions.submission3.id) is not None

        assert await uow.challenges.get_vote(seeded_votes.vote1.voter_id, seeded_votes.vote1.challenge_id, seeded_votes.vote1.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote2.voter_id, seeded_votes.vote2.challenge_id, seeded_votes.vote2.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote3.voter_id, seeded_votes.vote3.challenge_id, seeded_votes.vote3.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote4.voter_id, seeded_votes.vote4.challenge_id, seeded_votes.vote4.submission_id) is None

        assert await uow.challenges.get_winner(seeded_users.submission_author1.id,seeded_submissions.submission1.id,seeded_challenge.id) is not None
        assert await uow.challenges.get_winner(seeded_users.submission_author2.id,seeded_submissions.submission2.id, seeded_challenge.id) is not None
        assert await uow.challenges.get_winner(seeded_users.submission_author3.id,seeded_submissions.submission3.id, seeded_challenge.id) is not None

    async def test_cleanup_partial_votes(
            self, uow, seeded_users, seeded_challenge, seeded_submissions, seeded_votes, seeded_winners
    ):

        await uow.challenges.cleanup_challenge_data(seeded_submissions.submission_ids, [seeded_votes.all[0]], seeded_winners.all, seeded_challenge)

        assert await uow.challenges.get_submission(seeded_submissions.submission1.id) is not None
        assert await uow.challenges.get_submission(seeded_submissions.submission2.id) is not None
        assert await uow.challenges.get_submission(seeded_submissions.submission3.id) is not None

        assert await uow.challenges.get_vote(seeded_votes.vote1.voter_id, seeded_votes.vote1.challenge_id, seeded_votes.vote1.submission_id) is not None
        assert await uow.challenges.get_vote(seeded_votes.vote2.voter_id, seeded_votes.vote2.challenge_id, seeded_votes.vote2.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote3.voter_id, seeded_votes.vote3.challenge_id, seeded_votes.vote3.submission_id) is None
        assert await uow.challenges.get_vote(seeded_votes.vote4.voter_id, seeded_votes.vote4.challenge_id, seeded_votes.vote4.submission_id) is None

        assert await uow.challenges.get_winner(seeded_users.submission_author1.id,seeded_submissions.submission1.id,seeded_challenge.id) is not None
        assert await uow.challenges.get_winner(seeded_users.submission_author2.id,seeded_submissions.submission2.id, seeded_challenge.id) is not None
        assert await uow.challenges.get_winner(seeded_users.submission_author3.id,seeded_submissions.submission3.id, seeded_challenge.id) is not None

    async def test_cleanup_winners(
            self, uow, seeded_users, seeded_challenge, seeded_submissions, seeded_votes, seeded_winners
    ):
        
        await uow.challenges.cleanup_challenge_data(seeded_submissions.submission_ids, seeded_votes.all, [], seeded_challenge)

        assert await uow.challenges.get_submission(seeded_submissions.submission1.id) is not None
        assert await uow.challenges.get_submission(seeded_submissions.submission2.id) is not None
        assert await uow.challenges.get_submission(seeded_submissions.submission3.id) is not None

        assert await uow.challenges.get_vote(seeded_votes.vote1.voter_id, seeded_votes.vote1.challenge_id, seeded_votes.vote1.submission_id) is not None
        assert await uow.challenges.get_vote(seeded_votes.vote2.voter_id, seeded_votes.vote2.challenge_id, seeded_votes.vote2.submission_id) is not None
        assert await uow.challenges.get_vote(seeded_votes.vote3.voter_id, seeded_votes.vote3.challenge_id, seeded_votes.vote3.submission_id) is not None
        assert await uow.challenges.get_vote(seeded_votes.vote4.voter_id, seeded_votes.vote4.challenge_id, seeded_votes.vote4.submission_id) is not None

        assert await uow.challenges.get_winner(seeded_users.submission_author1.id,seeded_submissions.submission1.id,seeded_challenge.id) is None
        assert await uow.challenges.get_winner(seeded_users.submission_author2.id,seeded_submissions.submission2.id, seeded_challenge.id) is None
        assert await uow.challenges.get_winner(seeded_users.submission_author3.id,seeded_submissions.submission3.id, seeded_challenge.id) is None

    
    async def test_cleanup_partial_winners(
            self, uow, seeded_users, seeded_challenge, seeded_submissions, seeded_votes, seeded_winners
    ):
        
        await uow.challenges.cleanup_challenge_data(seeded_submissions.submission_ids, seeded_votes.all, [seeded_winners.all[0]], seeded_challenge)

        assert await uow.challenges.get_submission(seeded_submissions.submission1.id) is not None
        assert await uow.challenges.get_submission(seeded_submissions.submission2.id) is not None
        assert await uow.challenges.get_submission(seeded_submissions.submission3.id) is not None

        assert await uow.challenges.get_vote(seeded_votes.vote1.voter_id, seeded_votes.vote1.challenge_id, seeded_votes.vote1.submission_id) is not None
        assert await uow.challenges.get_vote(seeded_votes.vote2.voter_id, seeded_votes.vote2.challenge_id, seeded_votes.vote2.submission_id) is not None
        assert await uow.challenges.get_vote(seeded_votes.vote3.voter_id, seeded_votes.vote3.challenge_id, seeded_votes.vote3.submission_id) is not None
        assert await uow.challenges.get_vote(seeded_votes.vote4.voter_id, seeded_votes.vote4.challenge_id, seeded_votes.vote4.submission_id) is not None

        assert await uow.challenges.get_winner(seeded_users.submission_author1.id,seeded_submissions.submission1.id,seeded_challenge.id) is not None
        assert await uow.challenges.get_winner(seeded_users.submission_author2.id,seeded_submissions.submission2.id, seeded_challenge.id) is None
        assert await uow.challenges.get_winner(seeded_users.submission_author3.id,seeded_submissions.submission3.id, seeded_challenge.id) is None



    # MONTHLY CHALLENGES #



    async def test_bulk_insert_monthly_submissions(self, uow, seeded_users, seeded_monthly_challenge):
        submission1 = {
            "id":555,
            "author_id":seeded_users.submission_author1.id,
            "thread_id":111,
            "challenge_id":seeded_monthly_challenge.id,
            "title":"submission1",
            "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}


        submission2 = {
            "id":554,
            "author_id":seeded_users.submission_author2.id,
            "thread_id":111,
            "challenge_id":seeded_monthly_challenge.id,
            "title":"submission2",
            "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}
        
        submission3 = {
            "id":553,
            "author_id":seeded_users.submission_author3.id,
            "thread_id":111,
            "challenge_id":seeded_monthly_challenge.id,
            "title":"submission3",
            "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}
        
        await uow.challenges.bulk_insert_monthly_submissions([submission1, submission2, submission3])

        submission1_db = await uow.challenges.get_monthly_submission(555)
        submission2_db = await uow.challenges.get_monthly_submission(554)
        submission3_db = await uow.challenges.get_monthly_submission(553)

        assert submission1_db.id == 555
        assert submission1_db.title == "submission1"
        assert submission1_db.author_id == seeded_users.submission_author1.id
        assert submission1_db.challenge_id == seeded_monthly_challenge.id
        assert submission1_db.thread_id == 111
        assert submission1_db.created_at == datetime(year=2026, month=3, day=3, tzinfo=UTC)

        assert submission2_db.id == 554
        assert submission2_db.title == "submission2"
        assert submission2_db.author_id == seeded_users.submission_author2.id
        assert submission2_db.challenge_id == seeded_monthly_challenge.id
        assert submission2_db.thread_id == 111
        assert submission2_db.created_at == datetime(year=2026, month=3, day=3, tzinfo=UTC)

        assert submission3_db.id == 553
        assert submission3_db.title == "submission3"
        assert submission3_db.author_id == seeded_users.submission_author3.id
        assert submission3_db.challenge_id == seeded_monthly_challenge.id
        assert submission3_db.thread_id == 111
        assert submission3_db.created_at == datetime(year=2026, month=3, day=3, tzinfo=UTC)



    async def test_bulk_insert_updates_monthly_submissions(
            self, uow, seeded_users, seeded_monthly_challenge, seeded_monthly_submissions
    ):
    

        updated_submission ={
                "id":seeded_monthly_submissions.monthly_submission1.id,
                "author_id":seeded_users.submission_author1.id,
                "thread_id":111,
                "challenge_id":seeded_monthly_challenge.id,
                "title":"updated_title",
                "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}


        await uow.challenges.bulk_insert_monthly_submissions([updated_submission])

        submission = await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission1.id)

        assert submission.title == "updated_title"


    async def test_cleanup_monthly_submissions(
            self, uow, seeded_users, seeded_monthly_challenge, seeded_monthly_submissions
    ):
        #deleting all submissions
        await uow.challenges.cleanup_monthly_submissions(challenge=seeded_monthly_challenge, thread_id=111, submission_ids=[])
        


        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission0.id) is None
        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission1.id) is None
        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission2.id) is None

        # assert unrelated submissions (different thread_ids) are not affected
        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission3.id) is not None
        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission4.id) is not None
        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission5.id) is not None
    

    async def test_cleanup_partial_monthly_submissions(
            self, uow, seeded_users, seeded_monthly_challenge, seeded_monthly_submissions
    ):
        #keep only submission1, rest should cascade
        await uow.challenges.cleanup_monthly_submissions(challenge=seeded_monthly_challenge, thread_id=111, submission_ids=[seeded_monthly_submissions.monthly_submission0.id])
        


        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission0.id) is not None
        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission1.id) is None
        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission2.id) is None


        # assert unrelated submissions (different thread_ids) are not affected
        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission3.id) is not None
        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission4.id) is not None
        assert await uow.challenges.get_monthly_submission(seeded_monthly_submissions.monthly_submission5.id) is not None