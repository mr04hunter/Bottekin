from dataclasses import dataclass
from bot.database.models import User, Track, TrackWithNoFeedback, Feedback, Submission, Challenge, Vote, Winner
from bot.types.tests.user import UserCollection
from bot.types.tests.challenge import SubmissionCollection, VoteCollection, WinnerCollection
from bot.types.tests.track import TrackCollection
from bot.types.tests.feedback import FeedbackCollection
from bot.types.tests.collections import Collection

@dataclass
class SeededLbDb:
    users: UserCollection

    feedbacks: FeedbackCollection | None = None
    tracks: TrackCollection | None = None

    submissions: SubmissionCollection | None = None
    votes: VoteCollection | None = None
    winners: WinnerCollection | None = None


