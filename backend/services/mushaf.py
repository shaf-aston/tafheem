"""The printed mushafs the Qur'an tab can show as pages, line for line.

This module is the only reader of backend/data/quran/mushaf/. The printings are
listed in printings.json; each one's lines are its own file, built by
scripts/build_mushaf.py. A printing whose file is missing is simply not offered,
which is what a reader sees before the file has been built: the ayah list alone.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data" / "quran" / "mushaf"


@lru_cache(maxsize=1)
def _printings() -> dict[str, dict]:
    entries = json.loads((DATA_DIR / "printings.json").read_text(encoding="utf-8"))["printings"]
    return {entry["id"]: entry for entry in entries if (DATA_DIR / f"{entry['id']}.json").exists()}


def printings() -> list[dict]:
    """Every printing that can be shown, in the order printings.json lists them."""
    return list(_printings().values())


@lru_cache(maxsize=4)
def _pages(printing: str) -> tuple[list, dict[int, list[int]]]:
    """A printing's pages, and for each surah the pages it is on, its name's page included."""
    pages = json.loads((DATA_DIR / f"{printing}.json").read_text(encoding="utf-8"))["pages"]
    on: dict[int, list[int]] = {}
    for number, lines in enumerate(pages, start=1):
        for line in lines:
            surahs = [line[1]] if line[0] == "surah" else [run[0] for run in line[1]] if line[0] == "ayah" else []
            for surah in surahs:
                if not on.get(surah) or on[surah][-1] != number:
                    on.setdefault(surah, []).append(number)
    return pages, on


def for_surah(printing: str, surah: int) -> list[dict] | None:
    """Every whole page a surah is on, in order: a page it shares shows the other
    surah's lines too, as the print does. None for a printing there is no file for."""
    if printing not in _printings():
        return None
    pages, on = _pages(printing)
    return [{"page": number, "lines": pages[number - 1]} for number in on.get(surah, [])]
