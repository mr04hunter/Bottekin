from bot.database.unit_of_work import UnitOfWork
from bot.services import (
    TrackService, FeedbackService,
    StatsService, ChallengeService,
    LeaderboardService, RoleService,
    UserService, SyncService,
    RateLimiter, TrackNotificationService,GraphService
    
)

from typing import TYPE_CHECKING

from bot.services.challenge_validator import ChallengeValidator

if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider
    from bot.events.event import Emitter
    from bot.utils.extract_attachment_data import MessageExtractor
    from bot.scheduler.scheduler import Scheduler
    from bot.utils.converters import BotConverter
    from bot.config import Config
    from bot.utils.link_extractor import TrackDataExtractor
    from redis.asyncio import Redis

class ServiceContainer:
    def __init__(
        self,
        uow: UnitOfWork,
        bot: "ChannelProvider",
        config:"Config",
        event_handler:"Emitter",
        extractor:"MessageExtractor",
        scheduler:"Scheduler",
        converter:"BotConverter",
        track_extractor:"TrackDataExtractor",
        redis_client:"Redis"
        ) -> None:
        self.bot = bot
        self.uow = uow

        self.config = config
        self.user = UserService(uow=self.uow, bot=self.bot, event_handler=event_handler)
        self.track = TrackService(uow=self.uow, bot=bot, event_handler=event_handler)
        self.feedback = FeedbackService(uow=self.uow, event_handler=event_handler, bot=bot)
        self.stats = StatsService(uow=self.uow, bot=self.bot, converter=converter)
        self.challenge_validator = ChallengeValidator(config=config)
        self.challenge = ChallengeService(
        uow=self.uow, bot=self.bot, event_handler=event_handler,
        scheduler=scheduler,extractor=extractor, validator=self.challenge_validator,
        config=config, track_extractor=track_extractor)
        self.visualize_service = GraphService()
        self.leaderboard = LeaderboardService(uow=self.uow, bot=self.bot, converter=converter, config=self.config, visualize_data=self.visualize_service)
        self.role = RoleService(uow=self.uow, bot=self.bot, config=self.config)
        self.sync_service = SyncService(
        uow=self.uow, bot=self.bot,extractor=extractor,
        scheduler=scheduler, event_handler=event_handler,
        challenge_validator=self.challenge_validator,
        config=config)

        self.rate_limiter = RateLimiter(uow=self.uow, bot=self.bot, scheduler=scheduler, redis_client=redis_client)
        self.track_notification_service = TrackNotificationService(uow=self.uow, bot=self.bot)

    

def create_service_container(
    bot: "ChannelProvider",
    uow: UnitOfWork,
    extractor:"MessageExtractor",
    event_handler:"Emitter",
    scheduler:"Scheduler",
    converter:"BotConverter",
    config: "Config",
    track_extractor:"TrackDataExtractor",
    redis_client:"Redis"
    ) -> ServiceContainer:
    return ServiceContainer(
        uow=uow,bot=bot,
        event_handler=event_handler,
        scheduler=scheduler,
        extractor=extractor,
        converter=converter,
        config=config,
        track_extractor=track_extractor,
        redis_client=redis_client)