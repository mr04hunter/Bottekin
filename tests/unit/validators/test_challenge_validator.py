from unittest.mock import MagicMock
import pytest
from bot.database.models import Challenge, MonthlyChallenge
from bot.services.challenge_validator import ChallengeValidator
from bot.types.common import  ChallengeDurationData
from datetime import datetime, timedelta, UTC
from tests.factories.discord_factories import make_submission_message

class TestChallengeValidator:
    @pytest.fixture
    async def validator(self, test_config):
        return ChallengeValidator(config=test_config)

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
            spec=Challenge,
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
            spec=Challenge,
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
    

    @pytest.fixture
    def seeded_monthly_challenge(self, duration_data):
        challenge = MagicMock(
            spec=MonthlyChallenge,
            id=12345,
            title="test_official_challenge",
            starts_at=duration_data.starts_at,
            ends_at=duration_data.ends_at,
            is_active=False
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
        submission_message = make_submission_message(
            id=123456, author=MagicMock(id=123123),
            channel_id=test_config.tiny_submission_channel_id,
            content="content",
            attachments=[MagicMock(content_type="image")],
            created_at=seeded_community_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_community_challenge)

        assert is_valid == False


    async def test_valid_link_submission(self, seeded_monthly_challenge, validator):
        submission_message = make_submission_message(
            id=123456, author=MagicMock(id=324234),
            channel_id=4564564545,
            content="http://www.youtube.com/watch?v=asdasdfasfasdf",
            created_at=seeded_monthly_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_monthly_challenge)

        assert is_valid == True


    async def test_invalid_url_monthly_submission(self, validator, seeded_monthly_challenge):
        submission_message = make_submission_message(
            id=123456, author=MagicMock(id=123123),
            channel_id=45645464,
            content="https://wwdasdw.youtsadasasdasdaube.asdascom/wasadasdasdsdasdasdl",
            created_at=seeded_monthly_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_monthly_challenge)

        assert is_valid == False


    async def test_valid_attachment_monthly_submission(self, validator, seeded_monthly_challenge):
        submission_message = make_submission_message(
            id=123456, author=MagicMock(id=123123),
            channel_id=345344365,
            content="content",
            attachments=[MagicMock(content_type="audio/mpeg")],
            created_at=seeded_monthly_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_monthly_challenge)

        assert is_valid == True


    async def test_attachment_invalid_monthly_submission(self, validator, seeded_monthly_challenge):
        submission_message = make_submission_message(
            id=123456, author=MagicMock(id=123123),
            channel_id=345345345,
            content="content",
            attachments=[MagicMock(content_type="image")],
            created_at=seeded_monthly_challenge.ends_at - timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_monthly_challenge)

        assert is_valid == False



    async def test_invalid_monthly_submission_after_end_date(self, validator, seeded_monthly_challenge):
        submission_message = make_submission_message(
            id=123456, author=MagicMock(id=123123),
            channel_id=345344365,
            content="content",
            attachments=[MagicMock(content_type="image")],
            created_at=seeded_monthly_challenge.ends_at + timedelta(days=1))
        
        is_valid = validator.validate(submission_message, seeded_monthly_challenge)

        assert is_valid == False