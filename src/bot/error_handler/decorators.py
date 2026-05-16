from __future__ import annotations
import functools
import traceback as tb
import asyncio
from typing import TYPE_CHECKING, Callable, TypeVar, ParamSpec, Awaitable, Any
import discord

from bot.exceptions import (
    BotException, BotDatabaseException, BotDiscordApiError,
    BotRateLimitError, BotExternalApiError,
    BotNotFoundError, ErrorSeverity, ErrorCode, BotValidationError
)
from bot.logging import get_logger


if TYPE_CHECKING:
    from bot.error_handler.error_handler import ErrorHandler

logger = get_logger("decorators")
P = ParamSpec("P")
T = TypeVar("T")


_error_handler: "ErrorHandler | None" = None

def set_error_handler(handler: "ErrorHandler") -> None:
    """Called once during bot startup to wire in the handler."""
    global _error_handler
    _error_handler = handler

async def _observe(exc: BotException, operation: str) -> None:
    """Safe wrapper — if ErrorHandler isn't set up yet, do nothing."""
    if _error_handler is not None:
        try:
            await _error_handler.observe(exc, operation)
        except Exception:
            pass 


def discord_operation(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        try:
            return await func(*args, **kwargs)
        except discord.NotFound as e:
            bot_exc = BotDiscordApiError(
                message=f"{func.__name__}: Discord resource not found — {e}",
                error_code=ErrorCode.DISCORD_NOT_FOUND,
                severity=ErrorSeverity.LOW,
                context={"func": func.__name__},
                recoverable=False,
            )

            await _observe(bot_exc, func.__name__)
            raise bot_exc from e

        except discord.Forbidden as e:
            bot_exc = BotDiscordApiError(
            message=f"{func.__name__}: Missing Discord permissions — {e}",
            error_code=ErrorCode.DISCORD_FORBIDDEN,
            severity=ErrorSeverity.HIGH,
            context={"func": func.__name__},
            recoverable=False,
            )
            logger.bind(func=func.__name__, error=str(e)).warning(
                "Discord Forbidden — check bot permissions"
            )
            await _observe(bot_exc, func.__name__)
            raise bot_exc from e
        except discord.HTTPException as e:
            if e.status == 429:
                
                bot_exc = BotRateLimitError(
                    message=f"{func.__name__}: Rate limited",
                    retry_after=getattr(e, "retry_after", None),
                    context={"func": func.__name__},
                )
                await _observe(bot_exc, func.__name__)

                raise bot_exc from e
            bot_exc = BotDiscordApiError(
                message=f"{func.__name__}: HTTP {e.status} — {e}",
                status_code=e.status,
                context={"func": func.__name__},
            ) 

            await _observe(bot_exc, func.__name__)
            raise bot_exc from e
        except BotException as e:
            raise  
        except Exception as e:
           
            bot_exc = BotDiscordApiError(
                message=f"{func.__name__}: Unexpected Discord error — {e}",
                context={"func": func.__name__, "traceback": tb.format_exc()},
            ) 
            await _observe(bot_exc, func.__name__)
            raise bot_exc from e
    return wrapper


def external_api_call(
    platform: str = "unknown",
    fallback: Any = ("unknown title", "unknown"),
):
    
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except BotExternalApiError as e:
                logger.bind(
                    platform=platform,
                    func=func.__name__,
                    error=str(e),
                ).warning(f"External API call failed, using fallback")
                await _observe(e, func.__name__)
                return fallback  # type: ignore
            except asyncio.TimeoutError as e:
                bot_exc = BotExternalApiError(
                message=f"{func.__name__}: timed out",
                platform=platform,
                error_code=ErrorCode.EXTERNAL_API_TIMEOUT,
                severity=ErrorSeverity.MEDIUM,
            )
                logger.bind(
                    platform=platform,
                    func=func.__name__,
                ).warning("External API call timed out, using fallback")
                await _observe(bot_exc, func.__name__) 
                return fallback  # type: ignore
            except Exception as e:
                logger.bind(
                    platform=platform,
                    func=func.__name__,
                    error=str(e),
                    traceback=tb.format_exc(),
                ).error("Unexpected external API error, using fallback")
                bot_exc = BotException(
                    message=str(e),
                    severity=ErrorSeverity.HIGH,
                )
                await _observe(bot_exc, func.__name__) 
                return fallback  # type: ignore
        return wrapper
    return decorator



def background_task(
    operation_name: str | None = None,
    reraise_critical: bool = False,
):
    
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T | None]]:
        name = operation_name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
            try:
                return await func(*args, **kwargs)
            except BotException as e:
                if reraise_critical and e.severity == ErrorSeverity.CRITICAL:
                    logger.bind(
                        operation=name,
                        error_code=e.error_code,
                        error=str(e),
                    ).critical(f"Critical failure in background task '{name}'")
                    raise
                logger.bind(
                    operation=name,
                    severity=e.severity.value,
                    error_code=e.error_code.value if e.error_code else None,
                    error=str(e),
                ).error(f"Background task '{name}' failed (handled)")
                return None
            except Exception as e:
                logger.bind(
                    operation=name,
                    error=str(e),
                    traceback=tb.format_exc(),
                ).error(f"Background task '{name}' failed (unhandled)")
                bot_exc = BotException(
                message=f"{name}: {type(e).__name__}: {e}",
                severity=ErrorSeverity.HIGH,
                context={"operation": name, "exception_type": type(e).__name__},
            )
                print(f"ERRORRRR {str(e)}")
                await _observe(bot_exc, name) 
                return None
        return wrapper
    return decorator



