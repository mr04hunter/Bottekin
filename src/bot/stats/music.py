from bot.database.models import User
from bot.types.stats.database_layer import MusicStatsData
from bot.logging import get_logger
from collections import Counter

logger = get_logger("music_stats_data")

def make_music_stats(stats: User) -> MusicStatsData:
    try:
        tracks = stats.tracks
        music_feedback_givers_pair = []
        feedback_givers = set()
        all_feedback_givers = []
        all_feedbacks = []

        logger.bind(
            tracks=str(tracks),

        ).debug("Received data on music_stats")


        tracks = tracks
        for track in tracks:
            music_feedback_givers_pair.append((track,track.feedback_givers))
            feedback_givers.update(track.feedback_givers)
            all_feedback_givers.extend(track.feedback_givers)
            if hasattr(track, 'feedbacks') and track.feedbacks:
                all_feedbacks.extend(track.feedbacks)

        most_words_feedback = None
        if all_feedbacks:
            try:
                most_words_feedback = max(all_feedbacks, key=lambda feedback: feedback.word_count)
            except (AttributeError, ValueError) as e:
                logger.bind(
                    error=str(e)
                ).warning("Error most words feedback")
                most_words_feedback = None

        counter = Counter(all_feedback_givers)
        top_feedbacked_tracks = sorted(tracks, key=lambda track: len(track.feedbacks), reverse=True)[:3]
        
        top_feedback_givers = counter.most_common(3)
        most_reacted_music = max(tracks, key=lambda music: music.total_reactions)

        logger.bind(
            feedback_givers=str(feedback_givers),
            top_feedback_givers=str(top_feedback_givers),
            music_feedback_givers_pair=str(music_feedback_givers_pair),
            most_words_feedback=str(most_words_feedback),
            most_reacted_music=str(most_reacted_music),
            top_feedbacked_tracks=str(top_feedbacked_tracks)

        ).debug("Return value of music stats")
        music_stats = MusicStatsData(total_tracks=len(tracks), total_feedback_received=stats.total_feedbacks_received, top_fb_givers=top_feedback_givers,
                                    most_words_received_feedback=most_words_feedback, most_reacted_track=most_reacted_music,
                                    top_feedbacked_tracks=top_feedbacked_tracks)

        return music_stats
    except Exception as e:
        logger.bind(
            error=str(e)
        ).error("Error in music_stats")
        raise