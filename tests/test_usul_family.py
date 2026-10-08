"""Versions compared: the narrators counted at each place of a number's chains, and the words one telling alone has.

The pure parts run on small lists; the build part runs add_families on a tiny rijal.db whose mentions are placed in
real Arabic chains, so the chain cut, the mention rows and the written tables are all the real ones.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.scripts import build_rijal, build_usul  # noqa: E402
from backend.services.usul import family  # noqa: E402
from backend.services.usul.rule import rule  # noqa: E402

RC = rule()["routes"]
TERMS = RC["terms"]


def test_the_thinnest_place_sets_the_term_whatever_the_places_around_it_hold():
    # Chains in text order, the Companion last. Companions 3, then 1 narrator, then 2 (then 3 teachers of the compiler).
    chains = [[101, 102, 103, 10], [104, 102, 103, 11], [105, 106, 103, 12]]
    counts = [len(place) for place in family.layers(chains)]
    assert counts == [3, 1, 2, 3]
    assert family.term_of(min(counts), TERMS)["key"] == "gharib"


@pytest.mark.parametrize("thinnest, term", [(1, "gharib"), (2, "aziz"), (3, "mashhur"), (9, "mashhur")])
def test_one_narrator_alone_is_gharib_two_aziz_and_more_than_two_mashhur(thinnest, term):
    assert family.term_of(thinnest, TERMS)["key"] == term


def test_chains_are_lined_up_from_the_companion_end_not_from_the_compilers():
    short, long = [7, 10], [1, 2, 3, 7, 10]
    places = family.layers([short, long])
    assert places == [{10}, {7}]      # the short chain's 7 sits where the long chain's 7 does, one from the Companion
    assert family.layers([long, short]) == places


def test_a_telling_given_twice_does_not_double_a_place():
    assert family.layers([[1, 10], [1, 10], [2, 10]]) == [{10}, {1, 2}]


def test_no_places_without_a_chain():
    assert family.layers([]) == []


# ---- words ---------------------------------------------------------------------------------------------------------

BASE = "مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ".split()


def _marks(**tellings):
    found, left = family.marks({p: ws.split() if isinstance(ws, str) else ws for p, ws in tellings.items()}, RC)
    return {p: [(m.at, m.word, m.kind, m.other) for m in ms] for p, ms in found.items()}, left


def test_a_word_in_one_telling_alone_is_marked_on_that_telling_only():
    same = " ".join(BASE)
    found, left = _marks(a=same, b=" ".join(BASE[:-1]) + " لِيَسْكُتْ", c=same)
    assert found == {"b": [(9, "لِيَسْكُتْ", "only", "")]} and left == {}
    # c and a say لِيَصْمُتْ, so it is in two tellings and is nobody's alone.


def test_a_word_that_matches_only_without_its_dots_is_a_dot_difference_not_an_only():
    a = " ".join(BASE[:-3]) + " تَقُولُ"
    b = " ".join(BASE[:-3]) + " يَقُولُ"
    found, _ = _marks(a=a, b=b)
    assert found == {"a": [(7, "تَقُولُ", "dots", "يَقُولُ")], "b": [(7, "يَقُولُ", "dots", "تَقُولُ")]}


def test_a_clitic_or_a_spelling_the_app_folds_is_no_difference():
    a = "وَقَالَ " + " ".join(BASE) + " أَنَّهُ"
    b = "قَالَ " + " ".join(BASE) + " انَّهُ"
    assert _marks(a=a, b=b)[0] == {}


def test_a_ba_that_is_a_root_letter_is_not_taken_for_a_clitic():
    assert family.word_key("بَيْنِي", RC) == "بيني"      # four letters: kept whole
    assert family.word_key("بِاللَّهِ", RC) == "الله"     # a ba off a word that keeps four


def test_a_telling_too_short_to_set_against_the_others_is_listed_and_not_marked():
    found, left = _marks(a=" ".join(BASE), b=" ".join(BASE[:-1]) + " لِيَسْكُتْ", c="بِمِثْلِهِ")
    assert left == {"c": "short_matn"} and set(found) == {"a", "b"}


def test_the_rasm_fold_writes_letters_that_differ_by_dots_as_one():
    assert family.rasm("يقول", RC["rasm"]) == family.rasm("تقول", RC["rasm"]) == family.rasm("نقول", RC["rasm"])
    assert family.rasm("قيل", RC["rasm"]) != family.rasm("كيل", RC["rasm"])


# ---- the build, on real Arabic chains ------------------------------------------------------------------------------

def _chain(*names):
    """Arabic of a chain naming each name in order (Companion last) and the matn after it, with each name's place."""
    text = "حَدَّثَنَا " + " حَدَّثَنَا ".join(names[:-1]) + " عَنْ " + names[-1] + " قَالَ قَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم "
    return text, [(text.index(n), text.index(n) + len(n)) for n in names]


