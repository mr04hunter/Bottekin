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
            "total_feedbacks_given", "total_feedbacks_received",
            "total_feedback_words"]


BASE_IMAGE_URL = "https://raw.githubusercontent.com/mr04hunter/bot-assets/refs/heads/main/images/"

MUSIC_STATS_THUMBNAIL_URL = BASE_IMAGE_URL+"music.png"
FEEDBACK_STATS_THUMBNAIL_URL = BASE_IMAGE_URL+"feedback.png"
CHALLENGE_STATS_THUMBNAIL_URL = BASE_IMAGE_URL+"challenge.png"

GENERIC_LEADERBOARD_THUMBNAIL_URL = BASE_IMAGE_URL+"challenge_win.png"
ALL_TIME_CHALLENGES_LEADERBOARD_THUMBNAIL_URL = BASE_IMAGE_URL+"challenge_win.png"


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



