"""Video feed endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Channel, Video
from app.schemas import FeedResponse, VideoOut

router = APIRouter(prefix="/api/feed", tags=["feed"])


@router.get("/", response_model=FeedResponse)
async def get_feed(
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
    channel_id: str | None = Query(None, description="Filter by channel"),
    db: AsyncSession = Depends(get_db),
):
    """Return chronological video feed (newest first).

    Supports pagination and optional channel filtering.
    """
    base_query = select(Video)
    count_query = select(func.count()).select_from(Video)

    if channel_id:
        base_query = base_query.where(Video.channel_id == channel_id)
        count_query = count_query.where(Video.channel_id == channel_id)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    offset = (page - 1) * per_page
    result = await db.execute(
        base_query.order_by(Video.published_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    videos = result.scalars().all()

    # Enrich with channel names
    video_list = []
    for v in videos:
        ch_result = await db.execute(
            select(Channel.name).where(Channel.channel_id == v.channel_id)
        )
        ch_name = ch_result.scalar_one_or_none()

        video_out = VideoOut.model_validate(v)
        video_out.channel_name = ch_name
        video_list.append(video_out)

    return FeedResponse(
        videos=video_list,
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/refresh")
async def trigger_refresh(db: AsyncSession = Depends(get_db)):
    """Manually trigger a feed refresh."""
    from app.services.feed import refresh_all_feeds

    count = await refresh_all_feeds(db)
    return {"ok": True, "new_videos": count}
