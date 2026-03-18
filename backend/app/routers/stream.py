"""Video stream proxy via yt-dlp."""

import re
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, Response

from app.schemas import StreamInfo
from app.services.ytdlp import get_stream_info, get_subtitle_url

router = APIRouter(prefix="/api/stream", tags=["stream"])


@router.get("/{video_id}", response_model=StreamInfo)
async def stream_info(video_id: str, quality: int = Query(1440, ge=144, le=4320)):
    """Extract direct stream URLs for a YouTube video via yt-dlp."""
    try:
        info = await get_stream_info(video_id, quality)
        return info
    except Exception as e:
        raise HTTPException(500, f"Failed to extract stream: {str(e)}")


@router.get("/{video_id}/subtitles/{lang}")
async def get_subtitles(video_id: str, lang: str):
    """Proxy subtitle content to avoid CORS issues."""
    if not re.match(r'^[\w-]{1,20}$', video_id):
        raise HTTPException(400, "Invalid video ID")
    if not re.match(r'^[\w-]{1,20}$', lang):
        raise HTTPException(400, "Invalid language code")

    url = get_subtitle_url(video_id, lang)
    if not url:
        raise HTTPException(404, "Subtitle not found or expired")

    # Validate URL domain to prevent SSRF
    parsed = urlparse(url)
    allowed = (".youtube.com", ".google.com", ".googlevideo.com", ".ytimg.com")
    if not parsed.hostname or not any(parsed.hostname.endswith(d) for d in allowed):
        raise HTTPException(400, "Invalid subtitle source")

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return Response(
            content=resp.content,
            media_type="text/vtt",
            headers={"Cache-Control": "public, max-age=3600"},
        )


@router.get("/{video_id}/redirect")
async def stream_redirect(video_id: str):
    """Redirect to the direct video URL (single combined stream)."""
    try:
        info = await get_stream_info(video_id)
        return RedirectResponse(url=info.video_url)
    except Exception as e:
        raise HTTPException(500, f"Failed to extract stream: {str(e)}")
