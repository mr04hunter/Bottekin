from datetime import UTC, datetime
import pytest

from bot.types.common import MonthlyChallengeData
from bot.types.tests.challenge import MonthlySubmissionCollection


@pytest.fixture
async def seeded_monthly_challenge(uow):
    data = MonthlyChallengeData(
        id=111111111,
        title="2026_5",
        is_active=True,
        starts_at=datetime(year=2026, month=5, day=1, tzinfo=UTC),
        ends_at=datetime(year=2026, month=6, day=1, tzinfo=UTC)
    )
    challenge = await uow.challenges.create_or_update_monthly_challenge(data=data)

    return challenge

@pytest.fixture
async def seeded_ended_monthly_challenge(uow):
    data = MonthlyChallengeData(
        id=222222222222,
        title="2026_4",
        is_active=False,
        starts_at=datetime(year=2026, month=4, day=1, tzinfo=UTC),
        ends_at=datetime(year=2026, month=5, day=1, tzinfo=UTC)
    )
    challenge = await uow.challenges.create_or_update_monthly_challenge(data=data)

    return challenge

@pytest.fixture
async def seeded_monthly_submissions(uow, seeded_users, seeded_monthly_challenge):
    submission1 = {
            "id":555,
            "author_id":seeded_users.submission_author1.id,
            "thread_id":111,
            "challenge_id":seeded_monthly_challenge.id,
            "title":"submission1",
            "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}


    submission2 = {
        "id":554,
        "author_id":seeded_users.submission_author2.id,
        "thread_id":111,
        "challenge_id":seeded_monthly_challenge.id,
        "title":"submission2",
        "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}
    
    submission3 = {
        "id":553,
        "author_id":seeded_users.submission_author3.id,
        "thread_id":111,
        "challenge_id":seeded_monthly_challenge.id,
        "title":"submission3",
        "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}
    

    submission4 = {
            "id":552,
            "author_id":seeded_users.submission_author1.id,
            "thread_id":222,
            "challenge_id":seeded_monthly_challenge.id,
            "title":"submission1",
            "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}


    submission5 = {
        "id":551,
        "author_id":seeded_users.submission_author2.id,
        "thread_id":222,
        "challenge_id":seeded_monthly_challenge.id,
        "title":"submission2",
        "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}
    
    submission6 = {
        "id":550,
        "author_id":seeded_users.submission_author3.id,
        "thread_id":222,
        "challenge_id":seeded_monthly_challenge.id,
        "title":"submission3",
        "created_at":datetime(year=2026, month=3, day=3, tzinfo=UTC)}
    
    monthly_submissions = await uow.challenges.bulk_insert_monthly_submissions([submission1, submission2, submission3, submission4, submission5, submission6]) 

    monthly_submissions_data = {f"monthly_submission{i}":submission for i, submission in enumerate(monthly_submissions)}

    return MonthlySubmissionCollection(**monthly_submissions_data)
