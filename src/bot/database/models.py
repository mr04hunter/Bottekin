from __future__ import annotations
from typing import List, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import (
    BigInteger,
    Integer,
    ScalarSelect,
    Text,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Float,
    UniqueConstraint,
    select,
    Table,
    Column,
    Index,
    inspect,
    text
    
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# Base class for models
class Base(DeclarativeBase):
    pass








########### ------- ASSOCIATION TABLES  ------------#################33

user_tracks = Table("track_givers",
            Base.metadata,
            Column("feedback_id", ForeignKey("feedbacks.id", ondelete="CASCADE"), primary_key=True),
            Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
            Column("track_id", ForeignKey("tracks.id", ondelete="CASCADE"), primary_key=True)
            
            )


class TrackWithNoFeedback(Base):
    __tablename__ = "tracks_with_no_feedback"
    track_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("tracks.id", ondelete="CASCADE"),primary_key=True)
    message_id: Mapped[int] = mapped_column(BigInteger)
    message_url: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )


class UserLeftNotificationMessage(Base):
    __tablename__ = "user_left_notification_message"
    user_id: Mapped[int] = mapped_column(BigInteger,primary_key=True)
    message_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInteger)

class Winner(Base):
    __tablename__ = "winners"
    winner_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    submission_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("submissions.id", ondelete="CASCADE"), primary_key=True)
    challenge_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("challenges.id", ondelete="CASCADE"), primary_key=True)

    winner: Mapped["User"] = relationship(back_populates="challenges_won")
    submission: Mapped["Submission"] = relationship()
    challenge: Mapped["Challenge"] = relationship(back_populates="winners")


    def __str__(self) -> str:
        return f"winner_id: {self.winner_id}, submission_id: {self.submission_id}, challenge_id: {self.challenge_id}"
    


class Leaderboards(Base):
    __tablename__ = "leaderboards"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    type: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

