"""The timelines: the Prophets, the Seerah and the unseen, one section per file.

The only reader of data/timelines. library.json declares everything a section
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
from backend.services import provenance, quran_library, quran_meanings

logger = logging.getLogger(__name__)

KINDS = {"dated", "undated", "unseen"}
PERIODS = {"makkan", "madinan"}
HIJRI = re.compile(r"[1-9]\d* (AH|BH)")
# The two books of asbab al-nuzul, named in data/quran/editions.json. An event
# carries the reports whose wording names it; everything else sits on the Makkan
# or the Madinan stretch, by the surah it comes from.
ASBAB_ARABIC = "asbab-lubab-ar"
ASBAB_ENGLISH = "asbab-lubab-en"
SURAHS = 114
# How far an event may be broken down: the event, its steps, and the moments
# inside a step. Capped because the reader shows the whole run open, and a
# fourth level would be a page of indentation nobody reads down.
STEP_DEPTH = 2
# "12", "2:255" or "2:30-37". A range never crosses a surah.
QURAN_REF = re.compile(r"^(\d+)(?::(\d+)(?:-(\d+))?)?$")


def _quran_faults(ref: str, ayahs: dict[int, int]) -> list[str]:
    """What is wrong with one Qur'an reference. Bounds are skipped when counts are unknown."""
    match = QURAN_REF.match(ref)
    if not match:
        return [f"Qur'an reference {ref!r} is not S, S:A or S:A-B"]
    surah, first, last = (int(n) if n else None for n in match.groups())
    if not 1 <= surah <= SURAHS:
        return [f"Qur'an reference {ref!r} names surah {surah}, which does not exist"]
    if first is None:
        return []
    last = last or first
    if first < 1 or last < first:
        return [f"Qur'an reference {ref!r} runs backwards or from zero"]
    if ayahs and last > ayahs[surah]:
        return [f"Qur'an reference {ref!r} passes the end of surah {surah} ({ayahs[surah]} ayahs)"]
    return []


def _refs_faults(refs: list[dict], collections: dict, ayahs: dict[int, int]) -> list[str]:
    """Each reference sound, and none given twice: a repeat prints two identical pills."""
    said = [why for ref in refs for why in _ref_faults(ref, collections, ayahs)]
    keys = [json.dumps(ref, sort_keys=True) for ref in refs]
    said += [f"reference {k} is given twice" for k in sorted({k for k in keys if keys.count(k) > 1})]
    return said


def _ref_faults(ref: dict, collections: dict, ayahs: dict[int, int]) -> list[str]:
    kinds = [k for k in ("quran", "hadith", "book") if ref.get(k) is not None]
    if len(kinds) != 1:
        return [f"reference {ref} must name exactly one of quran, hadith or book"]
    if kinds[0] == "quran":
        return _quran_faults(ref["quran"], ayahs)
    key = ref[kinds[0]]
    if collections.get(key, {}).get("kind") != kinds[0]:
        return [f"reference names {kinds[0]} {key!r}, which library.json does not declare as one"]
    if kinds[0] == "hadith" and not isinstance(ref.get("number"), int):
        return [f"hadith reference to {key!r} has no number"]
    # sunnah.com letters the narrations that share one reference number. One
    # letter, lower case: anything else would build a link to a page that is not
    # there and look up words under a key nothing wrote.
    if ref.get("part") is not None and not re.fullmatch(r"[a-z]", str(ref["part"])):
        return [f"reference to {key!r} {ref.get('number')} has part {ref['part']!r}, which is not a single letter a-z"]
    # A number said to be checked has to be reachable, or the reader is asked to
    # take it on trust with the caution taken away and nothing put in its place.
    if ref.get("checked") and not collections[key].get("cite"):
        return [f"reference to {key!r} says its number is checked, but library.json gives it no cite link"]
    return []


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
        said.extend(f"{here}: {why}" for why in _refs_faults(step.get("refs") or [], library["collections"], ayahs))
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
        said.extend(f"{name}: {why}" for why in _refs_faults(event.get("refs") or [], library["collections"], ayahs))
        said.extend(_step_faults(event.get("steps") or [], library, ayahs, name, set()))
    return said


@lru_cache(maxsize=1)
def _library() -> dict:
    root = data_path("timelines_dir")
    library = json.loads((root / "library.json").read_text(encoding="utf-8"))
    library.pop("_about", None)
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
    return json.loads(path.read_text(encoding="utf-8"))["hadith"]


