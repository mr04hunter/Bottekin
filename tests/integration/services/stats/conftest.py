import discord
import pytest
from unittest.mock import MagicMock

from bot.database.models import Vote, Winner
from bot.types.tests.challenge import SubmissionCollection, VoteCollection, WinnerCollection
from bot.types.tests.feedback import FeedbackCollection
from bot.types.tests.stats import StatsTestData
from bot.types.tests.track import TrackCollection
from tests.factories.discord_factories import make_member, make_message, make_text_channel


@pytest.fixture
def mock_converter():
    converter = MagicMock()
    def mock_convert_data(data):
        async def _convert(data):
            converted_data = []
            for user_data in data:
                user, val = user_data
                converted_data.append((make_member(id=user.id).mention, val))

            return converted_data
        return _convert(data)
        
    converter.convert_users_to_members_data = MagicMock(side_effect=mock_convert_data)

    return converter




@pytest.fixture
async def seeded_stat_tracks(uow,seeded_users):
    track1 = {
        "id":1111,
        "thread_id":1111,
        "channel_id":111,
        "author_id":seeded_users.track_author1.id,
        "title":"test_title1",
        "platform":"test_platform1"
    }

    track2 = {
        "id":1112,
        "thread_id":1112,
        "channel_id":111,
        "author_id":seeded_users.track_author1.id,
        "title":"test_title2",
        "platform":"test_platform2"
    }
    
    track3 = {
        "id":1113,
        "thread_id":1113,
        "channel_id":111,
        "author_id":seeded_users.track_author1.id,
        "title":"test_title3",
        "platform":"test_platform3"
    }

    track4 = {
        "id":1114,
        "thread_id":1114,
        "channel_id":111,
        "author_id":seeded_users.track_author2.id,
        "title":"test_title3",
        "platform":"test_platform3"
    }

    track5 = {
        "id":1115,
        "thread_id":1115,
        "channel_id":111,
        "author_id":seeded_users.track_author3.id,
        "title":"test_title3",
        "platform":"test_platform3"
    }


    tracks = await uow.tracks.bulk_insert_track(tracks=[track1, track2, track3,
                                                        track4, track5])
    await uow.tracks.increment_track_reaction(track1["id"])
    track_data = {f"track{i}":track for i,track in enumerate(tracks)}
    return TrackCollection(**track_data)




