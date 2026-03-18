"""Video stream proxy via yt-dlp."""

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from app.schemas import StreamInfo
from app.services.ytdlp import get_stream_info

router = APIRouter(prefix="/api/stream", tags=["stream"])


@router.get("/{video_id}", response_model=StreamInfo)
async def stream_info(video_id: str):
    """Extract direct stream URLs for a YouTube video via yt-dlp.

    Returns video + audio URLs that the frontend can play with
    a native <video> element or a player like Plyr.
    """
    try:
        info = await get_stream_info(video_id)
        return info
    except Exception as e:
        raise HTTPException(500, f"Failed to extract stream: {str(e)}")


@router.get("/{video_id}/redirect")
async def stream_redirect(video_id: str):
    """Redirect to the direct video URL (single combined stream).

    Useful for simple <video src="..."> usage.
    """
    try:
        info = await get_stream_info(video_id)
        return RedirectResponse(url=info.video_url)
    except Exception as e:
        raise HTTPException(500, f"Failed to extract stream: {str(e)}")
