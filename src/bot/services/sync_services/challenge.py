from bot.database.models import Challenge
from discord import TextChannel, Object
from bot.database.unit_of_work import UnitOfWork
from bot.error_handler.decorators import background_task
from bot.logging import get_logger
from typing import cast, TYPE_CHECKING
from bot.services.base_service import BaseService
from bot.types.protocols import ChannelProvider
from bot.utils.retry import with_retry


if TYPE_CHECKING:
    from bot.utils.extract_attachment_data import MessageExtractor
    from bot.scheduler.scheduler import Scheduler
    from bot.services.challenge_validator import ChallengeValidator
    from bot.config import Config

logger = get_logger("challenge_sync") 


class ChallengeSync(BaseService): 
    def __init__(
        self,
        uow: UnitOfWork,
        bot: ChannelProvider,
        config:"Config",
        extractor:"MessageExtractor",
        scheduler:"Scheduler",
        validator:"ChallengeValidator") -> None:
        super().__init__(uow, bot)
        self.extractor = extractor
        self.scheduler = scheduler
        self.validator = validator
        self.config = config


    async def sync(self) -> None:
        challenge = await self.sync_current_challenge()

        if not challenge:
            logger.info("No challenge found in fetch_and_store_challenge_data")
            return
        

        existing_user_ids = await self.uow.users.get_all_ids()
        if challenge.type == "official":
            channel = self.bot.channels.official_submission
            
        else:
            channel = self.bot.channels.tiny_submission

        channel = cast(TextChannel, channel)

        await self.sync_data(
            channel=channel,
            challenge=challenge,
            existing_user_ids=existing_user_ids
        )




    async def sync_current_challenge(self) -> Challenge | None:
        """
        iterates through the challenge_info channel and creates or updates the first challenge found
        """ 
        challenge_info_channel = self.bot.channels.challenge_info
        messages = await self.bot.client.safe_fetch_messages(channel=challenge_info_channel, operation="sync_current_challenge fetch_messages", limit=None)
        if not messages:
            return
        for message in messages:
            if not message.author.id == self.config.dyno_id:
                logger.debug("Unrelated author on challenge info channel")
                continue

            if not message.embeds:
                logger.debug("no embeds found on message")
                continue

            logger.bind(
                message=str(message),
                embeds=[embed.to_dict() for embed in message.embeds],
            ).info("Fetched messages from challenge info channel")
            
            challenge_embed_data = await self.extractor.extract_embed_data(message_id=message.id, embed=message.embeds[0])
            if challenge_embed_data:
                challenge = await self.uow.challenges.create_or_update(data=challenge_embed_data)
                await self.scheduler.schedule_challenge_jobs(data=challenge_embed_data.duration)
                return challenge

            continue


    @background_task(operation_name="challenge_sync_data")
    @with_retry()
    async def sync_data(
        self,
        channel: TextChannel,
        challenge: Challenge,
        existing_user_ids: set[int]
        ) -> None:
        """
        Retrieves the last challenge from the database
        Iterates through all messages&reactions in the official or tiny submissions channel.
        This method runs on every startup
        """
        
        existing_author_ids = set()
        votes = {}
        all_submission_ids = set()
        submissions = []
        winners = set()
        after_date = challenge.starts_at
        while True:
            submission_messages = await self.bot.client.safe_fetch_messages(channel=channel, operation="sync_challenge_data", limit=100,after=after_date,before=challenge.ends_at, oldest_first=True)
            submission_messages = [message for message in submission_messages if message.author.id in existing_user_ids]
            logger.bind(
                after_date=after_date,
                before_date=challenge.ends_at,
                messages=str(submission_messages)
            ).debug("Submission messages debug")
            if not submission_messages:
                logger.debug("No submission messages")
                break

            after_date = Object(id=submission_messages[len(submission_messages)-1].id)
            for submission_message in submission_messages: 
                if submission_message.author.id in existing_author_ids:
                    logger.debug(f"Author already made a submission")
                    continue
                if not self.validator.validate(message=submission_message, challenge=challenge):
                    logger.bind(
                        message=str(submission_message),
                        message_content=str(submission_message.content)
                    ).info(f"Invalid submission message")
                    continue

                new_submission = await self.extractor.get_submission_data(message=submission_message, challenge=challenge)
                
                existing_author_ids.add(submission_message.author.id)
                all_submission_ids.add(submission_message.id)
                submissions.append(new_submission)

                reaction_emojis = {str(reaction.emoji): reaction for reaction in submission_message.reactions}
                
                votes = await self.extractor.collect_votes(
                    reaction_emojis=reaction_emojis,
                    message=submission_message,
                    existing_user_ids=existing_user_ids,
                    challenge=challenge,
                    votes=votes)  
                
                winners = await self.extractor.get_winner_data(
                    reaction_emojis=reaction_emojis,
                    message=submission_message,
                    existing_user_ids=existing_user_ids,
                    winners=winners,
                    challenge=challenge
                )
 

                if len(submissions) >= 50:
                    logger.bind(
                    submissions=[str(submission) for submission in submissions]
                    ).debug("Bulk inserting submissions")

                    await self.uow.challenges.bulk_insert_submissions(submissions=submissions)
                    submissions.clear()

            async with self.uow.transaction() as t:
                if submissions:
                    logger.bind(
                    submissions=[str(submission) for submission in submissions]
                    ).debug("Bulk inserting remaning submissions")

                    await t.challenges.bulk_insert_submissions(submissions=submissions)

                if votes and challenge.is_ongoing_voting:
                    logger.bind(
                    votes={user_id:str(votes[user_id]) for user_id in votes}
                    ).debug("Bulk inserting votes")

                    await t.challenges.bulk_insert_votes(votes=votes, challenge=challenge)

                if winners:
                    logger.bind(
                        winners=str(winners)
                    ).debug(f"Inserting winners")
                    await t.challenges.bulk_insert_winners(winners=winners)

                
        await self.uow.challenges.cleanup_challenge_data(
            submission_ids=list(all_submission_ids),
            votes=list(votes.values()),
            winners=list(winners),
            challenge=challenge)
