import asyncio
from datetime import UTC, datetime
from bot.database.models import Challenge, MonthlyChallenge
from discord import ForumChannel, TextChannel, Object, Thread
from bot.database.unit_of_work import UnitOfWork
from bot.error_handler.decorators import background_task
from bot.logging import get_logger
from typing import cast, TYPE_CHECKING
from bot.services.base_service import BaseService
from bot.types.common import MonthlyChallengeData
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

    

    async def sync_monthly(self):
        logger.debug(f"MONTHLY CHALLENGE SYNC STARTED")
        existing_user_ids = await self.uow.users.get_all_ids()
        monthly_challenge_channel = self.bot.channels.monthly_challenge_channel

        threads = await self._get_all_threads(channel=monthly_challenge_channel)
        monthly_challenge = await self.sync_monthly_challenge(threads=threads)
        if not monthly_challenge:
            return
        
        for thread in threads:
            logger.debug(f"MONTHLY SYNC THREAD {thread.id}")
            await self._sync_monthly_challenge_thread(challenge=monthly_challenge, thread=thread, existing_user_ids=existing_user_ids)
            await asyncio.sleep(0.5)



    async def _get_all_threads(
        self, 
        channel: ForumChannel) -> list[Thread]:

        active_threads = await self.bot.client.safe_discord_call(coro=lambda: self.bot.guild.active_threads(), operation="monthly_challenges active threads")

        if not active_threads:
            return []

        active_threads = [thread for thread in active_threads if thread.parent_id==channel.id]

        archived_threads = await self.bot.client.safe_fetch_threads(channel=channel, operation="monthly_challenge_sync fetch_all_threads", default=[])

        threads = active_threads+archived_threads
        threads = [thread for thread in threads if thread.id != self.config.monthly_challenge_info_thread_id]

        

        # Challenge Month concept is introduced in 2026 so thread.created_at should exist, ignore the type checking
        threads = sorted(threads, key= lambda t: t.created_at) #type: ignore
        logger.bind(
            threads=str(threads)
        ).debug("Threads on channel")

        return threads            



    async def sync_monthly_challenge(self, threads: list[Thread]) -> MonthlyChallenge | None:
        

        if not threads:
            return
        starter_message = await self.bot.client.safe_discord_call(
            coro=lambda t=threads[0]: t.fetch_message(t.id), operation="monthly challenge sync fetch starter message")
        
        if not starter_message:
            logger.info(f"Monthly challenge starter message could not found")
            return
        
        if starter_message.author.id != self.config.admin_id:
            logger.bind(
                author_id=str(starter_message.author.id)
            ).info(f"Challenge month starter message author id is not admin id")
            return 
        
        title_data = self.extractor.is_challenge_month_starter(threads[0].name)

        if not title_data:
            logger.bind(
                content=str(threads[0].name)
            ).info(f"No title data found for monthly challenge")
            return
        
        day, month, year = title_data

        challenge_date = threads[0].created_at

        # Challenge Month concept is introduced in 2026 so thread.created_at should exist
        if not challenge_date:
            return
        
        ends_at = datetime(year=challenge_date.year, month=challenge_date.month+1, day=1, tzinfo=UTC)

        is_active = True if datetime.now(tz=UTC) < ends_at else False

        challenge_data = MonthlyChallengeData(
            id=threads[0].id,
            title=f"{day}_{month}_{year}_monthly_challenge",
            starts_at=challenge_date,
            ends_at=datetime(year=challenge_date.year, month=challenge_date.month+1, day=1, tzinfo=UTC),
            is_active=is_active
        )
        
        monthly_challenge = await self.uow.challenges.create_or_update_monthly_challenge(data=challenge_data)

        if is_active:
            await self.scheduler.schedule_monthly_challenge_jobs(ends_at=challenge_data.ends_at)

        return monthly_challenge



    async def _sync_monthly_challenge_thread(self, challenge:MonthlyChallenge, thread: Thread, existing_user_ids:set[int]):
        submissions = {}
        all_submission_ids = set()
        after_date = None

        while True:
            submission_messages = await self.bot.client.safe_fetch_messages(channel=thread, operation="monthly_challenge_sync", limit=100, after=after_date, oldest_first=True)
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
                if not self.validator.validate(message=submission_message, challenge=challenge):
                    logger.bind(
                        message=str(submission_message),
                        message_content=str(submission_message.content)
                    ).info(f"Invalid submission message")
                    continue

                title = await self.extractor.get_submission_title(message=submission_message)

                submission_data = {
                    "id": submission_message.id,
                    "challenge_id":challenge.id,
                    "title": title,
                    "author_id":submission_message.author.id,
                    "thread_id":thread.id,
                    "created_at":submission_message.created_at,
                    "edited_at":submission_message.edited_at
                }

                all_submission_ids.add(submission_message.id)
                submissions[f"{thread.id}_{submission_message.author.id}"] = submission_data
                if len(submissions) >= 50:
                    logger.bind(
                    submissions=[str(submission) for submission in submissions]
                    ).debug("Bulk inserting monthly submissions")

                    await self.uow.challenges.bulk_insert_monthly_submissions(submissions=[sbm for sbm in submissions.values()])
                    submissions.clear()

        
        if submissions:
            logger.debug("Bulk inserting remaining monthly submissions")
            await self.uow.challenges.bulk_insert_monthly_submissions(submissions=[sbm for sbm in submissions.values()])

        await self.uow.challenges.cleanup_monthly_submissions(challenge=challenge, thread_id=thread.id, submission_ids=list(all_submission_ids))



            

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
