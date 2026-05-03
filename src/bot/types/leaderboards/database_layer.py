from dataclasses import dataclass
from datetime import datetime
from typing import Any
from bot.database.models import User, Submission

@dataclass
class BaseLeaderboardData:
    data: list[tuple[User, Any]]
    leaderboard_length: int = 0



@dataclass
class ChallengeLeaderboardData(BaseLeaderboardData):
    data: list[tuple[User, Submission]]
    challenge_title: str = "Current challenge"
    server_total_votes: int = 0
    server_total_submissions: int = 0
  

@dataclass
class AllTimeChallengeLeaderboardData(BaseLeaderboardData):
    data: list[tuple[User, int]]
    server_total_winners: int = 0


@dataclass
class SubmissionLeaderboardData(BaseLeaderboardData):
    data: list[tuple[User, int]]
    server_total_submissions: int = 0
    server_total_challenges: int = 0


@dataclass
class FeedbackLeaderboardData(BaseLeaderboardData):
    data: list[tuple[User, dict[str,int]]]
    server_total_feedback: int = 0
    server_total_tracks: int = 0
    server_total_fb_words: int = 0

@dataclass
class ServerActivityData:
    track_count: int
    feedback_count: int


@dataclass
class MostActivePeriodData:
    date:datetime
    total_feedback: int
    total_track: int
    total: int


@dataclass
class MostActiveMemberData:
    user: User
    total_feedback:int
    total_tracks:int