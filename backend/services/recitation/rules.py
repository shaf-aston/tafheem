"""What a listening request may ask for. Pure: no files, no network, no HTTP.

The router maps a `Refused` to a 422 and nothing more, so every rule here is
tested by calling it, and a second caller gets the same rules for free.
"""
from __future__ import annotations

import re

from backend.config import get_settings

AYAH_KEY = re.compile("[0-9]{1,3}:[0-9]{1,3}")


class Refused(ValueError):
    """A request the reader can fix. The message is written for the reader."""


def words_within_cap(name: str, words: str) -> None:
    """`before` and `heard` are each one reading's words, so they share one cap."""
    cap = get_settings().recitation_check_heard_max_chars
    if len(words) > cap:
        raise Refused(f"{name} must be at most {cap} characters.")


def checked_ayahs(check: str) -> list[str]:
    """The ayahs to score, from "1:1,1:2": few enough, all different, each a real key's shape."""
    keys = [key for key in check.split(",") if key]
    cap = get_settings().recitation_check_ayahs_max
    if len(keys) > cap or len(set(keys)) != len(keys) or not all(AYAH_KEY.fullmatch(key) for key in keys):
        raise Refused(f"check must be up to {cap} different ayahs, as 1:1,1:2.")
    return keys


def page_ends(near: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """The open page's first and last ayah, from "2:1-2:5" (shape already checked at the door)."""
    first, last = (tuple(map(int, key.split(":"))) for key in near.split("-"))
    return first, last
