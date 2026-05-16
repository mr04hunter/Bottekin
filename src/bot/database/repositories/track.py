from datetime import datetime
from sqlalchemy import distinct, func, or_, select, update, delete
from sqlalchemy.dialects.postgresql import insert
from bot.database.models import Track, TrackWithNoFeedback
from bot.database.repositories.base import BaseRepository
from bot.exceptions import BotDatabaseException
from bot.logging import get_logger, log_function
from sqlalchemy.orm import load_only
from bot.database.models import UserLeftNotificationMessage
from sqlalchemy.exc import IntegrityError

logger = get_logger("track_repository")

class TrackRepository(BaseRepository):
    @log_function
    async def add(self, track_data: dict) -> Track | None:                     
        """Create a new feedback music post"""
        async with self.get_session() as session:
            await session.execute(insert(Track).values(**track_data))

    @log_function
    async def get_track_with_no_feedback(self, track_id: int) -> TrackWithNoFeedback | None:
        async with self.get_session() as session:
            track_with_no_feedback = await session.get(TrackWithNoFeedback, track_id)
            return track_with_no_feedback

    @log_function
    async def create_track_with_no_feedback(self, track_id:int, message_id:int, url:str, created_at: datetime) -> None:
        async with self.get_session() as session:
            stmt = insert(TrackWithNoFeedback).values(
                track_id=track_id, message_id=message_id,
                message_url=url, created_at=created_at)
            stmt = stmt.on_conflict_do_update(index_elements=["track_id"], set_={
                "message_url":stmt.excluded.message_url,
                "created_at":stmt.excluded.created_at,
                "message_id":stmt.excluded.message_id
            })
            await session.execute(stmt)

    @log_function
    async def delete_track_with_no_feedback(self, track_id: int) -> None:
        async with self.get_session() as session:
            await session.execute(delete(TrackWithNoFeedback).where(TrackWithNoFeedback.track_id==track_id))


    @log_function
    async def cleanup_track_with_no_feedback(self, before: datetime) -> list[int]:
        async with self.get_session() as session:
            stmt = delete(TrackWithNoFeedback).filter(
                or_(TrackWithNoFeedback.created_at <= before,TrackWithNoFeedback.track_id.in_(
                select(Track.id).where(Track.total_feedbacks >= 3)
                ))).returning(TrackWithNoFeedback.message_id)
            deleted_message_ids = await session.execute(stmt)
            deleted_message_ids = deleted_message_ids.scalars().all()
            
            message_ids = await session.execute(select(TrackWithNoFeedback.message_id).where(TrackWithNoFeedback.message_id.not_in(deleted_message_ids)))
            message_ids = message_ids.scalars().all()

            return list(message_ids)

    @log_function
    async def cleanup_tracks(self, channel_id:int, track_ids: set[int], after:datetime | None, before: datetime | None) -> None:
        async with self.get_session() as session:
            stmt = delete(Track).where(Track.id.not_in(track_ids)).filter(Track.channel_id==channel_id)
            if after:
                stmt = stmt.filter(Track.created_at >= after)
            if before:
                stmt = stmt.filter(Track.created_at <= before)
            await session.execute(stmt)

    @log_function
    async def bulk_insert_track(self, tracks: list[dict]) -> list | None:
        async with self.get_session() as session:
            if self._bound_session is not None:
                    inserted = []
                    for track in tracks:
                        try:
                            async with session.begin_nested():
                                single_stmt = insert(Track).values([track])
                                single_stmt = single_stmt.on_conflict_do_update(index_elements=["id"], set_={
                                "channel_id":single_stmt.excluded.channel_id,
                                "platform":single_stmt.excluded.platform,
                                "total_reactions":single_stmt.excluded.total_reactions,
                                "title":single_stmt.excluded.title,
                                "created_at":single_stmt.excluded.created_at,
                                "edited_at":single_stmt.excluded.edited_at,
                                }).returning(Track)
                                result = await session.execute(single_stmt)
                                inserted.extend(result.scalars().all())
                        except IntegrityError:
                            logger.warning(f"Skipping track {track['id']}, user {track['author_id']} no longer exists")

             
                    return inserted
            
            else:
                try:
                    stmt = insert(Track).values(tracks)
                    stmt = stmt.on_conflict_do_update(index_elements=["id"], set_={
                        "channel_id":stmt.excluded.channel_id,
                        "platform":stmt.excluded.platform,
                        "total_reactions":stmt.excluded.total_reactions,
                        "title":stmt.excluded.title,
                        "created_at":stmt.excluded.created_at,
                        "edited_at":stmt.excluded.edited_at,
                    }).returning(Track)

                    result = await session.execute(stmt)
                    await session.flush()
                    
                    return list(result.scalars().all())
                except IntegrityError:
                    await session.rollback()


        inserted = []
        for track in tracks:
            try:
                async with self.get_session() as retry_session:
                    single_stmt = insert(Track).values([track])
                    single_stmt = single_stmt.on_conflict_do_update(index_elements=["id"], set_={
                    "channel_id":single_stmt.excluded.channel_id,
                    "platform":single_stmt.excluded.platform,
                    "total_reactions":single_stmt.excluded.total_reactions,
                    "title":single_stmt.excluded.title,
                    "created_at":single_stmt.excluded.created_at,
                    "edited_at":single_stmt.excluded.edited_at,
                    }).returning(Track)
                    result = await retry_session.execute(single_stmt)
                    inserted.extend(result.scalars().all())
            except BotDatabaseException:
                logger.warning(f"Skipping track {track['id']}, user {track['author_id']} no longer exists")

        return inserted

        
           

                    
            
    @log_function
    async def delete(self, track_id: int) -> None:
        async with self.get_session() as session:            
            await session.execute(delete(Track).where(Track.id==track_id))
            

    @log_function
    async def update(self, track_id: int, track_data: dict) -> None:
        async with self.get_session() as session:
            await session.execute(update(Track).where(Track.id==track_id).values(**track_data))

    @log_function
    async def increment_track_reaction(self, track_id: int, count: int = 1) -> None:
        async with self.get_session() as session:
            track_exists = await session.get(Track, track_id)
            if track_exists:
                await session.execute(update(Track).where(Track.id==track_id).values(total_reactions=Track.total_reactions + count))
                logger.info(f"FEEDBACK MUSIC: {track_id} TOTAL REACTION INCREMENTED BY {count}")

    @log_function
    async def decrement_track_reaction(self, track_id: int, count: int = 1) -> None:
        async with self.get_session() as session:
            track_exists = await session.get(Track, track_id)
            if track_exists:
                await session.execute(update(Track).where(Track.id==track_id).values(total_reactions=Track.total_reactions - count))
                logger.info(f"FEEDBACK MUSIC: {track_id} TOTAL REACTION DECREMENTED BY {count}")

    @log_function
    async def get_for_user(self, user_id: int) -> list[Track]:
        async with self.get_session() as session:
            track_result = await session.execute(select(Track).where(Track.author_id==user_id).options(load_only(Track.channel_id, Track.id)).order_by(Track.channel_id, Track.created_at.desc()).distinct(Track.channel_id).limit(3))
            tracks = track_result.scalars().all()
            return list(tracks)
        

    @log_function
    async def exists(self, track_id: int) -> bool:
        async with self.get_session() as session:
            exists = await session.get(Track, track_id)

            return exists is not None
        
    @log_function
    async def get(self, track_id: int) -> Track | None:
        async with self.get_session() as session:
            track = await session.get(Track, track_id)

            return track
        

    async def get_total_tracks_in_db(self):
        async with self.get_session() as session:
            result = await session.execute(select(func.count(distinct(Track.id))))
            result = result.scalar_one()
  
            return result
        

    async def get_user_left_notifications(self, user_id) -> list:
        async with self.get_session() as session:
            result = await session.execute(delete(UserLeftNotificationMessage).where(UserLeftNotificationMessage.user_id==user_id).returning(UserLeftNotificationMessage))
            return list(result.scalars().all())
        
    async def create_user_left_notif_message(self, user_id:int, message_id:int, channel_id:int) -> UserLeftNotificationMessage:
        async with self.get_session() as session:
            stmt = insert(UserLeftNotificationMessage).values(user_id=user_id, message_id=message_id, channel_id=channel_id)
            stmt = stmt.on_conflict_do_nothing(index_elements=["user_id", "message_id"])

            result = await session.execute(stmt.returning(UserLeftNotificationMessage))

            return result.scalar_one()
