from bot.database.models import Challenge, MonthlyChallenge
from discord import Message
from urlextract import URLExtract
from bot.database.unit_of_work import UnitOfWork
from bot.types.protocols import ChannelProvider
from bot.logging import get_logger
from bot.utils.extract_attachment_data import MessageExtractor
from bot.services.base_service import BaseService
from bot.types.common import ChallengeEmbedData, MonthlyChallengeData
from bot.events.event import  UPDATE_SUBMISSIONS_LEADERBOARD, UPDATE_CURRENT_CHALLENGE_LEADERBOARD, UPDATE_WINNERS_LEADERBOARD
from typing import TYPE_CHECKING
from bot.error_handler.decorators import service_operation

if TYPE_CHECKING:
    from bot.events.event import Emitter
    from bot.scheduler.scheduler import Scheduler
    from bot.utils.extract_attachment_data import MessageExtractor
    from bot.services.challenge_validator import ChallengeValidator
    from bot.config import Config
    from bot.utils.link_extractor import TrackDataExtractor

logger = get_logger("challenge_service")

class ChallengeService(BaseService):
    def __init__(
        self,
        uow: UnitOfWork,
        bot: ChannelProvider,
        config:"Config",
        event_handler:"Emitter",
        scheduler:"Scheduler",
        extractor:"MessageExtractor",
        validator:"ChallengeValidator",
        track_extractor:"TrackDataExtractor"
        ) -> None:
        super().__init__(uow, bot)
        self.event_handler = event_handler
        self.scheduler = scheduler
        self.extractor = extractor
        self.validator = validator
        self.config = config
        self.track_extractor = track_extractor


    @service_operation(operation_name="add_monthly_submission")
    async def add_monthly_submission(self, message:Message) -> None:
        challenge = await self.uow.challenges.get_current_monthly_challenge()
        if not challenge:
            return
        if not self.validator.validate(message=message, challenge=challenge):
            logger.bind(
                message=str(message)
            ).debug(f"Invalid submission")
            return
        
        title = await self.get_submission_title(message=message)

        await self.uow.challenges.create_or_update_monthly_submission(data={
            "id":message.id,
            "title":title,
            "challenge_id":challenge.id,
            "thread_id":message.channel.id,
            "created_at":message.created_at,
            "edited_at":message.edited_at,
            "author_id":message.author.id
        })
        



    @service_operation(operation_name="add_submission")
    async def add_submission(self,message: Message) -> None:
        """ Adds a submission to the ongoing official challenge or community challenge
            Use add_monthly_submission for monthly challenge submissions  
        """
        challenge = await self.get_current_challenge()
        if not challenge:
            return
        if not self.validator.validate(message=message, challenge=challenge):
            logger.bind(
                message=str(message)
            ).debug(f"Invalid submission")
            return
        submission = await self.extractor.get_submission_data(challenge=challenge, message=message)

        await self.uow.challenges.create_or_update_submission(data=submission)

        await self._safe_emit(UPDATE_SUBMISSIONS_LEADERBOARD)
        await self._safe_emit(UPDATE_CURRENT_CHALLENGE_LEADERBOARD)

    @service_operation(operation_name="delete_challenge")
    async def delete_challenge(self, challenge_id:int) -> None:
        await self.uow.challenges.delete_challenge(challenge_id=challenge_id)
        await self._safe_emit(UPDATE_CURRENT_CHALLENGE_LEADERBOARD)
        await self._safe_emit(UPDATE_WINNERS_LEADERBOARD)
        await self._safe_emit(UPDATE_SUBMISSIONS_LEADERBOARD)

    @service_operation(operation_name="delete_submission")
    async def delete_submission(self, submission_id: int) -> None:
        await self.uow.challenges.delete_submission(submission_id=submission_id)
        await self._safe_emit(UPDATE_SUBMISSIONS_LEADERBOARD)
        await self._safe_emit(UPDATE_CURRENT_CHALLENGE_LEADERBOARD)

    @service_operation(operation_name="delete_monthly_submission")
    async def delete_monthly_submission(self, submission_id: int) -> None:
        await self.uow.challenges.delete_monthly_submission(submission_id=submission_id)
        await self._safe_emit(UPDATE_SUBMISSIONS_LEADERBOARD)



    @service_operation(operation_name="update_submission")
    async def update_submission(self, message: Message) -> None:
        challenge = await self.uow.challenges.get_current()

        if not challenge:
            return
        
        if not self.validator.validate(message=message, challenge=challenge):
            return
        
        submission_data = await self.extractor.get_submission_data(challenge=challenge, message=message)

        await self.uow.challenges.create_or_update_submission(data=submission_data)


    

    @service_operation(operation_name="ge_current_challenge")
    async def get_current_challenge(self) -> Challenge | None:
        challenge = await self.uow.challenges.get_current()
        return challenge

    @service_operation(operation_name="add_vote")
    async def vote(
        self,
        submission_id: int,
        voter_id: int) -> None:

        async with self.uow.transaction() as t:
            challenge = await t.challenges.get_current()
            submission = await t.challenges.get_submission(submission_id=submission_id)
            if not challenge or not challenge.is_ongoing_voting or not submission:
                return
            await t.challenges.add_vote(
                submission_id=submission_id,
                challenge_id=challenge.id,
                voter_id=voter_id)
            logger.info("Vote added")

        await self._safe_emit(UPDATE_CURRENT_CHALLENGE_LEADERBOARD)
        

    @service_operation(operation_name="set_chosen_winner")
    async def set_chosen_winner(self, user_id: int, submission_id: int) -> None:
        submission = await self.uow.challenges.get_submission(submission_id=submission_id)

        if not submission or submission.winner_declared:
            return

        await self.uow.challenges.set_winner(
            user_id=user_id, submission_id=submission_id,
            challenge_id=submission.challenge_id)
        
        await self._safe_emit(UPDATE_WINNERS_LEADERBOARD)

    @service_operation(operation_name="remove_chosen_winner")
    async def remove_chosen_winner(self, user_id: int, submission_id: int) -> None:
        submission = await self.uow.challenges.get_submission(submission_id=submission_id)
        if not submission:
            return
        await self.uow.challenges.remove_winner(
            user_id=user_id, submission_id=submission_id,
            challenge_id=submission.challenge_id)
        
        await self._safe_emit(UPDATE_WINNERS_LEADERBOARD)

    @service_operation(operation_name="remove_vote")
    async def remove_vote(self, submission_id: int, voter_id: int) -> None:
        challenge = await self.uow.challenges.get_current()
        if not challenge or not challenge.is_ongoing_voting:
            return
        await self.uow.challenges.remove_vote(
            submission_id=submission_id, voter_id=voter_id)

        await self._safe_emit(UPDATE_CURRENT_CHALLENGE_LEADERBOARD)
        


    

    @service_operation(operation_name="get_submission_title")
    async def get_submission_title(self, message: Message) -> str:
        url_extractor = URLExtract()
        urls = url_extractor.find_urls(text=message.content) 

        if message.attachments:
            title = MessageExtractor.get_title(message.attachments[0])
        else:
            title, _ = await self.track_extractor.extract_title(str(urls[0]))

        return title

    @service_operation(operation_name="create_or_update_challenge")
    async def create_or_update_challenge(self,data: ChallengeEmbedData) -> Challenge:
        challenge = await self.uow.challenges.create_or_update(data=data)
        await self.scheduler.schedule_challenge_jobs(data=data.duration)

        await self._safe_emit(UPDATE_CURRENT_CHALLENGE_LEADERBOARD)
        return challenge
    
    @service_operation(operation_name="create_or_update_challenge")
    async def create_or_update_monthly_challenge(self,data: MonthlyChallengeData) -> MonthlyChallenge:
        challenge = await self.uow.challenges.create_or_update_monthly_challenge(data=data)
        await self.scheduler.schedule_monthly_challenge_jobs(ends_at=data.ends_at)
        return challenge

