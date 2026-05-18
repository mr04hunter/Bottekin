from datetime import UTC, datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import select, desc, distinct, union_all, literal
from bot.database.models import MonthlyChallenge, Track, Vote, Submission, User, Challenge, Leaderboards, Feedback
from bot.database.repositories.base import BaseRepository
from bot.logging import get_logger, log_function
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from bot.types.leaderboards.database_layer import ChallengeLeaderboardData, MostActiveMemberData, MostActivePeriodData, ServerActivityData, SubmissionLeaderboardData, AllTimeChallengeLeaderboardData, FeedbackLeaderboardData
from typing import cast

logger = get_logger("leaderboard_repository")

class LeaderboardRepository(BaseRepository):


    


    async def get_submissions_leaderboard(self) -> SubmissionLeaderboardData:
        async with self.get_session() as session:
            result = await session.execute(select(User).join(Submission, Submission.author_id == User.id, isouter=True).join(Challenge, Submission.challenge_id == Challenge.id, isouter=True)
                                           .options(
                                               selectinload(User.voted_submissions).selectinload(Submission.author)
                                           )
                                           .group_by(User.id).order_by(desc(User.total_submissions)).limit(10))
            
            total_official_challenges=await session.execute(select(func.count(Challenge.id)))
            total_official_challenges_result = cast(int,total_official_challenges.scalar())
            total_monthly_challenges=await session.execute(select(func.count(MonthlyChallenge.id)))
            total_monthly_challenges_result = cast(int,total_monthly_challenges.scalar())

            total_challenges = total_official_challenges_result+total_monthly_challenges_result

            total_submissions = await session.execute(select(func.coalesce(func.sum(User.total_submissions), 0)))
            leaderboard = [(user,user.total_submissions) for user in result.scalars().all() if user.total_submissions > 0]

            logger.bind(
                data=[str(value) for value in leaderboard]
            ).debug("Feedback leaderboard debug")

            leaderboard_data = SubmissionLeaderboardData(data=leaderboard, leaderboard_length=len(leaderboard),
                                                         server_total_submissions=cast(int,total_submissions.scalar()), server_total_challenges=total_challenges)

            return leaderboard_data

 
    async def get_feedback_leaderboard(self) -> FeedbackLeaderboardData:
        async with self.get_session() as session:
            result = await session.execute(select(User).where(User.total_feedbacks_given > 0)
                                           .options(
                                               selectinload(User.gave_feedback_to).selectinload(Track.author)
                                           )
                                           .group_by(User.id).order_by(desc(User.total_feedbacks_given)).limit(10))

            total_feedback = (await session.execute(select(func.coalesce(func.sum(User.total_feedbacks_given), 0)))).scalar()
            total_tracks = (await session.execute(select(func.count(distinct(Track.id))))).scalar()
            total_feedback_words = (await session.execute(select(func.coalesce(func.sum(User.total_feedback_words), 0)))).scalar()

            total_feedback = cast(int, total_feedback)
            total_tracks = cast(int, total_tracks)
            total_feedback_words = cast(int, total_feedback_words)

            logger.debug(f"TOTAL FEEDBACK {total_feedback}")
            logger.debug(f"TOTAL TRACKS {total_tracks}")
            logger.debug(f"TOTAL WORDS {total_feedback_words}")
            
            leaderboard = [(user,{
                "total_feedbacks_given":user.total_feedbacks_given,
                "total_feedback_words":user.total_feedback_words,"total_feedbacked_authors":
                len({track.author_id for track in user.gave_feedback_to})}) 
                for user in result.scalars().all() if user.total_feedbacks_given > 0]
            
            leaderboard_data = FeedbackLeaderboardData(
                data=leaderboard,
                leaderboard_length=len(leaderboard),
                server_total_feedback=total_feedback,
                server_total_tracks=total_tracks,
                server_total_fb_words=total_feedback_words
            )

            logger.bind(
                data=[str(value) for value in leaderboard]
            ).debug("Feedback leaderboard debug")

            return leaderboard_data

    async def get_all_time_challenge_leaderboard(self) -> AllTimeChallengeLeaderboardData:
        async with self.get_session() as session:
            leaderboard_results = await session.execute(select(User).where(User.total_challenges_won != 0)
                                                        .group_by(User.id)
                                                        .order_by(desc(User.total_challenges_won)).limit(10))
            

            

            result = [(user,user.total_challenges_won) for user in leaderboard_results.scalars().all() if user.total_challenges_won > 0]
            logger.bind(
                result = [str(v) for v in result]
            ).debug("all time debug")

            total_winners = len({winner for winner, count in result if count != 0})
            leaderboard_data = AllTimeChallengeLeaderboardData(data=result, leaderboard_length=len(result),
                                                                server_total_winners=total_winners)


            return leaderboard_data
        

    async def get_server_activity_data(self, trunc_by:str, date_type:str, limit:int) -> ServerActivityData | None:
        async with self.get_session() as session:
            now = datetime.now(tz=UTC)
            now = now.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=UTC)
            start_date = None
            if date_type == "month":
                start_date = now.replace(day=1) - relativedelta(months=limit - 1)
            
            elif date_type == "week":
                start_date = now - timedelta(weeks=limit)
                start_date = start_date - timedelta(days=start_date.weekday())

            
            def generate_periods(start: datetime, trunc_by: str) -> list[datetime]:
                periods = []
                current = start
                while current <= now:
                    periods.append(current)
                    if trunc_by == "day":
                        current += timedelta(days=1)
                    elif trunc_by == "week":
                        current += timedelta(weeks=1)
                    elif trunc_by == "month":
                        current += relativedelta(months=1)
                return periods
            
            if not start_date:
                return
            track_result = (await session.execute(
                select(
                func.date_trunc(trunc_by, Track.created_at).label("period"),
                func.count(distinct(Track.id)).label("track_count")).where(Track.created_at>=start_date).group_by("period").order_by("period"))).all()
            
            feedback_result = (await session.execute(
                select(
                func.date_trunc(trunc_by, Feedback.created_at).label("period"),
                func.count(distinct(Feedback.id)).label("feedback_count")).where(Feedback.created_at>=start_date).group_by("period").order_by("period"))).all()
            
            
            
            fmt_map = {
            "day":   "%b %d",
            "week":  "Week %W",
            "month": "%B",
            }
            fmt = fmt_map[trunc_by]

            

            track_result_map = {row.period: row.track_count for row in track_result}
            print(f"t map {track_result_map}")
            feedback_result_map = {row.period: row.feedback_count for row in feedback_result}

            all_periods = generate_periods(start_date, trunc_by)
            print(f"periods {all_periods}")
            labels = [p.strftime(fmt) for p in all_periods]
            track_values = [track_result_map.get(p, 0) for p in all_periods]
            feedback_values = [feedback_result_map.get(p, 0) for p in all_periods]

            return ServerActivityData(
                labels=labels,
                feedback_data=feedback_values,
                track_data=track_values
            )
        
    async def get_most_active_periods(self, admin_id:int) -> tuple[dict[str, MostActivePeriodData], MostActiveMemberData] | None:
        async with self.get_session() as session:
            most_active_member_query = (
                select(
                    User,
                    User.total_feedbacks_given.label("total_feedback"),
                    func.count(Track.id.distinct()).label("total_tracks"),
                )
                .where(User.id!=admin_id)
                .outerjoin(Track, Track.author_id == User.id)
                .group_by(User.id)
                .order_by(
                    desc(
                        User.total_feedbacks_given +
                        func.count(Track.id.distinct())
                    )
                )
                .limit(1)
            )

            most_active_member_result = await session.execute(most_active_member_query)

            most_active_member = most_active_member_result.first()

            most_active_member_data = None

            if not most_active_member:
                return
            
            user, total_feedback, total_tracks = most_active_member
            most_active_member_data = MostActiveMemberData(
                user=user, total_feedback=total_feedback,total_tracks=total_tracks
            )



            periods = ["day", "week", "month"]

            union_parts = []
            for period in periods:
                tracks_cte = (
                    select(
                        literal(period).label("period_type"),
                        func.date_trunc(period, Track.created_at).label("period"),
                        func.count(Track.id).label("track_count"),
                        literal(0).label("feedback_count"),
                    )
                    .group_by("period")
                )
                feedbacks_cte = (
                    select(
                        literal(period).label("period_type"),
                        func.date_trunc(period, Feedback.created_at).label("period"),
                        literal(0).label("track_count"),
                        func.count(Feedback.id).label("feedback_count"),
                    )
                    .group_by("period")
                )
                union_parts.extend([tracks_cte, feedbacks_cte])

            raw_cte = union_all(*union_parts).cte("raw_activity")

            aggregated_cte = (
                select(
                    raw_cte.c.period_type,
                    raw_cte.c.period,
                    func.sum(raw_cte.c.track_count).label("total_tracks"),
                    func.sum(raw_cte.c.feedback_count).label("total_feedback"),
                    (
                        func.sum(raw_cte.c.track_count) +
                        func.sum(raw_cte.c.feedback_count)
                    ).label("total"),
                )
                .group_by(raw_cte.c.period_type, raw_cte.c.period)
            ).cte("aggregated_activity")

            ranked_cte = (
                select(
                    aggregated_cte,
                    func.rank().over(
                        partition_by=aggregated_cte.c.period_type,
                        order_by=desc(aggregated_cte.c.total),
                    ).label("rnk"),
                )
            ).cte("ranked_activity")

            stmt = (
                select(ranked_cte)
                .where(ranked_cte.c.rnk == 1)
                .order_by(ranked_cte.c.period_type)
            )

            result = await session.execute(stmt)
            rows = result.all()

            if not rows:
                return None

            data: dict[str, MostActivePeriodData] = {}
            for row in rows:
                logger.bind(rows=str(row)).debug("ACTIVITY ROWS DEBUG")
                data[row.period_type] = MostActivePeriodData(
                    date=row.period,
                    total_feedback=row.total_feedback,
                    total_track=row.total_tracks,
                    total=row.total,
                )

            return data, most_active_member_data
        
            
    @log_function
    async def get_lb_message_id(self, lb_type: str) -> int | None:
        async with self.get_session() as session:
            result = await session.execute(select(Leaderboards.id).where(Leaderboards.type==lb_type))

            return result.scalar_one_or_none()

    @log_function
    async def insert_lb_message_id(self, id: int, lb_type: str) -> None:
        async with self.get_session() as session:
            existing_leaderboard_result = await session.execute(select(Leaderboards).where(Leaderboards.type==lb_type))
            leaderboard = existing_leaderboard_result.scalar_one_or_none()
            if leaderboard:
                await session.delete(leaderboard)
                await session.flush()
            new_leaderboard = Leaderboards(
                id=id, 
                type=lb_type)

            session.add(new_leaderboard)


    async def get_challenge_role_users(self) -> list[User] | None:
        async with self.get_session() as session:
            result = await session.execute(select(User).where(User.total_submissions!=0))
            return list(result.scalars().all())
        

    async def get_feedback_role_users(self) -> list[User] | None:
        async with self.get_session() as session: 
            result = await session.execute(select(User).where(User.total_feedbacks_given!=0))
            return list(result.scalars().all())