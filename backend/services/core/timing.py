"""One log line per timed call. "Still fast?" answered by grep on backend.log, not re-measured.

    timed("heard", hosted.transcribe, audio, key, lang, ear="groq", bytes=len(audio))
    -> heard  ear=groq  bytes=61094  out=9  247ms

`out` is len(result) when it has one. Exceptions pass through untimed; the caller logs those.
"""
from __future__ import annotations

import logging
import time

log = logging.getLogger("timing")


def timed(what: str, fn, *args, **fields):
    started = time.perf_counter()
    result = fn(*args)
    ms = (time.perf_counter() - started) * 1000
    if hasattr(result, "__len__"):
        fields["out"] = len(result)
    log.info("%s  %s  %.0fms", what, "  ".join(f"{k}={v}" for k, v in fields.items()), ms)
    return result
