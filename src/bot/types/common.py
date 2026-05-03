from dataclasses import dataclass
from datetime import datetime
from typing import Any



@dataclass
class UserData:
    id: int
    username: str
    display_name: str
    is_purge_data: bool = False

@dataclass
class FeedbackData:
    id: int
    track_id: int
    author: UserData
    channel_id: int
    content: str
    word_count: int



@dataclass
class EmbedData:
    field_names: list[str]
    field_values: list[Any]

@dataclass
class ChallengeEmbedData(EmbedData):
    id: int
    title: str
    description: str
    type: str

    duration:"ChallengeDurationData"

    is_active: bool
    is_ongoing_voting: bool


    host_id: int | None = None


@dataclass
class ChallengeDurationData:
    starts_at: datetime
    ends_at: datetime
    voting_ends_at: datetime
