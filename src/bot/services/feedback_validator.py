from bot.utils.message_detector import MessageDetector
from bot.logging import get_logger
logger = get_logger("feedback_validator")

MIN_WORD_COUNT_FOR_DUPLICATE_CHECK = 15

class FeedbackValidator:
    def __init__(self, uow) -> None:
        self.uow = uow

    async def validate(
        self,
        author_id: int,
        thread_id: int,
        content: str,
        word_count: int,
    ) -> tuple[bool, str]:
        """
        Returns (is_valid, reason).
        Reason is empty string if valid.
        """
        word_list = content.split()

        if MessageDetector.is_gibberish(word_list):
            logger.bind(author_id=author_id, thread_id=thread_id).info(
                "Rejected: gibberish"
            )
            return False, "gibberish"

        if word_count >= 5 and MessageDetector.is_duplicated_words(
            word_list=word_list, word_count=word_count
        ):
            logger.bind(author_id=author_id, thread_id=thread_id).info(
                "Rejected: duplicated words"
            )
            return False, "duplicated_words"

        logger.debug(f"author_id {author_id}, thread_id {thread_id}")
        already_gave_feedback = await self.uow.feedback.exists_for_author_in_thread(
            author_id=author_id, thread_id=thread_id
        )
        logger.debug(f"gave_feedback? {already_gave_feedback}")
        if already_gave_feedback:
            logger.bind(author_id=author_id, thread_id=thread_id).info(
                "Rejected: already gave feedback"
            )
            return False, "already_exists"

        if word_count >= MIN_WORD_COUNT_FOR_DUPLICATE_CHECK:
            is_duplicate = await self.uow.feedback.is_duplicate_content(content)
            if is_duplicate:
                logger.bind(author_id=author_id, thread_id=thread_id).info(
                    "Rejected: duplicate content"
                )
                return False, "duplicate_content"

        return True, ""