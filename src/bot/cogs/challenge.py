from discord.ext.commands import Cog
import discord
from discord import MessageType, RawMessageUpdateEvent, RawMessageDeleteEvent, RawReactionActionEvent, Message, TextChannel, Thread
from bot.logging.decorators import  log_function
from typing import TYPE_CHECKING
from bot.logging import get_logger
from bot.error_handler.decorators import cog_event_handler
from bot.types.common import MonthlyChallengeData

if TYPE_CHECKING:
    from bot.main import Bottekin
    from bot.services.container import ServiceContainer
    from bot.utils.extract_attachment_data import MessageExtractor
    from bot.config import Config

from datetime import UTC, datetime

ATTACHMENT_SUBMISSION = "attachment_submission"
EXTERNAL_SUBMISSION = "external_submission"


logger = get_logger("challenge")

VOTE_EMOJIS = [":thumbsup:", "👍"]
WIN_EMOJIS = [":trophy:", "🏆"]

class ChallengeCog(Cog):
    def __init__(self,bot: "Bottekin", services:"ServiceContainer", extractor:"MessageExtractor", config:"Config") -> None: 
        self.bot = bot
        self.services = services
        self.extractor = extractor
        self.config = config



    @log_function
    def _is_challenge_info_message(self, message: Message) -> bool:
        if message.author.id != self.config.dyno_id:
            return False
        
        if message.channel.id != self.config.challenge_info_channel_id:
            return False
        
        if not message.embeds:
            return False
        
        return True
  

    @Cog.listener()
    @cog_event_handler
    @log_function
    async def on_message(self,message: discord.Message) -> None:
        channel = message.channel
        if isinstance(channel, TextChannel) and channel.id not in [*self.config.all_submission_channel_ids, self.config.challenge_info_channel_id] :
            return
        if isinstance(channel, Thread) and channel.parent_id != self.config.monthly_challenge_channel_id:
            return
        if message.author.id == self.config.bot_id:
            return
        
        logger.bind(
            message=str(message)

        ).info("challenge cog | on_message")
        logger.debug(f"type{message.type}, thread {message.thread}, ch {message.channel}")
        if self._is_challenge_info_message(message=message):
            challenge_embed_data = await self.extractor.extract_embed_data(message_id=message.id, embed=message.embeds[0])
            if not challenge_embed_data:
                logger.bind(
                    message=str(message)
                ).warning("Challenge creation failed")
                return

            await self.services.challenge.create_or_update_challenge(data=challenge_embed_data)
            return
        
        elif message.channel.id in self.config.submission_channel_ids:    
            await self.services.challenge.add_submission(message=message)

        

        elif (isinstance(message.channel, Thread)
            and message.channel.parent_id == self.config.monthly_challenge_channel_id
            and message.thread and message.author.id == self.config.admin_id):
            title_data = self.extractor.is_challenge_month_starter(content=message.content)
            if not title_data:
                return
            day, month, year = title_data
            logger.debug(f"forum message thread: {message.thread} channel: {message.channel}")
            starts_at = message.created_at
            ends_at = datetime(year=starts_at.year, month=starts_at.month+1,day=1, tzinfo=UTC)
            is_active = True if datetime.now(tz=UTC) < ends_at else False
            data = MonthlyChallengeData(
                id=message.id, title=f"{day}_{month}_{year}_monthly_challenge", is_active=is_active, starts_at=starts_at, ends_at=ends_at)
            
            await self.services.challenge.create_or_update_monthly_challenge(data=data)
        
        elif isinstance(message.channel, Thread) and message.channel.parent_id == self.config.monthly_challenge_channel_id and not message.author.bot:
            await self.services.challenge.add_monthly_submission(message=message)

                
    @Cog.listener()
    @cog_event_handler
    @log_function
    async def on_raw_message_delete(self, payload: RawMessageDeleteEvent) -> None:
        if payload.channel_id in self.config.submission_channel_ids:
            logger.bind(
                message_id=str(payload.message_id),
                channel_id=str(payload.channel_id)
            ).info("challenge cog | official submission delete")
            await self.services.challenge.delete_submission(payload.message_id)
            return

        channel = await self.bot.client.safe_discord_call(
            coro=lambda: self.bot.guild.fetch_channel(payload.channel_id), operation="monthly_challenge: on_message delete fetch_channel")
        
        if isinstance(channel, Thread) and channel.parent_id == self.config.monthly_challenge_channel_id:
            logger.bind(
                message_id=str(payload.message_id),
                channel_id=str(payload.channel_id)
            ).info("challenge cog | monthly submission delete")
            await self.services.challenge.delete_monthly_submission(payload.message_id)

    @Cog.listener()
    @cog_event_handler
    @log_function
    async def on_raw_message_edit(self, payload: RawMessageUpdateEvent) -> None:
        if payload.channel_id == self.config.challenge_info_channel_id and payload.message.author.id == self.config.dyno_id and payload.message.embeds:
            logger.bind(
                message_id=str(payload.message_id),
                message=str(payload.message),
                data=str(payload.data)
            ).info("on_raw_message_edit")
            data = await self.extractor.extract_embed_data(
                message_id=payload.message_id, embed=payload.message.embeds[0])
            if not data:
                logger.bind(
                message=str(payload.message)
                ).warning("Challenge data could not retrieved after edit")
                return
                
            await self.services.challenge.create_or_update_challenge(data=data) 
            
            return
        
        elif payload.message.channel.id in self.config.submission_channel_ids:
            logger.bind(
                edited_at=str(payload.message.edited_at)
            ).debug("Submission edited at")


            await self.services.challenge.update_submission(message=payload.message)

        elif (isinstance(payload.message.channel, Thread)
            and payload.message.channel.parent_id == self.config.monthly_challenge_channel_id
            and payload.message.thread and payload.message.author.id == self.config.admin_id):
            title_data = self.extractor.is_challenge_month_starter(content=payload.message.content)
            if not title_data:
                return
            day, month, year = title_data
            logger.debug(f"forum message thread: {payload.message.thread} channel: {payload.message.channel}")
            starts_at = payload.message.created_at
            ends_at = datetime(year=starts_at.year, month=starts_at.month+1,day=1, tzinfo=UTC)
            is_active = True if datetime.now(tz=UTC) < ends_at else False
            
            data = MonthlyChallengeData(
                id=payload.message.id, title=f"{day}_{month}_{year}_monthly_challenge", is_active=is_active, starts_at=starts_at, ends_at=ends_at)
            
            await self.services.challenge.create_or_update_monthly_challenge(data=data)

        elif (isinstance(payload.message.channel, Thread)
              and payload.message.channel.parent_id == self.config.monthly_challenge_channel_id 
              and not payload.message.author.bot):
            
            await self.services.challenge.add_monthly_submission(message=payload.message)


    @Cog.listener()
    @cog_event_handler
    @log_function
    async def on_raw_reaction_add(self, payload:RawReactionActionEvent) -> None:

        if not payload.channel_id in self.config.submission_channel_ids:
            return
 
        
        logger.bind(
        channel_id=str(payload.channel_id),
        emoji=str(payload.emoji),
        message_author_id=str(payload.message_author_id)
        ).info("vote reaction action payload data")
        

        if payload.message_author_id and payload.user_id == self.config.admin_id and str(payload.emoji) in WIN_EMOJIS:
            logger.bind(
            submission_author_id=payload.message_author_id,
            emoji=str(payload.emoji)
            ).info("Chosen winner is being set")

            await self.services.challenge.set_chosen_winner(user_id=payload.message_author_id, submission_id=payload.message_id)


    @Cog.listener()
    @cog_event_handler
    @log_function
    async def on_raw_reaction_remove(self, payload:RawReactionActionEvent) -> None:
        if payload.channel_id in self.config.submission_channel_ids:
            logger.bind(
                message_id=str(payload.message_id),
                reaction_user_id=str(payload.user_id)
            ).info("Challenge cog on_raw_reaction_remove")
            if str(payload.emoji) in WIN_EMOJIS and payload.user_id == self.config.admin_id:
                channel = self.bot.channels.official_submission
                submission_message = await self.bot.client.safe_discord_call(coro=lambda:channel.fetch_message(payload.message_id), operation="challenge_cog:reaction_remove fetch reacted_message")
                if not submission_message:
                    logger.bind(
                        message_id=str(payload.message_id)
                    ).warning("failed to fetch submission message in challenge_cog:remove_reaction task aborted")
                    return

                logger.bind(
                user_id=submission_message.author.id,
                submission_id=submission_message.id
                ).info("Winner is being removed")

                await self.services.challenge.remove_chosen_winner(user_id=submission_message.author.id, submission_id=submission_message.id)


