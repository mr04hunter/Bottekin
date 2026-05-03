import pytest
from bot.database.models import Submission
from bot.views.embed_builder import EmbedBuilder
from unittest.mock import MagicMock
from bot.types.stats.presentation import FeedbackStatsDisplay, MusicStatsDisplay, ChallengeStatsDisplay
from tests.factories.discord_factories import make_member, make_message

class TestStatEmbedBuilder:
    @pytest.fixture
    def builder(self):
        return EmbedBuilder()
    

    def test_feedback_embed(self, builder):
        most_words_feedback_message = make_message(id=123)
        data = FeedbackStatsDisplay(
            total_feedback_word_count=100,
            total_feedbacks_given=10,
            most_words_feedback_message=(most_words_feedback_message, 30),
            most_feedbacked_members=[("member1", 2), ("member2",3), ("member3", 4)]
            )
        
        embed = builder.create_feedback_stats_embed(feedback_stats=data, display_name="test_display_name")

        embed_data = embed.to_dict()

        fields = embed_data.get("fields")

        assert len(fields) == 2

        top_supported_members_field, most_words_feedback_message_field = fields

        top_supported_members_val = top_supported_members_field.get("value")
        most_words_feedback_message_val = most_words_feedback_message_field.get("value")

        assert "test_display_name" in embed_data.get("description")
        assert str(data.total_feedbacks_given) in embed_data.get("description")
        assert str(data.total_feedback_word_count) in embed_data.get("description")

        assert data.most_feedbacked_members[0][0] in top_supported_members_val #type: ignore
        assert str(data.most_feedbacked_members[0][1]) in top_supported_members_val #type: ignore

        assert data.most_feedbacked_members[1][0] in top_supported_members_val #type: ignore
        assert str(data.most_feedbacked_members[1][1]) in top_supported_members_val #type: ignore

        assert data.most_feedbacked_members[2][0] in top_supported_members_val #type: ignore
        assert str(data.most_feedbacked_members[2][1]) in top_supported_members_val #type: ignore

        assert data.most_words_feedback_message[0].jump_url in most_words_feedback_message_val #type:ignore
        assert str(data.most_words_feedback_message[1]) in most_words_feedback_message_val #type:ignore
            

    def test_partial_feedback_embed(self, builder):
        data = FeedbackStatsDisplay(
            total_feedback_word_count=100,
            total_feedbacks_given=10
            )
        
        embed = builder.create_feedback_stats_embed(feedback_stats=data, display_name="test_display_name")

        embed_data = embed.to_dict()

        fields = embed_data.get("fields")

        assert fields is None

        assert "test_display_name" in embed_data.get("description")
        assert str(data.total_feedbacks_given) in embed_data.get("description")
        assert str(data.total_feedback_word_count) in embed_data.get("description")




    def test_music_embed(self, builder):
        top_feedbacked_tracks = [
            (make_message(id=12345), 3),
            (make_message(id=123456), 2),
            (make_message(id=1234567), 2)
        ]

        most_reacted_track_message = make_message(id=12133)
        most_words_fb_received_message = make_message(id=12133, author=make_member(id=123))

        data = MusicStatsDisplay(
            total_tracks=10,
            total_feedback_received=8,
            top_fb_givers=[("member1", 3), ("member2", 2), ("member3", 2)],
            top_feedbacked_track_messages=top_feedbacked_tracks, #type: ignore
            most_reacted_track_message=(most_reacted_track_message, 2),
            most_words_fb_received_message=(most_words_fb_received_message, 5)
        )

        embed = builder.create_music_stats_embed(music_stats=data, display_name="test_display_name")

        embed_data = embed.to_dict()

        fields = embed_data.get("fields")

        assert len(fields) == 4

        top_tracks_field, most_reacted_field, most_words_received_field, top_fb_givers_field = fields

        top_tracks_val = top_tracks_field.get("value")
        most_reacted_val = most_reacted_field.get("value")
        most_words_received_val = most_words_received_field.get("value")
        top_fb_givers_val = top_fb_givers_field.get("value")

        assert "test_display_name" in embed_data.get("description")
        assert str(data.total_tracks) in embed_data.get("description")
        assert str(data.total_feedback_received) in embed_data.get("description")

        assert top_feedbacked_tracks[0][0].jump_url in top_tracks_val #type: ignore
        assert str(top_feedbacked_tracks[0][1]) in top_tracks_val #type: ignore

        assert top_feedbacked_tracks[1][0].jump_url in top_tracks_val #type: ignore
        assert str(top_feedbacked_tracks[1][1]) in top_tracks_val #type: ignore

        assert top_feedbacked_tracks[2][0].jump_url in top_tracks_val #type: ignore
        assert str(top_feedbacked_tracks[2][1]) in top_tracks_val #type: ignore

        assert data.most_reacted_track_message[0].jump_url in most_reacted_val #type:ignore
        assert str(data.most_reacted_track_message[1]) in most_reacted_val #type:ignore

        assert most_words_fb_received_message.author.mention in most_words_received_val
        assert most_words_fb_received_message.jump_url in most_words_received_val
        assert str(data.most_words_fb_received_message[1]) in most_words_received_val #type: ignore


        assert data.top_fb_givers[0][0] in top_fb_givers_val #type: ignore
        assert str(data.top_fb_givers[0][1]) in top_fb_givers_val #type: ignore

        assert data.top_fb_givers[1][0] in top_fb_givers_val #type: ignore
        assert str(data.top_fb_givers[1][1]) in top_fb_givers_val #type: ignore

        assert data.top_fb_givers[2][0] in top_fb_givers_val #type: ignore
        assert str(data.top_fb_givers[2][1]) in top_fb_givers_val #type: ignore


    def test_partial_music_embed(self, builder):

        data = MusicStatsDisplay(
            total_tracks=10,
            total_feedback_received=8
        )

        embed = builder.create_music_stats_embed(music_stats=data, display_name="test_display_name")

        assert embed is not None

        embed_data = embed.to_dict()

        fields = embed_data.get("fields")

        assert fields is None




    def test_challenge_embed(self, builder):
        most_voted_submissions = [
            MagicMock(spec=Submission, id=12345, title="submission1", total_votes=10),
            MagicMock(spec=Submission, id=123456, title="submission2", total_votes=10),
            MagicMock(spec=Submission, id=1234567, title="submission3", total_votes=10)
        ]

        data = ChallengeStatsDisplay(
            most_voted_submissions=most_voted_submissions, #type: ignore
            total_votes_received=15,
            total_submissions=5,
            total_challenges_won=5,
            times_voted=3,
            most_votes_received_by_member=("most_votes_received_by_member",5),
            most_voted_member=("most_voted_member", 6)
        )


        embed = builder.create_challenge_stats_embed(challenge_stats=data, display_name="test_display_name")

        assert embed is not None

        embed_data = embed.to_dict()
        description = embed_data.get("description")

        assert "test_display_name" in description
        assert str(data.total_submissions) in description
        assert str(data.total_challenges_won) in description
        assert str(data.total_votes_received) in description
        assert str(data.times_voted) in description

        fields = embed_data.get("fields")
        assert len(fields) == 3

        most_voted_member_field, most_vote_received_member_field, most_voted_submissions_field = fields

        most_vote_received_member_val = most_vote_received_member_field.get("value")
        most_voted_member_val = most_voted_member_field.get("value")
        most_voted_submissions_val = most_voted_submissions_field.get("value")

        assert "test_display_name" in most_voted_member_val
        assert data.most_voted_member[0] in most_voted_member_val #type: ignore
        assert str(data.most_voted_member[1]) in most_voted_member_val #type: ignore

        assert data.most_votes_received_by_member[0] in most_vote_received_member_val #type: ignore
        assert str(data.most_votes_received_by_member[1]) in most_vote_received_member_val #type: ignore


        for submission in most_voted_submissions:
            assert submission.title in most_voted_submissions_val
            assert str(submission.total_votes) in most_voted_submissions_val


    
    def test_partial_challenge_embed(self, builder):
        data = ChallengeStatsDisplay(
            total_votes_received=15,
            total_submissions=5,
            total_challenges_won=5,
            times_voted=3,
            most_voted_submissions=[]
        )


        embed = builder.create_challenge_stats_embed(challenge_stats=data, display_name="test_display_name")

        assert embed is not None

        embed_data = embed.to_dict()
        description = embed_data.get("description")

        assert "test_display_name" in description
        assert str(data.total_submissions) in description
        assert str(data.total_challenges_won) in description
        assert str(data.total_votes_received) in description
        assert str(data.times_voted) in description

        fields = embed_data.get("fields")
        assert fields is None


    def test_no_submission_challenge_embed(self, builder):
        data = ChallengeStatsDisplay(
            total_votes_received=15,
            total_submissions=0, #builder is expected to return None when total_submissions==0
            total_challenges_won=5,
            times_voted=3,
            most_voted_submissions=[]
        )


        embed = builder.create_challenge_stats_embed(challenge_stats=data, display_name="test_display_name")

        assert embed is None
