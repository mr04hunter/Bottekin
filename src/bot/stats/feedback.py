from bot.database.models import User
from collections import Counter
from bot.logging import get_logger
from bot.types.stats.database_layer import FeedbackStatsData

logger = get_logger("feedback_stats_data")

def make_feedback_stats(stats: User) -> FeedbackStatsData:
    try:
        feedbacks = stats.feedbacks
        logger.bind(
            feedbacks=feedbacks
        ).debug("Received value on feedback_stats")
        all_feedbacked_authors = [feedback.track.author for feedback in feedbacks if feedback.track and feedback.track_id and feedback.track.author]
        most_feedbacked_authors = []
        count = 0
        if all_feedbacked_authors:
            
            most_feedbacked_authors = Counter(all_feedbacked_authors).most_common(3)
        
        most_words_feedback = max(feedbacks, key= lambda feedback: feedback.word_count)
    

        feedback_stats = FeedbackStatsData(total_feedback_word_count=stats.total_feedback_words,total_feedbacks_given=len(feedbacks),
                                        most_words_feedback=most_words_feedback, most_feedbacked_authors=most_feedbacked_authors, total_feedbacked_members=len(set(all_feedbacked_authors)))

        logger.bind(
            most_feedbacked_author=most_feedbacked_authors,
            most_words_feedback=most_words_feedback,
        ).debug("Return value of feedback_stats")
        return feedback_stats
    except Exception as e:
        logger.bind(error=str(e)).error("Error on feedback_stats")
        raise