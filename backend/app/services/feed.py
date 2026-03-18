"""RSS feed fetching and parsing service.

Uses the UULF playlist trick to get long-form-only feeds
(automatically excludes Shorts and live streams).
"""

import asyncio
import logging
from datetime import datetime

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import Channel, Video

logger = logging.getLogger("omnitube.feed")


def _build_rss_url(channel_id: str) -> str:
    """Build RSS URL using the UULF trick to exclude Shorts/lives.

    Converts UC... channel_id → UULF... playlist_id for long-form only.
    """
    if channel_id.startswith("UC"):
        playlist_id = "UULF" + channel_id[2:]
    else:
        playlist_id = channel_id
    return f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"


async def _fetch_feed(url: str) -> str:
    """Fetch RSS feed XML over HTTP."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def _parse_feed(xml_text: str) -> list[dict]:
    """Parse an Atom feed and return a list of video dicts."""
    feed = feedparser.parse(xml_text)
    videos = []
    for entry in feed.entries:
        video_id = entry.get("yt_videoid", "")
        if not video_id:
            # Try to extract from link
            link = entry.get("link", "")
            if "watch?v=" in link:
                video_id = link.split("watch?v=")[-1].split("&")[0]
        if not video_id:
            continue

        # Parse published date
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if published:
            pub_dt = datetime(*published[:6])
        else:
            pub_dt = datetime.utcnow()

        # Thumbnail
        thumbnail = None
        media_group = entry.get("media_group") or entry.get("media_thumbnail")
        if media_group:
            if isinstance(media_group, list) and len(media_group) > 0:
                thumbnail = media_group[0].get("url")
        if not thumbnail:
            thumbnail = f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg"

        # Channel ID from feed
        channel_id = ""
        if hasattr(entry, "yt_channelid"):
            channel_id = entry.yt_channelid
        elif "author_detail" in entry and "href" in entry.author_detail:
            href = entry.author_detail.href
            if "/channel/" in href:
                channel_id = href.split("/channel/")[-1]

        videos.append({
            "video_id": video_id,
            "channel_id": channel_id,
            "title": entry.get("title", "Untitled"),
            "thumbnail_url": thumbnail,
            "published_at": pub_dt,
            "description": entry.get("summary", None),
        })

    return videos


async def refresh_channel_feed(channel_id: str, db: AsyncSession) -> int:
    """Fetch and store new videos for a single channel. Returns count of new videos."""
    url = _build_rss_url(channel_id)
    new_count = 0

    try:
        xml_text = await _fetch_feed(url)
        videos = _parse_feed(xml_text)

        for v in videos:
            # Fix channel_id if not parsed from feed
            if not v["channel_id"]:
                v["channel_id"] = channel_id

            existing = await db.execute(
                select(Video).where(Video.video_id == v["video_id"])
            )
            if existing.scalar_one_or_none():
                continue

            video = Video(
                video_id=v["video_id"],
                channel_id=v["channel_id"],
                title=v["title"],
                thumbnail_url=v["thumbnail_url"],
                published_at=v["published_at"],
                description=v["description"],
            )
            db.add(video)
            new_count += 1

        await db.commit()
        logger.info(f"Channel {channel_id}: {new_count} new videos")

    except Exception as e:
        logger.error(f"Failed to fetch feed for {channel_id}: {e}")
        await db.rollback()

    return new_count


async def refresh_all_feeds(db: AsyncSession | None = None) -> int:
    """Refresh feeds for all subscribed channels.

    Can be called from the scheduler (no db param) or manually (with db).
    """
    if db is None:
        async with async_session() as db:
            return await _refresh_all_impl(db)
    return await _refresh_all_impl(db)


async def _refresh_all_impl(db: AsyncSession) -> int:
    """Implementation of refresh_all_feeds."""
    result = await db.execute(select(Channel.channel_id))
    channel_ids = [row[0] for row in result.all()]

    if not channel_ids:
        logger.info("No channels to refresh")
        return 0

    logger.info(f"Refreshing feeds for {len(channel_ids)} channels...")
    total_new = 0

    # Process channels sequentially to avoid sharing the async session
    # across concurrent tasks (SQLAlchemy async sessions are not task-safe)
    for cid in channel_ids:
        try:
            count = await refresh_channel_feed(cid, db)
            total_new += count
        except Exception as e:
            logger.error(f"Failed to refresh {cid}: {e}")

    logger.info(f"Feed refresh complete: {total_new} new videos total")
    return total_new
