import asyncio
from bot.database.unit_of_work import UnitOfWork
from bot.concurrency import init_guards
from bot.services import create_service_container
from bot.config import config
from bot.logging import setup_logging
from bot.logging import log_function
from bot.utils.extract_attachment_data import MessageExtractor
from bot.error_handler.error_handler import ErrorHandler
from bot.error_handler import decorators
from redis.asyncio import Redis
import uvicorn
from alembic.config import Config 
from alembic import command
import sys
from typing import TYPE_CHECKING, ParamSpec, Any
from pathlib import Path
from bot.events.event import (
    CLEANUP_TRACK_WITH_NO_FEEDBACK, DELETE_TRACK_WITH_NO_FEEDBACK, SYNC_TRACK_WITH_NO_FEEDBACK, create_event_handler,UPDATE_CURRENT_CHALLENGE_LEADERBOARD,
    UPDATE_FEEDBACK_LEADERBOARD,UPDATE_SUBMISSIONS_LEADERBOARD,
    UPDATE_WINNERS_LEADERBOARD, SET_CHALLENGE_ROLE,
    SET_FEEDBACK_ROLE, UPDATE_SERVER_ACTIVITIES_BOARD,
    UPDATE_MOST_ACTIVE_PERIODS_BOARD)

from bot.cogs.challenge import ChallengeCog
from bot.cogs.feedback import FeedbackCog
from bot.commands.commands import CommandsCog
from bot.commands.admin import AdminCommandCog
from bot.scheduler.scheduler import Scheduler
from bot.registry.channel_registry import ChannelRegistry
from bot.utils.converters import BotConverter
from bot.integrations.http.client import AioHttpClient
from bot.make_it_quote.quote_image_gen import QuoteService
from bot.utils.link_extractor import TrackDataExtractor
if TYPE_CHECKING:
    from bot.bottekin import Bottekin
    from bot.events.event import Emitter
    from bot.services.container import ServiceContainer


P = ParamSpec("P")

logger = setup_logging()


@log_function
def run_migrations() -> None:
    current_dir = Path(__file__).parent
    alembic_ini_path = current_dir / "alembic.ini"
    
    alembic_cfg = Config(str(alembic_ini_path))
    try:
        command.upgrade(alembic_cfg, "head")
    except Exception as e:
        logger.error("Database migration failed:", e)
        sys.exit(1)


    
async def start_bot(bot: "Bottekin") -> None:
    logger.debug(f"GUILD_ID {config.guild_id}")
    await bot.start(config.discord_token)
    
    

async def start_health_server(app:Any) -> None:
    config = uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    server = uvicorn.Server(config)
    await server.serve()

def register_bot_events(event_handler:"Emitter", services:"ServiceContainer") -> None:
    event_handler.on(SET_CHALLENGE_ROLE,callback=services.role.assign_challenge_roles)
    event_handler.on(SET_FEEDBACK_ROLE, callback=services.role.assign_feedback_roles)

    event_handler.on(CLEANUP_TRACK_WITH_NO_FEEDBACK, callback=services.track_notification_service.cleanup_tracks_no_feedback)
    event_handler.on(DELETE_TRACK_WITH_NO_FEEDBACK, callback=services.track_notification_service.delete_track_with_no_feedback_message)
    event_handler.on(SYNC_TRACK_WITH_NO_FEEDBACK, callback=services.track_notification_service.sync_track_with_no_feedback)
    event_handler.on(UPDATE_FEEDBACK_LEADERBOARD, callback=services.leaderboard.create_or_update_feedback_leaderboard)
    event_handler.on(UPDATE_SUBMISSIONS_LEADERBOARD, callback=services.leaderboard.create_or_update_submission_leaderboard)
    event_handler.on(UPDATE_WINNERS_LEADERBOARD, callback=services.leaderboard.create_or_update_all_time_challenges_won_leaderboard)


async def main() -> None:
    init_guards()
    from bot.healthcheck import app
    from bot.bottekin import create_bot
    from bot.events.discord_events import register_events
    async with AioHttpClient() as http_client:
        redis_client = Redis(
            host=str(config.redis_host),
            port=6379,
            username="default",
            password=str(config.redis_password),
            decode_responses=True
        )

        uow = UnitOfWork()
        scheduler = Scheduler(uow=uow)
        channels = ChannelRegistry()
        bot = create_bot(channels=channels, config=config)
        error_handler = ErrorHandler(
            webhook_url=config.dc_webhook,
        )
        decorators.set_error_handler(error_handler)
        track_extractor = TrackDataExtractor(http=http_client, config=config)


        converter = BotConverter(bot=bot)
        uow = uow
        event_handler = create_event_handler()
        event_handler = event_handler
        extractor = MessageExtractor(bot=bot, config=config, track_extractor=track_extractor)
        service_container = create_service_container(
        bot=bot, uow=uow, extractor=extractor,
        event_handler=event_handler, scheduler=scheduler,
        converter=converter, config=config, track_extractor=track_extractor, redis_client=redis_client)
        services = service_container


        await bot.add_cog(FeedbackCog(bot=bot,services=services, config=config, track_extractor=track_extractor))
        await bot.add_cog(ChallengeCog(bot=bot,services=services, extractor=extractor, config=config))

        miq_gen = QuoteService(client=http_client)
        commands_cog = CommandsCog(bot=bot, miq_gen=miq_gen, services=service_container, scheduler=scheduler, config=config)
        admin_commands_cog = AdminCommandCog(bot=bot, services=services, config=config)

        bot.tree.add_command(commands_cog.main_group, override=True)
        bot.tree.add_command(commands_cog.miq_command, override=True)
        bot.tree.add_command(admin_commands_cog.admin_group, override=True)
        bot.tree.add_command(admin_commands_cog.moderator_group, override=True)

        await bot.add_cog(commands_cog)
        await bot.add_cog(admin_commands_cog)
        
        register_bot_events(event_handler=event_handler, services=services)
        register_events(bot=bot, services=service_container, config=config)

        

        await wait_for_db()
        await asyncio.to_thread(run_migrations)
        await asyncio.gather(
            start_bot(bot),
            start_health_server(app)
        )

        


@log_function
async def wait_for_db(max_retries: int = 30, delay: int = 2) -> bool:
    """Wait for database to be available before starting services"""
    import asyncpg
    import os
    
    DB_URL = config.db_health_url
    
    for attempt in range(max_retries):
        try:
            conn = await asyncio.wait_for(
                asyncpg.connect(DB_URL), 
                timeout=5.0
            )
            await conn.execute("SELECT 1;")
            await conn.close()
            return True
        
        except Exception as e:
            logger.info(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(delay)
            else:
                raise Exception("Could not connect to database after maximum retries")
    return False

