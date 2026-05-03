import pytest
from bot.services.feedback import FeedbackValidator
from bot.types.common import UserData



class TestFeedbackValidatorIntegration:

    @pytest.fixture
    async def validator(self, uow):
        return FeedbackValidator(uow=uow)

    @pytest.fixture
    async def seeded_db(self, uow):
        await uow.users.create(UserData(111, "author", "Author", True))
        await uow.users.create(UserData(222, "reviewer", "Reviewer", True))
        await uow.tracks.add({
            "id": 987, "author_id": 111, "thread_id": 987,
            "channel_id": 111, "title": "Track", "platform": "youtube"
        })


    async def test_gibberish_rejected(self, validator):
        is_valid, reason = await validator.validate(
            author_id=222, thread_id=987,
            content="asdfgh qwerty zxcvbn poiuyt lkjhg",
            word_count=5,
        )
        assert is_valid is False
        assert reason == "gibberish"

    async def test_gibberish_check_does_not_hit_db(self, validator):

        is_valid, reason = await validator.validate(
            author_id=99999, 
            thread_id=99999,
            content="asdfgh qwerty zxcvbn",
            word_count=3,
        )
        assert is_valid is False
        assert reason == "gibberish"


    async def test_duplicated_words_rejected(self, validator):
        is_valid, reason = await validator.validate(
            author_id=222, thread_id=987,
            content="good good good good good good good good good good",
            word_count=10,
        )
        assert is_valid is False
        assert reason == "duplicated_words"

    async def test_already_gave_feedback_rejected(self, validator, uow, seeded_db):
        await uow.feedback.add({
            "id": 555, "track_id": 987, "author_id": 222,
            "thread_id": 987, "channel_id": 111,
            "content": "Great track with solid production",
            "word_count": 5,
        })

        is_valid, reason = await validator.validate(
            author_id=222, thread_id=987,
            content="Completely different content here",
            word_count=4,
        )
        assert is_valid is False
        assert reason == "already_exists"

    async def test_different_user_same_thread_is_allowed(self, validator, uow, seeded_db):
        """Two different users can both give feedback in the same thread."""
        await uow.users.create(UserData(333, "third", "Third", True))
        await uow.feedback.add({
            "id": 555, "track_id": 987, "author_id": 222,
            "thread_id": 987, "channel_id": 111,
            "content": "Great track with solid production",
            "word_count": 5,
        })

        is_valid, reason = await validator.validate(
            author_id=333,  
            thread_id=987, 
            content="Also a great track with nice melody",
            word_count=7,
        )
        assert is_valid is True
        assert reason == ""

    async def test_same_user_different_thread_is_allowed(self, validator, uow, seeded_db):
        await uow.tracks.add({
            "id": 988, "author_id": 111, "thread_id": 988,
            "channel_id": 111, "title": "Track 2", "platform": "youtube"
        })
        await uow.feedback.add({
            "id": 555, "track_id": 987, "author_id": 222,
            "thread_id": 987, "channel_id": 111,
            "content": "Great track with solid production",
            "word_count": 5,
        })

        is_valid, reason = await validator.validate(
            author_id=222,   
            thread_id=988,   
            content="Also a great track with nice melody",
            word_count=7,
        )
        assert is_valid is True
        assert reason == ""



    async def test_duplicate_content_rejected(self, validator, uow, seeded_db):
 
        content = ("This track has really solid production quality "
                   "and the melody is incredibly catchy throughout its really good")
        word_count = len(content.split()) 

        await uow.users.create(UserData(333, "third", "Third", True))
        await uow.tracks.add({
            "id": 988, "author_id": 111, "thread_id": 988,
            "channel_id": 111, "title": "Track 2", "platform": "youtube"
        })
        await uow.feedback.add({
            "id": 555, "track_id": 987, "author_id": 222,
            "thread_id": 987, "channel_id": 111,
            "content": content,
            "word_count": word_count,
        })


        is_valid, reason = await validator.validate(
            author_id=333,
            thread_id=988,
            content=content,  
            word_count=word_count,
        )
        assert is_valid is False
        assert reason == "duplicate_content"


    @pytest.mark.parametrize("p_content, expected_reason", [("good good good good", "duplicated_words"), ("Great track nice work", "duplicate_content")])
    async def test_duplicate_content_and_word_boundary(
        self, validator, uow, seeded_db, p_content, expected_reason
    ):
        content = p_content
        await uow.users.create(UserData(333, "third", "Third", True))
        await uow.tracks.add({
            "id": 988, "author_id": 111, "thread_id": 988,
            "channel_id": 111, "title": "Track 2", "platform": "youtube"
        })
        await uow.feedback.add({
            "id": 555, "track_id": 987, "author_id": 222,
            "thread_id": 987, "channel_id": 111,
            "content": content, "word_count": 4,
        })

        is_valid, reason = await validator.validate(
            author_id=333,
            thread_id=988,
            content=content,
            word_count=4,
        )
        assert reason != expected_reason


    async def test_gibberish_checked_before_db_queries(self, validator):

        is_valid, reason = await validator.validate(
            author_id=99999,
            thread_id=99999,
            content="asdfgh qwerty zxcvbn poiuyt",
            word_count=4,
        )
        assert is_valid is False
        assert reason == "gibberish"