"""Repair: إِنْ تَضْرِبْ أَضْرِبْ. A command answers a condition only with فَ written on it, so an
untied verb the parser read as a command, after a جازم condition and its verb, is the present
in jazm: its أ is the speaker's, not a command's hamza."""
from __future__ import annotations

from backend.services.nahw.book import condition_of
from backend.services.nahw.syntax.facts import is_prefix, is_verb


def untied_command(tokens: list[dict]) -> None:
    words = [t for t in tokens if not t["form"].endswith("+") and not t["form"].startswith("+")]
    for i, opener in enumerate(words[:-2]):
        frame = condition_of(opener["form"])
        if not frame or not frame.get("case") or not is_verb(words[i + 1]):
            continue
        answer = words[i + 2]
        tied = any(is_prefix(t) and t["id"] == answer["id"] - 1 for t in tokens)
        if is_verb(answer) and answer.get("asp") == "c" and not tied:
            answer["asp"] = "i"