def service_operation(
    operation_name: str | None = None,
    swallow_db_errors: bool = False,
):
   
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        name = operation_name or func.__name__

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except BotException as e:
                raise  
            except discord.NotFound as e:
                bot_exc = BotDiscordApiError(
                    message=f"{name}: Discord resource not found",
                    error_code=ErrorCode.DISCORD_NOT_FOUND,
                    severity=ErrorSeverity.LOW,
                    recoverable=False,
                    context={"operation": name},
                )
                await _observe(bot_exc, name)
                raise bot_exc from e
            except discord.Forbidden as e:
                bot_exc = BotDiscordApiError(
                    message=f"{name}: Discord permission denied",
                    error_code=ErrorCode.DISCORD_FORBIDDEN,
                    severity=ErrorSeverity.HIGH,
                    context={"operation": name},
                )
                await _observe(bot_exc, name)
                raise bot_exc from e
            except discord.HTTPException as e:
                bot_exc = BotDiscordApiError(
                    message=f"{name}: Discord HTTP error {e.status}",
                    status_code=e.status,
                    context={"operation": name},
                )
                await _observe(bot_exc, name)
                raise bot_exc from e
            except Exception as e:
                logger.bind(
                    operation=name,
                    error=str(e),
                    traceback=tb.format_exc(),
                ).error(f"Unhandled error in service operation '{name}'")
                bot_exc = BotException(
                    message=f"{name}: {type(e).__name__}: {e}",
                    user_message="An unexpected error occurred.",
                    severity=ErrorSeverity.HIGH,
                    context={"operation": name},
                )
                await _observe(bot_exc, name)
                raise bot_exc from e
        return wrapper
    return decorator




def cog_event_handler(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T | None]]:

    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T | None:
        try:
            return await func(*args, **kwargs)
        except BotNotFoundError as e:
            await _observe(e, func.__name__)
            logger.bind(handler=func.__name__).debug("Resource not found in event handler")
            return None
        except BotValidationError as e:
            await _observe(e, func.__name__)
            logger.bind(
                handler=func.__name__,
                error=str(e),
            ).debug("Validation rejected in event handler")
            return None
        except BotRateLimitError as e:
            await _observe(e, func.__name__)
            logger.bind(
                handler=func.__name__,
                retry_after=e.retry_after,
            ).warning("Rate limit exhausted in event handler, dropping event")
            return None  
        except BotDiscordApiError as e:
            await _observe(e, func.__name__)
            if e.error_code == ErrorCode.DISCORD_FORBIDDEN:
                logger.bind(
                    handler=func.__name__,
                    error=str(e),
                ).warning("Missing permissions in event handler")
            else:
                logger.bind(
                    handler=func.__name__,
                    error_code=e.error_code.value if e.error_code else None,
                    error=str(e),
                ).error("Discord API error in event handler")
            return None
        except BotDatabaseException as e:
            await _observe(e, func.__name__)
            logger.bind(
                handler=func.__name__,
                error_code=e.error_code.value if e.error_code else None,
                error=str(e),
            ).error("Database error in event handler")
            return None
        except BotException as e:
            logger.bind(
                handler=func.__name__,
                severity=e.severity.value,
                error=str(e),
            ).error("Bot error in event handler")
            return None
        except Exception as e:
            bot_exc = BotException(str(e), severity=ErrorSeverity.HIGH)
            await _observe(bot_exc, func.__name__)
            logger.bind(
                handler=func.__name__,
                error=str(e),
                traceback=tb.format_exc(),
            ).critical(f"UNHANDLED exception in event handler '{func.__name__}'")
            return None
    return wrapper