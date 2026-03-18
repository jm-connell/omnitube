"""Video stream proxy via yt-dlp."""

import re
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse, Response

from app.schemas import StreamInfo, CommentsResponse, Comment
from app.services.ytdlp import get_stream_info, get_subtitle_url, get_comments, get_download_url

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
        # Strip VTT cue positioning/alignment settings so captions render centered
        vtt_text = resp.text
        vtt_text = re.sub(
            r'([\d:.]+\s*-->\s*[\d:.]+)\s+[^\n]*',
            r'\1',
            vtt_text,
        )
        return Response(
            content=vtt_text.encode("utf-8"),
            media_type="text/vtt",
            headers={"Cache-Control": "public, max-age=3600"},
        )


@router.get("/{video_id}/comments", response_model=CommentsResponse)
async def video_comments(video_id: str, limit: int = Query(30, ge=1, le=100)):
    """Fetch top comments for a video."""
    if not re.match(r'^[\w-]{1,20}$', video_id):
        raise HTTPException(400, "Invalid video ID")
    try:
        comments_raw, total = await get_comments(video_id, limit)
        comments = [Comment(**c) for c in comments_raw]
        return CommentsResponse(comments=comments, count=total)
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch comments: {str(e)}")


@router.get("/{video_id}/redirect")
async def stream_redirect(video_id: str):
    """Redirect to the direct video URL (single combined stream)."""
    try:
        info = await get_stream_info(video_id)
        return RedirectResponse(url=info.video_url)
    except Exception as e:
        raise HTTPException(500, f"Failed to extract stream: {str(e)}")


@router.get("/{video_id}/download")
async def download_video(video_id: str, quality: int = Query(720, ge=144, le=4320)):
    """Get a combined-format download URL (less throttled by YouTube)."""
    if not re.match(r'^[\w-]{1,20}$', video_id):
        raise HTTPException(400, "Invalid video ID")
    try:
        url = await get_download_url(video_id, quality)
        if not url:
            raise HTTPException(500, "No combined format found")
        return {"url": url}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Download URL extraction failed: {str(e)}")
