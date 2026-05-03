from dataclasses import dataclass
from bot.database.models import User, Feedback, Track, Submission




@dataclass
class FeedbackStatsData:
    total_feedback_word_count: int
    total_feedbacks_given: int
    most_feedbacked_authors: list[tuple[User, int]]
    most_feedbacked_members: list[tuple[str, int]] | None = None
    most_words_feedback:  Feedback | None = None
    

     


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
    most_voted_submissions: list[Submission]
    total_votes_received: int
    total_submissions: int
    total_challenges_won: int
    times_voted: int
    most_voted_user: tuple[User, int] | None = None
    most_votes_received_by_user: tuple[User, int] | None = None
    





