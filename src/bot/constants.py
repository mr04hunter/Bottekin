from typing import Mapping
from discord import Object




FB_SYNC_DATA = "fb_sync_data"
CHALLENGE_SYNC_DATA = "challenge_sync_data"
SYNC_LATEST_CHALLENGE = "lates_challenge"
SET_PAST_WINNERS = "set_past_winners"

SERVER_ACTIVITY_LEADERBOARD_TYPE = "server_activity_leaderboard_type"
MOST_ACTIVE_PERIODS_BOARD_TYPE = "most_active_periods_board_type"
SUBMISSIONS_LEADERBOARD_TYPE = "all_time_submissions_leaderboard"
FEEDBACK_LEADERBOARD_TYPE = "all_time_feedback_leaderboard"
ALL_TIME_CHALLENGE_WON_LEADERBOARD_TYPE = "all_time_challenge_won_leaderboard"
CURRENT_CHALLENGE_LEADERBOARD_TYPE = "current_challenge_leaderboard"


STATS = [
            "total_challenges_won", "total_submissions",
            "total_feedbacks_given", "total_feedbacks_received"]


BASE_IMAGE_URL = "https://raw.githubusercontent.com/mr04hunter/bot-assets/refs/heads/main/images/"

MUSIC_STATS_THUMBNAIL_URL = BASE_IMAGE_URL+"music_stats.png"
FEEDBACK_STATS_THUMBNAIL_URL = BASE_IMAGE_URL+"feedback_stats.png"
CHALLENGE_STATS_THUMBNAIL_URL = BASE_IMAGE_URL+"challenge_stats.png"


SUBMISSIONS_LEADERBOARD_THUMBNAIL_URL= BASE_IMAGE_URL+"leaderboard_challengers.png"
FEEDBACK_LEADERBOARD_THUMBNAIL_URL= BASE_IMAGE_URL+"leaderboard_feedback.png"

GENERIC_LEADERBOARD_THUMBNAIL_URL = BASE_IMAGE_URL+"leaderboard_winners.png"
ALL_TIME_CHALLENGES_LEADERBOARD_THUMBNAIL_URL = BASE_IMAGE_URL+"leaderboard_winners.png"


MIQ_RATE_LIMIT_USAGE="miq:usage:"
STATS_RATE_LIMIT_USAGE="stats:usage:"

MIQ_RATE_LIMIT_LIMITED = "miq:limited:"
STATS_RATE_LIMIT_LIMITED = "stats:limited:"


get_winners_job_id = "get_winners_job_id"
challenge_update_data_job_id = "update_challenge_data_id"
get_last_challenge_job_id = "get_last_challenge_job_id"
end_challenge_job_id = "terminate_challenge_id"
end_monthly_challenge_job_id = "terminate_monthly_challenge_id"
end_voting_job_id = "end_voting_job_id"
update_most_active_periods_job_id = "most_active_periods_id"



PERIOD_MAP: Mapping[str, dict] = {
            "this_week":     dict(trunc_by="day",   date_type="week",  limit=1),
            "this_month":    dict(trunc_by="day",   date_type="month", limit=1),
            "last_3_months": dict(trunc_by="month", date_type="month", limit=3),
            "last_6_months": dict(trunc_by="month", date_type="month", limit=6),
            "last_12_months":dict(trunc_by="month", date_type="month", limit=12),
            "last_4_weeks":  dict(trunc_by="week",  date_type="week",  limit=4),
            "last_8_weeks":  dict(trunc_by="week",  date_type="week",  limit=8),
        }


MONTH_MAP = {
        "January":"Jan",
        "February":"Feb",
        "March":"Mar",
        "April":"Apr",
        "May":"May",
        "June":"June",
        "July":"July",
        "August":"Aug",
        "September":"Sept",
        "October":"Oct",
        "November":"Nov",
        "December":"Dec"
        }