@lru_cache(maxsize=1)
def _asbab() -> dict[str, dict]:
    """Every asbab report, keyed "2:255": the Arabic, and the English beside it.

    Read once from the Qur'an's library, which is the only reader of library.db.
    Empty when the books have not been imported, which is a valid state: the tab
    then shows no reports rather than an empty panel.
    """
    english = dict(quran_library.passages_of(ASBAB_ENGLISH))
    return {
        ref: {"ref": ref, "arabic": arabic, "english": english.get(ref, "")}
        for ref, arabic in quran_library.passages_of(ASBAB_ARABIC)
    }


@lru_cache(maxsize=1)
def _unplaced() -> int:
    """How many of the book's reports matched no single ayah and are not shown.

    Kept in front of the reader rather than in a file nobody opens: a panel that
    quietly holds nine reports out of ten is a panel that lies by omission.
    Written by scripts/build_asbab.py, which is also where the reports are.
    """
    path = data_path("asbab_unmatched_path")
    if not path.exists():
        return 0
    return len(json.loads(path.read_text(encoding="utf-8"))["reports"])


@lru_cache(maxsize=1)
def _surah_periods() -> dict[int, str]:
    """Which surahs came down at Makkah and which at Madinah. Empty if unfetched."""
    path = data_path("quran_surah_type_path")
    if not path.exists():
        logger.warning("Timelines: no surah-type.json, so no report sits on a revelation stretch")
        return {}
    return {int(n): where for n, where in json.loads(path.read_text(encoding="utf-8"))["places"].items()}


def _named_by(event: dict) -> list[str]:
    """The reports whose Arabic says this event's name, in mushaf order."""
    words = event.get("names") or []
    return [ref for ref, row in _asbab().items() if any(word in row["arabic"] for word in words)]


def _in_period(section: dict, event: dict) -> list[str]:
    """The reports on this stretch: its surahs' reports, less any event's own.

    Less the named ones on purpose: a report that says "on the day of Badr" is
    shown on Badr, and showing it again among four hundred others would bury it.
    """
    periods = _surah_periods()
    taken = {ref for other in section["events"] for ref in _named_by(other)}
    return [
        ref for ref in _asbab()
        if ref not in taken and periods.get(int(ref.split(":")[0])) == event["period"]
    ]


def _reports_on(section: dict, event: dict) -> list[dict]:
    """Every report this event carries, each saying how it got here."""
    found = [{"ref": ref, "how": "named"} for ref in _named_by(event)]
    if event.get("period"):
        found += [{"ref": ref, "how": "period"} for ref in _in_period(section, event)]
    return sorted(found, key=lambda row: [int(n) for n in row["ref"].split(":")])


def library() -> dict:
    """Every section in order, with the vocabulary they point at and their source.

    Each event carries how many asbab reports it holds, so the tab can offer the
    panel only where there is something in it, without fetching any of them.
    """
    data = _library()
    sections = [
        {**section, "events": [
            {**event, "asbab": len(_reports_on(section, event))} for event in section["events"]
        ]}
        for section in data["sections"]
    ]
    return {**data, "sections": sections, "source": provenance.of("timelines")}


def asbab(section_id: str, event_id: str) -> dict:
    """One event's reports on why an ayah came down, shortest form first.

    The list carries the opening of each report and not the whole of it: four
    hundred reports of running prose is a megabyte, and the panel shows one at a
    time. The chosen one is then read from the Qur'an's library like any other
    book on that ayah (`/api/quran/editions/{surah}/{ayah}`).
    """
    section = next((s for s in _library()["sections"] if s["id"] == section_id), None)
    event = next((e for e in section["events"] if e["id"] == event_id), None) if section else None
    if event is None:
        raise KeyError(f"no event {section_id}/{event_id}")
    names = quran_meanings.surah_names()
    reports = []
    for row in _reports_on(section, event):
        passage = _asbab()[row["ref"]]
        surah, ayah = (int(n) for n in row["ref"].split(":"))
        reports.append({
            "ref": row["ref"], "surah": surah, "ayah": ayah, "how": row["how"],
            # The name travels with the report so the list can group by surah
            # without the tab holding a second copy of the 114 names.
            "surah_name": names.get(surah, {}).get("name_en", f"Surah {surah}"),
            "opening": passage["english"][:200] or passage["arabic"][:200],
            "arabic_opening": passage["arabic"][:120],
        })
    return {"section": section_id, "event": event_id, "reports": reports,
            "unplaced": _unplaced(), "books": {"arabic": ASBAB_ARABIC, "english": ASBAB_ENGLISH},
            "source": provenance.of("lubab")}
