from datetime import UTC, datetime
from bot.types.common import UserData



class TestUserRepository:
    
    async def test_get_by_id(
            self, uow, seeded_users
    ):
        user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert user.id == seeded_users.submission_author1.id

    async def test_get_all_ids(
        self, uow, seeded_users
    ):
        all_ids = await uow.users.get_all_ids()

        assert all_ids == set(seeded_users.all_ids)

    async def test_exists(
            self, uow, seeded_users
    ):
        assert await uow.users.exists(seeded_users.submission_author1.id) == True
        assert await uow.users.exists(123213432) == False

    async def test_update(
            self, uow, seeded_users
    ):
        updated = {
            "is_purge_data":False,
            "username":"updated_username"
        }

        await uow.users.update(user_id=seeded_users.submission_author1.id, data=updated)

        user = await uow.users.get_by_id(seeded_users.submission_author1.id)

        assert user.is_purge_data == False
        assert user.username == "updated_username"

    async def test_bulk_insert(
            self, uow
    ):
        user1_data = {
            "id":999,
            "username":"username1",
            "display_name":"display_name1",
            "is_purge_data":True
            }
        
        user2_data = {
            "id":998,
            "username":"username2",
            "display_name":"display_name2",
            "is_purge_data":False
            }
        
        user3_data = {
            "id":997,
            "username":"username3",
            "display_name":"display_name3",
            "is_purge_data":True
            }
        
        users = [user1_data, user2_data, user3_data]

        await uow.users.bulk_insert_users(users)

        user1 = await uow.users.get_by_id(999)

        assert user1.id == 999
        assert user1.username == "username1"
        assert user1.display_name == "display_name1"
        assert user1.is_purge_data == True

        user2 = await uow.users.get_by_id(998)

        assert user2.id == 998
        assert user2.username == "username2"
        assert user2.display_name == "display_name2"
        assert user2.is_purge_data == False

        user3 = await uow.users.get_by_id(997)

        assert user3.id == 997
        assert user3.username == "username3"
        assert user3.display_name == "display_name3"
        assert user3.is_purge_data == True


    async def test_create(
            self, uow
    ):
        user_data = UserData(
            id=999,
            username="username",
            display_name="display_name",
            is_purge_data=True
        )

        await uow.users.create(user_data)
        
        user = await uow.users.get_by_id(999)
        assert user.id == 999
        assert user.username == "username"
        assert user.display_name == "display_name"
        assert user.is_purge_data == True


    async def test_bulk_upsert(
            self, uow, seeded_users
    ):
        updated1 = {
            "id":seeded_users.submission_author1.id,
            "username":"updated_username1",
            "display_name":"updated_display_name1",
            "is_purge_data":False
            }
        
        updated2 = {
            "id":seeded_users.submission_author2.id,
            "username":"updated_username2",
            "display_name":"updated_display_name2",
            "is_purge_data":True
            }
        
        updated3 = {
            "id":seeded_users.submission_author3.id,
            "username":"updated_username3",
            "display_name":"updated_display_name3",
            "is_purge_data":True
            }
        
        updated_users = [updated1, updated2, updated3]
        
        await uow.users.bulk_upsert(updated_users)

        user1 = await uow.users.get_by_id(seeded_users.submission_author1.id)
        assert user1.username == "updated_username1"
        assert user1.display_name == "updated_display_name1"
        assert user1.is_purge_data == False

        user2 = await uow.users.get_by_id(seeded_users.submission_author2.id)
        assert user2.username == "updated_username2"
        assert user2.display_name == "updated_display_name2"
        assert user2.is_purge_data == True

        user3 = await uow.users.get_by_id(seeded_users.submission_author3.id)
        assert user3.username == "updated_username3"
        assert user3.display_name == "updated_display_name3"
        assert user3.is_purge_data == True


    async def test_delete(
            self, uow, seeded_users
    ):
        await uow.users.delete(seeded_users.submission_author1.id)
        
        assert await uow.users.get_by_id(seeded_users.submission_author1.id) is None

    async def test_delete_user_feedback_cascade(
            self,uow, seeded_users, seeded_feedbacks
    ):
        await uow.users.delete(seeded_users.fb_author1.id)

        feedbacks = seeded_feedbacks.get_feedbacks_of_user(seeded_users.fb_author1.id)

        for feedback in feedbacks:
            assert await uow.feedback.exists(feedback.id) == False

    
    async def test_delete_user_track_cascade(
            self,uow, seeded_users, seeded_tracks
    ):
        await uow.users.delete(seeded_users.track_author1.id)

        tracks = seeded_tracks.get_tracks_of_user(seeded_users.track_author1.id)

        for track in tracks:
            assert await uow.tracks.exists(track.id) == False

    async def test_delete_user_submission_cascade(
            self,uow, seeded_users, seeded_submissions
    ):
        await uow.users.delete(seeded_users.submission_author1.id)

        submissions = seeded_submissions.get_submissions_of_user(seeded_users.submission_author1.id)

        for submission in submissions:
            assert await uow.challenges.get_submission(submission.id) is None


    async def test_delete_user_vote_cascade(
            self,uow, seeded_users, seeded_votes
    ):
        await uow.users.delete(seeded_users.voter1.id)

        votes = seeded_votes.get_votes_of_user(seeded_users.voter1.id)

        for vote in votes:
            assert await uow.challenges.get_vote(vote.voter_id, vote.challenge_id, vote.submission_id) is None


    async def test_delete_user_winner_cascade(
            self,uow, seeded_users, seeded_winners
    ):
        await uow.users.delete(seeded_users.submission_author1.id)

        wins = seeded_winners.get_wins_of_user(seeded_users.submission_author1.id)

        for win in wins:
            assert await uow.challenges.get_winner(win.winner_id, win.submission_id, win.challenge_id) is None


    async def test_get_for_challenge_roles(
            self, uow, seeded_users, seeded_submissions
    ):
        users = await uow.users.get_for_challenge_roles()
        user_ids = [user.id for user in users]

        assert seeded_users.submission_author1.id in user_ids
        assert seeded_users.submission_author2.id in user_ids
        assert seeded_users.submission_author3.id in user_ids
        assert len(user_ids) == 3

    
    async def test_get_for_feedback_roles(
            self, uow, seeded_users, seeded_feedbacks
    ):
        users = await uow.users.get_for_feedback_roles()
        user_ids = [user.id for user in users]

        assert seeded_users.fb_author1.id in user_ids
        assert seeded_users.fb_author2.id in user_ids
        assert seeded_users.fb_author3.id in user_ids
        assert len(user_ids) == 3


    async def test_cleanup_users_no_cleanup(
            self, uow, seeded_users_to_delete
    ):
        await uow.users.cleanup_users({
            seeded_users_to_delete.user1.id,
            seeded_users_to_delete.user2.id,
            seeded_users_to_delete.user3.id},
            None, None)
        
        assert await uow.users.exists(seeded_users_to_delete.user1.id) == True
        assert await uow.users.exists(seeded_users_to_delete.user2.id) == True
        assert await uow.users.exists(seeded_users_to_delete.user3.id) == True

    async def test_cleanup_users_clean_all(
            self, uow, seeded_users_to_delete
    ):
        await uow.users.cleanup_users({},
            None, None)
        
        assert await uow.users.exists(seeded_users_to_delete.user1.id) == False
        assert await uow.users.exists(seeded_users_to_delete.user2.id) == False
        assert await uow.users.exists(seeded_users_to_delete.user3.id) == False

    async def test_cleanup_users_clean_after(
            self, uow, seeded_users_to_delete
    ):
        await uow.users.cleanup_users({},
            None, datetime(year=2026, month=1, day=4, tzinfo=UTC))
        
        assert await uow.users.exists(seeded_users_to_delete.user1.id) == True
        assert await uow.users.exists(seeded_users_to_delete.user2.id) == True
        assert await uow.users.exists(seeded_users_to_delete.user3.id) == False

    async def test_cleanup_users_clean_before(
            self, uow, seeded_users_to_delete
    ):
        await uow.users.cleanup_users({},
            datetime(year=2026, month=1, day=4, tzinfo=UTC), None)
        
        assert await uow.users.exists(seeded_users_to_delete.user1.id) == False
        assert await uow.users.exists(seeded_users_to_delete.user2.id) == False
        assert await uow.users.exists(seeded_users_to_delete.user3.id) == True