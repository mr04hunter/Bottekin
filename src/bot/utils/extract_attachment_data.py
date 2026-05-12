from discord import Attachment, Message, Reaction
import discord
from bot.error_handler.decorators import background_task
from bot.types.common import ChallengeEmbedData, ChallengeDurationData
import re
from bot.logging import get_logger
from datetime import datetime, UTC, timedelta
from typing import TYPE_CHECKING
from urlextract import URLExtract
from bot.database.models import Challenge, Vote, Winner

if TYPE_CHECKING:
    from bot.bottekin import Bottekin
    from bot.config import Config
    from bot.utils.link_extractor import TrackDataExtractor

logger = get_logger("extract_attachment")

class MessageExtractor:
    def __init__(self, bot: "Bottekin", config:"Config", track_extractor:"TrackDataExtractor") -> None:
        self.bot = bot
        self.config = config
        self.track_extractor = track_extractor


    async def get_submission_title(self, message: Message) -> str:
        url_extractor = URLExtract()
        urls = url_extractor.find_urls(text=message.content)

        if message.attachments:
            title = MessageExtractor.get_title(message.attachments[0])
        else:
            title, _ = await self.track_extractor.extract_title(str(urls[0]))

        return title


    def is_challenge_month_starter(self, content: str) -> tuple[str, str, str] | None:
        """ Parses the message content and returns the challenge month title.
            Monthly challenge starter messages start with *DAY 1 (day/month/year)*
        """

        r = r"DAY 1[^0-9]*\(([0-9]{2})\.([0-9]{2})\.([0-9]{4})\)"

        matches = re.findall(r, content)

        if matches:
            return matches[0]


    async def extract_embed_data(self, message_id: int, embed: discord.Embed) -> ChallengeEmbedData | None:
        host_id = None
        if embed.fields:
            is_ongoing_voting = True
            is_active = True
            fields = {field.name.lower().replace(":",""): field.value.lower()
                    for field in embed.fields if field and field.value is not None and field.name is not None}
            
            if fields:
                challenge_duration = fields.get("challenge duration")
                if not challenge_duration:
                    logger.warning(str(fields))
                    logger.warning("Field: Challenge duration is not found")
                    return
                title = fields.get("title")
                if not title:
                    logger.bind(
                        embed=str(embed),
                        fields=str(fields)
                    ).warning("Title not found in embed")
                    return 
                
                description = fields.get("task description")
                if not description:
                    description = "unknown description"

                logger.bind(
                fields=fields
                ).debug("fields on challenge save")
                duration_data = self.extract_the_time_code(challenge_duration)
                if not duration_data:
                    logger.bind(
                        fields=str(fields)
                    ).warning(f"Challenge duration data not found")
                    return

                logger.bind(
                starts_at=str(duration_data.starts_at),
                ends_at=str(duration_data.ends_at),
                voting_ends_at=str(duration_data.voting_ends_at)
                ).info(f"Challenge duration")


                if duration_data.voting_ends_at.timestamp() < datetime.now(tz=UTC).timestamp():
                    logger.bind( 
                    end_date=str(duration_data.ends_at),
                    vote_end_date=str(duration_data.voting_ends_at),
                    current_date=str(datetime.now(tz=UTC))
                    ).debug("Last challenge is ended (no ongoing voting) leaving it to fetch_and_store_challenge_data")

                    is_ongoing_voting = False
                    
                if duration_data.ends_at.timestamp() < datetime.now(tz=UTC).timestamp():
                    logger.bind(
                        end_date=str(duration_data.ends_at)
                    ).debug("Challenge has already ended setting is_active to false")
                    is_active = False


                if "host" in fields:
                    host_member = await self.bot.client.safe_discord_call(coro=lambda:self.bot.get_member_named(fields["host"].strip()), operation="extractor:extract_embed_data: fetch_member_named")

                    logger.info(f"HOST MEMBER: {host_member}")
                    if host_member:
                        host_id = host_member.id
                type = "community" if "host" in fields else "official"
                
                return ChallengeEmbedData(
                    id=message_id,field_names=list(fields.keys()), 
                    field_values=list(fields.values()),
                    title=title, description=description, type=type,
                    duration=duration_data,
                    is_active=is_active, is_ongoing_voting=is_ongoing_voting,
                    host_id=host_id)
            
    @staticmethod
    def extract_the_time_code(content:str) -> ChallengeDurationData | None:
        logger.bind(
        content=content
        ).debug("Received raw time string")

        r = r"<t:(\d{10}|\d{13})>"
        groups = re.findall(pattern=r, string=content)
        if not len(groups) == 2:
            logger.error("Missing date")
            return
        start_unix = int(groups[0]) if len(str(groups[0])) == 10 else int(groups[0])/1000
        end_unix = int(groups[1]) if len(str(groups[1])) == 10 else int(groups[1])/1000
        start_date = datetime.fromtimestamp(start_unix, tz=UTC)
        end_date = datetime.fromtimestamp(end_unix, tz=UTC)
        vote_end_date = end_date + timedelta(days=1)

        logger.bind(
            start_date=str(start_date),
            end_date=str(end_date),
            vote_end_date=str(vote_end_date)
        ).debug("Challenge Dates")

        return ChallengeDurationData(starts_at=start_date, ends_at=end_date, voting_ends_at=vote_end_date)

    @background_task(operation_name="extract_track_message_title")
    async def extract_track_message_title(self, message:Message) -> tuple[str,str] | None:
        if message.channel.id in self.config.feedback_link_channel_ids:
            link_extractor = URLExtract()
            links = link_extractor.find_urls(message.content)
            if not links:
                logger.bind(
                    message=str(message)
                ).warning(f"Link not found on message")
                return
            
            logger.bind(
                links=str(links)
            ).debug(f"Links found")
            track_title, platform = await self.track_extractor.extract_title(url=str(links[0]))
            logger.debug(f"Title: {track_title} Platform: {platform}")
            return track_title, platform
        elif message.channel.id in self.config.feedback_attachment_channel_ids:
            attachments = message.attachments
            if not attachments:
                logger.bind(
                    track_message=str(message)
                ).warning(f"Attachment not found on message")
                return
            if not attachments[0].content_type not in ["audio/mpeg", "audio/wav"]:
                logger.warning(f"Invalid content type {message.id}")
                return
            logger.bind(
                attachments=str(attachments),
                title=str(attachments[0].title),
                file_name=str(attachments[0].filename)
            ).info(f"Attachments on message")
            track_title = MessageExtractor.get_title(attachment=attachments[0])
            
        
            platform = "attachment"

            return track_title, platform


    async def get_submission_data(self, challenge: Challenge, message: Message) -> dict:
        title = await self.get_submission_title(message=message)

        return {
        "id":message.id,
        "channel_id":message.channel.id,
        "title":title,
        "challenge_id":challenge.id, 
        "author_id":message.author.id,
        "created_at":message.created_at,
        "edited_at":message.edited_at}



    async def collect_votes(self, reaction_emojis:dict[str, Reaction],
        message: Message,
        existing_user_ids: set[int],
        challenge: Challenge,
        votes:dict[int, Vote]) -> dict[int,Vote]:
                
        thumbs_up_reaction = reaction_emojis.get("👍")
        if thumbs_up_reaction:
            users = await self.bot.client.safe_fetch_reaction_users(reaction=thumbs_up_reaction, operation="collect_votes",limit=None, default=[])
            users = [user for user in users if user.id != message.author.id and user.id in existing_user_ids]
            if not users:
                return votes



            votes.update({user.id: Vote(
                submission_id=message.id,
                challenge_id=challenge.id,
                voter_id=user.id 
            )  for user in users})


        return votes


    async def get_winner_data(self,
        reaction_emojis:dict[str, Reaction],
        message: Message,

        winners: set[Winner],
        existing_user_ids: set[int],
        challenge: Challenge,) -> set[Winner]:
        logger.bind(
            message=str(message),
            reaction_emojis=str(reaction_emojis),
            winners=str(winners),
            existing_user_ids=str(existing_user_ids),
            challenge=str(challenge)
        ).debug("Create winners debug")
        if message.author.id not in existing_user_ids:
            logger.bind(
                author_id=str(message.author.id)
            ).debug(f"Author id is not in existing user ids")
            return winners
        logger.debug("Creating winners")
        trophy_reaction = reaction_emojis.get("🏆")
        if trophy_reaction:
            logger.debug("Trophy reaction found")
            async for user in trophy_reaction.users(limit=None):
                if user.id == self.config.admin_id:
                    winners.add(
                    Winner(
                        winner_id=message.author.id,
                        submission_id=message.id,
                        challenge_id=challenge.id
                    ))
                    break
        return winners



    @staticmethod
    def get_username(attachment: Attachment) -> str | None:
        pattern = r"\s*([^-]+?)\s*-\s*(.+?)\s*$"
        if attachment.title:
            groups = re.findall(pattern=pattern, string=attachment.title)

            logger.bind(
                groups=groups
            ).debug("Groups") 

            return groups[0]

    @staticmethod
    def get_winner(text: str) -> str | None:
        pattern = r"31m([^[]+)\s*\u001b"
        groups = re.findall(pattern=pattern, string=text)

        logger.bind(groups=groups).debug("Groups")
        if groups:
            return groups[0]

    @classmethod
    def get_title(cls, attachment: Attachment) -> str:
        if attachment.title:
            return str(attachment.title)
        else:
            return cls.clear_filename_data(attachment.filename)
            
            
    @staticmethod
    def clear_filename_data(filename: str) -> str:
        pattern = r"_|-|\.mp3|\.wav"

        return re.sub(pattern=pattern, repl="", string=filename)


