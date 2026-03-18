"""RSS feed fetching and parsing service.

Uses the UULF playlist trick to get long-form-only feeds
(automatically excludes Shorts and live streams).
"""

import asyncio
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import feedparser
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models import Channel, Video

logger = logging.getLogger("omnitube.feed")


def _build_rss_urls(channel_id: str) -> list[str]:
    """Build RSS URLs with fallbacks for reliability.

    Tries UULF playlist first (excludes Shorts/lives),
    falls back to standard channel feed.
    """
    urls = []
    if channel_id.startswith("UC"):
        urls.append(f"https://www.youtube.com/feeds/videos.xml?playlist_id=UULF{channel_id[2:]}")
        urls.append(f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}")
    else:
        urls.append(f"https://www.youtube.com/feeds/videos.xml?playlist_id={channel_id}")
    return urls


async def _fetch_feed(url: str) -> str:
    """Fetch RSS feed XML over HTTP."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def _parse_view_counts(xml_text: str) -> dict[str, int]:
    """Parse view counts from raw XML since feedparser doesn't handle media:community well."""
    view_counts: dict[str, int] = {}
    try:
        root = ET.fromstring(xml_text)
        ns = {
            "atom": "http://www.w3.org/2005/Atom",
            "yt": "http://www.youtube.com/xml/schemas/2015",
            "media": "http://search.yahoo.com/mrss/",
        }
        for entry in root.findall("atom:entry", ns):
            vid_el = entry.find("yt:videoId", ns)
            if vid_el is None or not vid_el.text:
                continue
            video_id = vid_el.text.strip()
            community = entry.find("media:group/media:community", ns)
            if community is None:
                continue
            stats = community.find("media:statistics", ns)
            if stats is not None:
                views = stats.get("views")
                if views:
                    try:
                        view_counts[video_id] = int(views)
                    except (ValueError, TypeError):
                        pass
    except ET.ParseError:
        logger.warning("Failed to parse XML for view counts")
    return view_counts


def _parse_feed(xml_text: str) -> list[dict]:
    """Parse an Atom feed and return a list of video dicts."""
    feed = feedparser.parse(xml_text)
    # Extract view counts from raw XML (feedparser doesn't handle media:community well)
    view_counts = _parse_view_counts(xml_text)
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

        # Parse published date (feedparser returns UTC time)
        published = entry.get("published_parsed") or entry.get("updated_parsed")
        if published:
            pub_dt = datetime(*published[:6], tzinfo=timezone.utc)
        else:
            pub_dt = datetime.now(timezone.utc)

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

        # View count from XML parsing
        view_count = view_counts.get(video_id)

        videos.append({
            "video_id": video_id,
            "channel_id": channel_id,
            "title": entry.get("title", "Untitled"),
            "thumbnail_url": thumbnail,
            "published_at": pub_dt,
            "description": entry.get("summary", None),
            "view_count": view_count,
        })

    return videos


async def refresh_channel_feed(channel_id: str, db: AsyncSession) -> int:
    """Fetch and store new videos for a single channel. Returns count of new videos."""
    urls = _build_rss_urls(channel_id)
    new_count = 0
    videos: list[dict] = []

    for url in urls:
        try:
            xml_text = await _fetch_feed(url)
            videos = _parse_feed(xml_text)
            if videos:
                break
        except Exception as e:
            logger.warning(f"Feed URL failed for {channel_id}: {url} — {e}")
            continue

    if not videos:
        logger.error(f"No videos found for {channel_id} (tried {len(urls)} URLs)")
        return 0

    try:
        for v in videos:
            # Fix channel_id if not parsed from feed
            if not v["channel_id"]:
                v["channel_id"] = channel_id

            existing = await db.execute(
                select(Video).where(Video.video_id == v["video_id"])
            )
            existing_video = existing.scalar_one_or_none()
            if existing_video:
                # Update view count on existing videos
                if v.get("view_count") and v["view_count"] != existing_video.view_count:
                    existing_video.view_count = v["view_count"]
                continue

            video = Video(
                video_id=v["video_id"],
                channel_id=v["channel_id"],
                title=v["title"],
                thumbnail_url=v["thumbnail_url"],
                published_at=v["published_at"],
                description=v["description"],
                view_count=v.get("view_count"),
            )
            db.add(video)
            new_count += 1

        await db.commit()
        logger.info(f"Channel {channel_id}: {new_count} new videos")

    except Exception as e:
        logger.error(f"Failed to store videos for {channel_id}: {e}")
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
