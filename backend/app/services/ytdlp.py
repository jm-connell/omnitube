"""yt-dlp integration service.

Extracts direct stream URLs for ad-free YouTube playback.
"""

import asyncio
import logging
from functools import partial

import yt_dlp

from app.config import settings
from app.schemas import StreamInfo

logger = logging.getLogger("omnitube.ytdlp")

# yt-dlp options for stream extraction (no download)
YDL_OPTS = {
    "format": settings.ytdlp_format,
    "quiet": True,
    "no_warnings": True,
    "extract_flat": False,
    "skip_download": True,
    "no_color": True,
}

if settings.ytdlp_proxy:
    YDL_OPTS["proxy"] = settings.ytdlp_proxy


def _extract_sync(video_id: str) -> dict:
    """Synchronous yt-dlp extraction (runs in thread pool)."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        info = ydl.extract_info(url, download=False)
    return info


async def get_stream_info(video_id: str) -> StreamInfo:
    """Extract stream info for a video. Runs yt-dlp in a thread pool."""
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, partial(_extract_sync, video_id))

    # Get best video + audio URLs
    video_url = info.get("url", "")
    audio_url = None

    # If format has separate video/audio, find them in requested_formats
    requested = info.get("requested_formats", [])
    if requested:
        for fmt in requested:
            if fmt.get("vcodec", "none") != "none" and fmt.get("acodec") in ("none", None):
                video_url = fmt["url"]
            elif fmt.get("acodec", "none") != "none" and fmt.get("vcodec") in ("none", None):
                audio_url = fmt["url"]
            elif fmt.get("vcodec", "none") != "none" and fmt.get("acodec", "none") != "none":
                video_url = fmt["url"]

    # If we still don't have a video_url, use the main URL
    if not video_url:
        video_url = info.get("url", info.get("webpage_url", ""))

    # Extract chapters if available
    chapters = None
    if info.get("chapters"):
        chapters = [
            {
                "title": ch.get("title", ""),
                "start_time": ch.get("start_time", 0),
                "end_time": ch.get("end_time", 0),
            }
            for ch in info["chapters"]
        ]

    return StreamInfo(
        video_url=video_url,
        audio_url=audio_url,
        title=info.get("title", ""),
        duration=info.get("duration"),
        description=info.get("description"),
        view_count=info.get("view_count"),
        like_count=info.get("like_count"),
        channel=info.get("uploader") or info.get("channel"),
        chapters=chapters,
    )
