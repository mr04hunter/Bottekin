from __future__ import annotations
import asyncio
import functools
from typing import Callable, TypeVar, ParamSpec, Awaitable, Type

import discord
from bot.exceptions import BotValidationError
from bot.logging import get_logger
from sqlalchemy.exc import IntegrityError, OperationalError

logger = get_logger("retry")

P = ParamSpec("P")
T = TypeVar("T")


def with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0,
    retryable_exceptions: tuple[Type[Exception], ...] = (
    ConnectionError,
    ConnectionResetError,
    TimeoutError,
    asyncio.TimeoutError,
    discord.HTTPException,
    discord.GatewayNotFound,
    discord.ConnectionClosed,
    OperationalError,
    ),
    non_retryable_exceptions: tuple[Type[Exception], ...] = (IntegrityError, ValueError, BotValidationError, discord.Forbidden, discord.NotFound),
) -> Callable:
    """
    Decorator for async functions that retries on transient failures.

    Usage:
        @with_retry(max_attempts=3, retryable_exceptions=(discord.HTTPException,))
        async def my_func(): ...
    """
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            last_exc: Exception | None = None
            delay = base_delay

            for attempt in range(1, max_attempts + 1):
                logger.debug(f"ATTEMPT {attempt}")
                try:
                    return await func(*args, **kwargs)
                except non_retryable_exceptions as exc:
                    raise
                except retryable_exceptions as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        break

                    retry_after = getattr(exc, "retry_after", None)
                    actual_delay = retry_after if retry_after else min(delay, max_delay)

                    logger.bind(
                        func=func.__name__,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        delay=actual_delay,
                        error=str(exc),
                    ).warning(f"Retrying {func.__name__} after {actual_delay:.1f}s")

                    await asyncio.sleep(actual_delay)
                    delay = min(delay * backoff_factor, max_delay)

            raise last_exc  # type: ignore

        return wrapper
    return decorator