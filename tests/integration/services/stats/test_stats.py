import pytest
from bot.services.stats_services import StatsService
from tests.factories.discord_factories import make_member, make_message

class TestStatsService:
    @pytest.fixture
    async def service(self, uow, mock_bot,mock_converter):
        return StatsService(uow=uow, bot=mock_bot, converter=mock_converter)
    

    async def test_fetch_music_stats(
        self, service, seeded_stat_tracks,
        seeded_stat_feedbacks, mock_guild, seeded_stats):
        user = await service.uow.users.get_with_stats(seeded_stat_tracks.track1.author_id)

        embed = await service.fetch_music_stats(guild=mock_guild, user=user, display_name=user.display_name)

        assert embed is not None
        embed = embed.to_dict()
        music_stats_text = embed.get("description")
        
        assert user.display_name in music_stats_text
        assert str(len(user.tracks)) in music_stats_text 
        assert str(user.total_feedbacks_received) in music_stats_text

        fields = embed.get("fields")
        top_tracks, most_reacted_track, most_words_feedback, top_fb_givers = fields

        top_tracks_val = top_tracks.get("value")
        assert make_message(id=seeded_stat_tracks.track0.id).jump_url in top_tracks_val
        assert str(user.tracks[0].total_feedbacks) in top_tracks_val
        assert make_message(id=seeded_stat_tracks.track1.id).jump_url in top_tracks_val
        assert str(user.tracks[1].total_feedbacks) in top_tracks_val
        assert make_message(id=seeded_stat_tracks.track2.id).jump_url in top_tracks_val
        assert str(user.tracks[2].total_feedbacks) in top_tracks_val

        most_reacted_track_val = most_reacted_track.get("value")
        assert user.display_name in most_reacted_track_val
        assert make_message(seeded_stats.most_reacted_track.id).jump_url in most_reacted_track_val

        most_words_feedback_val = most_words_feedback.get("value")

        assert make_message(id=seeded_stats.most_words_feedback_received.id).jump_url in most_words_feedback_val

        top_fb_givers_val = top_fb_givers.get("value")

        top_fb_givers_users = seeded_stats.top_fb_givers(user.id)
        assert len(top_fb_givers_users) == 3
        for user_count in top_fb_givers_users:
            giver_id,count = user_count
            assert make_member(id=giver_id).mention in top_fb_givers_val
            assert str(count) in top_fb_givers_val






    async def test_fetch_feedback_stats(
        self, service, seeded_stat_tracks,
        seeded_stat_feedbacks, mock_guild, mock_bot_client, seeded_stats):
        user = await service.uow.users.get_with_stats(seeded_stat_feedbacks.feedback5.author_id)

        embed = await service.fetch_feedback_stats(guild=mock_guild, user=user, display_name=user.display_name, client=mock_bot_client)

        assert embed is not None
        embed = embed.to_dict()
        feedback_stats_text = embed.get("description")
        
        assert user.display_name in feedback_stats_text
        assert str(len(user.feedbacks)) in feedback_stats_text 
        assert str(seeded_stats.total_fb_word_count_of_user(user.id)) in feedback_stats_text

        fields = embed.get("fields")
        top_supported_authors, most_words_feedback = fields

        top_supported_authors_val = top_supported_authors.get("value")

        top_supported_authors = seeded_stats.top_supported_members(user.id)
        assert len(top_supported_authors) == 3

        for fb_count_author in top_supported_authors:
            author_id,fb_count = fb_count_author
            assert make_member(id=author_id).mention in top_supported_authors_val
            assert str(fb_count) in top_supported_authors_val


        most_words_feedback_val = most_words_feedback.get("value")

        assert make_message(id=seeded_stats.most_words_feedback_of_user(user.id).id).jump_url in most_words_feedback_val





    async def test_fetch_challenge_stats(
        self, service, seeded_submission_stats,
        seeded_vote_stats, seeded_winner_stats,
        mock_guild, mock_bot_client, seeded_stats,
        seeded_users):
        user = await service.uow.users.get_with_stats(seeded_users.submission_author1.id)

        embed = await service.fetch_challenge_stats(guild=mock_guild, user=user, display_name=user.display_name, client=mock_bot_client)

        assert embed is not None
        embed = embed.to_dict()
        challenge_stats_text = embed.get("description")
        
        assert user.display_name in challenge_stats_text
        assert str(len(user.submissions)) in challenge_stats_text 


        fields = embed.get("fields")
        voted_members_field, members_received_vote_from_field, most_voted_submissions_field = fields

        most_voted_members_val = voted_members_field.get("value")

        most_voted_members = seeded_stats.most_voted_members(user.id)
        assert len(most_voted_members) == 1

        for author_id_vote_count in most_voted_members:
            author_id,times_voted = author_id_vote_count
            assert make_member(id=author_id).mention in most_voted_members_val
            assert str(times_voted) in most_voted_members_val


        members_received_vote_from_val = members_received_vote_from_field.get("value")


        member_most_voted = seeded_stats.most_members_received_vote_from(user.id)
        voter_id, count = member_most_voted
        assert make_member(id=voter_id).mention in members_received_vote_from_val


        most_voted_submissions_val = most_voted_submissions_field.get("value")
        most_voted_submissions = seeded_stats.most_voted_submissions_of_user(user.id)

        assert len(most_voted_submissions) == 3
        
        for submission_vote_count in most_voted_submissions:
            submission, vote_count = submission_vote_count

            assert submission.title in most_voted_submissions_val
            assert str(vote_count) in most_voted_submissions_val


    
    async def test_empty_user_music_stats(self, mock_guild, service, seeded_users):
        user = await service.uow.users.get_with_stats(seeded_users.submission_author1.id)

        embed = await service.fetch_music_stats(guild=mock_guild, user=user, display_name=user.display_name)

        assert embed is None

        #no crash: pass


    async def test_empty_user_feedback_stats(self, mock_guild, mock_bot_client, service, seeded_users):
        user = await service.uow.users.get_with_stats(seeded_users.submission_author1.id)

        embed = await service.fetch_feedback_stats(guild=mock_guild, user=user, display_name=user.display_name, client=mock_bot_client)

        assert embed is None

        #no crash: pass


    async def test_empty_user_challenge_stats(self, mock_guild, mock_bot_client, service, seeded_users):
        user = await service.uow.users.get_with_stats(seeded_users.submission_author1.id)

        embed = await service.fetch_challenge_stats(guild=mock_guild, user=user, display_name=user.display_name, client=mock_bot_client)

        assert embed is None

        #no crash: pass