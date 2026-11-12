"""Asks a minute per visitor, in memory: a restart forgets them, which is fine for a limit that only stops hammering."""
from __future__ import annotations

import ipaddress
import threading
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
        self.lock = threading.Lock()  # sync routes run in a thread pool

    def too_many(self, who: str, cost: int = 1) -> bool:
        with self.lock:
            return self._too_many(who, cost)

    def _too_many(self, who: str, cost: int) -> bool:
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


class Names:
    """How many different names one visitor, and everyone together, asked about this minute: a page carries
    one name, a script probing which names exist or can be claimed (services/learner/identity.refused) carries
    many. The ceiling keys on nothing a request sends, so a forged address does not get past it. Sync routes
    run in a thread pool, hence the lock."""

    def __init__(self, each: str, everyone: str) -> None:
        self.each, self.everyone = each, everyone
        self.asked: dict[str, dict[str, float]] = {}
        self.all: dict[str, float] = {}  # everyone together, apart from the visitors so no flood evicts it
        self.lock = threading.Lock()

    def _fits(self, names: dict[str, float], name: str, setting: str, now: float) -> bool:
        for old in [n for n, at in names.items() if now - at > 60]:
            del names[old]
        return name in names or len(names) < getattr(get_settings(), setting)

    def too_many(self, who: str, name: str) -> bool:
        now = time.monotonic()
        with self.lock:
            while len(self.asked) > 10_000:  # never grows without end; the oldest visitor goes, not everyone
                self.asked.pop(next(iter(self.asked)))
            mine = self.asked.pop(who, {})
            self.asked[who] = mine  # most recent last, so the oldest is evicted first
            if not (self._fits(mine, name, self.each, now) and self._fits(self.all, name, self.everyone, now)):
                return True
            mine[name] = self.all[name] = now
            return False


# Names sent without a device token. Only a page from before tokens, or one not yet claimed, sends them;
# a cookie-holding page is never counted.
NAMELESS = Names("names_per_minute", "names_all_per_minute")


class Limit:
    """A route dependency: a share a minute per visitor, and a ceiling for everyone together. Until the origin
    gate (docs/plans/2026-11-11-security.md, Phase 2) a visitor's address can be forged; the ceiling keys on
    nothing a request sends. `settings` names the two config fields; `busy` the two answers."""

    def __init__(self, each: str, everyone: str, mine: str, busy: str) -> None:
        self.each, self.everyone = PerMinute(each), PerMinute(everyone)
        self.mine, self.busy = mine, busy

    def __call__(self, request: Request) -> None:
        self.check(visitor(request))

    def check(self, who: str) -> None:
        """The limit for `who` when a route counts by something other than the address (an account)."""
        if self.each.too_many(who):
            raise HTTPException(429, self.mine)
        if self.everyone.too_many("everyone"):
            raise HTTPException(429, self.busy)


# The parser, for routes that read a whole sentence with it: the Analyse page asks /analyze, then
# /dictionary/sentence and /practice for the same sentence, so those two share a count of their own.
ANALYZE = Limit("analyze_per_minute", "analyze_all_per_minute",
                "Too many analyses at once; try again in a minute", "Analysis is busy right now; try again in a minute")
READ = Limit("sentence_per_minute", "sentence_all_per_minute",
             "Too many sentences at once; try again in a minute", "Sentences are busy right now; try again in a minute")

# A recitation sends each reading to /listen and then /listen/check; the page paces itself under the hosted
# ear's allowance (recite.json asks-share), so these are far above a real reciter and only stop a loop.
RECORDING = Limit("recording_per_minute", "recording_all_per_minute",
                  "Too many recordings at once; try again in a minute", "Listening is busy right now; try again in a minute")
# Answers: far above a learner drilling fast; it slows a script filing the whole word list as learnt.
ANSWER = Limit("answer_per_minute", "answer_all_per_minute",
               "Too many answers at once; wait a minute", "Saving answers is busy right now; try again in a minute")
# Answers from one address across its accounts: a classroom fits, one person's fifty accounts do not.
ANSWER_PLACE = PerMinute("answer_address_per_minute")
# Sign-up and log-in: a person does each once on a device.
ACCOUNT = Limit("account_per_minute", "account_all_per_minute",
                "Too many tries at once; wait a minute", "Accounts are busy right now; try again in a minute")


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
