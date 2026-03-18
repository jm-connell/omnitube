# OmniTube

A minimalist, self-hosted YouTube frontend PWA. No algorithm, no ads, no shorts, no Google sign-in.

## Architecture

- **Frontend**: SvelteKit + Tailwind CSS + shadcn-svelte (PWA)
- **Backend**: FastAPI + yt-dlp + feedparser + APScheduler
- **Database**: SQLite (via SQLAlchemy 2.0)
- **Deployment**: Docker Compose on TrueNAS via Dockge

## Quick Start

```bash
docker compose up -d
```

Access at `http://<your-tailnet-host>:3000`

## Development

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Features (MVP)

- Import YouTube subscriptions via OPML/JSON export
- Chronological feed from subscribed channels (no algorithm)
- Ad-free playback via yt-dlp stream proxy
- Shorts filtered out automatically (UULF RSS trick)
- PWA installable on mobile and desktop
- Dark/light theme with customizable accent colors
- Toggle thumbnails, comments, descriptions, view/like counts
- Minimal Hyprland-inspired UI with monospace font
