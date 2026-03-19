"""Livestream detection service.

Checks each subscribed channel's /live page to detect active streams.
YouTube serves an SPA, so we parse the HTML body for live-stream markers
rather than relying on HTTP redirects.
"""

import asyncio
import logging
import re

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Channel

logger = logging.getLogger("omnitube.livestream")

# Patterns to detect an active livestream in the /live page HTML
_IS_LIVE_RE = re.compile(r'"isLive"\s*:\s*true', re.IGNORECASE)
# Extract the video ID from the canonical link or embedded data
_CANONICAL_VID_RE = re.compile(r'<link\s+rel="canonical"\s+href="https://www\.youtube\.com/watch\?v=([\w-]{11})"')
_VID_ID_RE = re.compile(r'"videoId"\s*:\s*"([\w-]{11})"')
_TITLE_RE = re.compile(r'"title"\s*:\s*"([^"]{1,200})"')
_OG_TITLE_RE = re.compile(r'<meta\s+property="og:title"\s+content="([^"]+)"', re.IGNORECASE)


async def _check_channel_live(
    client: httpx.AsyncClient,
    channel_id: str,
    channel_name: str,
) -> dict | None:
    """Check if a single channel is currently livestreaming."""
    url = f"https://www.youtube.com/channel/{channel_id}/live"
    try:
        resp = await client.get(url, follow_redirects=True)
        html = resp.text

        # Check if the page indicates an active livestream
        if not _IS_LIVE_RE.search(html):
            return None

        # Extract video ID — try canonical link first, then embedded JSON
        video_id = None
        m = _CANONICAL_VID_RE.search(html)
        if m:
            video_id = m.group(1)
        else:
            m = _VID_ID_RE.search(html)
            if m:
                video_id = m.group(1)

        if not video_id:
            return None

        # Extract title
        title = channel_name
        m = _OG_TITLE_RE.search(html)
        if m:
            raw = m.group(1).strip()
            if raw and raw.lower() != "youtube":
                title = raw
        else:
            m = _TITLE_RE.search(html)
            if m:
                raw = m.group(1).strip()
                if raw:
                    title = raw

        return {
            "channel_id": channel_id,
            "channel_name": channel_name,
            "video_id": video_id,
            "title": title,
            "thumbnail_url": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
        }

    except Exception as e:
        logger.debug(f"Livestream check failed for {channel_id}: {e}")
        return None


async def get_livestreams(db: AsyncSession) -> list[dict]:
    """Check all subscribed channels for active livestreams."""
    result = await db.execute(select(Channel.channel_id, Channel.name))
    channels = result.all()

    if not channels:
        return []

    livestreams: list[dict] = []

    async with httpx.AsyncClient(
        timeout=15.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    ) as client:
        # Check channels concurrently in batches of 5
        batch_size = 5
        for i in range(0, len(channels), batch_size):
            batch = channels[i : i + batch_size]
            tasks = [
                _check_channel_live(client, ch.channel_id, ch.name)
                for ch in batch
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, dict):
                    livestreams.append(r)

    logger.info(f"Livestream check: {len(livestreams)} live out of {len(channels)} channels")
    return livestreams
