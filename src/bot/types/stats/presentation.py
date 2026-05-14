from dataclasses import dataclass
from bot.database.models import  Submission
from discord import  Message



@dataclass
class FeedbackStatsDisplay:
    total_feedbacks_given: int = 0
    total_members_given_feedback:int = 0
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
    total_submissions: int
    total_challenges_won: int
