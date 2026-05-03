from contextlib import asynccontextmanager
from typing import AsyncGenerator, TypeVar, Self
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import (
    IntegrityError, OperationalError, DataError,
    TimeoutError as SATimeoutError
)
from bot.exceptions import BotDatabaseException, ErrorCode, ErrorSeverity
from bot.logging import get_logger

logger = get_logger("repository")
T = TypeVar("T")


class BaseRepository:
    def __init__(self, session_factory: async_sessionmaker) -> None:
        self._session_factory = session_factory
        self._bound_session: AsyncSession | None = None

    @classmethod
    def with_session(cls, session: AsyncSession) -> Self:
        instance = cls.__new__(cls)
        instance._session_factory = None
        instance._bound_session = session
        return instance

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if self._bound_session is not None:
            yield self._bound_session
            return

        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except IntegrityError as e:
                await session.rollback()
                raise BotDatabaseException(
                    message=str(e.orig),
                    user_message="This operation conflicts with existing data.",
                    error_code=ErrorCode.DB_CONSTRAINT_VIOLATION,
                    recoverable=False,
                ) from e
            except SATimeoutError as e:
                await session.rollback()
                raise BotDatabaseException(
                    message=f"Database query timed out: {e}",
                    user_message="The request took too long. Please try again.",
                    error_code=ErrorCode.DB_TIMEOUT,
                    recoverable=True,
                ) from e
            except OperationalError as e:
                await session.rollback()
                raise BotDatabaseException(
                    message=f"Database connection error: {e.orig}",
                    user_message="Database is temporarily unavailable.",
                    error_code=ErrorCode.DB_CONNECTION_FAILED,
                    severity=ErrorSeverity.CRITICAL,
                    recoverable=True,
                ) from e
            except DataError as e:
                await session.rollback()
                raise BotDatabaseException(
                    message=f"Invalid data format: {e.orig}",
                    user_message="Invalid data provided.",
                    error_code=ErrorCode.DB_UNEXPECTED,
                    recoverable=False,
                ) from e
            except BotDatabaseException:
                await session.rollback()
                raise
            except Exception as e:
                await session.rollback()
                raise BotDatabaseException(
                    message=f"Unexpected database error: {type(e).__name__}: {e}",
                    user_message="An unexpected error occurred.",
                    error_code=ErrorCode.DB_UNEXPECTED,
                    recoverable=True,
                ) from e