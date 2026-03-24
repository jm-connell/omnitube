"""Video stream proxy via yt-dlp."""

import re
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, Response, StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Video
from app.schemas import StreamInfo, CommentsResponse, Comment
from app.services.ytdlp import (
    get_stream_info, get_subtitle_url, get_comments, get_download_url,
    get_cached_stream_urls, invalidate_stream_url_cache,
)

router = APIRouter(prefix="/api/stream", tags=["stream"])

# 10MB chunk size — matches Invidious; YouTube throttles requests > 10MB
_PROXY_CHUNK_SIZE = 10_485_760
_ALLOWED_DOMAINS = (".youtube.com", ".google.com", ".googlevideo.com", ".ytimg.com")


@router.get("/{video_id}", response_model=StreamInfo)
async def stream_info(
    video_id: str,
    quality: int = Query(1440, ge=144, le=4320),
    db: AsyncSession = Depends(get_db),
):
    """Extract direct stream URLs for a YouTube video via yt-dlp."""
    try:
        info = await get_stream_info(video_id, quality)
        # Persist duration for Shorts filtering and display
        if info.duration:
            result = await db.execute(
                select(Video).where(Video.video_id == video_id)
            )
            video = result.scalar_one_or_none()
            if video and video.duration_seconds != info.duration:
                video.duration_seconds = info.duration
                await db.commit()
        return info
    except Exception as e:
        raise HTTPException(500, f"Failed to extract stream: {str(e)}")


async def _proxy_stream(
    video_id: str, quality: int, stream_type: str, request: Request,
):
    """Proxy a YouTube stream with chunked 10MB requests to avoid throttling."""
    if not re.match(r'^[\w-]{1,20}$', video_id):
        raise HTTPException(400, "Invalid video ID")

    video_url, audio_url = await get_cached_stream_urls(video_id, quality)
    if stream_type == "audio":
        if not audio_url:
            raise HTTPException(404, "No separate audio stream available")
        youtube_url = audio_url
    else:
        youtube_url = video_url

    # SSRF prevention
    parsed = urlparse(youtube_url)
    if not parsed.hostname or not any(parsed.hostname.endswith(d) for d in _ALLOWED_DOMAINS):
        raise HTTPException(400, "Invalid stream source")

    timeout = httpx.Timeout(30.0, read=300.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        # HEAD request to get total size
        try:
            head_resp = await client.head(youtube_url)
            head_resp.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 403:
                # URL expired — clear cache and re-extract once
                invalidate_stream_url_cache(video_id, quality)
                video_url, audio_url = await get_cached_stream_urls(video_id, quality)
                youtube_url = audio_url if stream_type == "audio" else video_url
                if not youtube_url:
                    raise HTTPException(502, "Stream URL expired")
                head_resp = await client.head(youtube_url)
                head_resp.raise_for_status()
            else:
                raise HTTPException(502, "Failed to reach video source")

        total_size = int(head_resp.headers.get("content-length", 0))
        content_type = head_resp.headers.get("content-type", "application/octet-stream")

    if not total_size:
        raise HTTPException(502, "Could not determine stream size")

    # Parse Range header from browser
    range_header = request.headers.get("range")
    start = 0
    end = total_size - 1
    if range_header:
        m = re.match(r"bytes=(\d+)-(\d*)", range_header)
        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else total_size - 1

    content_length = end - start + 1

    async def stream_chunks():
        pos = start
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as c:
            while pos <= end:
                chunk_end = min(pos + _PROXY_CHUNK_SIZE - 1, end)
                async with c.stream(
                    "GET", youtube_url,
                    headers={"Range": f"bytes={pos}-{chunk_end}"},
                ) as resp:
                    resp.raise_for_status()
                    async for data in resp.aiter_bytes(chunk_size=65536):
                        yield data
                pos = chunk_end + 1

    headers = {
        "Content-Type": content_type,
        "Accept-Ranges": "bytes",
        "Content-Length": str(content_length),
    }

    if range_header:
        headers["Content-Range"] = f"bytes {start}-{end}/{total_size}"
        return StreamingResponse(stream_chunks(), status_code=206, headers=headers)

    return StreamingResponse(stream_chunks(), status_code=200, headers=headers)


@router.get("/{video_id}/proxy/video")
async def proxy_video(
    video_id: str, request: Request, quality: int = Query(1440, ge=144, le=4320),
):
    """Proxy video stream through the server to avoid YouTube throttling."""
    return await _proxy_stream(video_id, quality, "video", request)


@router.get("/{video_id}/proxy/audio")
async def proxy_audio(
    video_id: str, request: Request, quality: int = Query(1440, ge=144, le=4320),
):
    """Proxy audio stream through the server to avoid YouTube throttling."""
    return await _proxy_stream(video_id, quality, "audio", request)


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