NAMES = {101: "قُتَيْبَةُ", 102: "اللَّيْثُ", 103: "سَعِيدٌ", 104: "يَحْيَى", 105: "مُحَمَّدٌ", 106: "سُفْيَانُ",
         10: "أَبُو هُرَيْرَةَ", 11: "ابْنُ عُمَرَ", 12: "عَائِشَةُ"}


@pytest.fixture()
def built():
    """A rijal.db of nine narrators and one number, muslim 1, told three ways; add_families run over it."""
    rijal = sqlite3.connect(":memory:")
    rijal.executescript(build_rijal._SCHEMA)
    conn = sqlite3.connect(":memory:")
    conn.executescript(build_usul._SCHEMA)
    hadith, rows = [], {}
    matn = {"a": " ".join(BASE), "b": " ".join(BASE[:-1]) + " لِيَسْكُتْ", "c": " ".join(BASE)}
    chains = {"a": (101, 102, 103, 10), "b": (104, 102, 103, 11), "c": (105, 106, 103, 12)}
    for who in NAMES:
        rows[who] = {"name_ar": NAMES[who], "generation_ar": "الأولى" if who < 100 else "الثالثة"}
    for part, ids in chains.items():
        text, spans = _chain(*(NAMES[w] for w in ids))
        hadith.append((("muslim", 1, part), text + matn[part], 1))
        for i, (who, (start, end)) in enumerate(zip(ids, spans)):
            for _ in range(2):   # every mention written twice at its start, as rijal.db sometimes does
                rijal.execute("INSERT INTO mention VALUES ('muslim', 1, 1, ?, ?, ?, ?, ?)", (part, start, end, who, i))
    report, results = build_usul.add_families(conn, rijal, hadith, rows, rule())
    return conn, report, results


def test_the_build_counts_each_place_once_and_gives_the_family_its_term(built):
    conn, report, results = built
    assert conn.execute("SELECT layer, count FROM family_layer ORDER BY layer").fetchall() == [(0, 3), (1, 1), (2, 2), (3, 3)]
    assert json.loads(conn.execute("SELECT ids FROM family_layer WHERE layer = 2").fetchone()[0]) == [102, 106]
    assert results[0]["term"] == "gharib" and "gharib 1" in report[1]


def test_the_build_writes_the_word_marked_in_one_telling_with_its_place_in_the_matn(built):
    conn, _, results = built
    (part, at, word, kind), = conn.execute("SELECT part, at, word, kind FROM family_word").fetchall()
    assert (part, word, kind) == ("b", "لِيَسْكُتْ", "only") and results[0]["matns"]["b"][at] == word


def test_a_family_whose_chain_has_two_companions_gets_no_term_and_is_counted_with_its_reason():
    rijal = sqlite3.connect(":memory:")
    rijal.executescript(build_rijal._SCHEMA)
    conn = sqlite3.connect(":memory:")
    conn.executescript(build_usul._SCHEMA)
    rows = {w: {"name_ar": NAMES[w], "generation_ar": "الأولى"} for w in (10, 11)}   # both Companions
    hadith = []
    for part in "ab":
        text, spans = _chain(NAMES[11], NAMES[10])
        hadith.append((("muslim", 2, part), text + " ".join(BASE), 1))
        for i, (who, (start, end)) in enumerate(zip((11, 10), spans)):
            rijal.execute("INSERT INTO mention VALUES ('muslim', 1, 2, ?, ?, ?, ?, ?)", (part, start, end, who, i))
    _, results = build_usul.add_families(conn, rijal, hadith, rows, rule())
    assert results[0]["term"] is None and results[0]["why"] == "two_companions"
    assert conn.execute("SELECT text, count FROM gap WHERE what = 'family_term'").fetchall() == [("two_companions", 1)]
    assert conn.execute("SELECT COUNT(*) FROM family_layer").fetchone()[0] == 0


def test_the_store_serves_the_term_with_its_quote_and_drops_a_mark_the_text_no_longer_holds(built, tmp_path, monkeypatch):
    from backend.services.usul import store

    conn, _, results = built
    conn.commit()
    target = tmp_path / "usul.db"
    disk = sqlite3.connect(target)
    conn.backup(disk)
    disk.close()
    monkeypatch.setattr(store, "data_path", lambda key: target)
    routes = store.family_routes("muslim", 1)
    assert routes["term"] == "gharib" and routes["layers"] == [3, 1, 2, 3] and routes["scope"] == RC["scope"]
    assert routes["definition"]["quote"] == TERMS[0]["quote"] and routes["definition"]["page"] == "p. 49"
    assert store.family_routes("muslim", 99) is None
    matn = " ".join(results[0]["matns"]["b"])
    assert [m["kind"] for m in store.family_words("muslim", 1, {"b": matn})["b"]] == ["only"]
    assert store.family_words("muslim", 1, {"b": matn.replace("لِيَسْكُتْ", "غَيْرُهُ")}) == {}
