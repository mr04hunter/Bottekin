from unittest.mock import MagicMock
import pytest
from bot.services.challenge_validator import ChallengeValidator
from bot.types.common import  ChallengeDurationData
from datetime import datetime, timedelta, UTC
from tests.factories.discord_factories import make_submission_message

class TestChallengeValidator:
    @pytest.fixture
    async def validator(self, test_config):
        return ChallengeValidator(config=test_config)



    # async def test_youtube_submission(self, validator, seeded_official_challenge, seeded_users, test_config):
    #     submission_youtube1 = make_submission_message(id=123456, author=MagicMock(id=seeded_users.submission_author1.id),
    #                                                 channel_id=test_config.official_submission_channel_id,
    #                                                 content="https://www.youtube.com/watch?v=mockurl",
    #                                                 created_at=seeded_official_challenge.ends_at - timedelta(days=1))
    #     submission_youtube2 = make_submission_message(id=123456, author=MagicMock(id=seeded_users.submission_author1.id),
    #                                                 channel_id=test_config.official_submission_channel_id,
    #                                                 content="https://youtu.be/asfdasfsadsafdsf",
    #                                                 created_at=seeded_official_challenge.ends_at - timedelta(days=1))
    #     submission_youtube3 = make_submission_message(id=123456, author=MagicMock(id=seeded_users.submission_author1.id),
    #                                                 channel_id=test_config.official_submission_channel_id,
    #                                                 content="https://youtu.be/asfdasfsadsafdsf",
    #                                                 created_at=seeded_official_challenge.ends_at - timedelta(days=1))
    #     submission_youtube4 = make_submission_message(id=123456, author=MagicMock(id=seeded_users.submission_author1.id),
    #                                                 channel_id=test_config.official_submission_channel_id,
    #                                                 content="https://youtu.be/asfdasfsadsafdsf",
    #                                                 created_at=seeded_official_challenge.ends_at - timedelta(days=1))
    #     submission_youtube5 = make_submission_message(id=123456, author=MagicMock(id=seeded_users.submission_author1.id),
    #                                                 channel_id=test_config.official_submission_channel_id,
    #                                                 content="https://youtu.be/asfdasfsadsafdsf",
    #                                                 created_at=seeded_official_challenge.ends_at - timedelta(days=1))
        
        
        
        
    #     is_valid1 = validator.validate(submission_youtube1, seeded_official_challenge)
    #     is_valid2 = validator.validate(submission_youtube2, seeded_official_challenge)

    #     assert is_valid1 == True



    # async def test_soundcloud_submission(self, validator, seeded_official_challenge, seeded_users, test_config):
    #     submission_youtube = make_submission_message(id=123456, author=MagicMock(id=seeded_users.submission_author1.id),
    #                                                 channel_id=test_config.official_submission_channel_id,
    #                                                 content="https://www.youtube.com/watch?v=mockurl",
    #                                                 created_at=seeded_official_challenge.ends_at - timedelta(days=1))
        
    #     submission_soundcloud = make_submission_message(id=12345234, author=MagicMock(id=seeded_users.submission_author1.id),
    #                                                 channel_id=test_config.official_submission_channel_id,
    #                                                 content="https://soundcloud.com/some_artist/some_music",
    #                                                 created_at=seeded_official_challenge.ends_at - timedelta(days=1))
        
    #     submission_spotify = make_submission_message(id=123452346, author=MagicMock(id=seeded_users.submission_author1.id),
    #                                                 channel_id=test_config.official_submission_channel_id,
    #                                                 content="https://open.spotify.com/intl-tr/track/4TrEdcXM6vmOVOZxpXFdl2?si=811c5f79568d41ae",
    #                                                 created_at=seeded_official_challenge.ends_at - timedelta(days=1))
        
    #     submission_message = make_submission_message(id=123234456, author=MagicMock(id=seeded_users.submission_author1.id),
    #                                                 channel_id=test_config.official_submission_channel_id,
    #                                                 content="https://www.youtube.com/watch?v=mockurl",
    #                                                 created_at=seeded_official_challenge.ends_at - timedelta(days=1))
        
    #     is_valid = validator.validate(submission_message, seeded_official_challenge)

    #     assert is_valid == True


    @pytest.fixture
    def duration_data(self):
        duration_data = ChallengeDurationData(
        starts_at=datetime(year=2026, month=1,day=1, tzinfo=UTC),
        ends_at=datetime(year=2026, month=1, day=8, tzinfo=UTC),
        voting_ends_at=datetime(year=2026, month=1, day=9, tzinfo=UTC))

        return duration_data

    @pytest.fixture
    def seeded_community_challenge(self, duration_data):
        challenge = MagicMock(
            id=12345,
            title="test_community_challenge",
            host_id=123,
            description="test_official_description",
            type="community",
            starts_at=duration_data.starts_at,
            ends_at=duration_data.ends_at,
            voting_ends_at=duration_data.voting_ends_at,
            is_active=False,
            is_ongoing_voting=False,
        )

        return challenge
    
    @pytest.fixture
    def seeded_official_challenge(self, duration_data):
        challenge = MagicMock(
            id=12345,
            title="test_official_challenge",
            host_id=123,
            description="test_official_description",
            type="official",
            starts_at=duration_data.starts_at,
            ends_at=duration_data.ends_at,
            voting_ends_at=duration_data.voting_ends_at,
            is_active=False,
            is_ongoing_voting=False,
        )

        return challenge



    async def test_valid_submission(self, seeded_official_challenge, validator, test_config):
        submission_message = make_submission_message(id=123456, author=MagicMock(id=324234),
                                                    channel_id=test_config.official_submission_channel_id,
                                                    content="http://www.youtube.com/watch?v=asdasdfasfasdf",
                                                    created_at=seeded_official_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_official_challenge)

        assert is_valid == True


    async def test_invalid_url_submission(self, validator, seeded_official_challenge, test_config):
        submission_message = make_submission_message(id=123456, author=MagicMock(id=123123),
                                                    channel_id=test_config.official_submission_channel_id,
                                                    content="https://wwdasdw.youtsadasasdasdaube.asdascom/wasadasdasdsdasdasdl",
                                                    created_at=seeded_official_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_official_challenge)

        assert is_valid == False

    
    async def test_invalid_channel_id(self, validator, seeded_official_challenge, test_config):
        submission_message = make_submission_message(id=123456, author=MagicMock(id=123123),
                                                    channel_id=2131231,
                                                    content="http://www.youtube.com/watch?v=asdasdfasfasdf",
                                                    created_at=seeded_official_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_official_challenge)

        assert is_valid == False

    async def test_invalid_submission_date(self, validator, seeded_official_challenge, test_config):
        submission_message = make_submission_message(id=123456, author=MagicMock(id=123123),
                                                    channel_id=test_config.official_submission_channel_id,
                                                    content="http://www.youtube.com/watch?v=asdasdfasfasdf",
                                                    created_at=seeded_official_challenge.ends_at + timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_official_challenge)

        assert is_valid == False

    
    async def test_invalid_submission_type_on_official_challenge(self, validator, seeded_official_challenge, test_config):
        submission_message = make_submission_message(id=123456, author=MagicMock(id=123123),
                                                    channel_id=test_config.tiny_submission_channel_id,
                                                    content="http://www.youtube.com/watch?v=asdasdfasfasdf",
                                                    created_at=seeded_official_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_official_challenge)

        assert is_valid == False

    async def test_invalid_submission_type_on_community_challenge(self, validator, seeded_community_challenge, test_config):
        submission_message = make_submission_message(id=123456, author=MagicMock(id=123123),
                                                    channel_id=test_config.official_submission_channel_id,
                                                    content="http://www.youtube.com/watch?v=asdasdfasfasdf",
                                                    created_at=seeded_community_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_community_challenge)

        assert is_valid == False

    async def test_attachment_valid_submission(self, validator, seeded_community_challenge, test_config):
        submission_message = make_submission_message(id=123456, author=MagicMock(id=123123),
                                                    channel_id=test_config.tiny_submission_channel_id,
                                                    content="content",
                                                    attachments=[MagicMock(content_type="audio/mpeg")],
                                                    created_at=seeded_community_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_community_challenge)

        assert is_valid == True


    async def test_attachment_invalid_submission(self, validator, seeded_community_challenge, test_config):
        submission_message = make_submission_message(id=123456, author=MagicMock(id=123123),
                                                    channel_id=test_config.tiny_submission_channel_id,
                                                    content="content",
                                                    attachments=[MagicMock(content_type="image")],
                                                    created_at=seeded_community_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_community_challenge)

        assert is_valid == False