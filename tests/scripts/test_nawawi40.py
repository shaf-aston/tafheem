"""Grow's Hadith world data (frontend/public/grow/nawawi40.json, built by backend/scripts/grow/build_nawawi40.py).

Every key line must be an exact quote of its hadith, in both languages: no word is the app's own.

Run: python -m pytest tests/scripts/test_nawawi40.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILT = json.loads((ROOT / "frontend/public/grow/nawawi40.json").read_text(encoding="utf-8"))
KEYS = json.loads((ROOT / "backend/data/grow/nawawi40_keys.json").read_text(encoding="utf-8"))["keys"]


def test_all_forty_two_in_order():
    assert [h["n"] for h in BUILT["hadiths"]] == list(range(1, 43))


def test_every_key_line_is_an_exact_quote():
    for h in BUILT["hadiths"]:
        assert h["key"]["ar"] in h["arabic"], h["n"]
        assert h["key"]["en"] in h["english"], h["n"]


def test_the_built_file_matches_the_hand_kept_keys():
    assert {str(h["n"]): [h["key"]["ar"], h["key"]["en"]] for h in BUILT["hadiths"]} == KEYS


def test_the_source_is_credited():
    sources = json.loads((ROOT / "backend/data/sources.json").read_text(encoding="utf-8"))
    assert BUILT["source"]["url"] == sources["hadith"]["url"]
    assert "grow" in sources["hadith"]["used_in"]
