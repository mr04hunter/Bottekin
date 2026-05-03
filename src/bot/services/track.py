from typing import TYPE_CHECKING
from bot.services.base_service import BaseService
from bot.events.event import  DELETE_TRACK_WITH_NO_FEEDBACK, UPDATE_FEEDBACK_LEADERBOARD, UPDATE_SERVER_ACTIVITIES_BOARD, SYNC_TRACK_WITH_NO_FEEDBACK
from bot.logging import get_logger

if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider

logger = get_logger("track_service")
class TrackService(BaseService):
    def __init__(self, uow, bot:"ChannelProvider", event_handler) -> None:
        super().__init__(uow=uow, bot=bot)
        self.event_handler = event_handler

    async def add_track(
        self, 
        track_id:int,
        author_id: int, 
        thread_id: int, 
        channel_id: int, 
        title: str, 
        platform: str) -> None:
        
        async with self.uow.transaction() as t:
            exists = await t.users.exists(author_id)

            if not exists:
                return
            
            track_data = {
                "id": track_id,
                "author_id":author_id,
                "thread_id":thread_id,
                "channel_id":channel_id,
                "title":title,
                "platform":platform
            }
        

            await t.tracks.add(track_data=track_data)
        
        await self._safe_emit(SYNC_TRACK_WITH_NO_FEEDBACK, track_id=track_id, total_feedback=0)

        await self._safe_emit(UPDATE_FEEDBACK_LEADERBOARD)
        await self._safe_emit(UPDATE_SERVER_ACTIVITIES_BOARD)

    
    async def delete_track(self, track_id: int) -> None:
        exists = await self.uow.tracks.exists(track_id)

        if not exists:
            return
        
        track_with_no_feedback = await self.uow.tracks.get_track_with_no_feedback(track_id=track_id)
        if track_with_no_feedback:
            await self._safe_emit(DELETE_TRACK_WITH_NO_FEEDBACK, message_id=track_with_no_feedback.message_id)
            
        await self.uow.tracks.delete(track_id)
        await self._safe_emit(UPDATE_FEEDBACK_LEADERBOARD)
        await self._safe_emit(UPDATE_SERVER_ACTIVITIES_BOARD)


    async def update_track(self, track_id: int, track_data: dict) -> None:
        exists = await self.uow.tracks.exists(track_id)

        if not exists:
            return
        
        await self.uow.tracks.update(track_id=track_id, track_data=track_data)

        

    async def increment_track_reaction(self, track_id: int) -> None:
        exists = await self.uow.tracks.exists(track_id=track_id)

        if not exists:
            return
        
        await self.uow.tracks.increment_track_reaction(track_id=track_id)

    async def decrement_track_reaction(self, track_id: int) -> None:
        exists = await self.uow.tracks.exists(track_id=track_id)

        if not exists:
            return
        
        await self.uow.tracks.decrement_track_reaction(track_id=track_id)