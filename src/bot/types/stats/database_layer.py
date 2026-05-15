from dataclasses import dataclass
from bot.database.models import User, Feedback, Track, Submission




@dataclass
class FeedbackStatsData:
    total_feedbacks_given: int
    total_feedbacked_members: int
    most_feedbacked_authors: list[tuple[User, int]]
    most_feedbacked_members: list[tuple[str, int]] | None = None

    

     


@dataclass
class MusicStatsData:
    total_tracks: int
    top_fb_givers:  list[tuple[User, int]] | None
    most_words_received_feedback: Feedback | None
    most_reacted_track: Track | None
    top_feedbacked_tracks: list[Track] | None
    most_reaction_count: int = 0
    most_fb_word_count: int = 0
    total_feedback_received: int = 0



@dataclass
class ChallengeStatsData:
    total_submissions: int
    total_challenges_won: int
    