# ---USERS---


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    times_voted: Mapped[int] = mapped_column(Integer, default=0)
    total_votes_received: Mapped[int] = mapped_column(Integer, default=0)
    total_feedbacks_given: Mapped[int] = mapped_column(Integer, default=0)
    total_feedback_words: Mapped[int] = mapped_column(Integer, default=0)
    total_feedbacks_received: Mapped[int] = mapped_column(Integer, default=0)
    total_submissions: Mapped[int] = mapped_column(Integer, default=0)
    total_challenges_won: Mapped[int] = mapped_column(Integer, default=0)

    last_submission: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_purge_data: Mapped[bool] = mapped_column(Boolean, server_default='true')

    # Relationships
    feedbacks: Mapped[List["Feedback"]] = relationship(back_populates="author", order_by="Feedback.created_at.desc()", cascade="all, delete-orphan")
    tracks: Mapped[List["Track"]] = relationship(back_populates="author", cascade="all, delete-orphan")
    gave_feedback_to: Mapped[List["Track"]] = relationship("Track", secondary=user_tracks, back_populates="feedback_givers")
    challenges_won: Mapped[List["Winner"]] = relationship(back_populates="winner")
    submissions: Mapped[List["Submission"]] = relationship(back_populates="author", cascade="all, delete-orphan", foreign_keys="Submission.author_id")
    votes: Mapped[List["Vote"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    voted_submissions: Mapped[List["Submission"]] = relationship(
    secondary="votes",
    primaryjoin="User.id == Vote.voter_id",
    secondaryjoin="Vote.submission_id == Submission.id",
    back_populates="voters",
    viewonly=True
)
    hosted_challenges: Mapped[List["Challenge"]] = relationship(back_populates="host", foreign_keys="Challenge.host_id")


    def __str__(self) -> str:

        result = f""" id: {self.id}, username:{self.username}, display_name:{self.display_name}, total_feedbacks_given: {self.total_feedbacks_given},
        total_feedback_words: {self.total_feedback_words}, total_feedbacks_received: {self.total_feedbacks_received},
          total_challenges: {self.total_submissions}, is_purge_data:{self.is_purge_data.__str__()}
        """
        insp = inspect(self)
        if "feedbacks" not in insp.unloaded:
            result += f"feedbacks: {self.feedbacks}"
        if "tracks" not in insp.unloaded:
            result += f"tracks: {self.tracks}"
        if "gave_feedback_to" not in insp.unloaded:
            result += f"gave_feedback_to: {self.gave_feedback_to}"
        if "challenges_won" not in insp.unloaded:
            result += f"challenges_won: {self.challenges_won}"
        if "submissions" not in insp.unloaded:
            result += f"submissions: {self.submissions}"
        if "votes" not in insp.unloaded:
            result += f"votes {self.votes}"
        if "voted_submissions" not in insp.unloaded:
            result += f"voted_submissions: {self.voted_submissions}"
        if "hosted_challenges" not in insp.unloaded:
            result += f"hosted_challenges: {self.hosted_challenges}"
        
        return result
    


    
    @hybrid_property
    def last_feedback(self) -> Optional[datetime]:
        return self.feedbacks[0].created_at if self.feedbacks else None


    @last_feedback.inplace.expression
    @classmethod
    def _last_feedback_expression(cls) -> ScalarSelect:
        return (
            select(Feedback.created_at)
            .where(Feedback.author_id == cls.id)
            .correlate_except(Feedback)
            .order_by(Feedback.created_at.desc())
            .limit(1)
            .scalar_subquery()
        )
    



# ---CHALLENGES---

class Challenge(Base):
    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    type: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    host_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, server_default=text("NULL")
    )
    total_votes: Mapped[int] = mapped_column(Integer, default=0)
    total_submissions: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    voting_ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    is_ongoing_voting: Mapped[bool] = mapped_column(Boolean, server_default="true")
    
    # Relationships
    host: Mapped[Optional["User"]] = relationship(back_populates="hosted_challenges", foreign_keys=[host_id])
    winners: Mapped[List["Winner"]] = relationship(back_populates="challenge", cascade="all, delete-orphan")
    submissions: Mapped[List["Submission"]] = relationship(back_populates="challenge", cascade="all, delete-orphan")
    votes: Mapped[List["Vote"]] = relationship(back_populates="challenge", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_challenge_id_is_active", "id", "is_active"),
    )


    def __str__(self) -> str:
        result = f""" id: {self.id}, name: {self.title}, description: {self.description}, type:{self.type}
"""     
        insp = inspect(self)
        if 'winners' not in insp.unloaded:
            result += f"winner: {self.winners}"
        
        if 'submissions' not in insp.unloaded:
            result += f"submissions: {self.submissions}"
        
        if 'votes' not in insp.unloaded:
            result += f"votes: {self.votes}"

        return result
# ---SUBMISSIONS---

class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    challenge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False
    )
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    total_votes: Mapped[int] = mapped_column(Integer, default=0)
    winner_declared: Mapped[bool] = mapped_column(Boolean, default=False)
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, 
    )

    __table_args__ = (
        UniqueConstraint("challenge_id", "author_id"),

    )

    # Relationships
    challenge: Mapped["Challenge"] = relationship(back_populates="submissions")
    author: Mapped["User"] = relationship(back_populates="submissions", foreign_keys=[author_id])
    votes: Mapped[List["Vote"]] = relationship(back_populates="submission", cascade="all, delete-orphan")
    voters: Mapped[List["User"]] = relationship(
        secondary="votes",
        primaryjoin="Submission.id == Vote.submission_id",
        secondaryjoin="Vote.voter_id == User.id",
        back_populates="voted_submissions",
        viewonly=True
    )


    def __str__(self) -> str:
        result = f""" id: {self.id},
        channel_id: {self.channel_id}, title: {self.title}, created_at: {self.created_at}, total_votes: {self.total_votes}, winner_declared: {self.winner_declared}"""
        insp = inspect(self)
        if "author_id" not in insp.unloaded:
            result += f"author_id: {self.author_id}"
        if "challenge_id" not in insp.unloaded:
            result += f"challenge_id: {self.challenge_id}"
        if "challenge" not in insp.unloaded:
            result += f"chalenge: {self.challenge}"
        if "author" not in insp.unloaded:
            result += f"author: {self.author}"
        if "votes" not in insp.unloaded:
            result += f"votes: {self.votes}"
        if "voters" not in insp.unloaded:
            result += f"voters {self.voters}"
        
        return result

