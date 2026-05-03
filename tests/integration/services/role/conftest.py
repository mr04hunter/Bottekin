import pytest


@pytest.fixture
async def seeded_feedback_role_users(uow, make_user):
    feedback_author1 = await make_user(user_id=699, username="fb_author1", display_name="fb_author_display_name1")
    feedback_author2 = await make_user(user_id=698, username="fb_author2", display_name="fb_author_display_name2")
    feedback_author3 = await make_user(user_id=697, username="fb_author3", display_name="fb_author_display_name3")
    feedback_author4 = await make_user(user_id=696, username="fb_author4", display_name="fb_author_display_name4")
    feedback_author5 = await make_user(user_id=695, username="fb_author5", display_name="fb_author_display_name5")

    await uow.users.update(feedback_author1.id, data={"total_feedbacks_given":15})
    await uow.users.update(feedback_author2.id, data={"total_feedbacks_given":30})
    await uow.users.update(feedback_author3.id, data={"total_feedbacks_given":50})

    await uow.users.update(feedback_author4.id, data={"total_feedbacks_given":100})
    await uow.users.update(feedback_author5.id, data={"total_feedbacks_given":1000})


@pytest.fixture
async def seeded_challenge_role_users(uow, make_user):
    submission_author1 = await make_user(user_id=699, username="fb_author1", display_name="fb_author_display_name1")
    submission_author2 = await make_user(user_id=698, username="fb_author2", display_name="fb_author_display_name2")
    submission_author3 = await make_user(user_id=697, username="fb_author3", display_name="fb_author_display_name3")
    submission_author4 = await make_user(user_id=696, username="fb_author4", display_name="fb_author_display_name4")
    submission_author5 = await make_user(user_id=695, username="fb_author5", display_name="fb_author_display_name5")

    await uow.users.update(submission_author1.id, data={"total_submissions":3})
    await uow.users.update(submission_author2.id, data={"total_submissions":10})
    await uow.users.update(submission_author3.id, data={"total_submissions":30})

    await uow.users.update(submission_author4.id, data={"total_submissions":50})
    await uow.users.update(submission_author5.id, data={"total_submissions":100})
