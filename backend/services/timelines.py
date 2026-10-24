"""The timelines: the Prophets, the Seerah and the unseen, one section per file.

With services/text/refs, the only reader of data/timelines. library.json declares everything a section
may point at (sciences, flags, places, collections, map views), so a place is
written once and a typo in a key is caught rather than drawn nowhere.

Checked when loaded, not trusted. An event out of order would draw the line
backwards; a stretch ending before it starts would draw a negative bar; a Qur'an
reference past the end of its surah would open an ayah that does not exist.
Any of those stops the app and names the event.
"""
from __future__ import annotations

import json
import logging
import re
from functools import lru_cache

from backend.config import data_path
from backend.services.quran import asbab
from backend.services.core import provenance
from backend.services.quran import meanings as quran_meanings
from backend.services.text import refs
from backend.services.hadith.chain import cut_of

logger = logging.getLogger(__name__)

KINDS = {"dated", "undated", "unseen"}
PERIODS = {"makkan", "madinan"}
HIJRI = re.compile(r"[1-9]\d* (AH|BH)")
# How far an event may be broken down: the event, its steps, and the moments
# inside a step. Capped because the reader shows the whole run open, and a
# fourth level would be a page of indentation nobody reads down.
STEP_DEPTH = 2


def _step_faults(steps: list, library: dict, ayahs: dict[int, int], name: str,
                 seen: set[str], depth: int = 1) -> list[str]:
    """What is wrong with one run of steps, and the moments inside them.

    `seen` is every step id already used anywhere in this event, so two steps
    cannot share an id: the reader keeps its folded state by that id, and a
    repeat would fold two places at once.
    """
    said = []
    if steps and depth > STEP_DEPTH:
        return [f"{name} is nested {depth} deep, past the {STEP_DEPTH} levels an event may be broken into"]
    for step in steps:
        here = f"{name} step {step.get('id')!r}"
        for field in ("id", "title", "summary"):
            if not str(step.get(field) or "").strip():
                said.append(f"{here} has no {field}")
        step_id = step.get("id")
        if step_id in seen:
            said.append(f"{here} uses an id already used in this event")
        seen.add(step_id)
        if not isinstance(step.get("aside", False), bool):
            said.append(f"{here}: aside must be true or false, not {step['aside']!r}")
        if step.get("place") is not None and step["place"] not in library["places"]:
            said.append(f"{here} is at place {step['place']!r}, which library.json does not declare")
        if step.get("path") is not None and step["path"] not in library["paths"]:
            said.append(f"{here} is on path {step['path']!r}, which library.json does not declare")
        for flag in step.get("flags") or []:
            if flag not in library["flags"]:
                said.append(f"{here} has flag {flag!r}, which library.json does not declare")
        said.extend(f"{here}: {why}" for why in refs.refs_faults(step.get("refs") or [], library["collections"], ayahs))
        said.extend(_step_faults(step.get("steps") or [], library, ayahs, here, seen, depth + 1))
    # Neighbouring steps on paths are drawn side by side, so a run of them needs
    # at least two paths, or it is one lane beside an empty column.
    run = []
    for step in [*steps, {}]:
        if step.get("path"):
            run.append(step)
            continue
        if run and len({s["path"] for s in run}) < 2:
            said.append(f"{name} step {run[0].get('id')!r} starts a side-by-side run with only the {run[0]['path']!r} path")
        run = []
    return said


