"""yt-dlp integration service.

Extracts direct stream URLs for ad-free YouTube playback.
"""

import asyncio
import logging
import time
from functools import partial
from typing import Optional

import yt_dlp

from app.config import settings
from app.schemas import StreamInfo, SubtitleTrack

logger = logging.getLogger("omnitube.ytdlp")

# Subtitle URL cache: {video_id: (timestamp, {lang: url})}
_subtitle_cache: dict[str, tuple[float, dict[str, str]]] = {}
_CACHE_TTL = 3600  # 1 hour

QUALITY_FORMATS = {
    2160: "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best[ext=mp4]/best",
    1440: "bestvideo[height<=1440][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1440]+bestaudio/best[ext=mp4]/best",
    1080: "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best[ext=mp4]/best",
    720: "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best[ext=mp4]/best",
    480: "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=480]+bestaudio/best[ext=mp4]/best",
    360: "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=360]+bestaudio/best[ext=mp4]/best",
}

DEFAULT_QUALITY = 1440

# Common languages for auto-captions (limit dropdown size)
_COMMON_LANGS = {"en", "es", "fr", "de", "it", "pt", "ja", "ko", "zh-Hans", "zh-Hant", "ru", "ar", "hi", "nl", "pl", "sv", "tr"}


def _build_ydl_opts(quality: int = DEFAULT_QUALITY) -> dict:
    fmt = QUALITY_FORMATS.get(quality, QUALITY_FORMATS[DEFAULT_QUALITY])
    opts = {
        "format": fmt,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
        "no_color": True,
    }
    if settings.ytdlp_proxy:
        opts["proxy"] = settings.ytdlp_proxy
    return opts


def _extract_sync(video_id: str, quality: int = DEFAULT_QUALITY) -> dict:
    """Synchronous yt-dlp extraction (runs in thread pool)."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    with yt_dlp.YoutubeDL(_build_ydl_opts(quality)) as ydl:
        info = ydl.extract_info(url, download=False)
    return info


def _get_available_qualities(info: dict) -> list[int]:
    """Extract available video quality levels from format list."""
    heights = set()
    for fmt in info.get("formats", []):
        h = fmt.get("height")
        vcodec = fmt.get("vcodec", "none")
        if h and vcodec and vcodec != "none":
            heights.add(h)

    if not heights:
        return [360]

    max_height = max(heights)
    standard = [2160, 1440, 1080, 720, 480, 360]
    return [q for q in standard if q <= max_height]


def get_subtitle_url(video_id: str, lang: str) -> Optional[str]:
    """Get cached subtitle URL for a video and language."""
    entry = _subtitle_cache.get(video_id)
    if entry:
        ts, subs = entry
        if time.time() - ts < _CACHE_TTL:
            return subs.get(lang)
    return None


async def get_stream_info(video_id: str, quality: int = DEFAULT_QUALITY) -> StreamInfo:
    """Extract stream info for a video. Runs yt-dlp in a thread pool."""
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, partial(_extract_sync, video_id, quality))

    # Get best video + audio URLs
    video_url = info.get("url", "")
    audio_url = None
    width = info.get("width")
    height = info.get("height")

    # If format has separate video/audio, find them in requested_formats
    requested = info.get("requested_formats", [])
    if requested:
        for fmt in requested:
            if fmt.get("vcodec", "none") != "none" and fmt.get("acodec") in ("none", None):
                video_url = fmt["url"]
                width = width or fmt.get("width")
                height = height or fmt.get("height")
            elif fmt.get("acodec", "none") != "none" and fmt.get("vcodec") in ("none", None):
                audio_url = fmt["url"]
            elif fmt.get("vcodec", "none") != "none" and fmt.get("acodec", "none") != "none":
                video_url = fmt["url"]
                width = width or fmt.get("width")
                height = height or fmt.get("height")

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

    # Extract subtitles
    subtitles: list[SubtitleTrack] = []
    sub_urls: dict[str, str] = {}

    manual_subs = info.get("subtitles") or {}
    auto_captions = info.get("automatic_captions") or {}

    # Manual subtitles (include all)
    for lang_code, formats in manual_subs.items():
        vtt = next((f for f in formats if f.get("ext") == "vtt"), None)
        if vtt and vtt.get("url"):
            label = vtt.get("name") or lang_code
            subtitles.append(SubtitleTrack(lang=lang_code, label=label))
            sub_urls[lang_code] = vtt["url"]

    # Auto-captions (only common languages, skip if manual exists)
    for lang_code, formats in auto_captions.items():
        if lang_code in sub_urls:
            continue
        if lang_code not in _COMMON_LANGS:
            continue
        vtt = next((f for f in formats if f.get("ext") == "vtt"), None)
        if vtt and vtt.get("url"):
            label = vtt.get("name") or lang_code
            subtitles.append(SubtitleTrack(lang=lang_code, label=f"{label} (auto)"))
            sub_urls[lang_code] = vtt["url"]

    # Cache subtitle URLs
    _subtitle_cache[video_id] = (time.time(), sub_urls)

    # Sort: English first, then alphabetical
    subtitles.sort(key=lambda s: (s.lang != "en", s.lang))

    # Available qualities
    available_qualities = _get_available_qualities(info)

    return StreamInfo(
        video_url=video_url,
        audio_url=audio_url,
        title=info.get("title", ""),
        duration=info.get("duration"),
        description=info.get("description"),
        view_count=info.get("view_count"),
        like_count=info.get("like_count"),
        channel=info.get("uploader") or info.get("channel"),
        channel_id=info.get("channel_id"),
        chapters=chapters,
        subtitles=subtitles if subtitles else None,
        width=width,
        height=height,
        available_qualities=available_qualities,
    )
