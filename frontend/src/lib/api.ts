/**
 * API client for OmniTube backend.
 *
 * In dev, Vite proxies /api → http://localhost:8000.
 * In production, the Docker Compose nginx serves both.
 */

const BASE = "";

export interface Channel {
  id: number;
  channel_id: string;
  name: string;
  thumbnail_url: string | null;
  created_at: string;
}

export interface Video {
  id: number;
  video_id: string;
  channel_id: string;
  title: string;
  thumbnail_url: string | null;
  published_at: string;
  description: string | null;
  duration_seconds: number | null;
  view_count: number | null;
  like_count: number | null;
  watched: boolean;
  watch_progress: number;
  channel_name: string | null;
}

export interface FeedResponse {
  videos: Video[];
  total: number;
  page: number;
  per_page: number;
}

export interface SubtitleTrack {
  lang: string;
  label: string;
}

export interface StreamInfo {
  video_url: string;
  audio_url: string | null;
  title: string;
  duration: number | null;
  description: string | null;
  view_count: number | null;
  like_count: number | null;
  channel: string | null;
  channel_id: string | null;
  chapters: Array<{
    title: string;
    start_time: number;
    end_time: number;
  }> | null;
  subtitles: SubtitleTrack[] | null;
  width: number | null;
  height: number | null;
  available_qualities: number[] | null;
}

export interface SetupStatus {
  setup_complete: boolean;
  channel_count: number;
  video_count: number;
}

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json", ...init?.headers },
    ...init,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

// ── App State ────────────────────────────────────────────────────

export function getStatus(): Promise<SetupStatus> {
  return fetchJSON("/api/status");
}

export function completeSetup(): Promise<{ ok: boolean }> {
  return fetchJSON("/api/setup-complete", { method: "POST" });
}

// ── Channels ─────────────────────────────────────────────────────

export function getChannels(): Promise<Channel[]> {
  return fetchJSON("/api/channels/");
}

export function addChannel(
  channel_id: string,
  name?: string,
): Promise<Channel> {
  return fetchJSON("/api/channels/", {
    method: "POST",
    body: JSON.stringify({ channel_id, name }),
  });
}

export function removeChannel(channel_id: string): Promise<{ ok: boolean }> {
  return fetchJSON(`/api/channels/${channel_id}`, { method: "DELETE" });
}

export function renameChannel(
  channel_id: string,
  name: string,
): Promise<Channel> {
  return fetchJSON(`/api/channels/${channel_id}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export function importChannels(
  channels: Array<{ channel_id: string; name?: string }>,
): Promise<Channel[]> {
  return fetchJSON("/api/channels/import", {
    method: "POST",
    body: JSON.stringify({ channels }),
  });
}

export function importOPML(opml_xml: string): Promise<Channel[]> {
  return fetchJSON("/api/channels/import-opml", {
    method: "POST",
    body: JSON.stringify({ opml_xml }),
  });
}

// ── Feed ─────────────────────────────────────────────────────────

export function getFeed(
  page = 1,
  per_page = 30,
  channel_id?: string,
): Promise<FeedResponse> {
  const params = new URLSearchParams({
    page: String(page),
    per_page: String(per_page),
  });
  if (channel_id) params.set("channel_id", channel_id);
  return fetchJSON(`/api/feed/?${params}`);
}

export function refreshFeed(): Promise<{ ok: boolean; new_videos: number }> {
  return fetchJSON("/api/feed/refresh");
}

// ── Stream ───────────────────────────────────────────────────────

export function getStreamInfo(
  video_id: string,
  quality?: number,
): Promise<StreamInfo> {
  const params = quality ? `?quality=${quality}` : "";
  return fetchJSON(`/api/stream/${video_id}${params}`);
}

export function getStreamRedirectURL(video_id: string): string {
  return `${BASE}/api/stream/${video_id}/redirect`;
}

// ── Comments ─────────────────────────────────────────────────────

export interface CommentData {
  author: string;
  text: string;
  likes: number;
  time_text: string | null;
  is_pinned: boolean;
}

export interface CommentsResponse {
  comments: CommentData[];
  count: number | null;
}

export function getComments(
  video_id: string,
  limit = 30,
): Promise<CommentsResponse> {
  return fetchJSON(`/api/stream/${video_id}/comments?limit=${limit}`);
}
