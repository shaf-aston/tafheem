"""The asbab al-nuzul reports that hang on a timeline event.

An event carries the reports whose wording names it; everything else sits on the
Makkan or the Madinan stretch, by the surah it comes from. Takes the section and
event as dicts (services/timelines finds them), so this file never reads the
timelines themselves.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache

from backend.config import data_path
from backend.services import provenance, quran_library, quran_meanings

logger = logging.getLogger(__name__)

# The two books of asbab al-nuzul, named in data/quran/editions.json.
ASBAB_ARABIC = "asbab-lubab-ar"
ASBAB_ENGLISH = "asbab-lubab-en"


@lru_cache(maxsize=1)
def _passages() -> dict[str, dict]:
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
    return [ref for ref, row in _passages().items() if any(word in row["arabic"] for word in words)]


def _in_period(section: dict, event: dict) -> list[str]:
    """The reports on this stretch: its surahs' reports, less any event's own.

    Less the named ones on purpose: a report that says "on the day of Badr" is
    shown on Badr, and showing it again among four hundred others would bury it.
    """
    periods = _surah_periods()
    taken = {ref for other in section["events"] for ref in _named_by(other)}
    return [
        ref for ref in _passages()
        if ref not in taken and periods.get(int(ref.split(":")[0])) == event["period"]
    ]


def reports_on(section: dict, event: dict) -> list[dict]:
    """Every report this event carries, each saying how it got here."""
    found = [{"ref": ref, "how": "named"} for ref in _named_by(event)]
    if event.get("period"):
        found += [{"ref": ref, "how": "period"} for ref in _in_period(section, event)]
    return sorted(found, key=lambda row: [int(n) for n in row["ref"].split(":")])


def listing(section: dict, event: dict) -> dict:
    """One event's reports on why an ayah came down, shortest form first.

    The list carries the opening of each report and not the whole of it: four
    hundred reports of running prose is a megabyte, and the panel shows one at a
    time. The chosen one is then read from the Qur'an's library like any other
    book on that ayah (`/api/quran/editions/{surah}/{ayah}`).
    """
    names = quran_meanings.surah_names()
    reports = []
    for row in reports_on(section, event):
        passage = _passages()[row["ref"]]
        surah, ayah = (int(n) for n in row["ref"].split(":"))
        reports.append({
            "ref": row["ref"], "surah": surah, "ayah": ayah, "how": row["how"],
            # The name travels with the report so the list can group by surah
            # without the tab holding a second copy of the 114 names.
            "surah_name": names.get(surah, {}).get("name_en", f"Surah {surah}"),
            "opening": passage["english"][:200] or passage["arabic"][:200],
            "arabic_opening": passage["arabic"][:120],
        })
    return {"section": section["id"], "event": event["id"], "reports": reports,
            "unplaced": _unplaced(), "books": {"arabic": ASBAB_ARABIC, "english": ASBAB_ENGLISH},
            "source": provenance.of("lubab")}