def _faults(section: dict, library: dict, ayahs: dict[int, int]) -> list[str]:
    """What is wrong with one section, in plain words. Empty means sound."""
    said = []
    if section.get("science") not in {s["key"] for s in library["sciences"]}:
        said.append(f"science {section.get('science')!r} is not declared in library.json")
    if section.get("kind") not in KINDS:
        said.append(f"kind {section.get('kind')!r} is not one of {sorted(KINDS)}")
    if section.get("map") is not None and section["map"] not in library["map"]["views"]:
        said.append(f"map view {section['map']!r} is not declared in library.json")
    events = section.get("events") or []
    if not events:
        said.append("has no events")
    ids = [e.get("id") for e in events]
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        said.append(f"event id {dup!r} is used more than once")
    at_of = {e.get("id"): e.get("at") for e in events}
    periods = [e["period"] for e in events if e.get("period")]
    for twice in sorted({p for p in periods if periods.count(p) > 1}):
        said.append(f"two events claim the {twice} stretch, so every report of it would be shown twice")
    previous = None
    for event in events:
        name = f"event {event.get('id')!r}"
        for field in ("id", "title", "arabic", "when", "summary"):
            if not str(event.get(field) or "").strip():
                said.append(f"{name} has no {field}")
        at = event.get("at")
        if not isinstance(at, (int, float)):
            said.append(f"{name} has no numeric at")
            continue
        if previous is not None and at < previous:
            said.append(f"{name} at {at} comes before the event above it ({previous})")
        previous = at
        # The Hijri year beside the common-era one, e.g. "5 AH" or "13 BH".
        if "hijri" in event and not HIJRI.fullmatch(str(event["hijri"])):
            said.append(f"{name} has hijri {event['hijri']!r}, which is not like '5 AH' or '13 BH'")
        if event.get("place") is not None and event["place"] not in library["places"]:
            said.append(f"{name} is at place {event['place']!r}, which library.json does not declare")
        if event.get("period") is not None and event["period"] not in PERIODS:
            said.append(f"{name} has period {event['period']!r}, which is not one of {sorted(PERIODS)}")
        if any(not str(word or "").strip() for word in event.get("names") or []):
            said.append(f"{name} has an empty word in its names, which would match every report")
        for flag in event.get("flags") or []:
            if flag not in library["flags"]:
                said.append(f"{name} has flag {flag!r}, which library.json does not declare")
        until = event.get("until")
        if until is not None:
            if not isinstance(at_of.get(until), (int, float)):
                said.append(f"{name} lasts until {until!r}, which is not an event in this section with a when")
            elif until == event["id"] or at_of[until] <= at:
                # <= and not <: a stretch ending where it starts draws a bar of
                # no height, which says "this lasted no time" and is not what
                # anybody meant by writing it.
                said.append(f"{name} lasts until {until!r}, which does not come after it")
        if not event.get("refs"):
            said.append(f"{name} has no references")
        said.extend(f"{name}: {why}" for why in refs.refs_faults(event.get("refs") or [], library["collections"], ayahs))
        # An estimate of when is only shown beside the source that states it.
        for date in event.get("dates") or []:
            if not isinstance(date, dict) or not isinstance(date.get("ref"), dict):
                said.append(f"{name} has a date {date!r} that is not {{says, ref}}")
                continue
            if not str(date.get("says") or "").strip():
                said.append(f"{name} has a date that says nothing")
            said.extend(f"{name} date {date.get('says')!r}: {why}"
                        for why in refs.ref_faults(date["ref"], library["collections"], ayahs))
        said.extend(_step_faults(event.get("steps") or [], library, ayahs, name, set()))
    return said


@lru_cache(maxsize=1)
def _library() -> dict:
    root = data_path("timelines_dir")
    library = dict(refs.declared())
    ayahs = {n: s["ayahs"] for n, s in quran_meanings.surah_names().items()}
    if not ayahs:
        logger.warning("Timelines: meanings.db is not built, so ayah ranges are not checked")
    sections, broken = [], []
    for path in sorted((root / "sections").glob("*.json")):
        section = json.loads(path.read_text(encoding="utf-8"))
        if faults := _faults(section, library, ayahs):
            broken.append(f"{path.name}: " + "; ".join(faults))
        sections.append(section)
    ids = [s.get("id") for s in sections]
    orders = [s.get("order") for s in sections]
    if len(set(ids)) != len(ids) or len(set(orders)) != len(orders):
        broken.append(f"section ids {ids} or orders {orders} repeat")
    if broken:
        raise ValueError("Timelines data is broken. " + " | ".join(broken))
    return {**library, "hadith": _hadith(), "sections": sorted(sections, key=lambda s: s["order"])}


@lru_cache(maxsize=1)
def _hadith() -> dict[str, dict]:
    """The words of the hadiths the sections cite, keyed "muslim:2902".

    Sent with the library rather than fetched per event: the reader shows every
    hadith of an opened event at once, and an event's own words arriving after
    its summary is a page that moves under the eye.

    Written by scripts/fetch_timeline_hadith.py. Missing is a valid state, as
    it was before that script existed: the tab then prints the number alone.
    """
    path = data_path("timelines_dir") / "hadith.json"
    if not path.exists():
        logger.warning("Timelines: hadith.json is not fetched, so events print their numbers alone")
        return {}
    found = json.loads(path.read_text(encoding="utf-8"))["hadith"]
    return {key: {**row, "cut": cut_of(row["arabic"])} for key, row in found.items()}


def library() -> dict:
    """Every section in order, with the vocabulary they point at and their source.

    Each event carries how many asbab reports it holds, so the tab can offer the
    panel only where there is something in it, without fetching any of them.
    """
    data = _library()
    sections = [
        {**section, "events": [
            {**event, "asbab": len(asbab.reports_on(section, event))} for event in section["events"]
        ]}
        for section in data["sections"]
    ]
    return {**data, "sections": sections, "source": provenance.of("timelines")}


def find(section_id: str, event_id: str) -> tuple[dict, dict]:
    """A section and one of its events by id; KeyError when either is not declared."""
    section = next((s for s in _library()["sections"] if s["id"] == section_id), None)
    event = next((e for e in section["events"] if e["id"] == event_id), None) if section else None
    if event is None:
        raise KeyError(f"no event {section_id}/{event_id}")
    return section, event
