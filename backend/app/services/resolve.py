"""Resolve YouTube channel handles, URLs, and vanity names to UC... channel IDs."""

import logging
import re

import httpx

logger = logging.getLogger("omnitube.resolve")

# Regex to find the canonical channel ID in YouTube page HTML
_CHANNEL_ID_RE = re.compile(r'"externalId"\s*:\s*"(UC[a-zA-Z0-9_-]{22})"')
_META_CHANNEL_RE = re.compile(
    r'<meta\s+itemprop="channelId"\s+content="(UC[a-zA-Z0-9_-]{22})"',
)
_LINK_CANONICAL_RE = re.compile(
    r'<link\s+rel="canonical"\s+href="https://www\.youtube\.com/channel/(UC[a-zA-Z0-9_-]{22})"',
)


async def resolve_channel_id(input_str: str) -> tuple[str, str | None]:
    """Resolve a user-provided string to (channel_id, display_name).

    Accepts:
      - UC... channel IDs (returned as-is)
      - https://youtube.com/@handle
      - https://youtube.com/channel/UC...
      - https://youtube.com/c/VanityName
      - @handle (with or without @)
      - bare vanity names

    Returns (channel_id, name) where name is scraped from the page title,
    or None if we couldn't determine it.
    """
    raw = input_str.strip()

    # Already a UC... channel ID
    if re.match(r"^UC[a-zA-Z0-9_-]{22}$", raw):
        return raw, None

    # Extract from /channel/ URL
    m = re.search(r"youtube\.com/channel/(UC[a-zA-Z0-9_-]{22})", raw)
    if m:
        return m.group(1), None

    # Build URL to scrape
    if raw.startswith("http"):
        url = raw
    elif raw.startswith("@"):
        url = f"https://www.youtube.com/{raw}"
    else:
        # Could be a vanity name or handle without @
        url = f"https://www.youtube.com/@{raw}"

    return await _scrape_channel_id(url)


async def _scrape_channel_id(url: str) -> tuple[str, str | None]:
    """Fetch a YouTube URL and extract the channel ID from the page source."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    async with httpx.AsyncClient(
        timeout=15.0, follow_redirects=True, headers=headers
    ) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        html = resp.text

    # Try multiple patterns
    for pattern in (_META_CHANNEL_RE, _LINK_CANONICAL_RE, _CHANNEL_ID_RE):
        m = pattern.search(html)
        if m:
            channel_id = m.group(1)
            name = _extract_title(html)
            logger.info(f"Resolved {url!r} -> {channel_id} ({name})")
            return channel_id, name

    raise ValueError(f"Could not resolve channel ID from: {url}")


def _extract_title(html: str) -> str | None:
    """Extract channel display name from page title."""
    m = re.search(r"<title>([^<]+)</title>", html)
    if m:
        title = m.group(1).strip()
        # YouTube titles often end with " - YouTube"
        if title.endswith(" - YouTube"):
            title = title[: -len(" - YouTube")].strip()
        return title or None
    return None
