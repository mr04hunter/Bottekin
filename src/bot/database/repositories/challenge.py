from sqlalchemy import select, update, delete, desc, tuple_, and_
from sqlalchemy.dialects.postgresql import insert
from bot.database.models import Challenge, Submission, Vote, Winner, User
from bot.database.repositories.base import BaseRepository
from bot.logging import get_logger

logger = get_logger("challenge_repository")


class ChallengeRepository(BaseRepository):

    async def get_current(self) -> Challenge | None:
        async with self.get_session() as session:
            result = await session.execute(
                select(Challenge)
                .order_by(desc(Challenge.created_at))
                .limit(1)
            )
            return result.scalar_one_or_none()

    async def create_or_update(self, data) -> Challenge:
        challenge = None
        async with self.get_session() as session:
            challenge = await session.get(Challenge, data.id)
            if not challenge:
                challenge = Challenge(
                    id=data.id,
                    title=data.title,
                    description=data.description,
                    type=data.type,
                    host_id=data.host_id,
                    starts_at=data.duration.starts_at,
                    ends_at=data.duration.ends_at,
                    voting_ends_at=data.duration.voting_ends_at,
                    is_active=data.is_active,
                    is_ongoing_voting=data.is_ongoing_voting,
                )
                session.add(challenge)
            else:
                challenge.title = data.title
                challenge.description = data.description
                challenge.type = data.type
                challenge.host_id = data.host_id
                challenge.starts_at = data.duration.starts_at
                challenge.ends_at = data.duration.ends_at
                challenge.voting_ends_at = data.duration.voting_ends_at
                challenge.is_active = data.is_active
                challenge.is_ongoing_voting = data.is_ongoing_voting

                

            await session.execute(
                update(Challenge)
                .where(Challenge.id != data.id)
                .values(is_active=False, is_ongoing_voting=False)
            )

        return challenge



    async def delete_challenge(self, challenge_id: int) -> None:
        async with self.get_session() as session:
            challenge = await session.get(Challenge, challenge_id)
            if not challenge:
                return
            await session.delete(challenge)

    async def terminate(self) -> None:
        async with self.get_session() as session:
            challenge = await self.get_current()
            if challenge:
                await session.execute(
                    update(Challenge)
                    .where(Challenge.id == challenge.id)
                    .values(is_active=False)
                )

    async def end_voting(self) -> None:
        async with self.get_session() as session:
            challenge = await self.get_current()
            if challenge:
                await session.execute(
                    update(Challenge)
                    .where(Challenge.id == challenge.id)
                    .values(is_ongoing_voting=False)
                )

    async def create_or_update_submission(self, data: dict) -> Submission | None:
        """Returns True if inserted, False if author already submitted."""
        async with self.get_session() as session:
            existing = await session.execute(
                select(Submission).where(
                    Submission.challenge_id == data["challenge_id"],
                    Submission.author_id == data["author_id"]
                )
            )
            existing = existing.scalar_one_or_none()
            if existing and existing.id != data["id"]:
                return
            stmt = insert(Submission).values(**data)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={"title": stmt.excluded.title, "edited_at": stmt.excluded.edited_at}
            ).returning(Submission)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()

    async def delete_submission(self, submission_id: int) -> bool:
        """Returns True if deleted."""
        async with self.get_session() as session:
            submission = await session.get(Submission, submission_id)
            if not submission:
                return False
            challenge = await session.get(Challenge, submission.challenge_id)
            if not challenge or not challenge.is_active:
                return False
            await session.delete(submission)
            return True

    async def add_vote(
        self, submission_id: int, challenge_id: int, voter_id: int
    ) -> bool:
        async with self.get_session() as session:
            await session.execute(
                delete(Vote).where(
                    Vote.challenge_id == challenge_id,
                    Vote.voter_id == voter_id
                )
            )
            session.add(Vote(
                submission_id=submission_id,
                challenge_id=challenge_id,
                voter_id=voter_id,
            ))
            return True

    async def remove_vote(self, submission_id: int, voter_id: int) -> None:
        async with self.get_session() as session:
            submission = await session.get(Submission, submission_id)
            if not submission:
                return
            challenge = await session.get(Challenge, submission.challenge_id)
            if not challenge or not challenge.is_ongoing_voting:
                return
            vote = await session.get(Vote, (submission_id, challenge.id, voter_id))
            if vote:
                await session.delete(vote)

    async def set_winner(self, user_id: int, submission_id: int, challenge_id: int) -> bool:
        async with self.get_session() as session:
            session.add(Winner(
                winner_id=user_id,
                submission_id=submission_id,
                challenge_id=challenge_id,
            ))
            return True
        
    async def get_submission(self, submission_id: int) -> Submission | None:
        async with self.get_session() as session:
            submission = await session.get(Submission, submission_id)
            return submission
    
    async def remove_winner(self, user_id: int, submission_id: int, challenge_id: int) -> None:
        async with self.get_session() as session:
            winner = await session.get(
                Winner, (user_id, submission_id, challenge_id)
            )
            if winner:
                await session.delete(winner)

    async def bulk_insert_submissions(self, submissions: list[dict]) -> list | None:
        async with self.get_session() as session:
            stmt = insert(Submission).values(submissions)
            stmt = stmt.on_conflict_do_update(
                index_elements=["id"],
                set_={"title": stmt.excluded.title, "edited_at": stmt.excluded.edited_at}
            ).returning(Submission)
            result = await session.execute(stmt)

            return list(result.scalars().all())

    async def get_vote(self, voter_id:int, challenge_id: int, submission_id: int) -> Vote | None:
        async with self.get_session() as session:
            vote = await session.get(Vote, (submission_id, challenge_id, voter_id))
            return vote


    async def bulk_insert_votes(
        self, votes: dict[int, Vote], challenge: Challenge
    ) -> list:
        async with self.get_session() as session:
            await session.execute(
                delete(Vote).where(
                    Vote.challenge_id == challenge.id,
                    Vote.voter_id.in_(votes.keys())
                )
            )
            existing_ids_result = await session.execute(
                select(Submission.id).where(
                    Submission.challenge_id == challenge.id
                )
            )
            existing_ids = set(existing_ids_result.scalars().all())
            valid = [v for v in votes.values() if v.submission_id in existing_ids]
            session.add_all(valid)
            return valid


    async def bulk_insert_winners(self, winners: set[Winner]) -> None:
        async with self.get_session() as session:
            submission_ids = [winner.submission_id for winner in winners]
            result = await session.execute(select(Winner.submission_id).where(Winner.submission_id.in_(submission_ids)))
            existing_winners = result.scalars().all()
            new_winners = [winner for winner in winners if winner.submission_id not in existing_winners]

            if new_winners:
                session.add_all(new_winners)

    
        

    async def set_past_winners(self, winners: list) -> None:
        async with self.get_session() as session:

            stmt = update(User).where(
                    User.total_challenges_won==0)

            await session.execute(stmt.execution_options(synchronize_session=False),winners)
            logger.info("Past winners reflected to the db")


    async def get_winner(self, user_id: int, submission_id: int, challenge_id:int,) -> Winner | None:
        async with self.get_session() as session:
            winner = await session.get(Winner, (user_id, submission_id, challenge_id))
            return winner

  
    async def cleanup_challenge_data(self, 
        submission_ids: list[int],
        votes: list[Vote], 
        winners: list[Winner],
        challenge: Challenge) -> None:

        async with self.get_session() as session:
            #cleanup votes
            if challenge.is_ongoing_voting:
                voter_challenge_submission_ids = [(vote.voter_id, vote.challenge_id, vote.submission_id) for vote in votes]
                await session.execute(delete(Vote).where(
                    and_(~tuple_(Vote.voter_id, Vote.challenge_id, Vote.submission_id).in_(voter_challenge_submission_ids),
                          Vote.challenge_id==challenge.id)))

            #cleanup submissions
            if challenge.is_active:
                deleted_submission_result = await session.execute(select(Submission.id).where(
                    and_(~Submission.id.in_(submission_ids), Submission.challenge_id==challenge.id)))
                deleted_submissions = deleted_submission_result.scalars().all()

                if deleted_submissions:
                    await session.execute(delete(Submission).where(Submission.id.in_(deleted_submissions)))



            #cleanup winners
            winner_submission_ids = [(winner.winner_id, winner.submission_id) for winner in winners]

            await session.execute(delete(Winner).where(and_(~tuple_(Winner.winner_id, Winner.submission_id).in_(winner_submission_ids), 
                                                            Winner.challenge_id == challenge.id)))