import asyncio
from bot.database.unit_of_work import UnitOfWork
from typing import TYPE_CHECKING
from bot.database.unit_of_work import UnitOfWork
from discord import TextChannel
from typing import TYPE_CHECKING
from bot.services.sync_services.challenge import ChallengeSync
from bot.logging import get_logger
from bot.events.event import CLEANUP_TRACK_WITH_NO_FEEDBACK, UPDATE_MOST_ACTIVE_PERIODS_BOARD, UPDATE_SERVER_ACTIVITIES_BOARD, UPDATE_FEEDBACK_LEADERBOARD, SET_FEEDBACK_ROLE, UPDATE_CURRENT_CHALLENGE_LEADERBOARD, UPDATE_SUBMISSIONS_LEADERBOARD, UPDATE_WINNERS_LEADERBOARD, SET_CHALLENGE_ROLE
from bot.services.sync_services.feedback import FeedbackSyncService
from bot.services.sync_services.track import TrackSyncService
from bot.services.sync_services.user import UserSyncService
from bot.services.base_service import BaseService

logger = get_logger("base_sync")

if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider
    from bot.utils.extract_attachment_data import MessageExtractor
    from bot.events.event import Emitter
    from bot.scheduler.scheduler import Scheduler
    from bot.services.challenge_validator import ChallengeValidator
    from bot.config import Config

class SyncService(BaseService):
    def __init__(
        self,
        uow: UnitOfWork,
        bot: "ChannelProvider",
        config:"Config",
        extractor: "MessageExtractor",
        event_handler:"Emitter",
        scheduler:"Scheduler",
        challenge_validator:"ChallengeValidator"
        ) -> None:
        super().__init__(uow=uow, bot=bot)
        self.feedback = FeedbackSyncService(uow=self.uow, bot=self.bot, event_handler=event_handler)
        self.track = TrackSyncService(uow=self.uow, bot=self.bot, extractor=extractor)
        self.challenge = ChallengeSync(uow=self.uow, bot=self.bot, extractor=extractor, scheduler=scheduler, validator=challenge_validator, config=config)
        self.user = UserSyncService(uow=self.uow, bot=self.bot)
        self.event_handler = event_handler


    

    async def sync_all(self) -> None:
        await self.user.update_members()
        existing_user_ids = await self.uow.users.get_all_ids()
        if not existing_user_ids:
            return


        await self.challenge.sync()
        await self.challenge.sync_monthly()

        


        for channel in self.bot.channels.feedback:
            await self._sync_channel(channel=channel, existing_user_ids=existing_user_ids)
        
        await self._safe_emit(CLEANUP_TRACK_WITH_NO_FEEDBACK)
        await self._safe_emit(UPDATE_FEEDBACK_LEADERBOARD)
        await self._safe_emit(SET_FEEDBACK_ROLE)
        await self._safe_emit(UPDATE_CURRENT_CHALLENGE_LEADERBOARD)
        await self._safe_emit(UPDATE_WINNERS_LEADERBOARD)
        await self._safe_emit(UPDATE_SUBMISSIONS_LEADERBOARD)
        await self._safe_emit(SET_CHALLENGE_ROLE)
        await self._safe_emit(UPDATE_SERVER_ACTIVITIES_BOARD)
        await self._safe_emit(UPDATE_MOST_ACTIVE_PERIODS_BOARD)


    async def _sync_channel(
        self,
        channel: TextChannel,
        existing_user_ids: set[int],
    ) -> None:

        author_track_ids = await self.track.sync_channel(
            channel=channel,
            existing_user_ids=existing_user_ids,
        )
        if not author_track_ids:
            return

        await self.feedback.sync_channel(
            channel=channel,
            existing_user_ids=existing_user_ids,
            author_track_ids=author_track_ids, 
        )
