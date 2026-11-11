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
# The cookie is the device token (backend/identity.py): Vercel's edge may cache a request that carries one.
_IDENTITY = {b"x-tafheem-profile", b"x-tafheem-guest", b"cookie"}
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


# What a browser says about where a request came from (Fetch Metadata). "none" is the reader typing an address;
# same-site covers a dev page on another localhost port. vercel.app is a public suffix, so another *.vercel.app
# site, a preview deployment included, is cross-site.
_ALLOWED_SITES = {b"same-origin", b"same-site", b"none"}
_WRITES = {"POST", "PUT", "PATCH", "DELETE"}


class SameOrigin:
    """Refuses (403) a write to /api that a browser says another site's page sent.

    The device-token cookie is SameSite=Strict, so such a request already carries no token; this is the second
    lock OWASP recommends, and it also stops another site making a reader sign up or log in, or spending the AI
    budget from their browser. A request with no Sec-Fetch-Site (a script, an old browser) is not a browser
    page's cross-site request, and passes as before.
    """

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send) -> None:
        if (scope["type"] == "http" and scope["method"] in _WRITES and scope["path"].startswith("/api/")
                and (site := _header(scope, b"sec-fetch-site")) is not None and site not in _ALLOWED_SITES):
            await send({"type": "http.response.start", "status": 403,
                        "headers": [(b"content-type", b"application/json")]})
            await send({"type": "http.response.body", "body": b'{"detail":"Not from this site"}'})
            return
        await self.app(scope, receive, send)


def _header(scope: dict, name: bytes) -> bytes | None:
    return next((value.lower() for key, value in scope.get("headers", ()) if key == name), None)
