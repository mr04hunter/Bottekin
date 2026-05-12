from discord.ext.commands import Cog
from discord import DMChannel
import discord
from discord import RawMessageUpdateEvent, RawMessageDeleteEvent, TextChannel, RawReactionActionEvent, ChannelType, Thread, Message, Reaction
from discord import TextChannel
from bot.logging import log_function
from discord.errors import HTTPException
from typing import TYPE_CHECKING, cast
from urlextract import URLExtract
from collections import Counter
from bot.utils.extract_attachment_data import MessageExtractor
from bot.logging import get_logger
from bot.types import FeedbackData, UserData
from bot.error_handler.decorators import cog_event_handler
import asyncio


logger = get_logger("feedback")



feedback_update_job_id = "fetch_feedback_data"

if TYPE_CHECKING:
    from bot.main import Bottekin
    from bot.services.container import ServiceContainer
    from bot.config import Config
    from bot.utils.link_extractor import TrackDataExtractor


class FeedbackCog(Cog):
    def __init__(self, bot: "Bottekin", services: "ServiceContainer", config:"Config", track_extractor:"TrackDataExtractor") -> None:
        self.bot=bot
        self.services = services
        self.config = config
        self.track_extractor = track_extractor


    
    @Cog.listener()
    @cog_event_handler
    @log_function
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent) -> None:
       
        logger.debug(f"Message delete called\nMessage_id: {payload.message_id}\nchannel_id: {payload.channel_id}")
        thread = await self.bot.client.safe_discord_call(coro=lambda:self.bot.fetch_channel(payload.channel_id), operation="feedback_cog on_raw_message_delete")
        if not thread:
            logger.bind(
                channel_id=str(payload.channel_id)
            ).warning("Channel not found")
            return
        thread = cast(Thread, thread)
        if isinstance(thread,DMChannel):
            return
        thread_id = thread.id
        if thread.type == discord.ChannelType.text and thread_id not in self.config.feedback_channel_ids:
            logger.debug("Unrelated message delete on feedback cog returning")
            return

        if thread.type == discord.ChannelType.text and thread_id in self.config.feedback_channel_ids:
            await self.services.track.delete_track(track_id=payload.message_id)
            thread = await self.bot.client.safe_discord_call(coro=lambda:self.bot.fetch_channel(payload.message_id), operation="feedback_cog:message_delete_event", default=None)
            if not thread:
                logger.bind(
                    thread_id=str(payload.message_id)
                ).warning("Thread for message could not found task aborted")
                return
            thread = cast(Thread, thread)
            await self.bot.client.safe_discord_write_call(
                coro=lambda:thread.delete(), operation="feedback_cog track delete")
             
            return
        if thread and thread.parent_id not in self.config.feedback_channel_ids:
            logger.debug(f"CHANNEL NOT FOUND")
            return
        elif (thread.type == ChannelType.private_thread or thread.type == ChannelType.public_thread) and thread.parent_id in self.config.feedback_channel_ids:
            await self.services.feedback.delete_feedback(thread_id= thread.id, feedback_id=payload.message_id)
    
    @Cog.listener()
    @cog_event_handler
    @log_function
    async def on_raw_message_edit(self,payload: RawMessageUpdateEvent) -> None:
        if payload and payload.message and payload.cached_message:   
            if payload.message.content == payload.cached_message.content:
                return
            thread = await self.bot.client.safe_discord_call(coro=lambda:self.bot.fetch_channel(payload.message.channel.id), operation="feedback_cog:message_edit fetch_channel")
            if not thread:
                logger.bind(
                    channel_id=str(payload.message.channel.id)
                ).warning("Channel not found in feedback_cog:on_raw_message_edit")
                return
            
            if isinstance(thread, TextChannel) and thread.id in self.config.feedback_channel_ids:
                if not payload.cached_message.thread:
                    return
                logger.bind(
                    message=str(payload.message)
                ).info(f"[Feedback] Message update: {payload.channel_id}")
                if thread.id in self.config.feedback_attachment_channel_ids:
                    if not payload.message.attachments:
                        logger.bind(
                            message=str(payload.message)
                        ).warning("Attachment removed on track")
                    new_title = MessageExtractor.get_title(payload.message.attachments[0])
                    platform = "attachment"
                    
                    
                else:
                    url_extractor = URLExtract()
                    links = url_extractor.find_urls(payload.message.content)
                    if not links:
                        return
                    new_title, platform = await self.track_extractor.extract_title(url=str(links[0]))
                    if not new_title:
                        logger.error(f"Error on message edit, title could not extracted")
                        return
                await self.services.track.update_track(track_id=payload.message_id, track_data={"title":new_title, "platform":platform})
                return

        
        new_content = payload.message.content
        new_word_count = len(new_content.split())
        await self.services.feedback.update_feedback(feedback_id=payload.message.id, feedback_data={"word_count":new_word_count, "content":new_content})



    async def _get_user_reaction_count(self, user_id: int, reactions:list[Reaction]) -> int:
        reacted_users = []

        for reaction in reactions:
            after_member = None
            while True:
                users = await self.bot.client.safe_fetch_reaction_users(reaction=reaction,operation="feedback_cog fetch_track_reactions",limit=100, after=after_member) 
                users = [user for user in users if not user.bot]               
                if users:
                    logger.bind(
                        users=str(users)
                    ).debug("reaction users")
    

                if not users:
                    break
                
                reacted_users.extend([user.id for user in users])
                after_member = users[-1] 
                await asyncio.sleep(0.2) 
        
        c = Counter(reacted_users)
        return c.get(user_id, 0)

    @Cog.listener()
    @cog_event_handler
    @log_function
    async def on_raw_reaction_add(self, payload:RawReactionActionEvent) -> None:
        if payload.member:
            if payload.member.bot:
                return
            if payload.member.id == payload.message_author_id:
                return
            
            channel = await self.bot.client.safe_discord_call(coro=lambda:self.bot.fetch_channel(payload.channel_id), operation="feedback_cog:reaction_add")
            if not channel:
                logger.warning("Failed to fetch channel in feedback_cog:reaction_add_event")
                return
            channel = cast(TextChannel | Thread, channel)
            reacted_message = await self.bot.client.safe_discord_call(coro=lambda:channel.fetch_message(payload.message_id), operation="feedback_cog:fetch reacted_message")
            if not reacted_message:
                logger.bind(
                    message_id=str(payload.message_id)
                ).warning("failed to fetch the reacted message, task aborted")
                return
            

            

            user_reaction_count = await self._get_user_reaction_count(user_id=payload.member.id, reactions=reacted_message.reactions)
            if user_reaction_count >= 2:
                logger.debug(f"User has already reacted.\nReturning...")
                return

            if channel.type == ChannelType.public_thread or channel.type == ChannelType.private_thread:
                pass

            elif channel.type == ChannelType.text:
                if channel.id not in self.config.feedback_channel_ids:
                    return
                await self.services.track.increment_track_reaction(track_id=payload.message_id)

    @Cog.listener()
    @cog_event_handler
    @log_function
    async def on_raw_reaction_remove(self, payload:RawReactionActionEvent) -> None:
        if self.bot.user:
            if payload.user_id == self.bot.user.id:
                return
        
            channel = await self.bot.client.safe_discord_call(coro=lambda:self.bot.fetch_channel(payload.channel_id), operation="feedback_cog:reaction_remove")
            if not channel:
                logger.bind(
                    channel_id=str(payload.channel_id)
                ).warning("Failed to fetch channel in feedback_cog:reaction_remove")
                return
            channel = cast(TextChannel | Thread, channel)
            if channel.type == ChannelType.text and channel.id not in self.config.feedback_channel_ids:
                return
            elif (channel.type == ChannelType.private_thread or channel.type == ChannelType.public_thread) and channel.parent_id not in self.config.feedback_channel_ids:
                return
            message = await self.bot.client.safe_discord_call(coro=lambda:channel.fetch_message(payload.message_id), operation="feedback_cog:reaction_remove fetch reacted message")
            if not message:
                logger.bind(
                    message_id=str(payload.message_id)
                ).warning("Failed to fetch the reacted message in feedback_cog:reaction_remove task aborted")
                return
            if payload.user_id == message.author.id:
                return
            if channel.type == ChannelType.public_thread or channel.type == ChannelType.private_thread:
                pass
                # await self.db.decrement_feedback_reaction(feedback_id=payload.message_id)
            elif channel.type == ChannelType.text:
                if channel.id not in self.config.feedback_channel_ids:
                    return
                await self.services.track.decrement_track_reaction(track_id=payload.message_id)

    @Cog.listener()
    @cog_event_handler
    async def on_message(self, message: Message) -> None:
        if message.author.bot:
            return
        channel = cast(TextChannel | Thread, message.channel)
        logger.bind(
            channel_name=str(cast(TextChannel,message.channel).name),
            message=str(message)
        ).info(f"[Feedback] On Message")

        if message.channel.id in self.config.feedback_channel_ids:
            channel = cast(TextChannel, channel)
            try:
                await message.create_thread(name=f"Thread for {message.author.display_name}")
            except HTTPException as e:
                logger.bind(
                    error=str(e),
                    message=str(message)
                ).warning(f"Thread already created (potential clash)")
            
            await self.handle_feedback_track(message, channel)
       
        elif (message.channel.type == ChannelType.public_thread or message.channel.type==ChannelType.private_thread):
                channel = cast(Thread, channel)
                if channel.parent_id in self.config.feedback_channel_ids:
                    thread = await self.bot.client.safe_discord_call(coro=lambda:self.bot.fetch_channel(message.channel.id), operation="feedback_cog:on_message fetch_channel")
                    if not thread:
                        logger.warning("Failed to fetch thread in feedback_cog:on_message")
                        return
                    thread = cast(Thread, thread)
                
                    if thread.parent_id in self.config.feedback_channel_ids:
                        parent_channel = cast(TextChannel, thread.parent)
                        track_message = await self.bot.client.safe_discord_call(coro=lambda:parent_channel.fetch_message(thread.id), operation="feedback_cog: fetch track message")
                        if not track_message:
                            logger.bind(
                                message_id=str(thread.id)
                            ).warning("Track message does not exist task aborted")
                            return
                        if message.author.id != track_message.author.id:
                            await self.handle_feedback(message,thread)


        
    @log_function
    async def handle_feedback_track(self, message: Message, channel: TextChannel) -> None:
        url_extractor = URLExtract()
        track_id = message.id
        thread_id = message.id
        channel_id = channel.id
        author_id = message.author.id
        if channel_id in self.config.feedback_link_channel_ids:
            urls = url_extractor.find_urls(message.content)
            logger.debug(f"track links {urls}")
            if not urls:
                return
            
            track_title, platform = await self.track_extractor.extract_title(url=str(urls[0]))
            logger.debug(f"Title: {track_title} Platform: {platform}")

        else:
            attachments = message.attachments
            if not attachments:
                logger.bind(
                    message=str(message)
                ).warning(f"[Feedback] Attachment not found on message")
                return
            
            content_type = attachments[0].content_type
            if not content_type:
                content_type = "audio" if attachments[0].filename.lower().endswith(".wav") or attachments[0].filename.lower().endswith(".mp3") else "invalid"

            if not content_type.lower().startswith("audio"):
                logger.bind(
                    content_type=str(attachments[0].content_type),
                    message=str(message)
                ).warning(f"[Feedback] Invalid content type on message")
                return
            logger.bind(
                attachments=str(attachments),
                title=str(attachments[0].title),
                filename=str(attachments[0].filename)
            ).debug(f"[Feedback] Attachments")
            track_title = MessageExtractor.get_title(attachment=attachments[0])
                
            
            platform = "attachment"
        
        await self.services.track.add_track(track_id=track_id, author_id=author_id, thread_id=thread_id, channel_id=channel_id, title=track_title, platform=platform)
        await message.add_reaction("👍")
        logger.bind(
            channel_name=str(cast(TextChannel,message.channel).name),
            message=str(message)
        ).info(f"Track added")


    @log_function
    async def handle_feedback(self, message: Message, thread: Thread) -> None:
        id = message.id
        track_id = thread.id
        author_id = message.author.id
        content = message.content
        channel_id = thread.parent_id
        word_count = len(content.split())
        is_valid, reason = await self.services.feedback.validator.validate(
            author_id=author_id,
            thread_id=thread.id,
            content=content,
            word_count=word_count,
        )
        if not is_valid:
            logger.bind(
                feedback_id=id,
                author_id=author_id,
                reason=reason
            ).info("Feedback rejected")
            return

        user_data = UserData(
            id=author_id,
            display_name=message.author.display_name,
            username=message.author.name
        )
        feedback_data = FeedbackData(
            id=message.id,
            track_id=track_id,
            author=user_data,
            channel_id=channel_id,
            content=content, 
            word_count=word_count
        )
        await self.services.feedback.add_feedback(data=feedback_data)
        await message.add_reaction("👍")
 
    
 