from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from bot.database.repositories.user import UserRepository
from bot.database.repositories.challenge import ChallengeRepository
from bot.database.repositories.feedback import FeedbackRepository
from bot.database.repositories.track import TrackRepository
from bot.database.repositories.leaderboard import LeaderboardRepository
from bot.exceptions import BotDatabaseException
from sqlalchemy.exc import IntegrityError, OperationalError


class UnitOfWork:
    """
    Single entry point for all database access.
    Replaces DatabaseManager as the object injected into the bot.
    """

    def __init__(self, session_factory: async_sessionmaker | None = None) -> None:
        if session_factory is None:
            from bot.database.engine import get_session_factory
            session_factory = get_session_factory() 
        self._session_factory = session_factory

        self.users = UserRepository(session_factory)
        self.challenges = ChallengeRepository(session_factory)
        self.feedback = FeedbackRepository(session_factory)
        self.tracks = TrackRepository(session_factory)
        self.leaderboards = LeaderboardRepository(session_factory)

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator["TransactionContext", None]:
        """
        Yields a TransactionContext where all repositories 
        share a single session and single commit/rollback.
        """
        async with self._session_factory() as session:
            async with session.begin():
                try:
                    ctx = TransactionContext(session)
                    yield ctx
                except IntegrityError as e:
                    await session.rollback()
                    raise BotDatabaseException(
                        message=str(e.orig),
                        user_message="Database constraint violation"
                    )
                except OperationalError as e:
                    await session.rollback()
                    raise BotDatabaseException(
                        message=str(e.orig),
                        user_message="Database connection error"
                    )
                except BotDatabaseException:
                    await session.rollback()
                    raise
                except Exception as e:
                    await session.rollback()
                    raise BotDatabaseException(
                        message=str(e),
                        user_message="Unexpected database error"
                    )



class TransactionContext:
    """
    Holds session-bound versions of each repository.
    All operations share the same session — one commit or rollback.
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users = UserRepository.with_session(session)
        self.challenges = ChallengeRepository.with_session(session)
        self.feedback = FeedbackRepository.with_session(session)
        self.tracks = TrackRepository.with_session(session)
        self.leaderboards = LeaderboardRepository.with_session(session)


def create_uow() -> UnitOfWork:
    return UnitOfWork() 