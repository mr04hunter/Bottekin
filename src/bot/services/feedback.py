from bot.database.unit_of_work import UnitOfWork
from bot.services.feedback_validator import FeedbackValidator
from bot.types import FeedbackData
from typing import TYPE_CHECKING
from bot.events.event import (
    UPDATE_FEEDBACK_LEADERBOARD,
    SET_FEEDBACK_ROLE,
    UPDATE_SERVER_ACTIVITIES_BOARD,
    SYNC_TRACK_WITH_NO_FEEDBACK
)
from bot.logging import get_logger
from bot.services.base_service import BaseService
from bot.error_handler.decorators import service_operation

logger = get_logger("feedback_service")

if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider

class FeedbackService(BaseService):
    def __init__(self, uow: UnitOfWork, bot:"ChannelProvider", event_handler) -> None:
        super().__init__(uow=uow, bot=bot)
        self.event_handler = event_handler
        self.validator = FeedbackValidator(uow=uow)


    @service_operation(operation_name="add_feedback")
    async def add_feedback(self, data: FeedbackData) -> bool:
        """
        Returns True if feedback was added, False if rejected.
        """

        async with self.uow.transaction() as t:
            user_exists = await t.users.exists(data.author.id)
            if not user_exists:
                await t.users.create(data.author)
            track_exists = await t.tracks.exists(data.track_id)

            feedback_data = {
                "id": data.id,
                "track_id": data.track_id if track_exists else None,
                "author_id": data.author.id,
                "thread_id": data.track_id,
                "channel_id": data.channel_id,
                "content": data.content,
                "word_count": data.word_count,
            }

            total_feedback = await t.feedback.add(feedback_data)


        if data.track_id and total_feedback:
            await self._safe_emit(SYNC_TRACK_WITH_NO_FEEDBACK, track_id=data.track_id, total_feedback=total_feedback)

        logger.bind(
            feedback_id=data.id,
            thread_id=data.track_id,
            author_id=data.author.id
        ).info("Feedback added")

        await self._safe_emit(UPDATE_FEEDBACK_LEADERBOARD)
        await self._safe_emit(SET_FEEDBACK_ROLE)
        await self._safe_emit(UPDATE_SERVER_ACTIVITIES_BOARD)

        return True





    @service_operation(operation_name="update_feedback")
    async def update_feedback(self, feedback_id: int, feedback_data: dict) -> None:
        exists = await self.uow.feedback.exists(feedback_id=feedback_id)

        if not exists:
            return
        
        await self.uow.feedback.update_feedback(feedback_id=feedback_id, data=feedback_data)
        await self._safe_emit(UPDATE_FEEDBACK_LEADERBOARD)

    @service_operation(operation_name="delete_feedback")
    async def delete_feedback(self, thread_id: int, feedback_id: int) -> None:
        total_feedback = await self.uow.feedback.delete_feedback(track_id=thread_id, feedback_id=feedback_id)
        if total_feedback:
            await self._safe_emit(SYNC_TRACK_WITH_NO_FEEDBACK, track_id=thread_id, total_feedback=total_feedback)
        await self._safe_emit(UPDATE_FEEDBACK_LEADERBOARD)
        await self._safe_emit(SET_FEEDBACK_ROLE)
        await self._safe_emit(UPDATE_SERVER_ACTIVITIES_BOARD)


    
