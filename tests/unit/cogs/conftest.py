import pytest
from unittest.mock import AsyncMock, MagicMock
from bot.services.feedback_validator import FeedbackValidator




@pytest.fixture
def validator(mock_uow):
    validator = FeedbackValidator(uow=mock_uow)
    validator.validate = AsyncMock(return_value=(True, None))
    
    return validator

@pytest.fixture
def mock_services(validator):
    services = MagicMock()
    track = MagicMock()
    track.add_track = AsyncMock()
    track.delete_track = AsyncMock()
    track.update_track = AsyncMock()
    track.increment_track_reaction = AsyncMock()
    track.decrement_track_reaction = AsyncMock()
    services.track = track

    feedback = MagicMock()
    feedback.add_feedback = AsyncMock()
    feedback.delete_feedback = AsyncMock()
    feedback.update_feedback = AsyncMock()
    feedback.validator = validator
    services.feedback = feedback

    challenge = MagicMock()
    challenge.create_or_update_challenge = AsyncMock()
    challenge.add_submission = AsyncMock()
    challenge.delete_submission = AsyncMock()
    challenge.update_submission = AsyncMock()
    challenge.vote = AsyncMock()
    challenge.remove_vote = AsyncMock()
    challenge.set_chosen_winner = AsyncMock()
    challenge.remove_chosen_winner = AsyncMock()

    services.challenge = challenge


    return services

