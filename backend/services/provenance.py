"""Where a fact came from.

Every answer this app gives is only as good as what produced it: a hand-checked
corpus, a fixed rule table, or a model having a guess. The reader is entitled to
know which, so each result carries its source and every panel shows it.

This module is the only reader of data/sources.json. Ask it by key, "corpus",
"rules", "ai", and it returns the wording the UI prints.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

SOURCES_FILE = Path(__file__).parent.parent / "data" / "sources.json"


@lru_cache(maxsize=1)
def _sources() -> dict:
    data = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    return {key: value for key, value in data.items() if not key.startswith("_")}


def of(key: str) -> dict:
    """One source as the API returns it. An unknown key is a bug, so it says so
    rather than quietly claiming the fact came from nowhere."""
    source = _sources().get(key)
    if source is None:
        raise KeyError(f"Unknown source '{key}'. Add it to {SOURCES_FILE.name}.")
    return {"key": key, "label": source["label"], "confidence": source["confidence"], "detail": source["detail"]}


def category_of(key: str) -> str:
    """The shelf that source sits on, or empty where it is not on one.

    Empty is not a defect: a source nothing groups by is simply never offered
    as a shelf to choose from.
    """
    return _sources().get(key, {}).get("category", "")


def for_edition(edition: dict) -> dict:
    """The badge for one book of the Qur'an's library.

    A library holds many books under one entry here: `qul` says how far that
    library is trusted and what its terms are, and each book then names itself
    on its own badge. Writing an entry per book by hand instead would mean
    keeping this file in step with the manifest forever, which is the one thing
    a second copy of a list never stays in.

    `credit` comes from the manifest, so an unknown key still fails loudly in
    `of()` rather than quietly crediting nobody.
    """
    return {**of(edition["credit"]), "label": edition["name"], "confidence": edition["confidence"]}


def url_for(key: str) -> str:
    """The download a build script needs, kept beside the attribution it belongs to."""
    return _sources()[key].get("url", "")


def all_sources() -> list[dict]:
    """Every source, for the reference list the app shows in Settings.

    A badge answers "where did this one line come from". This answers the wider
    question a reader is entitled to ask once and not have to ask again: what is
    this app built on, where does each piece live, and what may I not trust.

    Carries two fields `of()` leaves out because a badge has no room for them:
    `where`, one plain sentence about where the thing physically lives, and
    `used_in`, the tabs that read it. Order follows the file, so the reading
    order is decided where the wording is, not here.
    """
    return [
        {
            **of(key),
            "url": source.get("url", ""),
            "where": source.get("where", ""),
            "used_in": source.get("used_in", []),
        }
        for key, source in _sources().items()
    ]

