"""The security log: one JSON line for every event that says who did what to an account, or what was refused.

backend.log answers "what did the server do"; this answers "who tried what, and was it allowed",
fast, with grep or jq (deploy/security-report.sh). Built like the recitation journal
(services/learner/journal.py): its own logger, propagate=False, secrets scrubbed. Two differences, both
because two server processes (tafheem@8000, @8001) write it at once: the file is opened for append and
never rotated from Python (deploy/logrotate.conf does it, once, for both; a RotatingFileHandler in each
process would rename the file under the other), and every line also goes to stderr, so journald keeps a
copy the app's own user cannot rewrite.

Every line: {"at", "kind", "request_id", "ip", "method", "route", "status"} plus what that kind knows.
`route` is the matched route's template (/api/progress/circles/{circle}), never the raw path or the
query string, so text someone typed never lands here. Bodies and headers are never written.
Usernames appear only on account events (sign-up, log-in, deletion, ranking), where they are the
point. See docs/plans/2026-11-11-security.md (Logging).

`SecurityLog` is the ASGI middleware that gives each request an id (X-Request-ID, echoed back so a
learner's report can quote it) and writes a line for each refused or failed answer. Pure ASGI rather
than @app.middleware: that wraps every request in a second task and queue, this adds a dict lookup.
"""
from __future__ import annotations

import contextvars
import json
import logging
import logging.handlers
import re
import sys
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.config import get_settings
from backend.services.learner.journal import scrub

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent

_log = logging.getLogger("security")
_log.propagate = False
_built_from: str | None = None
_configure_lock = threading.Lock()

# Set once per request by SecurityLog, read by `event` wherever in the request it is called.
request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
client_ip: contextvars.ContextVar[str] = contextvars.ContextVar("client_ip", default="")

# An id a caller may hand us (a proxy's, or the page's own) must look like one: no spaces, no
# newlines, short. Anything else is replaced, never trusted into the log.
_INBOUND_ID = re.compile(r"[A-Za-z0-9._-]{8,64}")
_FIELD_MAX = 200
_CONTROL = re.compile(r"[\x00-\x1f\x7f-\x9f]")

# The answers worth a line on their own. 404 is not here: a mistyped surah is not an attack, and
# routes where a 404 means something (an unknown account) write their own event.
# 405 is a probe for a method a route does not take (scanners walk PUT/DELETE across every path).
WATCHED = frozenset({401, 403, 405, 413, 415, 422, 429})


def _ensure_configured() -> None:
    global _built_from
    key = get_settings().security_log_path
    if key == _built_from:
        return
    with _configure_lock:
        if key == _built_from:
            return
        for old in list(_log.handlers):
            _log.removeHandler(old)
            old.close()
        path = (_PROJECT_ROOT / key).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        to_file = logging.handlers.WatchedFileHandler(path, encoding="utf-8")  # reopens after logrotate moves it
        to_file.setFormatter(logging.Formatter("%(message)s"))
        to_journal = logging.StreamHandler(sys.stderr)
        to_journal.setFormatter(logging.Formatter("security %(message)s"))
        _log.addHandler(to_file)
        _log.addHandler(to_journal)
        _log.setLevel(logging.INFO)
        _built_from = key


def _clean(value: Any) -> Any:
    """Numbers and booleans as they are; anything else a short string with no secret in it.
    JSON encoding escapes CR and LF, so a value cannot forge a second line."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    # Control characters (C0, DEL, C1) would reach the reader's terminal raw: JSON leaves C1 as is.
    return _CONTROL.sub("?", scrub(str(value)))[:_FIELD_MAX]


def event(kind: str, **fields: Any) -> None:
    """Write one line. Never raises: a full disk must not turn a log-in into a 500."""
    try:
        _ensure_configured()
        line = {
            "at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "kind": kind,
            "request_id": request_id.get(),
            "ip": _clean(client_ip.get()),  # from a header: forgeable, so cleaned like any other field
            **{name: _clean(value) for name, value in fields.items()},
        }
        _log.info(json.dumps(line, ensure_ascii=False))
    except Exception:  # noqa: BLE001 - logging must never break the answer
        logging.getLogger(__name__).exception("security log write failed")


# What kind of device a user-agent says it is: the family alone, never the string (it is a fingerprint, and
# forgeable anyway). Enough to settle "that claim was not my phone" (scripts/recovery_code.py). First match wins.
_DEVICE_KINDS = (("iphone", "iPhone"), ("ipad", "iPad"), ("android", "Android"), ("windows", "Windows"),
                 ("cros", "ChromeOS"), ("mac os", "Mac"), ("linux", "Linux"))


def device_kind(user_agent: str | None) -> str:
    """"Android", "iPhone", ... or "other" (curl, a bot, no header)."""
    agent = (user_agent or "").lower()
    return next((kind for marker, kind in _DEVICE_KINDS if marker in agent), "other")


def _header(scope: dict, name: bytes) -> str:
    for key, value in scope.get("headers", ()):
        if key == name:
            return value.decode("latin-1")
    return ""


def route_of(scope: dict) -> str:
    """The matched route's template, or "unmatched": never the raw path, which can carry typed text."""
    route = scope.get("route")
    return getattr(route, "path", None) or "unmatched"


class SecurityLog:
    """Request id in, X-Request-ID out, and a line for every refused or failed answer."""

    def __init__(self, app, client=None) -> None:
        self.app = app
        # Who the visitor is (services/core/ratelimit.visitor's rule), given the scope; injected so
        # this file does not decide which proxy headers to trust.
        self.client = client or (lambda scope: (scope.get("client") or ("",))[0])

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        sent = _header(scope, b"x-request-id")
        rid = sent if _INBOUND_ID.fullmatch(sent) else uuid.uuid4().hex
        # Also on the scope, for the crash handler (main.py's log_crash): it answers from outside every
        # middleware (Starlette's ServerErrorMiddleware), after this one has reset its context.
        scope.setdefault("state", {})["request_id"] = rid
        id_token = request_id.set(rid)
        ip_token = client_ip.set(self.client(scope))
        status = 0

        async def send_with_id(message) -> None:
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
                headers = list(message.get("headers", []))
                if not any(name.lower() == b"x-request-id" for name, _ in headers):
                    headers.append((b"x-request-id", rid.encode()))
                message["headers"] = headers
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception:
            # Started means the client already has its status (an audio stream cut short): say so.
            event("error", method=scope.get("method"), route=route_of(scope), status=500, **({"started": status} if status else {}))
            raise
        else:
            if status in WATCHED or status >= 500:
                event("refused" if status < 500 else "error", method=scope.get("method"), route=route_of(scope), status=status)
        finally:
            request_id.reset(id_token)
            client_ip.reset(ip_token)


class NoQuery(logging.Filter):
    """Drops the query from every address a library logs (httpx's "HTTP Request: GET https://...?q=..."):
    the Qur'an search sends what a learner typed as ?q=, and uvicorn's own access log is already off for
    the same reason (deploy/tafheem@.service). Host, path and status stay, which deploy/usage.py counts."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, tuple):
            record.args = tuple(_no_query(arg) for arg in record.args)
        return True


def _no_query(arg: Any) -> Any:
    text = str(arg) if type(arg).__name__ == "URL" or isinstance(arg, str) else None
    if text and text.startswith(("http://", "https://")) and "?" in text:
        return text.split("?", 1)[0] + "?…"
    return arg

