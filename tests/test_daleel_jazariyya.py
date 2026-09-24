"""The tajweed poem as quotable passages.

The poem is stored as half-lines, and a search result is a whole line, so the
join is the thing worth pinning down. Written against a three-verse file of our
own so the tests still say what they mean if a gloss in the real poem is
reworded.

The root lookup is replaced throughout: it asks the 23,715-entry dictionary a
question per word, which is right at index build time and pointless here, where
nothing being tested depends on the answer.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.services import provenance  # noqa: E402
from backend.services.daleel.sources import jazariyya  # noqa: E402

_POEM = {
    "totalBayt": 3,
    "bayt": [
        {
            "n": 1,
            "sadr": "يَقُولُ رَاجِي عَفْوِ رَبٍّ سَامِعِ",
            "ajuz": "مُحَمَّدُ بْنُ الْجَزَرِيِّ الشَّافِعِي",
            "english": "The poet introduces himself.",
        },
        # A line the scan lost half of. Quoting it whole would put half a verse
        # of poetry on screen as if it were the verse.
        {"n": 2, "sadr": "وَبَعْدُ إِنَّ هَذِهِ مُقَدِّمَهْ", "ajuz": "", "english": "Half a line."},
        # And a line with no gloss written yet, which must still be searchable
        # in Arabic rather than dropped for missing its English.
        {"n": 3, "sadr": "إِذْ وَاجِبٌ عَلَيْهِمُ مُحَتَّمُ", "ajuz": "قَبْلَ الشُّرُوعِ أَوَّلًا أَنْ يَعْلَمُوا", "english": ""},
    ],
}


@pytest.fixture()
def poem(tmp_path, monkeypatch):
    path = tmp_path / "poem.json"
    path.write_text(json.dumps(_POEM, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(jazariyya, "_POEM", path)
    monkeypatch.setattr(jazariyya, "roots_in", lambda words: "")
    return path


def test_a_bayt_is_one_passage_of_both_halves(poem):
    first = next(iter(jazariyya.JazariyyaSource().passages()))
    assert first.arabic == _POEM["bayt"][0]["sadr"] + " " + _POEM["bayt"][0]["ajuz"]
    assert first.locator == "Bayt 1"
    assert first.english == "The poet introduces himself."
    assert first.source == "jazariyya"


def test_the_harakat_survive(poem):
    """The whole point of this book: it is the only vowelled text Daleel holds."""
    assert "\u064f" in next(iter(jazariyya.JazariyyaSource().passages())).arabic


def test_half_a_line_is_not_quoted_and_a_missing_gloss_is_not_fatal(poem):
    got = list(jazariyya.JazariyyaSource().passages())
    assert [p.locator for p in got] == ["Bayt 1", "Bayt 3"]
    assert got[1].english == ""


def test_a_missing_file_is_silence_not_a_crash(tmp_path, monkeypatch):
    monkeypatch.setattr(jazariyya, "_POEM", tmp_path / "gone.json")
    assert not list(jazariyya.JazariyyaSource().passages())


def test_the_real_poem_is_where_the_adapter_looks_and_is_all_107():
    got = list(jazariyya.JazariyyaSource().passages())
    assert len(got) == 107, "the poem states its own length in its closing line"


def test_the_badge_this_source_asks_for_exists():
    """A passage whose source has no entry in sources.json cannot be shown."""
    assert provenance.of("jazariyya")["label"]
    assert provenance.category_of("jazariyya") == "Tajweed"
