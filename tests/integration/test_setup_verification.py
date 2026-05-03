from bot.types.common import UserData


class TestSetupVerification:
    async def test_can_write_and_read_from_db(self, uow):
        await uow.users.create(UserData(
            id=111, username="verify_user", display_name="Verify"
        ))
        user = await uow.users.get_by_id(111)
        assert user is not None
        assert user.username == "verify_user"
    async def test_data_is_isolated_between_tests_part_one(self, uow):
        await uow.users.create(UserData(
            id=999, username="should_not_persist", display_name="Ghost"
        ))
        user = await uow.users.get_by_id(999)
        assert user is not None 


    

    async def test_data_is_isolated_between_tests_part_two(self, uow):
        user = await uow.users.get_by_id(999)
        assert user is None  

    async def test_triggers_fire_on_real_db(self, uow):
        await uow.users.create(UserData(
            id=111, username="author", display_name="Author"
        ))
        await uow.users.create(UserData(
            id=222, username="reviewer", display_name="Reviewer"
        ))
        await uow.tracks.add({
            "id": 555, "author_id": 111, "thread_id": 333,
            "channel_id": 444, "title": "Test Track", "platform": "youtube"
        })
        await uow.feedback.add({
            "id": 777, "track_id": 555, "author_id": 222,
            "thread_id": 333, "channel_id": 444,
            "content": "Great track with solid production quality",
            "word_count": 6,
        })

        reviewer = await uow.users.get_by_id(222)
        author = await uow.users.get_by_id(111)

        assert reviewer.total_feedbacks_given == 1
        assert reviewer.total_feedback_words == 6
        assert author.total_feedbacks_received == 1

    