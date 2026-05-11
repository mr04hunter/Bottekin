import asyncio
from datetime import UTC, datetime, timedelta
from discord import Message, TextChannel, Thread, Object, NotFound
from bot.database.unit_of_work import UnitOfWork
from bot.events.event import SYNC_TRACK_WITH_NO_FEEDBACK
from bot.types.protocols import ChannelProvider
from bot.utils.message_detector import MessageDetector
from bot.logging import get_logger
from bot.services.base_service import BaseService
from typing import TYPE_CHECKING
from bot.error_handler.decorators import background_task
from bot.error_handler.error_handler import BotDatabaseException  

if TYPE_CHECKING:
    from bot.events.event import Emitter

logger = get_logger("feedback_sync")

class FeedbackSyncService(BaseService):
    def __init__(self, uow: UnitOfWork, bot: ChannelProvider, event_handler:"Emitter") -> None:
        super().__init__(uow, bot)
        self.event_handler = event_handler

    def is_valid_feedback(self,message:Message, author_thread_pairs:set, thread_id:int) -> bool:
        
        if (message.author.id, thread_id) in author_thread_pairs:
            logger.bind(
                pair=f"{message.author.id}, {thread_id}"
            ).info("Invalid author_id, thread_id pair")
            return False
        word_list = [word for word in message.content.replace("?","").replace(".","").replace("/","").replace(";","").replace(",","").split() if word.isalpha()]
        word_count = len(word_list)
        if word_count < 2:
            logger.bind(
                word_list=word_list,
                word_count=word_count
            ).info("Too little words")
            return False
        if MessageDetector.is_duplicated_words(word_list=word_list,word_count=word_count):
            logger.bind(
                word_list=word_list[:10]
            ).info(f"Duplicated content")
            return False
        if MessageDetector.is_gibberish(words=word_list):
            logger.bind(
                word_list=word_list[:10]
            ).info(f"Gibberish content")
            return False
        
        return True

    async def get_all_threads(
        self, 
        channel: TextChannel,
        author_track_ids:dict[int,int]) -> set[Thread]:


        fetched = []

        open_threads = list(channel.threads)

        for tid in author_track_ids.keys():
            thread = channel.get_thread(tid)
            if thread:
                fetched.append(thread)
                continue
            
            await asyncio.sleep(0.2)
            
            thread = await self.bot.client.safe_discord_call(coro=lambda:self.bot.guild.fetch_channel(tid), operation="feedback_sync_service",default=None)
            if thread:
                fetched.append(thread)

        archived_threads = await self.bot.client.safe_fetch_threads(channel=channel, operation="feedback_sync fetch_all_threads", default=[])

    

        threads = set(open_threads+archived_threads+fetched)
        logger.bind(
            threads=str(threads)
        ).debug("Threads on channel")

        return threads            

    async def sync_thread(
        self,
        thread: Thread,
        author_track_ids: dict[int,int],
        existing_user_ids: set[int],
        channel: TextChannel) -> None:
        
        feedback_ids_in_thread = set()
        after_date = None
        track_id = thread.id if thread.id in author_track_ids else None
        author_thread_pairs: set[tuple[int, int]] = set()
        feedbacks = []
        feedback_track_data = []
        logger.debug("Sync thread started")
        total_feedback_on_track = 0
        while True:
            messages = await self.bot.client.safe_fetch_messages(channel=thread, operation="feedback_sync_thread",limit=100, oldest_first=True, after=after_date)
            messages = [message for message in messages
                        if message.author.id in existing_user_ids
                        and author_track_ids.get(thread.id, None) != message.author.id]
            

            if not messages:
                logger.bind(thread_id=str(thread.id)).debug("No more feedback messages in thread")
                break
            

            logger.bind(
                messages=[message.content for message in messages if messages]
            ).debug("Messages in sync_thread")

            for message in messages:

                if not self.is_valid_feedback(message=message, author_thread_pairs=author_thread_pairs,thread_id=thread.id):
                    logger.debug("Invalid feedback message")
                    continue
                
                feedbacks.append(
                            {
                            "id":message.id,
                            "channel_id":channel.id,
                            "track_id":track_id,
                            "content":message.content,
                            "author_id":message.author.id,
                            "thread_id":thread.id,
                            "word_count":len(message.content.split()),
                            "created_at":message.created_at,
                            "edited_at":message.edited_at}  
                            )
                
                total_feedback_on_track += 1
                feedback_ids_in_thread.add(message.id)
                author_thread_pairs.add((message.author.id, thread.id))
                if track_id:
                    feedback_track_data.append( {
                        "feedback_id":message.id,
                        "user_id":message.author.id,
                        "track_id":track_id
                    })

                if len(feedbacks) >= 100:
                    feedback_ids_in_batch = [feedback["id"] for feedback in feedbacks]
                    author_ids_in_batch = [feedback["author_id"] for feedback in feedbacks]
                    logger.debug("bulk inserting feedbacks")
                    async with self.uow.transaction() as t:
                        await t.feedback.bulk_delete_with_author_threads(feedback_ids=feedback_ids_in_batch, author_ids=author_ids_in_batch, thread_id=thread.id)
                        await t.feedback.bulk_insert_feedback(feedbacks=feedbacks)
                        if feedback_track_data:
                            await t.feedback.bulk_update_relations(feedback_track_data=feedback_track_data)
                    feedbacks.clear()
                    feedback_track_data.clear()
                    logger.debug("bulk inserted feedbacks")
                        

            logger.bind(thread_id=str(thread.id)).debug("Thread sync completed")
            if messages:
                after_date = Object(id=messages[len(messages)-1].id)
                
        

        if feedbacks:
            feedback_ids_in_batch = [feedback["id"] for feedback in feedbacks]
            author_ids_in_batch = [feedback["author_id"] for feedback in feedbacks]
            logger.debug("Adding remaining feedbacks")
            async with self.uow.transaction() as t:
                await t.feedback.bulk_delete_with_author_threads(feedback_ids=feedback_ids_in_batch, author_ids=author_ids_in_batch, thread_id=thread.id)
                await t.feedback.bulk_insert_feedback(feedbacks=feedbacks)
                if feedback_track_data:
                    await t.feedback.bulk_update_relations(feedback_track_data=feedback_track_data)
            
            logger.debug("Added remaining feedbacks")
        
        if track_id and thread.created_at:
            if thread.created_at >= datetime.now(tz=UTC) - timedelta(days=14):
                await self._safe_emit(SYNC_TRACK_WITH_NO_FEEDBACK, track_id=track_id, total_feedback=total_feedback_on_track)

        await self.uow.feedback.cleanup_feedbacks_on_thread(
                thread_id=thread.id, feedback_ids=feedback_ids_in_thread, 
                after=None, before=None)


    @background_task(operation_name="feedback_channel_sync")
    async def sync_channel(
        self,
        channel:TextChannel,
        author_track_ids:dict[int,int],
        existing_user_ids: set[int]
            ) -> None:
        logger.info(f"Scanning feedback channels...")


                    
        threads = await self.get_all_threads(channel=channel, author_track_ids=author_track_ids)
        thread_ids = {thread.id for thread in threads}
        await self.uow.feedback.cleanup_feedbacks(thread_ids=thread_ids, channel_id=channel.id)
        
        for thread in threads:
            logger.debug(f"THREAD ID {thread.id}")
            await self._sync_thread_safe(
                thread=thread,
                channel=channel,
                existing_user_ids=existing_user_ids,
                author_track_ids=author_track_ids)
            
            await asyncio.sleep(0.2)


 
    
    async def _sync_thread_safe(self, thread, channel, existing_user_ids, author_track_ids) -> None:
        """Per-thread sync with isolated error handling."""
        try:
            await self.sync_thread(
                thread=thread,
                channel=channel,
                existing_user_ids=existing_user_ids,
                author_track_ids=author_track_ids,
            )
        except BotDatabaseException as e:
            logger.bind(
                thread_id=thread.id,
                error=str(e),
            ).error("DB error syncing thread, skipping")
        except NotFound:
            logger.bind(thread_id=thread.id).debug("Thread deleted during sync, skipping")
        except Exception as e:
            logger.bind(
                thread_id=thread.id,
                error=str(e),
            ).error("Unexpected error syncing thread, skipping")