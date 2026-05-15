from datetime import UTC, datetime, timedelta



class TestLeaderboardRepository:

    async def test_get_feedback_leaderboard_returns_correct_data(
        self, uow, seeded_feedbacks
    ):

        data = await uow.leaderboards.get_feedback_leaderboard()

        assert data.leaderboard_length == 3
        assert data.server_total_feedback == seeded_feedbacks.total_feedbacks
        assert data.server_total_tracks == 3
        assert data.server_total_fb_words == seeded_feedbacks.total_feedback_words

        user, feedback_stats = data.data[0]
        assert user.id == seeded_feedbacks.author_most_feedback_sent.id
        assert feedback_stats["total_feedbacks_given"] == 3
        assert feedback_stats["total_feedback_words"] == 17

    async def test_get_feedback_leaderboard_empty(self, uow):
        data = await uow.leaderboards.get_feedback_leaderboard()

        assert data.leaderboard_length == 0
        assert data.server_total_feedback == 0
        assert data.data == []

    async def test_get_daily_server_activity_data(self, uow, seeded_activity_feedbacks, seeded_activity_tracks):
        from datetime import timezone
        yesterday = datetime.now(tz=UTC) - timedelta(days=1)
        tracks = await seeded_activity_tracks(yesterday)
        feedbacks = await seeded_activity_feedbacks(yesterday)

        data = await uow.leaderboards.get_server_activity_data(date=yesterday)

        assert data.feedback_count == feedbacks.total_feedbacks
        assert data.track_count == tracks.total_tracks

    async def test_get_weekly_server_activity_data(self, uow, seeded_activity_feedbacks, seeded_activity_tracks):
        from datetime import timezone
        last_week = datetime.now(tz=UTC) - timedelta(days=7)
        tracks = await seeded_activity_tracks(last_week)
        feedbacks = await seeded_activity_feedbacks(last_week)

        data = await uow.leaderboards.get_server_activity_data(date=last_week)

        assert data.feedback_count == feedbacks.total_feedbacks
        assert data.track_count == tracks.total_tracks

    async def test_get_monthly_server_activity_data(self, uow, seeded_activity_feedbacks, seeded_activity_tracks):
        from datetime import timezone
        last_month = datetime.now(tz=UTC) - timedelta(days=30)
        tracks = await seeded_activity_tracks(last_month)
        feedbacks = await seeded_activity_feedbacks(last_month)

        data = await uow.leaderboards.get_server_activity_data(date=last_month)

        assert data.feedback_count == feedbacks.total_feedbacks
        assert data.track_count == tracks.total_tracks

    async def test_lb_message_id_insert_and_get(self, uow):
        await uow.leaderboards.insert_lb_message_id(99999, "test_type")
        stored = await uow.leaderboards.get_lb_message_id("test_type")
        assert stored == 99999

    async def test_lb_message_id_update(self, uow):
        await uow.leaderboards.insert_lb_message_id(99999, "test_type")
        await uow.leaderboards.insert_lb_message_id(88888, "test_type")

        stored = await uow.leaderboards.get_lb_message_id("test_type")
        assert stored == 88888


    async def test_submission_lb_returns_correct_data(
            self, uow, seeded_challenge, seeded_users, make_submission, make_challenge
    ):
        second_challenge = await make_challenge(id=10001)
        await make_submission(12345, seeded_users.submission_author1.id, 
                         seeded_challenge.id, 111, "sub1", datetime.now(tz=UTC))
        await make_submission(123456, seeded_users.submission_author1.id,
                            second_challenge.id, 111, "sub2", datetime.now(tz=UTC))
        data = await uow.leaderboards.get_submissions_leaderboard()

        

        user, total_submission = data.data[0]

        assert data.server_total_submissions == 2
        assert data.server_total_challenges == 2
        assert user.id == seeded_users.submission_author1.id
        assert total_submission == 2

    async def test_submission_lb_returns_empty(
            self, uow
    ):
        data = await uow.leaderboards.get_submissions_leaderboard()

        assert data.server_total_submissions == 0
        assert data.server_total_challenges == 0
        assert data.data == []

    async def test_get_all_time_winners_lb_returns_correct_data(
            self, uow, seeded_users, seeded_submissions, seeded_winners, make_challenge, make_submission
    ):
        new_challenge = await make_challenge(10001)
        new_submission = await make_submission(12345678, seeded_users.submission_author1.id, 
                         new_challenge.id, 111, "sub1", datetime.now(tz=UTC))
        
        await uow.challenges.set_winner(seeded_users.submission_author1.id, new_submission.id, new_challenge.id)
        data = await uow.leaderboards.get_all_time_challenge_leaderboard()

        assert data.server_total_winners == 3
        user, total_wins = data.data[0]

        assert user.id == 999
        assert total_wins == 2

    async def test_get_all_time_winners_lb_returns_empty(
            self, uow
    ):
        data = await uow.leaderboards.get_all_time_challenge_leaderboard()

        assert data.server_total_winners == 0


    async def test_most_active_time_periods_returns_correct_data(
            self, uow, seeded_users, most_active_periods_data, test_config
    ):
        data = await uow.leaderboards.get_most_active_periods(admin_id=test_config.admin_id)
        periods_data, most_active_member_data = data
        most_active_day_data = periods_data["day"]
        most_active_week_data = periods_data["week"]
        most_active_month_data = periods_data["month"]


        assert most_active_member_data.user.id == seeded_users.track_author1.id
        assert most_active_member_data.total_feedback == 0
        assert most_active_member_data.total_tracks == 4

        assert most_active_day_data.date == datetime(year=2026, month=1, day=5, tzinfo=UTC)
        assert most_active_day_data.total_feedback == 4
        assert most_active_day_data.total_track == 3
        assert most_active_day_data.total == 7


        assert most_active_week_data.date == datetime(year=2026, month=1, day=5, tzinfo=UTC)
        assert most_active_week_data.total_feedback == 5
        assert most_active_week_data.total_track == 4
        assert most_active_week_data.total == 9

        assert most_active_month_data.date == datetime(year=2026, month=1, day=1, tzinfo=UTC)
        assert most_active_month_data.total_feedback == 5
        assert most_active_month_data.total_track == 4
        assert most_active_month_data.total == 9


    async def test_most_active_time_periods_return_empty(
            self, uow, test_config
    ):
        data = await uow.leaderboards.get_most_active_periods(admin_id=test_config.admin_id)
        assert data is None


        

    async def test_get_feedback_role_users(
            self, uow,  seeded_users, seeded_feedbacks, make_user
    ):
        
        users = await uow.leaderboards.get_feedback_role_users()
        user_ids = [user.id for user in users]

        assert seeded_users.fb_author1.id in user_ids
        assert seeded_users.fb_author2.id in user_ids
        assert seeded_users.fb_author3.id in user_ids


        #author users aer only submission&track authors and never feedback givers or voters so assert they are not in the list
        assert seeded_users.track_author1.id not in user_ids
        assert seeded_users.track_author2.id not in user_ids
        assert seeded_users.track_author3.id not in user_ids


    async def test_get_challenge_role_users(
            self, uow, seeded_users, seeded_submissions
    ):
        

        users = await uow.leaderboards.get_challenge_role_users()
        user_ids = [user.id for user in users]

        assert seeded_users.submission_author1.id in user_ids
        assert seeded_users.submission_author2.id in user_ids
        assert seeded_users.submission_author3.id in user_ids


        #support users aer only feedback authors and never submission & track authors so assert they are not in the list
        assert seeded_users.fb_author1.id not in user_ids
        assert seeded_users.fb_author2.id not in user_ids
        assert seeded_users.fb_author3.id not in user_ids

    async def test_get_feedback_role_users_excludes_zero_feedback_users(
        self, uow, make_user
    ):
        
        await make_user(user_id=999, username="u", display_name="U",
                        total_feedbacks_given=0)

        users = await uow.leaderboards.get_feedback_role_users()
        assert users == []

    async def test_get_challenge_role_users_excludes_zero_feedback_users(
        self, uow, make_user
    ):
        
        
        await make_user(user_id=999, username="u", display_name="U",
                        total_submissions=0)

        users = await uow.leaderboards.get_challenge_role_users()
        assert users == []




    async def test_more_than_10_users_submissions_leaderboard(self, uow, seeded_challenge, update_total_submissions):
        data = await uow.leaderboards.get_submissions_leaderboard()

        for user_submission in data.data:
            user, total_submission = user_submission


        assert len(data.data) == 10

    async def test_more_than_10_users_feedback_leaderboard(self, uow, seeded_challenge, update_total_feedbacks):
        data = await uow.leaderboards.get_feedback_leaderboard()

        for user_feedback in data.data:
            user, total_feedback = user_feedback


        assert len(data.data) == 10

    async def test_more_than_10_users_all_time_challenge_leaderboard(self, uow, seeded_challenge, update_total_challenges_won):
        data = await uow.leaderboards.get_all_time_challenge_leaderboard()

        for user_wins in data.data:
            user, total_wins = user_wins


        assert len(data.data) == 10