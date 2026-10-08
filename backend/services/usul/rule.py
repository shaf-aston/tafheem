"""Read usul.json: the twelve levels, where support lifts one, and the books behind them.

The only reader of usul.json. Pure but for that one read, cached.
"""
from __future__ import annotations

import json
from functools import lru_cache

from backend.config import data_path


@lru_cache(maxsize=1)
def rule() -> dict:
    return json.loads((data_path("usul_dir") / "usul.json").read_text(encoding="utf-8"))
