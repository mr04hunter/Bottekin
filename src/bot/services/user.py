from discord import TextChannel, Thread
from bot.database.models import User
from bot.database.unit_of_work import UnitOfWork
from bot.events.event import UPDATE_CURRENT_CHALLENGE_LEADERBOARD, UPDATE_SUBMISSIONS_LEADERBOARD, UPDATE_WINNERS_LEADERBOARD, UPDATE_FEEDBACK_LEADERBOARD
from bot.logging import get_logger
from bot.services.base_service import BaseService
from bot.types import UserData
from bot.types.protocols import ChannelProvider
logger = get_logger("user_service")

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from bot.events.event import Emitter

class UserService(BaseService):
    def __init__(self, uow: UnitOfWork, bot: ChannelProvider, event_handler:"Emitter") -> None:
        super().__init__(uow, bot)
        self.event_handler = event_handler

    async def create_user(self,
        user_id: int, 
        username: str,
        display_name: str,
        is_purge_data: bool = False
    ) -> None:
        
        exists = await self.uow.users.exists(user_id)

        if exists:
            await self.uow.users.update(
                user_id=user_id,
                data={"username":username,
                "display_name":display_name,
                "is_purge_data":is_purge_data})
        
        else:
            await self.uow.users.create(
                UserData(
                id=user_id,
                username=username,
                display_name=display_name,
                is_purge_data=is_purge_data
                )
            )
    
    async def get_user(self, user_id:int) -> User | None:
        user = await self.uow.users.get_by_id(user_id=user_id)
        return user

        
    async def delete_user(self, user_id: int) -> None:
        
        await self.uow.users.delete(user_id)
        await self._safe_emit(UPDATE_SUBMISSIONS_LEADERBOARD)
        await self._safe_emit(UPDATE_CURRENT_CHALLENGE_LEADERBOARD)
        await self._safe_emit(UPDATE_WINNERS_LEADERBOARD)
        await self._safe_emit(UPDATE_FEEDBACK_LEADERBOARD)


    async def change_stats(self, user_id: int, field: str, count:int) -> None:
        await self.uow.users.increment_stat(user_id=user_id, field=field, count=count)
        await self._safe_emit(UPDATE_SUBMISSIONS_LEADERBOARD)
        await self._safe_emit(UPDATE_CURRENT_CHALLENGE_LEADERBOARD)
        await self._safe_emit(UPDATE_WINNERS_LEADERBOARD)
        await self._safe_emit(UPDATE_FEEDBACK_LEADERBOARD)

    async def set_purge_data(self, user_id: int, purge: bool) -> None:
        exists = await self.uow.users.exists(user_id)

        if not exists:
            return
        
        await self.uow.users.set_purge_data(user_id=user_id, purge=purge)

    async def get_with_stats(self, user_id: int) -> User | None:
        user = await self.uow.users.get_with_stats(user_id=user_id)
        
        return user

    async def handle_member_leave(self, user_id: int) -> None:
        tracks_to_notify = []

    
        user = await self.uow.users.get_by_id(user_id)
        if not user:
            return

        tracks_to_notify = await self.uow.tracks.get_for_user(user_id)

        if user.is_purge_data:
            await self.uow.users.delete(user_id)

        for track in tracks_to_notify:
            try:
                await self._notify_track_thread(track, user_id)
            except Exception as e:
                logger.bind(track_id=track.id, error=str(e)).warning(
                    "Failed to notify track thread after user leave"
                )

        await self._safe_emit(UPDATE_SUBMISSIONS_LEADERBOARD)
        await self._safe_emit(UPDATE_CURRENT_CHALLENGE_LEADERBOARD)
        await self._safe_emit(UPDATE_WINNERS_LEADERBOARD)
        await self._safe_emit(UPDATE_FEEDBACK_LEADERBOARD)

    async def _notify_track_thread(self, track, user_id:int) -> None:
        from discord import TextChannel
        from typing import cast
        channel = self.bot.guild.get_channel(track.channel_id)
        if not channel:
            channel = await self.bot.client.safe_discord_call(coro=lambda t=track:self.bot.guild.fetch_channel(t.channel_id), operation="user_service fetch track channel", default=None)
            if not channel:
                logger.warning("Could not fetch channle on notify_track_thread, task aborted")
                return 
                
        channel = cast(TextChannel, channel)
        message = await self.bot.client.safe_discord_call(coro=lambda t=track,ch=channel:ch.fetch_message(t.id), operation="user left notification fetch message")
        if not message:
            return
        if message.thread:
            notif_message = await self.bot.client.safe_discord_write_call(coro=lambda th=message.thread:th.send("**The author of this track has left the server.**"), operation="notify user left send message")
            if not notif_message:
                return
           
            await self.uow.tracks.create_user_left_notif_message(user_id=user_id, channel_id=notif_message.channel.id, message_id=notif_message.id)


    async def clean_user_left_messages(self, user_id):
        notif_messages = await self.uow.tracks.get_user_left_notifications(user_id=user_id)

        if not notif_messages:
            return
        
        for notif_message in notif_messages:
            channel = await self.bot.client.safe_discord_call(coro=lambda msg=notif_message:self.bot.guild.fetch_channel(msg.channel_id), operation="get_thread_of_user_left_notification_message")

            if not isinstance(channel, Thread):
                logger.bind(
                    channel_id=str(notif_message.channel_id)
                ).warning(f"Channel not found for user left notification")
                continue

            message = await self.bot.client.safe_discord_call(coro=lambda ch=channel,msg=notif_message:ch.fetch_message(msg.message_id), operation="user_left_notif_retrieve")
            if not message:
                continue

            await self.bot.client.safe_discord_call(coro=lambda msg=message:msg.delete(),operation="user_left_notif_delete")





