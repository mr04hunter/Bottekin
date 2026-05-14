from discord import Object, Reaction
from datetime import datetime

from bot.logging import get_logger
from typing import TYPE_CHECKING
from bot.concurrency import get_guards
from bot.utils.retry import with_retry
from typing import TypeVar, Callable, Awaitable

if TYPE_CHECKING:
    from bot.types.protocols import ChannelProvider


logger = get_logger("base_service")

T = TypeVar("T")
class DcClient:
    def __init__(self, bot: "ChannelProvider") -> None:
        self._bot = bot



    @with_retry()
    async def safe_discord_call(self, coro:Callable[[], Awaitable[T]], operation: str, default=None) -> T | None: 
        """
        Execute a Discord API call, handling NotFound/Forbidden gracefully.
        Returns default value instead of raising for expected Discord errors.
        """
        guards = get_guards()
        import discord
        try:
            async with guards.general_call:
                return await coro()
        except discord.NotFound:
            logger.bind(operation=operation).debug("Discord resource not found, skipping")
            return default
        except discord.Forbidden:
            logger.bind(operation=operation).warning("Missing Discord permissions")
            return default
        except discord.HTTPException as e:
            if e.status == 429:
                logger.bind(
                    operation=operation,
                    retry_after=getattr(e, "retry_after", None)
                ).warning("Discord rate limit hit")
            else:
                logger.bind(operation=operation, status=e.status).error("Discord HTTP error")
            return default
        

    @with_retry()
    async def safe_discord_write_call(self, coro:Callable[[], Awaitable[T]], operation: str, default=None) -> T | None:
        """
        Execute a Discord API write call. Write calls are more restrictive than read calls so it needs seperate limiting
        """
        guards = get_guards()
        import discord
        try:
            async with guards.write_call:
                return await coro()
        except discord.NotFound:
            logger.bind(operation=operation).debug("Discord resource not found, skipping")
            return default
        except discord.Forbidden:
            logger.bind(operation=operation).warning("Missing Discord permissions")
            return default
        except discord.HTTPException as e:
            if e.status == 429:
                logger.bind(
                    operation=operation,
                    retry_after=getattr(e, "retry_after", None)
                ).warning("Discord rate limit hit")
            else:
                logger.bind(operation=operation, status=e.status).error("Discord HTTP error")
            return default

    
    @with_retry()
    async def safe_fetch_messages(
        self,
        channel,
        operation: str,
        limit:int | None = None,
        after:Object | datetime | None = None,
        before:Object | datetime | None = None,
        oldest_first: bool = False,
        default=[]) -> list:

        guards = get_guards()
        import discord
        try:
            async with guards.message_fetch:
                messages = [message async for message in channel.history(limit=limit, after=after, before=before, oldest_first=oldest_first)]
                return messages
        except discord.NotFound:
            logger.bind(operation=operation).debug("Discord resource not found, skipping")
            return default
        except discord.Forbidden:
            logger.bind(operation=operation).warning("Missing Discord permissions")
            return default
        except discord.HTTPException as e:
            if e.status == 429:
                logger.bind(
                    operation=operation,
                    retry_after=getattr(e, "retry_after", None)
                ).warning("Discord rate limit hit")
            else:
                logger.bind(operation=operation, status=e.status).error("Discord HTTP error")
            return default
        

    @with_retry()
    async def safe_fetch_members(
        self,
        guild,
        operation: str,
        limit:int | None = None,
        after:Object | datetime | None = None,
        before:Object | datetime | None = None,
        oldest_first: bool = False,
        default=[]) -> list:
        guards = get_guards()
        import discord
        try:
            async with guards.member_fetch:
                members = [member async for member in guild.fetch_members(limit=limit, after=after)]
                return members
        except discord.NotFound:
            logger.bind(operation=operation).debug("Discord resource not found, skipping")
            return default
        except discord.Forbidden:
            logger.bind(operation=operation).warning("Missing Discord permissions")
            return default
        except discord.HTTPException as e:
            if e.status == 429:
                logger.bind(
                    operation=operation,
                    retry_after=getattr(e, "retry_after", None)
                ).warning("Discord rate limit hit")
            else:
                logger.bind(operation=operation, status=e.status).error("Discord HTTP error")
            return default
        
    
    @with_retry()
    async def safe_fetch_reaction_users(
        self,
        reaction: "Reaction",
        operation: str,
        limit:int | None = None,
        after:Object | None = None,
        before:Object | datetime | None = None,
        oldest_first: bool = False,
        default=[]) -> list:
        guards = get_guards()
        import discord
        try:
            async with guards.reaction_fetch:
                users = [user async for user in reaction.users(limit=limit, after=after) if not user.bot]
                return users
        except discord.NotFound:
            logger.bind(operation=operation).debug("Discord resource not found, skipping")
            return default
        except discord.Forbidden:
            logger.bind(operation=operation).warning("Missing Discord permissions")
            return default
        except discord.HTTPException as e:
            if e.status == 429:
                logger.bind(
                    operation=operation,
                    retry_after=getattr(e, "retry_after", None)
                ).warning("Discord rate limit hit")
            else:
                logger.bind(operation=operation, status=e.status).error("Discord HTTP error")
            return default
    
    
    @with_retry()
    async def safe_fetch_threads(
        self,
        channel,
        operation: str,
        limit:int | None = None,
        after:Object | datetime | None = None,
        before:Object | datetime | None = None,
        oldest_first: bool = False,
        default=[]) -> list:
        guards = get_guards()
        import discord
        try:
            async with guards.thread_fetch:
                threads = [user async for user in channel.archived_threads(limit=limit)]
                return threads
        except discord.NotFound:
            logger.bind(operation=operation).debug("Discord resource not found, skipping")
            return default
        except discord.Forbidden:
            logger.bind(operation=operation).warning("Missing Discord permissions")
            return default
        except discord.HTTPException as e:
            if e.status == 429:
                logger.bind(
                    operation=operation,
                    retry_after=getattr(e, "retry_after", None)
                ).warning("Discord rate limit hit")
            else:
                logger.bind(operation=operation, status=e.status).error("Discord HTTP error")
            return default
    


   