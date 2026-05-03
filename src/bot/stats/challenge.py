from bot.database.models import User
from bot.logging import get_logger
from bot.types.stats.database_layer import ChallengeStatsData
from collections import Counter

logger = get_logger("challenge_stats_data")


def make_challenge_stats(stats: User) -> ChallengeStatsData:
    logger.bind(
        submission=[str(submission) for submission in stats.submissions],
        voters=[str(submission.voters) for submission in stats.submissions]
    ).debug("Submission debug")
    total_challenges_won = stats.total_challenges_won
    challenges_won = stats.challenges_won
    total_submissions = stats.total_submissions

    submissions = stats.submissions


    times_voted = stats.times_voted
    votes = stats.votes
    voted_submissions = stats.voted_submissions

    most_voted_submissions = []
    if total_submissions:
        vote_received_submissions = [submission for submission in stats.submissions if submission.total_votes > 0]
        most_voted_submissions = sorted(vote_received_submissions, reverse=True, key=lambda submission: submission.total_votes)


    most_received_vote_by_user = None
    vote_users_received = [user for submission in submissions if not isinstance(submission.voters,User) for user in submission.voters]
    if vote_users_received:
        vote_users_received_counter =  Counter(vote_users_received)
        most_received_vote_by_user = vote_users_received_counter.most_common(1)[0]
    most_voted_user_data = None
    if voted_submissions:
        voted_users_counter = Counter([submission.author for submission in voted_submissions if submission.author])
        most_voted_user_data = voted_users_counter.most_common(1)[0]
    
    
    total_received_vote_count = sum([submission.total_votes for submission in submissions])  
    
    challenge_stats = ChallengeStatsData(total_votes_received=total_received_vote_count,total_submissions=total_submissions,
                                        total_challenges_won=total_challenges_won, times_voted=times_voted,
                                        most_voted_user=most_voted_user_data,
                                        most_votes_received_by_user=most_received_vote_by_user,
                                        most_voted_submissions=most_voted_submissions)
    
    return challenge_stats