from dataclasses import dataclass
from typing import Any
from bot.database.models import Submission
from bot.types.leaderboards.database_layer import ServerActivityData, MostActivePeriodData

@dataclass
class BaseLeaderboardDisplay:
    data: list[tuple[str, Any]] | None = None



@dataclass
class ChallengeLeaderboardDisplay(BaseLeaderboardDisplay):
    data: list[tuple[str, Submission]] | None = None
    challenge_title: str = "Current challenge"
    server_total_votes: int = 0
    server_total_submissions: int = 0

@dataclass
class AllTimeChallengeLeaderboardDisplay(BaseLeaderboardDisplay):
    data: list[tuple[str, int]] | None = None
    server_total_winners: int = 0
    leaderboard_length: int = 0

@dataclass
class SubmissionLeaderboardDisplay(BaseLeaderboardDisplay):
    data: list[tuple[str, int]] | None = None
    total_submissions: int = 0
    leaderboard_length: int = 0
    server_total_challenges: int = 0
    server_total_submissions: int = 0

@dataclass
class FeedbackLeaderboardDisplay(BaseLeaderboardDisplay):
    data: list[tuple[str, dict[str,int]]] | None = None
    server_total_feedback: int = 0
    server_total_tracks: int = 0
    server_total_fb_words: int = 0
    leaderboard_length: int = 0

@dataclass
class ServerActivityDisplay:
    today_activity: ServerActivityData
    week_activity: ServerActivityData
    month_activity: ServerActivityData


@dataclass
class MostActivePeriodDisplay:
    day: MostActivePeriodData
    week: MostActivePeriodData
    month: MostActivePeriodData

@dataclass
class MostActiveMemberDisplay:
    member: str
    total_feedback:int
    total_tracks:int