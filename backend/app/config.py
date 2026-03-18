from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application configuration.

    All values can be overridden via environment variables prefixed with OMNITUBE_.
    """

    database_url: str = "sqlite+aiosqlite:///./data/omnitube.db"
    data_dir: Path = Path("./data")

    # RSS polling interval in minutes
    rss_poll_interval: int = 15

    # yt-dlp settings
    ytdlp_format: str = "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"
    ytdlp_proxy: str | None = None

    # CORS origins (frontend URL)
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    # Whether first-time setup has been completed
    setup_complete: bool = False

    model_config = {"env_prefix": "OMNITUBE_"}


settings = Settings()
