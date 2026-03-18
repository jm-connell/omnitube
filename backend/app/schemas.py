"""Pydantic schemas for API request/response validation."""

from datetime import datetime

from pydantic import BaseModel


# ── Channels ──────────────────────────────────────────────────────────

class ChannelCreate(BaseModel):
    channel_id: str
    name: str | None = None


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


# ── App State ─────────────────────────────────────────────────────────

class SetupStatus(BaseModel):
    setup_complete: bool
    channel_count: int
    video_count: int
