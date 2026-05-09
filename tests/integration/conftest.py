import pytest
import asyncpg
from pathlib import Path
from testcontainers.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from alembic.config import Config as AlembicConfig
from alembic import command as alembic_command
from bot.database.unit_of_work import UnitOfWork
from bot.database.unit_of_work import UnitOfWork


TABLES_TO_TRUNCATE = [
    "track_givers",
    "tracks_with_no_feedback",
    "winners",
    "votes",
    "feedbacks",
    "submissions",
    "tracks",
    "challenges",
    "leaderboards",
    "users",
    "monthly_submissions",
    "monthly_challenges"
]



    


@pytest.fixture(scope="session")
def pg_container():
    with PostgresContainer("postgres:15") as pg:
        yield pg


@pytest.fixture(scope="session")
def sync_db_url(pg_container):
    return pg_container.get_connection_url()


@pytest.fixture(scope="session")
def async_db_url(pg_container):
    url = pg_container.get_connection_url()
    if "+psycopg2" in url:
        url = url.replace("+psycopg2", "+asyncpg")
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@pytest.fixture(scope="session")
def raw_db_url(pg_container):
    url = pg_container.get_connection_url()
    url = url.replace("+psycopg2", "").replace("+asyncpg", "")
    if not url.startswith("postgresql://"):
        url = "postgresql://" + url.split("://", 1)[1]
    return url


@pytest.fixture(scope="session")
def run_migrations(sync_db_url):
    project_root = Path(__file__).parent.parent.parent
    ini_path = project_root / "src" / "bot" / "alembic.ini"
    cfg = AlembicConfig(str(ini_path))
    cfg.set_section_option("alembic", "sqlalchemy.url", sync_db_url)
    alembic_command.upgrade(cfg, "head")
    return True



@pytest.fixture
async def session_factory(async_db_url, run_migrations):
    from sqlalchemy.pool import NullPool

    engine = create_async_engine(
        async_db_url,
        poolclass=NullPool,
    )
    factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    yield factory
    await engine.dispose()


@pytest.fixture(autouse=True)
async def truncate_tables(raw_db_url, run_migrations):
    conn = await asyncpg.connect(raw_db_url)
    try:
        tables = ", ".join(TABLES_TO_TRUNCATE)
        await conn.execute(
            f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"
        )
    finally:
        await conn.close()
    yield


@pytest.fixture
def uow(session_factory):
    return UnitOfWork(session_factory=session_factory)