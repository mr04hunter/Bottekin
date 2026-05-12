from typing import TYPE_CHECKING
from bot.logging import get_logger
from discord import Message
from urlextract import URLExtract
from bot.utils.link_extractor import TrackDataExtractor
from bot.database.models import Challenge, MonthlyChallenge

if TYPE_CHECKING:
    from bot.config import Config

logger = get_logger("challenge_validator")

class ChallengeValidator:
    def __init__(self, config:"Config") -> None:
        self.config = config


    def validate(self, message: Message, challenge: Challenge | MonthlyChallenge) -> bool:
        if isinstance(challenge, Challenge):
            if challenge.type == "community" and message.channel.id == self.config.official_submission_channel_id:
                logger.debug(f"Ongoing challenge is community challenge, received submission is in official challenges channel")
                return False
        
            if challenge.type == "official" and message.channel.id == self.config.tiny_submission_channel_id:
                logger.debug(f"Ongoing challenge is official challenge, received submission is in community challenges channel")
                return False
            
            if message.channel.id not in self.config.submission_channel_ids:
                logger.debug(f"Submission Message is sent from an unrelated channel")
                return False
            
        if message.created_at > challenge.ends_at:
            logger.debug(f"Submission Message is sent after challenge is ended")
            return False
        
        url_extractor = URLExtract()
        urls = url_extractor.find_urls(message.content)

        if not message.attachments and not urls:
            logger.debug("No links or audio attachments could found in submission message")
            return False
        
        if urls:
            platform = TrackDataExtractor.detect_platform(str(urls[0]))
            logger.bind(
                platform=platform
            ).debug("Detected platform")
            if platform != "unknown":
                return True

        
        attachments = message.attachments

        content_type = attachments[0].content_type
        if not content_type:
            content_type = "audio" if attachments[0].filename.lower().endswith(".wav") or attachments[0].filename.lower().endswith(".mp3") else "invalid"

        if content_type.lower().startswith("audio"):
            logger.bind(
                content_type=str(content_type),
                message=str(message)
            ).info("Validated Submission")
            return False
        

        return False    