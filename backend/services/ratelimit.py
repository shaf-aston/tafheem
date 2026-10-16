"""Asks a minute per visitor, in memory: a restart forgets them, which is fine for a limit that only stops hammering."""
from __future__ import annotations

import time
from collections import deque

from fastapi import Request

from backend.config import get_settings


def visitor(request: Request) -> str:
    """Behind Vercel and Caddy the visitor is the first forwarded address. A visitor can fake that
    header, so this slows casual abuse, not a determined one."""
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "")


class PerMinute:
    """One route's recent asks per visitor; `setting` names the config field holding its limit."""

    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.asks: dict[str, deque[float]] = {}

    def too_many(self, who: str, cost: int = 1) -> bool:
        now = time.monotonic()
        if len(self.asks) > 10_000:  # never grows without end
            self.asks.clear()
        recent = self.asks.setdefault(who, deque())
        while recent and now - recent[0] > 60:
            recent.popleft()
        if len(recent) + cost > getattr(get_settings(), self.setting):
            return True
        recent.extend([now] * cost)
        return False
