"""Asks a minute per visitor, in memory: a restart forgets them, which is fine for a limit that only stops hammering."""
from __future__ import annotations

import ipaddress
import time
from collections import deque

from fastapi import HTTPException, Request

from backend.config import get_settings
from backend.services.core import audit


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


class Limit:
    """A route dependency: a share a minute per visitor, and a ceiling for everyone together. Until the origin
    gate (docs/plans/2026-11-11-security.md, Phase 2) a visitor's address can be forged; the ceiling keys on
    nothing a request sends. `settings` names the two config fields; `busy` the two answers."""

    def __init__(self, each: str, everyone: str, mine: str, busy: str) -> None:
        self.each, self.everyone = PerMinute(each), PerMinute(everyone)
        self.mine, self.busy = mine, busy

    def __call__(self, request: Request) -> None:
        if self.each.too_many(visitor(request)):
            raise HTTPException(429, self.mine)
        if self.everyone.too_many("everyone"):
            raise HTTPException(429, self.busy)


# The parser, for routes that read a whole sentence with it: the Analyse page asks /analyze, then
# /dictionary/sentence and /practice for the same sentence, so those two share a count of their own.
ANALYZE = Limit("analyze_per_minute", "analyze_all_per_minute",
                "Too many analyses at once; try again in a minute", "Analysis is busy right now; try again in a minute")
READ = Limit("sentence_per_minute", "sentence_all_per_minute",
             "Too many sentences at once; try again in a minute", "Sentences are busy right now; try again in a minute")


class OverBudget(HTTPException):
    """A model call this visitor, or everyone together, may not make this minute. An HTTPException, so
    unless something catches it the answer is a 429 (and a line in the security log). Code that turns a
    failed model call into a gentler answer re-raises this one: being refused is not the model failing."""

    def __init__(self, detail: str) -> None:
        super().__init__(429, detail)


class Budget:
    """What the model's quota (Groq) may be spent on: a fair share per visitor, and a ceiling for
    everyone together. Charged in services/ai._ask, once per call that would reach the model, so a
    kept answer, a refused input and a page that asks twice for what is already on file cost nothing,
    and a route added later cannot forget it. The ceiling keys on nothing a request sends, so no forged
    address gets past it (docs/plans/2026-11-11-security.md, Phase 2)."""

    def __init__(self, each: str, everyone: str) -> None:
        self.each, self.everyone = PerMinute(each), PerMinute(everyone)

    def spend(self) -> None:
        """Charge one model call to this request's visitor. Outside a request (startup, a script under
        backend/scripts) there is no visitor and nothing is charged: the server spending its own key on
        its own work is not abuse."""
        if not audit.request_id.get():
            return
        if self.each.too_many(audit.client_ip.get()):
            raise OverBudget("Too many explanations at once; try again in a minute")
        if self.everyone.too_many("everyone"):
            raise OverBudget("Explanations are busy right now; try again in a minute")


# One budget for every model call, so a visitor cannot spread the same spend across routes.
AI = Budget("ai_per_minute", "ai_all_per_minute")