@pytest.fixture
async def seeded_stat_feedbacks(uow,seeded_users, seeded_stat_tracks):
    feedback1 = {
        "id":2111,
        "thread_id":seeded_stat_tracks.track0.id,
        "track_id":seeded_stat_tracks.track0.id,
        "channel_id":111,
        "author_id":seeded_users.fb_author1.id,
        "content":"test content feedback",
        "word_count":3
    }

    feedback2 = {
        "id":2112,
        "thread_id":seeded_stat_tracks.track1.id,
        "track_id":seeded_stat_tracks.track1.id,
        "channel_id":111,
        "author_id":seeded_users.fb_author1.id,
        "content":"test content feedback",
        "word_count":3
    }
    
    feedback3 = {
        "id":2113,
        "thread_id":seeded_stat_tracks.track2.id,
        "track_id":seeded_stat_tracks.track2.id,
        "channel_id":111,
        "author_id":seeded_users.fb_author1.id,
        "content":"test content feedback",
        "word_count":3
    }


    feedback4 = {
        "id":2114,
        "thread_id":seeded_stat_tracks.track0.id,
        "track_id":seeded_stat_tracks.track0.id,
        "channel_id":111,
        "author_id":seeded_users.fb_author2.id,
        "content":"test content feedback",
        "word_count":3
    }

    feedback5 = {
        "id":2115,
        "thread_id":seeded_stat_tracks.track1.id,
        "track_id":seeded_stat_tracks.track1.id,
        "channel_id":111,
        "author_id":seeded_users.fb_author2.id,
        "content":"test content feedback",
        "word_count":3
    }
    
    feedback6 = {
        "id":2116,
        "thread_id":seeded_stat_tracks.track2.id,
        "track_id":seeded_stat_tracks.track2.id,
        "channel_id":111,
        "author_id":seeded_users.fb_author2.id,
        "content":"test content feedback most words feedback",
        "word_count":6
    }

    feedback7 = {
        "id":2117,
        "thread_id":seeded_stat_tracks.track0.id,
        "track_id":seeded_stat_tracks.track0.id,
        "channel_id":111,
        "author_id":seeded_users.fb_author3.id,
        "content":"test content feedback",
        "word_count":3
    }

    feedback8 = {
        "id":2118,
        "thread_id":seeded_stat_tracks.track1.id,
        "track_id":seeded_stat_tracks.track1.id,
        "channel_id":111,
        "author_id":seeded_users.fb_author3.id,
        "content":"test content feedback",
        "word_count":3
    }

    feedback9 = {
        "id":2119,
        "thread_id":seeded_stat_tracks.track1.id,
        "track_id":seeded_stat_tracks.track1.id,
        "channel_id":111,
        "author_id":seeded_users.voter1.id,
        "content":"test content feedback",
        "word_count":3
    }


    feedback10 = {
        "id":2120,
        "thread_id":seeded_stat_tracks.track3.id,
        "track_id":seeded_stat_tracks.track3.id,
        "channel_id":111,
        "author_id":seeded_users.fb_author2.id,
        "content":"test content feedback",
        "word_count":3
    }

    feedback11 = {
        "id":2121,
        "thread_id":seeded_stat_tracks.track4.id,
        "track_id":seeded_stat_tracks.track4.id,
        "channel_id":111,
        "author_id":seeded_users.fb_author2.id,
        "content":"test content feedback",
        "word_count":3
    }


    feedbacks = await uow.feedback.bulk_insert_feedback(feedbacks=[
        feedback1, feedback2, feedback3,
        feedback4, feedback5, feedback6,
        feedback7, feedback8, feedback9,
        feedback10, feedback11])
    feedback_data = {f"feedback{i}":feedback for i,feedback in enumerate(feedbacks)}

    track_feedback_relations_data = []
    for feedback in feedbacks:
        track_feedback_relations_data.append({
            "track_id":feedback.track_id,
            "user_id":feedback.author_id,
            "feedback_id":feedback.id
        })

    await uow.feedback.bulk_update_relations(track_feedback_relations_data)

    return FeedbackCollection(**feedback_data)


@pytest.fixture
async def seeded_submission_stats(
    uow,
    seeded_challenge,
    seeded_challenge2,
    seeded_challenge3,
    seeded_users
):
    submission1 = {
        "id":3111,
        "challenge_id":seeded_challenge.id,
        "channel_id":111,
        "author_id":seeded_users.submission_author1.id,
        "title":"test_submission1"
    }

    submission2 = {
        "id":3112,
        "challenge_id":seeded_challenge.id,
        "channel_id":111,
        "author_id":seeded_users.submission_author2.id,
        "title":"test_submission2"
    }

    submission3 = {
        "id":3113,
        "challenge_id":seeded_challenge.id,
        "channel_id":111,
        "author_id":seeded_users.submission_author3.id,
        "title":"test_submission3"
    }

    submission4 = {
        "id":3114,
        "challenge_id":seeded_challenge.id,
        "channel_id":111,
        "author_id":seeded_users.fb_author1.id,
        "title":"test_submission4"
    }

    submission5 = {
        "id":3115,
        "challenge_id":seeded_challenge2.id,
        "channel_id":111,
        "author_id":seeded_users.submission_author1.id,
        "title":"test_submission5"
    }

    submission6 = {
        "id":3116,
        "challenge_id":seeded_challenge3.id,
        "channel_id":111,
        "author_id":seeded_users.submission_author1.id,
        "title":"test_submission6"
    }



    submission1_db = await uow.challenges.create_or_update_submission(submission1)
    submission2_db = await uow.challenges.create_or_update_submission(submission2)
    submission3_db = await uow.challenges.create_or_update_submission(submission3)
    submission4_db = await uow.challenges.create_or_update_submission(submission4)
    submission5_db = await uow.challenges.create_or_update_submission(submission5)
    submission6_db = await uow.challenges.create_or_update_submission(submission6)

    return SubmissionCollection(
        submission1=submission1_db,
        submission2=submission2_db,
        submission3=submission3_db,
        submission4=submission4_db,
        submission5=submission5_db,
        submission6=submission6_db)


