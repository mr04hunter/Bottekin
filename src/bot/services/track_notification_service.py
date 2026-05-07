import asyncio
from bot.database.unit_of_work import UnitOfWork
from bot.logging import get_logger
from discord import NotFound, Object
from datetime import datetime, timedelta, UTC
from bot.services.base_service import BaseService
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider

logger = get_logger("track_notification_service")



class TrackNotificationService(BaseService):
    def __init__(self, uow: UnitOfWork, bot: "ChannelProvider") -> None:
        super().__init__(uow, bot)


    
    async def sync_track_with_no_feedback(self, track_id: int, total_feedback: int) -> None:
        async with self.uow.transaction() as t:
            track_with_no_feedback = await t.tracks.get_track_with_no_feedback(track_id=track_id)
            if total_feedback < 3 and not track_with_no_feedback:
                try:
                    thread = await self.bot.channels.tracks_no_feedback.guild.fetch_channel(track_id)
                    message = await self.bot.channels.tracks_no_feedback.send(f"{thread.jump_url} | Total feedback: {total_feedback}")
                    await t.tracks.create_track_with_no_feedback(track_id=thread.id, message_id=message.id, url=thread.jump_url, created_at=message.created_at)
                except NotFound as e:
                    logger.bind(
                        error=str(e)
                    ).warning(f"Error on creating track_with_no_feedback")
                    return
            elif total_feedback >= 3 and track_with_no_feedback:
                try:
                    message = await self.bot.channels.tracks_no_feedback.fetch_message(track_with_no_feedback.message_id)
                    await message.delete()
                    await t.tracks.delete_track_with_no_feedback(track_id=track_id)
                except NotFound as e:
                    logger.bind(
                        error=str(e)
                    ).warning(f"Error on removing track_with_no_feedback")
                    return
            elif total_feedback < 3 and track_with_no_feedback:
                thread = await self.bot.channels.tracks_no_feedback.guild.fetch_channel(track_id)
                try:
                    message = await self.bot.channels.tracks_no_feedback.fetch_message(track_with_no_feedback.message_id)
                    await message.edit(content=f"{thread.jump_url} | Total feedback: {total_feedback}")
                except NotFound as e:
                    logger.bind(
                        error=str(e)
                    ).warning("Failed to edit the track_with_no_feedback message Proceeding to create it")
                    
                    message = await self.bot.channels.tracks_no_feedback.send(f"{thread.jump_url} | Total feedback: {total_feedback}")
                    await t.tracks.create_track_with_no_feedback(track_id=thread.id, message_id=message.id, url=thread.jump_url, created_at=message.created_at)
                    return
                

    async def cleanup_tracks_no_feedback(self) -> None:
        before = datetime.now(tz=UTC) - timedelta(days=14)
        message_ids = set(await self.uow.tracks.cleanup_track_with_no_feedback(before=before))
        logger.bind(
            valid_message_ids=str(message_ids)
        ).debug(f"Valid message_ids in cleanup_tracks_no_feedback")

        after = None
        while True: 
            messages = await self.bot.client.safe_fetch_messages(channel=self.bot.channels.tracks_no_feedback,operation="cleanup_track_with_no_feedback_channel",limit=100, oldest_first=True, after=after)
            if not messages:
                break
            for message in messages:
                if message.id not in message_ids:
                    await message.delete()
                    await asyncio.sleep(0.5)
            after = Object(id=messages[len(messages)-1].id)
    


    async def delete_track_with_no_feedback_message(self, message_id: int) -> None:
        try:
            message = await self.bot.channels.tracks_no_feedback.fetch_message(message_id)
            await message.delete()
        except Exception as e:
            logger.bind(
                error=str(e),
                message_id=str(message_id)
            ).warning(f"Track with no feedback message delete operation failed")