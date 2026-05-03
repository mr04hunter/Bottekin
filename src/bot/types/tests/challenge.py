from dataclasses import dataclass
from unittest.mock import MagicMock
from bot.database.models import User, Submission, Challenge, Vote, Winner
from bot.types.common import ChallengeEmbedData
from bot.types.tests.collections import Collection


class SubmissionCollection(Collection[Submission]):
    @property
    def submission_ids(self):
        return [submission.id for submission in self._items.values()]
    
    def get_submissions_of_user(self, user_id:int):
        return [submission for submission in self._items.values() if submission.author_id==user_id]
    def get_total_of_user(self,user_id:int):
        return len([submission for submission in self._items.values() if submission.author_id==user_id])
    def get_submission_ids_of_user(self, user_id:int):
        return [submission.id for submission in self._items.values() if submission.author_id==user_id]
    


class VoteCollection(Collection[Vote]):
    def get_votes_of_user(self, user_id:int):
        return [vote for vote in self._items.values() if isinstance(vote, Vote) and vote.voter_id==user_id]
    def get_total_votes_received(self, submission_ids: list[int]):
        return len([vote for vote in self._items.values() if vote.submission_id in submission_ids])
    def get_times_voted(self, user_id: int):
        return len([vote for vote in self._items.values() if vote.voter_id==user_id])
    
class WinnerCollection(Collection[Winner]):
    def get_wins_of_user(self, user_id: int):
        return [winner for winner in self._items.values() if isinstance(winner, Winner) and winner.winner_id==user_id]
    def get_total_wins(self, user_id:int):
        return len([winner for winner in self._items.values() if winner.winner_id==user_id])
    

@dataclass
class ChallengeSyncData:
    existing_users:list[MagicMock]

    challenge_data: ChallengeEmbedData
    challenge: Challenge
    submission_messages: list[MagicMock]
    votes: list[MagicMock]
    winners: list[MagicMock]

    submission_channel: MagicMock
    challenge_info_channel: MagicMock