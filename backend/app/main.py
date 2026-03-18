"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import app_state, channels, feed, stream
from app.services.scheduler import start_scheduler, stop_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("omnitube")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Ensure data directory exists
    Path(settings.data_dir).mkdir(parents=True, exist_ok=True)

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Start background RSS scheduler
    start_scheduler()
    logger.info("OmniTube backend ready")

    yield

    # Shutdown
    stop_scheduler()
    logger.info("OmniTube backend stopped")


app = FastAPI(
    title="OmniTube",
    description="Minimalist YouTube frontend API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(channels.router)
app.include_router(feed.router)
app.include_router(stream.router)
app.include_router(app_state.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "omnitube"}
