from sqlalchemy import select, update, delete, and_
from sqlalchemy.dialects.postgresql import insert
from bot.database.models import User
from bot.database.repositories.base import BaseRepository
from bot.logging import get_logger
from bot.logging.decorators import log_function
from datetime import datetime
from bot.constants import STATS
from bot.types import UserData


logger = get_logger("user_repository")


class UserRepository(BaseRepository):

    async def get_by_id(self, user_id: int) -> User | None:
        async with self.get_session() as session:
            return await session.get(User, user_id)

    async def get_all_ids(self) -> set[int]:
        async with self.get_session() as session:
            result = await session.execute(select(User.id))
            return set(result.scalars().all())

    async def exists(self, user_id: int) -> bool:
        async with self.get_session() as session:
            result = await session.execute(
                select(1).where(User.id == user_id)
            )
            return result.scalar_one_or_none() is not None



    @log_function
    async def update(self, user_id: int, data: dict) -> None:
        async with self.get_session() as session:
            await session.execute(update(User).where(User.id==user_id).values(**data))


    @log_function
    async def bulk_insert_users(self, users: list[dict]) -> None:
        async with self.get_session() as session:
            stmt = insert(User).values(users)
            stmt = stmt.on_conflict_do_update(index_elements=["id"],set_={ 
                "display_name":stmt.excluded.display_name,
                "username": stmt.excluded.username,
                "is_purge_data":stmt.excluded.is_purge_data,

            })

            await session.execute(stmt)


    async def create(
        self,
        data: UserData
    ) -> User:
        user = User(
                id=data.id,
                username=data.username,
                display_name=data.display_name,
                is_purge_data=data.is_purge_data
            )
        async with self.get_session() as session:
            session.add(user)
            await session.flush()

        
        return user 

    async def bulk_upsert(self, users: list[dict]) -> None:
        async with self.get_session() as session:
            stmt = insert(User).values(users)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "display_name": stmt.excluded.display_name,
                    "username": stmt.excluded.username,
                    "is_purge_data": stmt.excluded.is_purge_data,
                }
            )
            await session.execute(stmt)


    async def set_purge_data(self, user_id: int, purge: bool) -> None:
        async with self.get_session() as session:
            await session.execute(update(User).where(User.id==user_id).values(is_purge_data=purge))

    async def delete(self, user_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(delete(User).where(User.id==user_id))


    async def increment_stat(self, user_id: int, field: str, count: int) -> None:
        if field not in STATS:
            logger.info(f"{field}")
            logger.bind(
                field=str(field)
            ).warning("Invalid stat field provided")
            return
        column = getattr(User, field, None)
        if column is None:
            raise ValueError(f"User has no field '{field}'")
        async with self.get_session() as session:
            await session.execute(
                update(User)
                .where(User.id == user_id)
                .values({field: column + count})
            )

    async def get_with_stats(self, user_id: int) -> User | None:
        from sqlalchemy.orm import selectinload
        from bot.database.models import Feedback, Track, Submission, Vote
        async with self.get_session() as session:
            result = await session.execute(
                select(User)
                .options(
                    selectinload(User.feedbacks).selectinload(Feedback.track).selectinload(Track.author),
                    selectinload(User.submissions).selectinload(Submission.voters),
                    selectinload(User.votes).selectinload(Vote.submission).selectinload(Submission.author),
                    selectinload(User.tracks).options(selectinload(Track.feedback_givers),selectinload(Track.feedbacks).selectinload(Feedback.author)),
                    selectinload(User.challenges_won),
                    selectinload(User.voted_submissions),
                    selectinload(User.hosted_challenges),
                )
                .where(User.id == user_id)
            )
            return result.scalar_one_or_none()

    async def get_for_feedback_roles(self) -> list[User]:
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.total_feedbacks_given != 0)
            )
            return list(result.scalars().all())

    async def get_for_challenge_roles(self) -> list[User]:
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.total_submissions != 0)
            )
            return list(result.scalars().all())
        

    @log_function
    async def cleanup_users(self, user_ids: set[int], before: datetime | None, after: datetime | None) -> None:
        async with self.get_session() as session:
            stmt = delete(User).where(and_(User.id.not_in(user_ids), User.is_purge_data==True))
            if after:
                stmt = stmt.filter(User.created_at >= after)
            if before:
                stmt = stmt.filter(User.created_at <= before)
            
            await session.execute(stmt)

