from datetime import datetime
from sqlalchemy import distinct, func, select, update, delete, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from bot.database.models import Feedback, Track, user_tracks
from bot.database.repositories.base import BaseRepository
from bot.logging import get_logger, log_function

logger = get_logger("feedback_repository")

MIN_WORD_COUNT_FOR_DUPLICATE_CHECK = 15

class FeedbackRepository(BaseRepository):
    @log_function
    async def cleanup_feedbacks_on_thread(self, thread_id: int, feedback_ids: set[int], after: datetime | None, before: datetime | None) -> None:
        async with self.get_session() as session:
                                      
            stmt = delete(Feedback).where(
                and_(Feedback.id.not_in(
                    feedback_ids), Feedback.thread_id==thread_id))
            if after:
                stmt = stmt.filter(Feedback.created_at >= after)
            
            if before:
                stmt = stmt.filter(Feedback.created_at <= before)


            await session.execute(stmt)

    async def cleanup_feedbacks(
            self,
            thread_ids:set[int],
            channel_id:int
    ):
        logger.bind(
            thread_ids=thread_ids
        ).debug("THREAD_IDS")
        async with self.get_session() as session:
            stmt = delete(Feedback).where(and_(
                Feedback.thread_id.not_in(thread_ids), Feedback.channel_id==channel_id)
            )
            await session.execute(stmt)

    async def add(self, feedback_data: dict) -> int | None:
        """
        Just writes. Assumes all validation and existence
        checks already happened in the service layer.
        """
        async with self.get_session() as session:
            feedback = Feedback(**feedback_data)
            session.add(feedback)
            await session.flush()
            await self.update_relations(session, feedback)
            if feedback_data.get("track_id", None):
                track = await session.get(Track, feedback_data.get("track_id"))
                return track.total_feedbacks if track else None
            
            return

        

    @log_function
    async def update_feedback(self, feedback_id: int, data: dict) -> None:
        async with self.get_session() as session:
            await session.execute(update(Feedback)
                    .where(Feedback.id==feedback_id)
                    .values(**data))
        
        logger.info(f"FEEDBACK UPDATED {feedback_id}")

    @log_function
    async def delete_feedback(self,track_id:int, feedback_id: int) -> int | None:
        async with self.get_session() as session:
            feedback = await session.get(Feedback, feedback_id)
            if not feedback:
                logger.info(f"FEEDBACK {feedback_id} NOT FOUND ON DELETE_FEEDBACK")
                return
            await session.execute(delete(Feedback).where(Feedback.id==feedback_id))
            logger.info(f"FEEDBACK DELETED")
  
            track = await session.get(Track, track_id)
            return track.total_feedbacks if track else None
            


    @log_function
    async def get(self, feedback_id: int) -> Feedback | None:
        async with self.get_session() as session:
            result = await session.get(Feedback, feedback_id)
            return result


    @log_function
    async def exists(self, feedback_id: int) -> bool:
        async with self.get_session() as session:
            result = await session.get(Feedback, feedback_id)
            return result is not None
        
    @log_function
    async def exists_for_author_in_thread(
        self, author_id: int, thread_id: int
    ) -> bool:
        async with self.get_session() as session:
            result = await session.execute(
                select(1).where(
                    and_(
                        Feedback.author_id == author_id,
                        Feedback.thread_id == thread_id
                    )
                ).limit(1)
            )
            return result.scalar_one_or_none() is not None



    @log_function
    async def is_duplicate_content(self, content: str) -> bool:
        async with self.get_session() as session:
            result = await session.execute(
                select(Feedback.id).where(Feedback.content == content)
            )
            return result.scalar_one_or_none() is not None
 
    @log_function
    async def bulk_update_relations(self, feedback_track_data:list[dict]) -> None:
        async with self.get_session() as session:
            stmt = insert(user_tracks).values(feedback_track_data)
            stmt = stmt.on_conflict_do_update(index_elements=["feedback_id", "user_id", "track_id"],set_={
                "user_id":stmt.excluded.user_id,
                "feedback_id":stmt.excluded.feedback_id,
                "track_id":stmt.excluded.track_id
            })

            await session.execute(stmt)


        
    
    @log_function
    async def update_relations(self, session: AsyncSession, feedback: Feedback) -> None:
        if None not in (feedback.author_id, feedback.track_id):
            await session.execute(insert(user_tracks).values(feedback_id=feedback.id, user_id=feedback.author_id, track_id=feedback.track_id))

    @log_function
    async def bulk_insert_feedback(self, feedbacks: list[dict]) -> list | None:
        async with self.get_session() as session:
        
            stmt = insert(Feedback).values(feedbacks)
            stmt = stmt.on_conflict_do_update(
            index_elements=["id"],
            set_={
            "content": stmt.excluded.content,
            "word_count": stmt.excluded.word_count,
            "created_at": stmt.excluded.created_at,
            "edited_at": stmt.excluded.edited_at,
            "channel_id": stmt.excluded.channel_id,

            }).returning(Feedback)

           

            result = await session.execute(stmt)
            await session.flush()

            return list(result.scalars().all())

    async def get_total_feedbacks(self):
        async with self.get_session() as session:
            result = await session.execute(select(func.count(distinct(Feedback.id))))

            count = result.scalar_one()

            return count