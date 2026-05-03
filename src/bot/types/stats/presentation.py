from dataclasses import dataclass
from bot.database.models import  Submission
from discord import  Message



@dataclass
class FeedbackStatsDisplay:
    total_feedback_word_count: int
    total_feedbacks_given: int
    most_words_feedback_message: tuple[Message, int] | None = None
    most_feedbacked_members: list[tuple[str, int]] | None = None
    

     


@dataclass
class MusicStatsDisplay:
    total_tracks: int
    total_feedback_received: int = 0
    top_fb_givers:  list[tuple[str, int]] | None = None

    top_feedbacked_track_messages: list[tuple[Message, int]] | None = None
    most_reacted_track_message: tuple[Message, int] | None = None
    most_words_fb_received_message: tuple[Message, int] | None = None 


@dataclass
class ChallengeStatsDisplay:
    most_voted_submissions: list[Submission]
    total_votes_received: int
    total_submissions: int
    total_challenges_won: int
    times_voted: int
    

    most_votes_received_by_member: tuple[str, int] | None = None
    most_voted_member: tuple[str, int] | None = None
