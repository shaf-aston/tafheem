"""The spoken dialects and their units, the only reader of data/colloquial.

spine.json is the course outline, written once: every unit, lesson and phrase
slot with its English and picture. A dialect is a folder of unit files and one
line in dialects.json, and a unit file only fills the spine's slots with that
dialect's words, dialogue and exercises. So every dialect walks the same course,
and a lesson added to the spine is missing, loudly, from every dialect until
written. A dialect may leave whole units unwritten; those are listed as coming.
Nothing here knows the name of any dialect or unit.

Checked when loaded, not trusted. A repeated exercise id would file two
different questions under one learner history; an unknown exercise type would
draw nothing at all; a missing accepted list would mark every other spelling of
the right answer wrong. Any of those stops the app and names the unit.

The shape itself is written in prose in data/colloquial/FORMAT.md, and
docs/colloquial-authoring-prompt.md is what generates a unit in that shape.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache

from backend.config import data_path
from backend.services import provenance
from backend.services.colloquial.exercises import registry

logger = logging.getLogger(__name__)

SOURCE = "colloquial"


def _credit(image: str) -> dict:
    """Who took a picture, under what licence, and where it came from.

    Read from the attribution.json the fetch script keeps beside the pictures.
    Empty when there is no entry, which `_phrase_faults` reports, because a
    licence that asks for credit is not met by a picture shown without one.
    """
    folder = (data_path("colloquial_dir") / "images").resolve()
    target = (folder / image).resolve()
    try:
        entry = json.loads((target.parent / "attribution.json").read_text(encoding="utf-8"))[target.name]
    except (OSError, KeyError, ValueError):
        return {}
    licence = f"CC {entry['license'].upper()} {entry.get('license_version', '')}".strip()
    return {"credit": f"{entry['creator']}, {licence}", "credit_url": entry["foreign_landing_url"]}


def _phrase_faults(phrase: dict, name: str) -> list[str]:
    said = [f"{name} has no {field}" for field in ("arabic", "transliteration", "english")
            if not str(phrase.get(field) or "").strip()]
    if phrase.get("image") and image_path(phrase["image"]) is None:
        said.append(f"{name} names a picture that is not on disk: {phrase['image']}")
    elif phrase.get("image") and not phrase.get("credit"):
        said.append(f"{name} has a picture with no entry in attribution.json: {phrase['image']}")
    reply = phrase.get("reply")
    if reply is not None:
        said.extend(_phrase_faults(reply, f"{name} reply"))
    return said


def _lesson_faults(lesson: dict, seen_ids: set[str]) -> list[str]:
    """What is wrong with one lesson. seen_ids is shared across the whole unit."""
    name = f"lesson {lesson.get('lesson')!r}"
    said = []
    if not str(lesson.get("title") or "").strip():
        said.append(f"{name} has no title")
    for part in ("phrases", "dialogue", "exercises"):
        if not lesson.get(part):
            said.append(f"{name} has no {part}")
    if not str(lesson.get("culture") or "").strip():
        said.append(f"{name} has no culture note")
    for at, phrase in enumerate(lesson.get("phrases") or [], 1):
        said.extend(_phrase_faults(phrase, f"{name} phrase {at}"))
    for at, line in enumerate(lesson.get("dialogue") or [], 1):
        where = f"{name} dialogue line {at}"
        if not str(line.get("speaker") or "").strip():
            said.append(f"{where} has no speaker")
        said.extend(_phrase_faults(line, where))
    for at, drill in enumerate(lesson.get("de_book") or [], 1):
        said.extend(_phrase_faults(drill.get("pair") or {}, f"{name} pair {at} question"))
        said.extend(_phrase_faults(drill.get("response") or {}, f"{name} pair {at} answer"))
    for at, exercise in enumerate(lesson.get("exercises") or [], 1):
        where = f"{name} exercise {at}"
        given = exercise.get("id")
        if given in seen_ids:
            said.append(f"{where} uses the id {given!r} again, so both would share one answer history")
        seen_ids.add(given)
        said.extend(f"{where} {why}" for why in registry.faults(exercise))
    return said


def _fill(outline: dict, written: dict) -> tuple[dict, list[str]]:
    """One dialect's unit file laid onto its spine unit: the unit a learner sees.

    The spine gives the titles, the order, each phrase's English and picture; the
    dialect gives everything said. A slot or lesson on one side only is a fault,
    so a template change can never reach one dialect and quietly miss another.
    """
    said = []
    lessons = {lesson.get("lesson"): lesson for lesson in written.get("lessons") or []}
    for extra in sorted(set(lessons) - {lesson["lesson"] for lesson in outline["lessons"]}, key=str):
        said.append(f"lesson {extra!r} is not in spine.json")
    filled = []
    for plan in outline["lessons"]:
        lesson = lessons.get(plan["lesson"])
        if lesson is None:
            said.append(f"lesson {plan['lesson']!r} of spine.json is not written")
            continue
        given = [phrase.get("slot") for phrase in lesson.get("phrases") or []]
        for twice in sorted({slot for slot in given if given.count(slot) > 1}, key=str):
            said.append(f"lesson {plan['lesson']!r} fills {twice!r} twice")
        words = {phrase.get("slot"): phrase for phrase in lesson.get("phrases") or []}
        slots = [slot["slot"] for slot in plan["phrases"]]
        for extra in sorted(set(words) - set(slots), key=str):
            said.append(f"lesson {plan['lesson']!r} fills {extra!r}, which spine.json does not have")
        for missing in (slot for slot in slots if slot not in words):
            said.append(f"lesson {plan['lesson']!r} has no words for {missing!r}")
        phrases = [{**slot, **words[slot["slot"]]} for slot in plan["phrases"] if slot["slot"] in words]
        filled.append({**lesson, "title": plan["title"], "phrases": phrases})
    return {**written, "title": outline["title"], "lessons": filled}, said


def _unit_faults(unit: dict) -> list[str]:
    said = []
    for field in ("unit", "title", "dialect"):
        if not str(unit.get(field) or "").strip():
            said.append(f"has no {field}")
    if not unit.get("transliteration_key"):
        said.append("has no transliteration key, so its spelling is unexplained")
    lessons = unit.get("lessons") or []
    if not lessons:
        said.append("has no lessons")
    numbers = [lesson.get("lesson") for lesson in lessons]
    for dup in sorted({n for n in numbers if numbers.count(n) > 1}):
        said.append(f"has two lessons numbered {dup!r}")
    seen_ids: set[str] = set()
    for lesson in lessons:
        said.extend(_lesson_faults(lesson, seen_ids))
    challenge = unit.get("challenge")
    if not challenge:
        said.append("has no challenge")
    elif not (challenge.get("instructions") and challenge.get("required_elements")):
        said.append("has a challenge with no instructions or nothing required in it")
    return said


@lru_cache(maxsize=1)
def _content() -> dict:
    """Every dialect with its units, read once and checked as a whole.

    One raise naming every fault in every unit, rather than one per file: a
    newly generated unit usually has the same mistake in several places, and
    fixing them one app restart at a time is the slow way to find that out.
    """
    root = data_path("colloquial_dir")
    manifest = json.loads((root / "dialects.json").read_text(encoding="utf-8"))
    spine = json.loads((root / "spine.json").read_text(encoding="utf-8"))["units"]
    dialects, broken = [], []
    for dialect in sorted(manifest["dialects"], key=lambda d: d["order"]):
        folder = root / dialect["folder"]
        written = {}
        for path in sorted(folder.glob("unit-*.json")):
            unit = json.loads(path.read_text(encoding="utf-8"))
            if unit.get("unit") in written:
                broken.append(f"dialect {dialect['key']!r} has two units named {unit.get('unit')!r}")
            written[unit.get("unit")] = unit
        for extra in sorted(set(written) - {outline["unit"] for outline in spine}, key=str):
            broken.append(f"{dialect['key']}/{extra}: is not in spine.json")
        if not written:
            broken.append(f"dialect {dialect['key']!r} has no units in {folder.name}/")
        units = []
        for outline in spine:
            if outline["unit"] not in written:
                units.append({"unit": outline["unit"], "title": outline["title"], "written": False,
                              "lessons": [{"lesson": lesson["lesson"], "title": lesson["title"]}
                                          for lesson in outline["lessons"]]})
                continue
            unit, faults = _fill(outline, written[outline["unit"]])
            for lesson in unit["lessons"]:
                for phrase in lesson["phrases"]:
                    if phrase.get("image"):
                        phrase.update(_credit(phrase["image"]))
            if faults := faults + _unit_faults(unit):
                broken.append(f"{dialect['key']}/{outline['unit']}: " + "; ".join(faults))
            units.append({**unit, "written": True})
        dialects.append({**dialect, "units": units})
    keys = [d["key"] for d in dialects]
    if len(set(keys)) != len(keys):
        broken.append(f"dialects.json names a dialect twice: {keys}")
    if broken:
        raise ValueError("Colloquial data is broken. " + " | ".join(broken))
    return {"dialects": dialects}


def catalogue() -> dict:
    """Every dialect and the units in it, without the lessons.

    Every spine unit is listed for every dialect; `written` says which can be
    opened, so an unwritten unit shows as coming instead of vanishing.

    The tab opens on this, so it stays small: a unit's own lessons are about
    sixty kilobytes and there is no reason to send fifteen of them to draw a
    list of titles.
    """
    return {
        "dialects": [
            {
                "key": dialect["key"],
                "label": dialect["label"],
                "arabic": dialect["arabic"],
                "where": dialect["where"],
                "units": [{"unit": u["unit"], "title": u["title"], "written": u["written"],
                           "lessons": [{"lesson": lesson["lesson"], "title": lesson["title"]}
                                       for lesson in u["lessons"]]}
                          for u in dialect["units"]],
            }
            for dialect in _content()["dialects"]
        ],
        "source": provenance.of(SOURCE),
    }


def unit(dialect: str, name: str) -> dict:
    """One whole unit. An unknown dialect or unit is a KeyError, so the route 404s."""
    for known in _content()["dialects"]:
        if known["key"] != dialect:
            continue
        for one in known["units"]:
            if one["unit"] == name and one["written"]:
                return {**one, "dialect_key": dialect, "source": provenance.of(SOURCE)}
        raise KeyError(f"{dialect} has no unit {name!r}")
    raise KeyError(f"no dialect {dialect!r}")


def image_path(relative: str):
    """A picture file under the content's own images folder, or None.

    `relative` is what a phrase's `image` field holds, like
    "unit-01/greeting.jpg". Resolved and checked to still sit inside the
    folder, so a request cannot climb out of it with "..".
    """
    folder = (data_path("colloquial_dir") / "images").resolve()
    target = (folder / relative).resolve()
    return target if target.is_file() and folder in target.parents else None
