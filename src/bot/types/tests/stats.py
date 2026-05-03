from typing import TYPE_CHECKING

from bot.database.models import Feedback, Submission, Track, Vote

if TYPE_CHECKING:
    from bot.types.tests.challenge import SubmissionCollection, VoteCollection, WinnerCollection
    from bot.types.tests.feedback import FeedbackCollection
    from bot.types.tests.track import TrackCollection




class StatsTestData:
    def __init__(
    self,
    tracks:"TrackCollection",
    feedbacks:"FeedbackCollection",
    submissions:"SubmissionCollection",
    votes:"VoteCollection",
    winners:"WinnerCollection"
    ) -> None:
        self.tracks = tracks
        self.feedbacks = feedbacks
        self.submissions = submissions
        self.votes = votes
        self.winners = winners

    
    @property
    def most_words_feedback_received(self):
        sorted_feedbacks = sorted([feedback for feedback in self.feedbacks if isinstance(feedback, Feedback)], key=lambda t: t.word_count, reverse=True)
        return sorted_feedbacks[0]
    
    
    @property
    def most_reacted_track(self):
        sorted_tracks = sorted([track for track in self.tracks if isinstance(track, Track)], key=lambda t: t.total_reactions, reverse=True)
        return sorted_tracks[0]
    
    def top_fb_givers(self, user_id:int):
        track_ids = [track.id for track in self.tracks if isinstance(track, Track) and track.author_id==user_id]
        fb_givers = [feedback.author_id for feedback in self.feedbacks if isinstance(feedback, Feedback) and feedback.track_id in track_ids]
        from collections import Counter
        counter = Counter(fb_givers)

        return counter.most_common(3)
    
    def most_words_feedback_of_user(self, user_id:int):
        feedbacks = sorted([feedback for feedback in self.feedbacks if isinstance(feedback, Feedback) and feedback.author_id == user_id],
                            key=lambda f: f.word_count, reverse=True)
        

        return feedbacks[0]



    def total_fb_word_count_of_user(self, user_id):
        return sum([feedback.word_count for feedback in self.feedbacks if isinstance(feedback, Feedback) and feedback.author_id==user_id])
    
    def top_supported_members(self, user_id):
        author_track_data = {track.id:track.author_id for track in self.tracks if isinstance(track, Track)}

        authors = [author_track_data.get(feedback.track_id) for feedback in self.feedbacks
            if isinstance(feedback, Feedback) and feedback.author_id==user_id and feedback.track_id]
        from collections import Counter
        counter = Counter(authors)
        return counter.most_common(3)

    def most_voted_members(self, user_id):
        submission_author_data = {submission.id:submission.author_id for submission in self.submissions if isinstance(submission, Submission)}

        voted_members = [submission_author_data.get(vote.submission_id) for vote in self.votes if isinstance(vote, Vote) and vote.voter_id==user_id]
        from collections import Counter
        counter = Counter(voted_members)
        return counter.most_common(3)
    

    def most_members_received_vote_from(self, user_id):
        submission_ids = [submission.id for submission in self.submissions if isinstance(submission, Submission) and submission.author_id==user_id]
        voter_ids = [vote.voter_id for vote in self.votes if isinstance(vote, Vote) and vote.submission_id in submission_ids]

        from collections import Counter
        counter = Counter(voter_ids)
        return counter.most_common(1)[0]
    
    def most_voted_submissions_of_user(self, user_id):
        user_submissions = {submission.id:submission for submission in self.submissions if isinstance(submission, Submission) and submission.author_id==user_id}
        voted_submissions = [user_submissions[vote.submission_id] for vote in self.votes if isinstance(vote, Vote) and vote.submission_id in user_submissions]
        

        from collections import Counter
        counter = Counter(voted_submissions)
  
        return counter.most_common(3)
        