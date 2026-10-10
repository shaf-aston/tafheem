"""The content rules in data/colloquial/colloquial.json, read once and checked."""
from __future__ import annotations

import json
from functools import lru_cache

from backend.config import data_path

FILE = "colloquial.json"


def read(path) -> dict:
    """The rules in a JSON file; a comment key is dropped, any other value must be a whole number above 0."""
    rules = {k: v for k, v in json.loads(path.read_text(encoding="utf-8")).items() if not k.startswith("_")}
    for name, value in rules.items():
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError(f"{path.name}: {name!r} must be a whole number above 0, not {value!r}")
    return rules


@lru_cache(maxsize=None)
def knob(name: str) -> int:
    return read(data_path("colloquial_dir") / FILE)[name]
