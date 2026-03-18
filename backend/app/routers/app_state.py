"""App-level status and settings endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import AppState, Channel, Video
from app.schemas import SetupStatus

router = APIRouter(prefix="/api", tags=["app"])


@router.get("/status", response_model=SetupStatus)
async def get_status(db: AsyncSession = Depends(get_db)):
    """Check if initial setup is complete."""
    state = await db.execute(
        select(AppState).where(AppState.key == "setup_complete")
    )
    setup_row = state.scalar_one_or_none()
    setup_complete = setup_row.value == "true" if setup_row else False

    ch_count = await db.execute(select(func.count()).select_from(Channel))
    vid_count = await db.execute(select(func.count()).select_from(Video))

    return SetupStatus(
        setup_complete=setup_complete,
        channel_count=ch_count.scalar(),
        video_count=vid_count.scalar(),
    )


@router.post("/setup-complete")
async def mark_setup_complete(db: AsyncSession = Depends(get_db)):
    """Mark initial setup as done."""
    state = await db.execute(
        select(AppState).where(AppState.key == "setup_complete")
    )
    row = state.scalar_one_or_none()
    if row:
        row.value = "true"
    else:
        db.add(AppState(key="setup_complete", value="true"))
    await db.commit()
    return {"ok": True}
