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
            total_members_given_feedback=15,
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
        assert str(data.total_members_given_feedback) in embed_data.get("description")

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
            total_feedbacks_given=10
            )
        
        embed = builder.create_feedback_stats_embed(feedback_stats=data, display_name="test_display_name")

        embed_data = embed.to_dict()

        fields = embed_data.get("fields")

        assert fields is None

        assert "test_display_name" in embed_data.get("description")
        assert str(data.total_feedbacks_given) in embed_data.get("description")
    




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


    def test_no_submission_challenge_embed(self, builder):
        data = ChallengeStatsDisplay(
           
            total_submissions=0, #builder is expected to return None when total_submissions==0
            total_challenges_won=5,
            
        )


        embed = builder.create_challenge_stats_embed(challenge_stats=data, display_name="test_display_name")

        assert embed is None
