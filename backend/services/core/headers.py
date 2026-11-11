"""Headers every /api answer carries, so a browser never treats one as a page.

An answer from this server is JSON, audio or a file: never something to render, run or frame.
`nosniff` stops a browser guessing that a JSON body holding "<script>" is HTML; the CSP makes
any answer opened directly a dead page (no scripts, no styles, no frames, not frameable);
no-referrer keeps a learner's address out of whatever a response links to.

Only /api: the docs page (/docs) loads its own scripts and is left as FastAPI serves it.
The website's own headers are set where it is served (vercel.json, deploy/Caddyfile);
see docs/plans/2026-11-11-security.md (Headers).
"""
from __future__ import annotations

API_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"content-security-policy", b"default-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'"),
    (b"referrer-policy", b"no-referrer"),
    (b"cross-origin-resource-policy", b"same-site"),
]
_NAMES = {name for name, _ in API_HEADERS}
# A request that names a learner gets an answer about that learner, unless the route already said it
# is the same for everyone (main.py's day-long cache). Never kept by Vercel's edge or a shared cache:
# Vercel honours an upstream Cache-Control on rewrites, so the absence of one is not a promise.
_IDENTITY = {b"x-tafheem-profile", b"x-tafheem-guest"}
PRIVATE = (b"cache-control", b"private, no-store")


def crash_headers(request_id: str) -> dict[str, str]:
    """For the crash answer, which Starlette sends from outside every middleware (main.py's log_crash)."""
    headers = {name.decode(): value.decode() for name, value in API_HEADERS}
    if request_id:
        headers["X-Request-ID"] = request_id
    return headers


class ApiHeaders:
    """Adds API_HEADERS to every /api answer that has not set its own."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http" or not scope["path"].startswith("/api/"):
            await self.app(scope, receive, send)
            return

        personal = any(name in _IDENTITY for name, _ in scope.get("headers", ()))

        async def send_with_headers(message) -> None:
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                names = {name.lower() for name, _ in headers}
                added = [pair for pair in API_HEADERS if pair[0] not in names]
                if personal and b"cache-control" not in names:
                    added.append(PRIVATE)
                message["headers"] = headers + added
            await send(message)

        await self.app(scope, receive, send_with_headers)
