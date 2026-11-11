"""Asks a minute per visitor, in memory: a restart forgets them, which is fine for a limit that only stops hammering."""
from __future__ import annotations

import ipaddress
import time
from collections import deque

from fastapi import HTTPException, Request

from backend.config import get_settings


# Where the visitor's address is, most trusted first. Vercel's edge overwrites x-real-ip and
# x-vercel-forwarded-for with the address it saw (a visitor's own value never survives), and Caddy passes
# them on untouched. X-Forwarded-For is last: Caddy rewrites it to its own peer, which behind Vercel is
# Vercel's edge, so every learner would share one count. It is still the address on a direct call or a dev server.
# Until the origin gate (docs/plans/2026-11-11-security.md, Phase 2) a caller that skips Vercel can send
# x-real-ip itself and pick its own count; Budget's ceiling for everyone is what holds then.
_ADDRESS_HEADERS = ("x-real-ip", "x-vercel-forwarded-for", "x-forwarded-for")


def visitor(request: Request) -> str:
    """The visitor's address, as one count: an IPv6 visitor by its /64, which one home or phone hops around in."""
    for name in _ADDRESS_HEADERS:
        if (address := _address(request.headers.get(name, ""))) is not None:
            return address
    return request.client.host if request.client else ""


def _address(value: str) -> str | None:
    try:
        ip = ipaddress.ip_address(value.split(",")[0].strip())
    except ValueError:
        return None
    if ip.version == 6:
        if ip.ipv4_mapped:
            return str(ip.ipv4_mapped)
        return str(ipaddress.ip_network(f"{ip}/64", strict=False))
    return str(ip)


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


class Budget:
    """A route dependency for routes that spend a model's quota (Groq): a fair share per visitor, and a
    ceiling for everyone together. The ceiling keys on nothing a request sends, so no forged address
    gets past it; it protects the key (and the hosted ear, which may share it) when the per-visitor
    count cannot be trusted (docs/plans/2026-11-11-security.md, Phase 2). A 429 lands in the security log."""

    def __init__(self, each: str, everyone: str) -> None:
        self.each, self.everyone = PerMinute(each), PerMinute(everyone)

    def __call__(self, request: Request) -> None:
        if self.each.too_many(visitor(request)):
            raise HTTPException(429, "Too many explanations at once; try again in a minute")
        if self.everyone.too_many("everyone"):
            raise HTTPException(429, "Explanations are busy right now; try again in a minute")


# One budget for every model-backed route, so a visitor cannot spread the same spend across routes.
AI = Budget("ai_per_minute", "ai_all_per_minute")
