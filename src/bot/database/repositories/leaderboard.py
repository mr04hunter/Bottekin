from datetime import datetime
from sqlalchemy import select, desc, distinct, union_all, literal
from bot.database.models import Track, Vote, Submission, User, Challenge, Leaderboards, Feedback
from bot.database.repositories.base import BaseRepository
from bot.logging import get_logger, log_function
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from bot.types.leaderboards.database_layer import ChallengeLeaderboardData, MostActiveMemberData, MostActivePeriodData, ServerActivityData, SubmissionLeaderboardData, AllTimeChallengeLeaderboardData, FeedbackLeaderboardData
from typing import cast

logger = get_logger("leaderboard_repository")

class LeaderboardRepository(BaseRepository):


    @log_function
    async def get_challenge_leaderboard(self, challenge: Challenge) -> ChallengeLeaderboardData | None:
        """Get leaderboard for a challenge"""
        async with self.get_session() as session:
            # if not challenge:
            #     return
            # if not challenge.is_ongoing_voting:
            #     return
            result = await session.execute(
                select(Submission, User)
                .join(User, Submission.author_id == User.id)
                .outerjoin(Vote, 
                    (Vote.submission_id == Submission.id) 
                )
                .where(Submission.challenge_id == challenge.id)
                .group_by(Submission.id, User.id)
                .order_by(Submission.total_votes.desc())
                .limit(10)
                
            )
            
            leaderboard = []
            for submission, user in result:
                logger.bind(
                    submission=str(submission),
                    ser=str(user),
                    vote=str(submission.total_votes)
                ).debug("Vote count")
                leaderboard.append((user,submission))
            
            leaderboard_data = ChallengeLeaderboardData(data=leaderboard, challenge_title=challenge.title,
                                                         server_total_submissions=challenge.total_submissions,
                                                         server_total_votes=challenge.total_votes, leaderboard_length=len(leaderboard))
            
            return leaderboard_data


    async def get_submissions_leaderboard(self) -> SubmissionLeaderboardData:
        async with self.get_session() as session:
            result = await session.execute(select(User).join(Submission, Submission.author_id == User.id, isouter=True).join(Challenge, Submission.challenge_id == Challenge.id, isouter=True)
                                           .options(
                                               selectinload(User.voted_submissions).selectinload(Submission.author)
                                           )
                                           .group_by(User.id).order_by(desc(User.total_submissions)).limit(10))
            
            total_challenges= await session.execute(select(func.count(Challenge.id)))
            total_submissions = await session.execute(select(func.coalesce(func.sum(User.total_submissions), 0)))
            leaderboard = [(user,user.total_submissions) for user in result.scalars().all() if user.total_submissions > 0]

            logger.bind(
                data=[str(value) for value in leaderboard]
            ).debug("Feedback leaderboard debug")

            leaderboard_data = SubmissionLeaderboardData(data=leaderboard, leaderboard_length=len(leaderboard),
                                                         server_total_submissions=cast(int,total_submissions.scalar()), server_total_challenges=cast(int,total_challenges.scalar()))

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
        

    async def get_server_activity_data(self, date: datetime) -> ServerActivityData:
        async with self.get_session() as session:
            track_count = (await session.execute(select(func.count(distinct(Track.id))).filter(Track.created_at >= date))).scalar_one()
            feedback_count = (await session.execute(select(func.count(distinct(Feedback.id))).filter(Feedback.created_at >= date))).scalar_one()
            
            return ServerActivityData(
                track_count=track_count,
                feedback_count=feedback_count
            )
        
    async def get_most_active_periods(self) -> tuple[dict[str, MostActivePeriodData], MostActiveMemberData] | None:
        async with self.get_session() as session:
            most_active_member_query = (
                select(
                    User,
                    User.total_feedbacks_given.label("total_feedback"),
                    func.count(Track.id.distinct()).label("total_tracks"),
                )
                .join(Track, Track.author_id == User.id)
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