"""SQLAlchemy ORM models.

Structured for MVP with extension points for future advanced features
(watch history, playlists, tags, etc.).
"""

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Channel(Base):
    """A subscribed YouTube channel."""

    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    channel_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Future: tag_id foreign key for channel tagging
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Video(Base):
    """A video from an RSS feed entry."""

    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_id: Mapped[str] = mapped_column(String(16), unique=True, nullable=False, index=True)
    channel_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    published_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    view_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    like_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Future extension columns (nullable so they don't break existing rows)
    watched: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    watch_progress: Mapped[int] = mapped_column(Integer, default=0, server_default="0")  # seconds

    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AppState(Base):
    """Key-value store for app-level state (setup_complete, etc.)."""

    __tablename__ = "app_state"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
