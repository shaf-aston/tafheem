"""Dawah: common questions put to Islam, with a short reply, a full answer and evidence.

The only reader of data/dawah. References share the timelines' shape and its
collections (timelines.collections), so one hadith collection is declared once
and the tab draws references with the same row.

Checked when loaded, not trusted: a missing reply, a repeated id, a point with
no evidence or a Qur'an reference past the end of its surah stops the app and
names the question.
"""
from __future__ import annotations

import json
from functools import lru_cache

from backend.config import data_path
from backend.services import provenance, quran_meanings, timelines

TOPIC_FIELDS = ("id", "title", "arabic", "blurb")
QUESTION_FIELDS = ("id", "q", "short")
POINT_FIELDS = ("title", "text")


def faults(data: dict, collections: dict, ayahs: dict[int, int]) -> list[str]:
    """Everything wrong with the file; empty when it is sound."""
    said = []
    topics = data.get("topics") or []
    if not topics:
        said.append("no topics")
    if "{number}" not in str((data.get("islamqa") or {}).get("cite", "")):
        said.append("islamqa.cite has no {number} to fill")
    seen_topics, seen_questions = set(), set()
    for topic in topics:
        name = f"topic {topic.get('id')!r}"
        said += [f"{name} has no {f}" for f in TOPIC_FIELDS if not str(topic.get(f) or "").strip()]
        if topic.get("id") in seen_topics:
            said.append(f"{name} is given twice")
        seen_topics.add(topic.get("id"))
        if not topic.get("questions"):
            said.append(f"{name} has no questions")
        for question in topic.get("questions") or []:
            here = f"{name} question {question.get('id')!r}"
            said += [f"{here} has no {f}" for f in QUESTION_FIELDS if not str(question.get(f) or "").strip()]
            # Ids are unique across topics: the address names a question alone.
            if question.get("id") in seen_questions:
                said.append(f"{here} uses an id already used")
            seen_questions.add(question.get("id"))
            points = question.get("points") or []
            if not points or not all(str(p.get(f) or "").strip() for p in points for f in POINT_FIELDS):
                said.append(f"{here} has no reasoning, or a point missing its title or text")
            fatwa = question.get("islamqa")
            if fatwa is not None and not (isinstance(fatwa.get("number"), int) and str(fatwa.get("title") or "").strip()):
                said.append(f"{here}: islamqa needs a whole number and a title, or null")
            # Evidence sits under the point it proves, so every point names its own.
            for point in points:
                if not point.get("refs") and not str(point.get("note") or "").strip():
                    said.append(f"{here} point {point.get('title')!r} has no evidence")
                said += [f"{here}: {why}" for why in timelines.refs_faults(point.get("refs") or [], collections, ayahs)]
    return said


@lru_cache(maxsize=1)
def _library() -> dict:
    data = json.loads(data_path("dawah_path").read_text(encoding="utf-8"))
    data.pop("_about", None)
    ayahs = {n: s["ayahs"] for n, s in quran_meanings.surah_names().items()}
    if broken := faults(data, timelines.collections(), ayahs):
        raise ValueError("Dawah data is broken. " + " | ".join(broken))
    return {**data, "collections": timelines.collections()}


def library() -> dict:
    """Every topic and question, sent whole: about forty answers, fixed for the life of the app."""
    return {**_library(), "source": provenance.of("dawah")}
