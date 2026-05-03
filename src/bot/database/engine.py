from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import Optional

_engine = None
_async_session: Optional[async_sessionmaker] = None


def get_engine():
    global _engine
    if _engine is None:
        from bot.config import config 
        _engine = create_async_engine(
            config.db_url,
            echo=False,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
        )
    return _engine


def get_session_factory() -> async_sessionmaker:
    global _async_session
    if _async_session is None:
        _async_session = async_sessionmaker(
            get_engine(),
            expire_on_commit=False,
            class_=AsyncSession
        )
    return _async_session


