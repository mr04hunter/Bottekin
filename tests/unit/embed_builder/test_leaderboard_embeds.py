from datetime import datetime, UTC
import pytest
from bot.types.leaderboards.database_layer import MostActivePeriodData, ServerActivityData
from bot.views.embed_builder import EmbedBuilder
from unittest.mock import MagicMock
from bot.types.leaderboards.presentation import (
    FeedbackLeaderboardDisplay, ChallengeLeaderboardDisplay,
    AllTimeChallengeLeaderboardDisplay, MostActiveMemberDisplay, ServerActivityDisplay, SubmissionLeaderboardDisplay,
    MostActivePeriodDisplay)
import math

class TestLeaderboardEmbedBuilder:
    @pytest.fixture
    def builder(self):
        return EmbedBuilder()
    

    def test_challenge_embed(self, builder):
        leaderboard_data = [
            ("member1", MagicMock(total_votes=10)),
            ("member2", MagicMock(total_votes=9)),
            ("member3", MagicMock(total_votes=8)),
            ("member4", MagicMock(total_votes=7)),
            ("member5", MagicMock(total_votes=6)),
            ("member6", MagicMock(total_votes=5)),
            ("member7", MagicMock(total_votes=4)),
            ("member8", MagicMock(total_votes=3)),
            ("member9", MagicMock(total_votes=2)),
            ("member10", MagicMock(total_votes=1))
        ]
        data = ChallengeLeaderboardDisplay(
            data=leaderboard_data, #type: ignore
            server_total_votes=45,
            server_total_submissions=6,
            challenge_title="test_challenge_title"

        )

        embed = builder.create_challenge_leaderboard_embed(leaderboard_data=data)

        assert embed is not None

        embed_data = embed.to_dict()

        title = embed_data.get("title")

        description = embed_data.get("description")

        assert "TEST_CHALLENGE_TITLE" in title

        assert str(data.server_total_submissions) in description
        assert str(data.server_total_votes) in description

        fields = embed_data.get("fields")


        assert len(fields) == 1

        leaderboard_field = fields[0]
        leaderboard_val = leaderboard_field.get("value")

        assert f":first_place: member1 total votes received: **10**" in leaderboard_val
        assert f":second_place: member2 total votes received: **9**" in leaderboard_val
        assert f":third_place: member3 total votes received: **8**" in leaderboard_val
        assert f":four: member4 total votes received: **7**" in leaderboard_val
        assert f":five: member5 total votes received: **6**" in leaderboard_val
        assert f":six: member6 total votes received: **5**" in leaderboard_val
        assert f":seven: member7 total votes received: **4**" in leaderboard_val
        assert f":eight: member8 total votes received: **3**" in leaderboard_val
        assert f":nine: member9 total votes received: **2**" in leaderboard_val
        assert f":number_10: member10 total votes received: **1**" in leaderboard_val



    def test_challenge_embed_empty_data(self, builder):
        
        data = ChallengeLeaderboardDisplay(
            data=[], #type: ignore
            server_total_votes=45,
            server_total_submissions=6,
            challenge_title="test_challenge_title"

        )

        embed = builder.create_challenge_leaderboard_embed(leaderboard_data=data)

        assert embed is not None

        embed_data = embed.to_dict()

        title = embed_data.get("title")

        description = embed_data.get("description")

        assert "TEST_CHALLENGE_TITLE" in title

        assert str(data.server_total_submissions) in description
        assert str(data.server_total_votes) in description

        fields = embed_data.get("fields")

        leaderboard_field = fields[0]

        leaderboard_val = leaderboard_field.get("value")

        assert leaderboard_val == "\nNot enough data yet\nA leaderboard will be displayed here!"


        
        
    def test_all_time_challenges_won_leaderboard(self, builder):
        data = [
            ("member1", 10),
            ("member2", 9),
            ("member3", 8),
            ("member4", 7),
            ("member5", 6),
            ("member6", 5),
            ("member7", 4),
            ("member8", 3),
            ("member9", 2),
            ("member10", 1),

        ]

        data = AllTimeChallengeLeaderboardDisplay(
            data=data,
            server_total_winners=10,
            leaderboard_length=10
        )

        embed = builder.create_all_time_challenges_won_leaderboards(leaderboard_data=data)

        embed_data = embed.to_dict()

        title = embed_data.get("title")
        description = embed_data.get("description")

        assert title == "**WINNERS LEADERBOARD**"

        assert str(data.server_total_winners) in description

        fields = embed_data.get("fields")

        leaderboard_field = fields[0]

        leaderboard_val = leaderboard_field.get("value")

        assert f":first_place: member1\nTotal wins: **10**" in leaderboard_val
        assert f":second_place: member2\nTotal wins: **9**" in leaderboard_val
        assert f":third_place: member3\nTotal wins: **8**" in leaderboard_val
        assert f":four: member4\nTotal wins: **7**" in leaderboard_val
        assert f":five: member5\nTotal wins: **6**" in leaderboard_val
        assert f":six: member6\nTotal wins: **5**" in leaderboard_val
        assert f":seven: member7\nTotal wins: **4**" in leaderboard_val
        assert f":eight: member8\nTotal wins: **3**" in leaderboard_val
        assert f":nine: member9\nTotal wins: **2**" in leaderboard_val
        assert f":number_10: member10\nTotal wins: **1**" in leaderboard_val


    def test_all_time_challenges_won_leaderboard_empty_data(self, builder):
        data = []

        data = AllTimeChallengeLeaderboardDisplay(
            data=data,
            server_total_winners=10,
            leaderboard_length=10
        )

        embed = builder.create_all_time_challenges_won_leaderboards(leaderboard_data=data)

        embed_data = embed.to_dict()

        title = embed_data.get("title")
        description = embed_data.get("description")

        assert title == "**WINNERS LEADERBOARD**"

        assert str(data.server_total_winners) in description

        fields = embed_data.get("fields")

        leaderboard_field = fields[0]

        leaderboard_val = leaderboard_field.get("value")

        assert leaderboard_val == "\nNot enough data yet\nA leaderboard will be displayed here!"

 

    def test_all_time_submissions_leaderboard(self, builder):
        
        leaderboard_data = [
            ("member1", 10),
            ("member2", 9),
            ("member3", 8),
            ("member4", 7),
            ("member5", 6),
            ("member6", 5),
            ("member7", 4),
            ("member8", 3),
            ("member9", 2),
            ("member10", 1),

        ]

        data = SubmissionLeaderboardDisplay(
            data=leaderboard_data,
            total_submissions=55,
            leaderboard_length=10,
            server_total_challenges=55,
            server_total_submissions=55
        )

        embed = builder.create_all_time_submissions_leaderboards(leaderboard_data=data)

        embed_data = embed.to_dict()

        title = embed_data.get("title")
        description = embed_data.get("description")

        assert title == "**MOST ACTIVE CHALLENGERS**"

        assert str(data.server_total_challenges) in description
        assert str(data.server_total_submissions) in description

        fields = embed_data.get("fields")

        leaderboard_field = fields[0]

        leaderboard_val = leaderboard_field.get("value")

        assert f":first_place: member1\nTotal submissions: **10**" in leaderboard_val
        assert f":second_place: member2\nTotal submissions: **9**" in leaderboard_val
        assert f":third_place: member3\nTotal submissions: **8**" in leaderboard_val
        assert f":four: member4\nTotal submissions: **7**" in leaderboard_val
        assert f":five: member5\nTotal submissions: **6**" in leaderboard_val
        assert f":six: member6\nTotal submissions: **5**" in leaderboard_val
        assert f":seven: member7\nTotal submissions: **4**" in leaderboard_val
        assert f":eight: member8\nTotal submissions: **3**" in leaderboard_val
        assert f":nine: member9\nTotal submissions: **2**" in leaderboard_val
        assert f":number_10: member10\nTotal submissions: **1**" in leaderboard_val


    def test_all_time_submissions_leaderboard_empty_data(self, builder):
        
        leaderboard_data = []

        data = SubmissionLeaderboardDisplay(
            data=leaderboard_data,
            total_submissions=0,
            leaderboard_length=0,
            server_total_challenges=0,
            server_total_submissions=0
        )

        embed = builder.create_all_time_submissions_leaderboards(leaderboard_data=data)

        embed_data = embed.to_dict()

        title = embed_data.get("title")
        description = embed_data.get("description")

        assert title == "**MOST ACTIVE CHALLENGERS**"

        assert str(data.server_total_challenges) in description
        assert str(data.server_total_submissions) in description

        fields = embed_data.get("fields")

        leaderboard_field = fields[0]

        leaderboard_val = leaderboard_field.get("value")

        assert leaderboard_val == "\nNot enough data yet\nA leaderboard will be displayed here!"

    
    def test_feedback_leaderboard(self, builder):
        leaderboard_data = [
            ("member1", {
                "total_feedbacks_given":10,
                "total_feedback_words":100,
                "total_feedbacked_authors":10
            }),

            ("member2", {
                "total_feedbacks_given":9,
                "total_feedback_words":99,
                "total_feedbacked_authors":9
            }),

            ("member3", {
                "total_feedbacks_given":8,
                "total_feedback_words":88,
                "total_feedbacked_authors":8
            }),

            ("member4", {
                "total_feedbacks_given":7,
                "total_feedback_words":77,
                "total_feedbacked_authors":7
            }),

            ("member5", {
                "total_feedbacks_given":6,
                "total_feedback_words":66,
                "total_feedbacked_authors":6
            }),

            ("member6", {
                "total_feedbacks_given":5,
                "total_feedback_words":55,
                "total_feedbacked_authors":5
            }),

            ("member7", {
                "total_feedbacks_given":4,
                "total_feedback_words":44,
                "total_feedbacked_authors":4
            }),

            ("member8", {
                "total_feedbacks_given":3,
                "total_feedback_words":33,
                "total_feedbacked_authors":3
            }),

            ("member9", {
                "total_feedbacks_given":2,
                "total_feedback_words":22,
                "total_feedbacked_authors":2
            }),

            ("member10", {
                "total_feedbacks_given":1,
                "total_feedback_words":11,
                "total_feedbacked_authors":1
            })
        ]

        data = FeedbackLeaderboardDisplay(
            data=leaderboard_data,
            leaderboard_length=10,
            server_total_feedback=55,
            server_total_fb_words=595,
            server_total_tracks=20
        )
        embed = builder.create_feedback_leaderboard(leaderboard_data=data)

        embed_data = embed.to_dict()

        title = embed_data.get("title")
        description = embed_data.get("description")

        assert title == "**FEEDBACK LEADERBOARD**"

        assert str(data.server_total_fb_words) in description
        assert str(data.server_total_feedback) in description
        assert str(data.server_total_tracks) in description

        fields = embed_data.get("fields")

        leaderboard_field = fields[0]

        leaderboard_val = leaderboard_field.get("value")

        assert f":first_place: member1\nTotal feedback: **10**\nTotal words: **100**\nGave feedback to **10**" in leaderboard_val
        assert f":second_place: member2\nTotal feedback: **9**\nTotal words: **99**\nGave feedback to **9**" in leaderboard_val
        assert f":third_place: member3\nTotal feedback: **8**\nTotal words: **88**\nGave feedback to **8**" in leaderboard_val
        assert f":four: member4\nTotal feedback: **7**\nTotal words: **77**\nGave feedback to **7**" in leaderboard_val
        assert f":five: member5\nTotal feedback: **6**\nTotal words: **66**\nGave feedback to **6**" in leaderboard_val
        assert f":six: member6\nTotal feedback: **5**\nTotal words: **55**\nGave feedback to **5**" in leaderboard_val
        assert f":seven: member7\nTotal feedback: **4**\nTotal words: **44**\nGave feedback to **4**" in leaderboard_val
        assert f":eight: member8\nTotal feedback: **3**\nTotal words: **33**\nGave feedback to **3**" in leaderboard_val
        assert f":nine: member9\nTotal feedback: **2**\nTotal words: **22**\nGave feedback to **2**" in leaderboard_val
        assert f":number_10: member10\nTotal feedback: **1**\nTotal words: **11**\nGave feedback to **1**" in leaderboard_val


    def test_feedback_leaderboard_empty_data(self, builder):
        leaderboard_data = []

        data = FeedbackLeaderboardDisplay(
            data=leaderboard_data,
            leaderboard_length=0,
            server_total_feedback=0,
            server_total_fb_words=0,
            server_total_tracks=0
        )
        embed = builder.create_feedback_leaderboard(leaderboard_data=data)

        embed_data = embed.to_dict()

        title = embed_data.get("title")
        description = embed_data.get("description")

        assert title == "**FEEDBACK LEADERBOARD**"

        assert str(data.server_total_fb_words) in description
        assert str(data.server_total_feedback) in description
        assert str(data.server_total_tracks) in description

        fields = embed_data.get("fields")

        leaderboard_field = fields[0]

        leaderboard_val = leaderboard_field.get("value")

        assert leaderboard_val == "\nNot enough data yet\nA leaderboard will be displayed here!"


    def test_server_activity_board(self, builder):
        today_activity = ServerActivityData(
            track_count=10, feedback_count=10
        )
        week_activity = ServerActivityData(
            track_count=9, feedback_count=9
        )
        month_activity = ServerActivityData(
            track_count=8, feedback_count=8
        )

        leaderboard_data = ServerActivityDisplay(
            today_activity=today_activity,
            week_activity=week_activity,
            month_activity=month_activity
        )

        embed = builder.create_server_activity_board(activity_data=leaderboard_data)

        embed_data = embed.to_dict()

        title = embed_data.get("title")
        description = embed_data.get("description")

        assert title == "**SERVER ACTIVITY**"
        assert description == "Daily/Weekly/monthly server activity"

        fields = embed_data.get("fields")

        daily_field, weekly_field, monthly_field = fields

        daily_val = daily_field.get("value")
        weekly_val = weekly_field.get("value")
        monthly_val = monthly_field.get("value")

        assert str(leaderboard_data.today_activity.feedback_count) in daily_val
        assert str(leaderboard_data.today_activity.track_count) in daily_val

        assert str(leaderboard_data.week_activity.feedback_count) in weekly_val
        assert str(leaderboard_data.week_activity.track_count) in weekly_val

        assert str(leaderboard_data.month_activity.feedback_count) in monthly_val
        assert str(leaderboard_data.month_activity.track_count) in monthly_val



    def test_most_active_periods_board(self, builder):
        day = MostActivePeriodData(
            date=datetime(year=2026, month=2, day=1, tzinfo=UTC),
            total_feedback=30, total_track=30, total=60
        )

        week = MostActivePeriodData(
            date=datetime(year=2026, month=1, day=15, tzinfo=UTC),
            total_feedback=30, total_track=30, total=60
        )

        month = MostActivePeriodData(
            date=datetime(year=2026, month=1, day=1, tzinfo=UTC),
            total_feedback=30, total_track=30, total=60
        )

        leaderboard_data = MostActivePeriodDisplay(
            day=day, week=week, month=month

        )

        most_active_member_data = MostActiveMemberDisplay(member="test_most_active_member", total_feedback=12, total_tracks=15)

        embed = builder.create_most_active_periods_board(activity_data=leaderboard_data, most_active_member_data=most_active_member_data)

        embed_data = embed.to_dict()

        title = embed_data.get("title")
        description = embed_data.get("description")

        assert title == "**MOST ACTIVE TIME PERIODS**"
        assert description == "Most active day/week/month"

        fields = embed_data.get("fields")
        
        day_field, week_field, month_field, most_active_member_field = fields

        day_val = day_field.get("value")
        week_val = week_field.get("value")
        month_val = month_field.get("value")
        most_active_member_val = most_active_member_field.get("value")

        assert day.date.strftime("%Y/%m/%d") in day_val
        assert str(day.total_track) in day_val
        assert str(day.total_feedback) in day_val
        assert str(day.total) in day_val

        assert str(math.ceil(week.date.day/7)) in week_val
        assert str(week.total_track) in week_val
        assert str(week.total_feedback) in week_val
        assert str(week.total) in week_val

        assert month.date.strftime("%Y %B") in month_val
        assert str(month.total_track) in month_val
        assert str(month.total_feedback) in month_val
        assert str(month.total) in month_val

        assert most_active_member_data.member in most_active_member_val
        assert str(most_active_member_data.total_feedback) in most_active_member_val
        assert str(most_active_member_data.total_tracks) in most_active_member_val
        assert str(most_active_member_data.total_feedback+most_active_member_data.total_tracks) in most_active_member_val