# ---FEEDBACK-MUSIC---

class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    thread_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(Text, default="attachment")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    total_feedbacks: Mapped[int] = mapped_column(Integer, default=0)
    total_reactions: Mapped[int] = mapped_column(Integer, default=0)
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )


    # Relationships
    author: Mapped["User"] = relationship(back_populates="tracks")
    feedbacks: Mapped[List["Feedback"]] = relationship(back_populates="track")
    feedback_givers: Mapped[List["User"]] =  relationship("User", secondary=user_tracks,back_populates="gave_feedback_to",)

    __table_args__ = (
        Index("idx_author_id_track_id", "id", "author_id", unique=True),
        Index("idx_track_id_channel_id","id", "channel_id", unique=True)
    )

    def __str__(self) -> str:
        result = f"""
        id: {self.id}, thread_id: {self.thread_id}, channel_id: {self.channel_id}, title: {self.title}, platform: {self.platform},
        created_at: {self.created_at}, total_feedbacks: {self.total_feedbacks}, total_reactions: {self.total_reactions}
"""     
        insp = inspect(self)
        if "author_id" not in insp.unloaded:
            result += f"author_id: {self.author_id}"
        if "author" not in insp.unloaded:
            result += f"author: {self.author}"
        if "feedbacks" not in insp.unloaded:
            result += f"feedbacks: {self.feedbacks}"
        if "feedback_givers" not in insp.unloaded:
            result += f"feedback_givers: {self.feedback_givers}"

        return result
# ---FEEDBACKS---

class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    thread_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    word_count: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    edited_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    feedback_score: Mapped[float] = mapped_column(Float, default=0.0)
    track_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("tracks.id", ondelete="SET NULL"), nullable=True
    )
    author_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    # Relationships
    track: Mapped["Track | None"] = relationship(back_populates="feedbacks")
    author: Mapped["User"] = relationship(back_populates="feedbacks")

    __table_args__ = (
        Index("idx_author_thread_pairs", "author_id", "thread_id", unique=True),
        Index("idx_feedback_channel_id","id","channel_id"),
        Index("idx_thread_created", "thread_id", "created_at"),
    )

    def __str__(self) -> str:
        result = f"""
        id: {self.id}, thread_id: {self.thread_id}, channel_id: {self.channel_id},
        content: {self.content}, word_count: {self.word_count}, created_at: {self.created_at},
        feedback_score: {self.feedback_score}
"""
        insp = inspect(self)

        if "author_id" not in insp.unloaded:
            result += f"author_id: {self.author_id}"
        if "track_id" not in insp.unloaded:
            result += f"track_id: {self.track_id}"
        if "track" not in insp.unloaded:
            result += f"track: {self.track}"
        if "author" not in insp.unloaded:
            result += f"author: {self.author}"
        
        return result






# ---VOTES---

class Vote(Base):
    __tablename__ = "votes"

    submission_id: Mapped[int] = mapped_column(
    BigInteger, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False, primary_key=True
)
    challenge_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, primary_key=True
    )
    voter_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    __table_args__ = (
        Index("idx_challenge_id_voter_id_submission_id", "challenge_id", "voter_id", "submission_id"),
       
    )

    # Relationships 
    user: Mapped["User"] = relationship(back_populates="votes")
    challenge: Mapped["Challenge"] = relationship(back_populates="votes")
    submission: Mapped["Submission"] = relationship(back_populates="votes")

    def __str__(self) -> str:
        result = f"""
        created_at: {self.created_at}
"""
        insp = inspect(self)

        if "submission_id" not in insp.unloaded:
            result += f"submission_id: {self.submission_id}"

        if "challenge_id" not in insp.unloaded:
            result += f"challenge_id: {self.challenge_id}"

        if "user_id" not in insp.unloaded:
            result += f"user_id: {self.voter_id}"

        if "user" not in insp.unloaded:
            result += f"user: {self.user}"
        
        if "challenge" not in insp.unloaded:
            result += f"challenge: {self.challenge}"

        if "submission" not in insp.unloaded:
            result += f"submission: {self.submission}"

        return result



