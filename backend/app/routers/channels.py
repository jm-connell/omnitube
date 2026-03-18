"""Channel / subscription management endpoints."""

import xml.etree.ElementTree as ET
from urllib.parse import parse_qs, urlparse

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Channel, Video
from app.schemas import ChannelCreate, ChannelImport, ChannelOut, OPMLImport
from app.services.feed import refresh_channel_feed
from app.services.resolve import resolve_channel_id

router = APIRouter(prefix="/api/channels", tags=["channels"])


@router.get("/", response_model=list[ChannelOut])
async def list_channels(db: AsyncSession = Depends(get_db)):
    """Return all subscribed channels."""
    result = await db.execute(select(Channel).order_by(Channel.name))
    return result.scalars().all()


@router.post("/", response_model=ChannelOut)
async def add_channel(data: ChannelCreate, db: AsyncSession = Depends(get_db)):
    """Subscribe to a single channel.

    Accepts UC... channel IDs, @handles, or full YouTube URLs.
    The backend resolves them to the canonical UC... channel ID.
    """
    try:
        channel_id, resolved_name = await resolve_channel_id(data.channel_id)
    except (ValueError, Exception) as e:
        raise HTTPException(400, f"Could not resolve channel: {e}")

    existing = await db.execute(
        select(Channel).where(Channel.channel_id == channel_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(400, "Channel already subscribed")

    channel = Channel(
        channel_id=channel_id,
        name=data.name or resolved_name or channel_id,
    )
    db.add(channel)
    await db.commit()
    await db.refresh(channel)

    # Kick off initial feed fetch for this channel (non-blocking is fine for MVP)
    try:
        await refresh_channel_feed(channel.channel_id, db)
    except Exception:
        pass  # Feed fetch failure shouldn't block subscription

    return channel


@router.delete("/{channel_id}")
async def remove_channel(channel_id: str, db: AsyncSession = Depends(get_db)):
    """Unsubscribe from a channel and remove its videos."""
    result = await db.execute(
        select(Channel).where(Channel.channel_id == channel_id)
    )
    channel = result.scalar_one_or_none()
    if not channel:
        raise HTTPException(404, "Channel not found")

    # Remove videos from this channel
    await db.execute(delete(Video).where(Video.channel_id == channel_id))
    await db.delete(channel)
    await db.commit()
    return {"ok": True}


@router.post("/import", response_model=list[ChannelOut])
async def import_channels(data: ChannelImport, db: AsyncSession = Depends(get_db)):
    """Bulk-import channels from a list.

    Each entry can be a UC... ID, @handle, or full YouTube URL.
    """
    added = []
    for ch in data.channels:
        try:
            channel_id, resolved_name = await resolve_channel_id(ch.channel_id)
        except (ValueError, Exception):
            continue  # Skip unresolvable entries during bulk import

        existing = await db.execute(
            select(Channel).where(Channel.channel_id == channel_id)
        )
        if existing.scalar_one_or_none():
            continue
        channel = Channel(
            channel_id=channel_id,
            name=ch.name or resolved_name or channel_id,
        )
        db.add(channel)
        added.append(channel)

    await db.commit()
    for ch in added:
        await db.refresh(ch)
    return added


@router.post("/import-opml", response_model=list[ChannelOut])
async def import_opml(data: OPMLImport, db: AsyncSession = Depends(get_db)):
    """Import subscriptions from YouTube's OPML/XML export.

    YouTube Takeout provides an OPML file with channel subscription URLs.
    Each <outline> has xmlUrl like:
      https://www.youtube.com/feeds/videos.xml?channel_id=UC...
    """
    try:
        root = ET.fromstring(data.opml_xml)
    except ET.ParseError:
        raise HTTPException(400, "Invalid XML")

    channels_to_add: list[dict] = []
    for outline in root.iter("outline"):
        xml_url = outline.get("xmlUrl", "")
        title = outline.get("title", outline.get("text", ""))
        if "channel_id=" in xml_url:
            parsed = parse_qs(urlparse(xml_url).query)
            cid = parsed.get("channel_id", [None])[0]
            if cid:
                channels_to_add.append({"channel_id": cid, "name": title or cid})

    if not channels_to_add:
        raise HTTPException(400, "No channels found in OPML")

    added = []
    for ch in channels_to_add:
        existing = await db.execute(
            select(Channel).where(Channel.channel_id == ch["channel_id"])
        )
        if existing.scalar_one_or_none():
            continue
        channel = Channel(channel_id=ch["channel_id"], name=ch["name"])
        db.add(channel)
        added.append(channel)

    await db.commit()
    for ch in added:
        await db.refresh(ch)
    return added


@router.get("/count")
async def channel_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(func.count()).select_from(Channel))
    return {"count": result.scalar()}
