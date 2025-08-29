import datetime as dt
from enum import Enum as PyEnum
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    display_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True),  server_default=func.now())

class Room(Base):
    __tablename__ = "rooms"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(12), unique=True, nullable=False)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    host_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True),  server_default=func.now())

class RoomMember(Base):
    __tablename__ = "room_members"
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), primary_key=True)
    role: Mapped[str] = mapped_column(String, default="guest", nullable=False)
    joined_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    #add index on common lookups
    __table_args__ = (
        Index("ix_room_members_room_id", "room_id"),
        Index("ix_room_members_user_id", "user_id"),
    )

class Track(Base):
    __tablename__ = "tracks"
    id: Mapped[str] = mapped_column(String, primary_key=True)  #mock:track:1 or a Spotify ID
    title: Mapped[str] = mapped_column(String, nullable=False)
    artist: Mapped[str] = mapped_column(String, nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=180_000)  # 3 min default

    __table_args__ = (
        Index("ix_tracks_title", "title"),
        Index("ix_tracks_artist", "artist"),
    )

class TrackStatus(PyEnum):
    queued = "queued"
    playing = "playing"
    played = "played"
    removed = "removed"

class RoomTrack(Base):
    __tablename__ = "room_tracks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("rooms.id"), nullable=False)
    track_id: Mapped[str] = mapped_column(String, ForeignKey("tracks.id"), nullable=False)
    added_by_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status: Mapped[TrackStatus] = mapped_column(SAEnum(TrackStatus, name="track_status"), default=TrackStatus.queued, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True),  server_default=func.now())
   
    __table_args__ = (
        Index("ix_room_tracks_room_id", "room_id"),
        Index("ix_room_tracks_track_id", "track_id"),
    )

class Vote(Base):
    __tablename__ = "votes"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    room_track_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("room_tracks.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    value: Mapped[int] = mapped_column(Integer, nullable=False)  # +1 or -1
    created_at: Mapped[dt.datetime] = mapped_column(DateTime(timezone=True),  server_default=func.now())

    __table_args__ = (
        UniqueConstraint("room_track_id", "user_id", name="uq_vote_per_user_per_track"),
        CheckConstraint("value IN (-1, 1)", name="ck_vote_value"),
        Index("ix_votes_room_track_id", "room_track_id"),
        Index("ix_votes_user_id", "user_id"),
    )