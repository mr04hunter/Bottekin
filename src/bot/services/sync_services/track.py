import asyncio
import datetime
from discord import Message, TextChannel, Reaction, Object, NotFound
from bot.database.unit_of_work import UnitOfWork
from bot.logging import get_logger
from bot.services.base_service import BaseService
from bot.types.protocols import ChannelProvider
from typing import TYPE_CHECKING
from bot.error_handler.decorators import background_task
if TYPE_CHECKING:
    from bot.utils.extract_attachment_data import MessageExtractor


logger = get_logger("track_sync")



class TrackSyncService(BaseService):
    def __init__(
        self,
        uow: UnitOfWork, 
        bot: ChannelProvider,
        extractor:"MessageExtractor"
        ) -> None:
        super().__init__(uow, bot)
        self.extractor = extractor
        self._reaction_semaphore = asyncio.Semaphore(1)
        self._track_semaphore = asyncio.Semaphore(3)

    async def _get_total_reactions(self, author_id: int, reactions:list[Reaction]) -> int:
        reacted_users = set()
        
        for reaction in reactions:
            after_member = None
            while True:
                users = await self.bot.client.safe_fetch_reaction_users(reaction=reaction,operation="track_sync_service fetch_track_reactions",limit=100, after=after_member) 
                users = [user for user in users if not user.bot and user.id != author_id]               
                if users:
                    logger.bind(
                        users=str(users)
                    ).debug("reaction users")
                
                if not users:
                    break
                
                
                reacted_users.update(users)
                after_member = users[-1] 
                await asyncio.sleep(0.2) 
        return len(reacted_users)


    @background_task(operation_name="sync_track_channel")
    async def sync_channel(self, channel: TextChannel, existing_user_ids: set[int]) -> dict[int,int]:
        author_track_ids: dict[int,int] = {}  
        tracks = []
        after_date = None
        before_date = None

    
 
        async def process_message(message: Message):
            async with self._track_semaphore:
                title_platform = await self.extractor.extract_track_message_title(message)
                if not title_platform:
                    return (None, None, None, None)
                title, platform = title_platform
                if not message.thread:
                    try:
                        await message.create_thread(name=f"Thread for {message.author.display_name}") 
                    except:
                        logger.warning(f"Failed to create thread for message {message.id}")
                total_reactions = await self._get_total_reactions(
                    author_id=message.author.id,
                    reactions=message.reactions
                )
                await asyncio.sleep(0.1) 
                return (message, title, platform, total_reactions)
            

        while True:
            messages = await self.bot.client.safe_fetch_messages(channel=channel, operation="sync_track", limit=100, oldest_first=True, after=after_date)
            messages = [message for message in messages if message.author.id in existing_user_ids]
            if not messages:
                break
            
            results = await asyncio.gather(*[
            process_message(m) for m in messages
            ])

            for result in results:
                if not result[0]:
                    continue
                message, title, platform, total_reactions = result
                author_track_ids[message.id] = message.author.id
                tracks.append({
                    "id":message.id,
                    "title":title,
                    "platform":platform,
                    "author_id":message.author.id,
                    "thread_id":message.id,
                    "channel_id":message.channel.id,
                    "total_reactions":total_reactions,
                    "created_at":message.created_at, 
                    "edited_at":message.edited_at
                })

            if len(tracks) >= 100:
                await self.uow.tracks.bulk_insert_track(tracks=tracks)
                tracks.clear()
            

            
            after_date = Object(id=messages[len(messages)-1].id)
            await asyncio.sleep(0.2) 

        if tracks:
            await self.uow.tracks.bulk_insert_track(tracks=tracks)

        await self.uow.tracks.cleanup_tracks(
                channel_id=channel.id, track_ids=set(author_track_ids.keys()), 
                after=None, before=None)

        return author_track_ids


    