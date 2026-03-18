import type { Handle } from "@sveltejs/kit";

const API_BACKEND = "http://127.0.0.1:8000";

/**
 * Server hook that proxies /api/* and /health requests to the FastAPI backend.
 *
 * This replaces Vite's server.proxy — works in both dev and production.
 * In production (Docker), change API_BACKEND via environment variable.
 */
export const handle: Handle = async ({ event, resolve }) => {
  const { pathname } = event.url;

  // Proxy API requests to FastAPI backend
  if (pathname.startsWith("/api") || pathname === "/health") {
    const backendUrl = `${API_BACKEND}${pathname}${event.url.search}`;

    try {
      // Build headers — forward content-type but strip host
      const headers = new Headers();
      const contentType = event.request.headers.get("content-type");
      if (contentType) headers.set("content-type", contentType);
      const accept = event.request.headers.get("accept");
      if (accept) headers.set("accept", accept);

      const body =
        event.request.method !== "GET" && event.request.method !== "HEAD"
          ? await event.request.text()
          : undefined;

      const res = await fetch(backendUrl, {
        method: event.request.method,
        headers,
        body,
      });

      // Forward the response back
      return new Response(res.body, {
        status: res.status,
        statusText: res.statusText,
        headers: res.headers,
      });
    } catch (err) {
      console.error(`[proxy] Failed to reach backend: ${err}`);
      return new Response(JSON.stringify({ error: "Backend unavailable" }), {
        status: 502,
        headers: { "Content-Type": "application/json" },
      });
    }
  }

  return resolve(event);
};
