from bot.database.models import User
from bot.logging import get_logger
from bot.types.stats.database_layer import ChallengeStatsData
from collections import Counter

logger = get_logger("challenge_stats_data")


def make_challenge_stats(stats: User) -> ChallengeStatsData:
    logger.bind(
        submission=[str(submission) for submission in stats.submissions]
    ).debug("Submission debug")
    total_challenges_won = stats.total_challenges_won
    total_submissions = stats.total_submissions

    challenge_stats = ChallengeStatsData(total_submissions=total_submissions,
                                        total_challenges_won=total_challenges_won)
    
    return challenge_stats