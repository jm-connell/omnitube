"""Pydantic schemas for API request/response validation."""

from datetime import datetime, timezone

from pydantic import BaseModel, field_validator


# ── Channels ──────────────────────────────────────────────────────────

class ChannelCreate(BaseModel):
    channel_id: str
    name: str | None = None


class ChannelUpdate(BaseModel):
    name: str


class ChannelOut(BaseModel):
    id: int
    channel_id: str
    name: str
    thumbnail_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChannelImport(BaseModel):
    """Accepts a list of channel objects (from YouTube export or manual entry)."""
    channels: list[ChannelCreate]


class OPMLImport(BaseModel):
    """Raw OPML XML string from YouTube subscription export."""
    opml_xml: str


# ── Videos ────────────────────────────────────────────────────────────

class VideoOut(BaseModel):
    id: int
    video_id: str
    channel_id: str
    title: str
    thumbnail_url: str | None = None
    published_at: datetime
    description: str | None = None
    duration_seconds: int | None = None
    view_count: int | None = None
    like_count: int | None = None
    watched: bool = False
    watch_progress: int = 0
    channel_name: str | None = None  # joined from channels table

    @field_validator("published_at", mode="before")
    @classmethod
    def ensure_utc(cls, v: datetime | str) -> datetime:
        """Ensure published_at always has UTC timezone info."""
        if isinstance(v, str):
            v = datetime.fromisoformat(v)
        if v.tzinfo is None:
            v = v.replace(tzinfo=timezone.utc)
        return v

    model_config = {"from_attributes": True}


class FeedResponse(BaseModel):
    videos: list[VideoOut]
    total: int
    page: int
    per_page: int


# ── Stream ────────────────────────────────────────────────────────────

class SubtitleTrack(BaseModel):
    lang: str
    label: str


class StreamInfo(BaseModel):
    video_url: str
    audio_url: str | None = None
    title: str
    duration: int | None = None
    description: str | None = None
    view_count: int | None = None
    like_count: int | None = None
    channel: str | None = None
    channel_id: str | None = None
    chapters: list[dict] | None = None
    subtitles: list[SubtitleTrack] | None = None
    width: int | None = None
    height: int | None = None
    available_qualities: list[int] | None = None


class Comment(BaseModel):
    author: str
    text: str
    likes: int = 0
    time_text: str | None = None
    is_pinned: bool = False


class CommentsResponse(BaseModel):
    comments: list[Comment]
    count: int | None = None


# ── App State ─────────────────────────────────────────────────────────

class SetupStatus(BaseModel):
    setup_complete: bool
    channel_count: int
    video_count: int