@pytest.fixture
async def seeded_vote_stats(
    uow,
    seeded_challenge,
    seeded_challenge2,
    seeded_challenge3,
    seeded_users,
    seeded_submission_stats
):
    voter_ids = [seeded_users.voter1.id, seeded_users.voter2.id, seeded_users.voter3.id]
    votes = {}
    for voter_id in voter_ids:
        votes[voter_id] = Vote(
            voter_id=voter_id,
            submission_id=seeded_submission_stats.submission1.id,
            challenge_id=seeded_challenge.id
        )





    votes[seeded_users.submission_author1.id] = Vote(
            voter_id=seeded_users.submission_author1.id,
            submission_id=seeded_submission_stats.submission3.id,
            challenge_id=seeded_challenge.id                                                     
)
            
        

    votes_db = await uow.challenges.bulk_insert_votes(votes, challenge=seeded_challenge)

    #extra votes for most_voted_member and most_voted_submissions
    await uow.challenges.add_vote(submission_id=seeded_submission_stats.submission5.id, voter_id=seeded_users.voter1.id, challenge_id=seeded_challenge2.id)
    await uow.challenges.add_vote(submission_id=seeded_submission_stats.submission6.id, voter_id=seeded_users.voter1.id, challenge_id=seeded_challenge3.id)

    vote_data = {f"vote{i}":vote for i,vote in enumerate(votes_db+[Vote(
        submission_id=seeded_submission_stats.submission5.id,
        voter_id=seeded_users.voter1.id, challenge_id=seeded_challenge2.id
    ), Vote(
        submission_id=seeded_submission_stats.submission6.id,
        voter_id=seeded_users.voter1.id,challenge_id=seeded_challenge3.id
    )])}

    return VoteCollection(**vote_data)


@pytest.fixture
async def seeded_winner_stats(
    uow,
    seeded_users,
    seeded_challenge,
    seeded_submission_stats
):
    await uow.challenges.set_winner(
        user_id=seeded_users.submission_author1.id, submission_id=seeded_submission_stats.submission1.id, challenge_id=seeded_challenge.id)
    
    return WinnerCollection(
        winner1=Winner(
            winner_id=seeded_users.submission_author1.id,
            submission_id=seeded_submission_stats.submission1.id,
            challenge_id=seeded_challenge.id
        )
    )





@pytest.fixture
def seeded_stats(
    seeded_stat_feedbacks,
    seeded_stat_tracks,
    seeded_submission_stats,
    seeded_vote_stats,
    seeded_winner_stats
):
    return StatsTestData(
        tracks=seeded_stat_tracks.all,
        feedbacks=seeded_stat_feedbacks.all,
        submissions=seeded_submission_stats.all,
        votes=seeded_vote_stats.all,
        winners=seeded_winner_stats.all
    )




@pytest.fixture
def mock_client():
    client = MagicMock()

    def mock_fetch_user(id):
        async def _fetch(id):
            return make_member(id=id)
        
        return _fetch(id)

    client.fetch_user = MagicMock(side_effect=mock_fetch_user)

    return client

@pytest.fixture
def mock_guild():
    guild = MagicMock(spec=discord.Guild)

    def mock_fetch_channel(id):
        async def _fetch(id):
            channel = make_text_channel(id=id)

            def mock_fetch_message(id):
                async def _fetch_message(id):
                    return make_message(id=id)
                return _fetch_message(id)

            channel.fetch_message = MagicMock(side_effect=mock_fetch_message)
            return channel
        return _fetch(id)

    guild.fetch_channel = MagicMock(side_effect=mock_fetch_channel)

    return guild


