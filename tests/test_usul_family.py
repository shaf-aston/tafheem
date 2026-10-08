"""Versions compared: the narrators counted at each place of a number's chains, and the words one telling alone has.

The pure parts run on small lists; the build part runs add_families on a tiny rijal.db whose mentions are placed in
real Arabic chains, so the chain cut, the mention rows and the written tables are all the real ones. Tellings of
other numbers are in the build too, because a word's weight is read off all the tellings the books hold.
"""
from __future__ import annotations

import itertools
import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.scripts import build_rijal, build_usul  # noqa: E402
from backend.services.usul import family  # noqa: E402
from backend.services.usul.rule import rule  # noqa: E402

FC = rule()["family"]
REASONS = FC["reasons"]


def test_chains_are_lined_up_from_the_companion_end_not_from_the_compilers():
    short, long = [7, 10], [1, 2, 3, 7, 10]
    places = family.places([short, long])
    assert places == [{10}, {7}]      # the short chain's 7 sits where the long chain's 7 does, one from the Companion
    assert family.places([long, short]) == places


def test_a_telling_given_twice_does_not_double_a_place():
    assert family.places([[1, 10], [1, 10], [2, 10]]) == [{10}, {1, 2}]


def test_no_places_without_a_chain():
    assert family.places([]) == []


# ---- words ---------------------------------------------------------------------------------------------------------

BASE = "مَنْ كَانَ يُؤْمِنُ بِاللَّهِ وَالْيَوْمِ الآخِرِ فَلْيَقُلْ خَيْرًا أَوْ لِيَصْمُتْ".split()
OTHER = "كَانَ لِرَسُولِ حَصِيرٌ يُحَجِّرُهُ مِنَ اللَّيْلِ فَيُصَلِّي فِيهِ فَجَعَلَ النَّاسُ يُصَلُّونَ بِصَلاَتِهِ".split()


def _filler(n: int) -> list[str]:
    """n sentences of ten words no other sentence shares: the other numbers of the books."""
    letters = "ءآأؤإئابةتثجحخدذرزسشصضطظعغفقكلمنهوي"
    words = ["".join(w) for w in itertools.product(letters, repeat=3)]
    return [" ".join(words[i * 10:(i + 1) * 10]) for i in range(n)]


def _weights(*tellings: list[str]) -> dict[str, float]:
    keys = [{k for w in t if (k := family.word_key(w, FC))} for t in (*tellings, *(f.split() for f in _filler(30)))]
    return family.weights(keys)


def _marks(**tellings):
    words = {p: ws.split() if isinstance(ws, str) else ws for p, ws in tellings.items()}
    found, left = family.marks(words, FC, _weights(*words.values()))
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
    assert family.word_key("بَيْنِي", FC) == "بيني"      # four letters: kept whole
    assert family.word_key("بِاللَّهِ", FC) == "الله"     # a ba off a word that keeps four


def test_a_telling_too_short_to_set_against_the_others_is_listed_and_not_marked():
    found, left = _marks(a=" ".join(BASE), b=" ".join(BASE[:-1]) + " لِيَسْكُتْ", c="بِمِثْلِهِ")
    assert left == {"c": "short_matn"} and set(found) == {"a", "b"}


def test_two_different_texts_under_one_number_are_not_compared_and_say_so():
    # Two tellings of one text beside a third that is another text: the pair is set against each other, the third is left out whole
    # (its words are not marked as "only here" against a text it does not share).
    same = " ".join(BASE)
    found, left = _marks(a=same, b=" ".join(BASE[:-1]) + " لِيَسْكُتْ", c=" ".join(OTHER))
    assert set(found) == {"a", "b"} and left == {"c": "different_text"}
    assert set(_marks(a=same, c=" ".join(OTHER))[0]) == set()
    assert _marks(a=same, c=" ".join(OTHER))[1] == {"a": "different_text", "c": "different_text"}


def test_the_rasm_fold_writes_letters_that_differ_by_dots_as_one():
    assert family.rasm("يقول", FC["rasm"]) == family.rasm("تقول", FC["rasm"]) == family.rasm("نقول", FC["rasm"])
    assert family.rasm("قيل", FC["rasm"]) != family.rasm("كيل", FC["rasm"])


# ---- the build, on real Arabic chains ------------------------------------------------------------------------------

TAIL = " قَالَ قَالَ رَسُولُ اللَّهِ صلى الله عليه وسلم "


def _chain(names, joins=()):
    """Arabic of a chain naming each name in order (Companion last) and the text after it, with each name's place.
    A name whose index is in `joins` follows the one before it with a bare وَ, not a transmission word."""
    text, spans = "", []
    for i, name in enumerate(names):
        text += "حَدَّثَنَا " if i == 0 else (" وَ " if i in joins else (" عَنْ " if i == len(names) - 1 else " حَدَّثَنَا "))
        spans.append((len(text), len(text) + len(name)))
        text += name
    return text + TAIL, spans


NAMES = {101: "قُتَيْبَةُ", 102: "اللَّيْثُ", 103: "سَعِيدٌ", 104: "يَحْيَى", 105: "مُحَمَّدٌ", 106: "سُفْيَانُ",
         107: "أَبُو صَالِحٍ", 10: "أَبُو هُرَيْرَةَ", 11: "ابْنُ عُمَرَ", 12: "عَائِشَةُ"}


def _run(families: dict[int, dict[str, tuple[tuple, str, tuple]]]):
    """add_families over `families`: {number: {part: (chain ids, matn, joined indexes)}}; the filler numbers are added."""
    rijal = sqlite3.connect(":memory:")
    rijal.executescript(build_rijal._SCHEMA)
    conn = sqlite3.connect(":memory:")
    conn.executescript(build_usul._SCHEMA)
    rows = {who: {"name_ar": NAMES[who], "generation_ar": "الأولى" if who < 100 else "الثالثة"} for who in NAMES}
    hadith = []
    for number, parts in {**families, **{1000 + i: {"a": ((101, 10), f, ()), "b": ((101, 10), f, ())}
                                         for i, f in enumerate(_filler(30))}}.items():
        for part, (ids, matn, joins) in parts.items():
            text, spans = _chain([NAMES[w] for w in ids], joins)
            hadith.append((("muslim", number, part), text + matn, 1))
            for i, (who, (start, end)) in enumerate(zip(ids, spans)):
                for _ in range(2):   # every mention written twice at its start, as rijal.db sometimes does
                    rijal.execute("INSERT INTO mention VALUES ('muslim', 1, ?, ?, ?, ?, ?, ?)", (number, part, start, end, who, i))
    report, results = build_usul.add_families(conn, rijal, hadith, rows, rule())
    return conn, report, {r["number"]: r for r in results}


BASE_TEXT = " ".join(BASE)
THREE = {"a": ((101, 102, 103, 10), BASE_TEXT, ()),
         "b": ((104, 102, 103, 11), " ".join(BASE[:-1]) + " لِيَسْكُتْ", ()),
         "c": ((105, 106, 103, 12), BASE_TEXT, ())}


@pytest.fixture()
def built():
    return _run({1: THREE})


def test_the_build_counts_each_place_once_and_marks_the_place_one_narrator_carries(built):
    conn, _, results = built
    assert conn.execute("SELECT place, count FROM family_place WHERE number = 1 ORDER BY place").fetchall() == [(0, 3), (1, 1), (2, 2), (3, 3)]
    assert json.loads(conn.execute("SELECT ids FROM family_place WHERE number = 1 AND place = 2").fetchone()[0]) == [102, 106]
    assert [len(s) for s in results[1]["places"]] == [3, 1, 2, 3]


def test_the_build_writes_the_word_marked_in_one_telling_with_its_place_in_the_matn(built):
    conn, _, results = built
    (part, at, word, kind), = conn.execute("SELECT part, at, word, kind FROM family_word WHERE number = 1").fetchall()
    assert (part, word, kind) == ("b", "لِيَسْكُتْ", "only") and results[1]["matns"]["b"][at] == word


def test_a_chain_with_two_names_at_one_place_gets_no_picture_and_is_counted_with_its_reason():
    # b: Qutayba, then Abu Salih and Layth joined by a bare وَ, then the Companion. Which of them narrates from whom is not written.
    conn, _, results = _run({2: {"a": ((101, 102, 10), BASE_TEXT, ()), "b": ((101, 107, 102, 10), BASE_TEXT, (2,))}})
    assert results[2]["why"] == "names_joined" and results[2]["places"] == []
    assert conn.execute("SELECT COUNT(*) FROM family_place WHERE number = 2").fetchone()[0] == 0
    assert (REASONS["names_joined"], 1) in conn.execute("SELECT text, count FROM gap WHERE what = 'family_place'").fetchall()


def test_a_family_whose_chain_has_two_companions_gets_no_picture_and_is_counted_with_its_reason():
    rijal = sqlite3.connect(":memory:")
    rijal.executescript(build_rijal._SCHEMA)
    conn = sqlite3.connect(":memory:")
    conn.executescript(build_usul._SCHEMA)
    rows = {w: {"name_ar": NAMES[w], "generation_ar": "الأولى"} for w in (10, 11)}   # both Companions
    hadith = []
    for part in "ab":
        text, spans = _chain([NAMES[11], NAMES[10]])
        hadith.append((("muslim", 2, part), text + BASE_TEXT, 1))
        for i, (who, (start, end)) in enumerate(zip((11, 10), spans)):
            rijal.execute("INSERT INTO mention VALUES ('muslim', 1, 2, ?, ?, ?, ?, ?)", (part, start, end, who, i))
    _, results = build_usul.add_families(conn, rijal, hadith, rows, rule())
    assert results[0]["places"] == [] and results[0]["why"] == "two_companions"
    assert conn.execute("SELECT text, count FROM gap WHERE what = 'family_place'").fetchall() == [(REASONS["two_companions"], 1)]
    assert conn.execute("SELECT COUNT(*) FROM family_place").fetchone()[0] == 0


def test_the_build_leaves_a_telling_of_another_text_out_of_the_marks_and_counts_it():
    other = {"a": ((101, 10), BASE_TEXT, ()), "b": ((101, 10), " ".join(BASE[:-1]) + " لِيَسْكُتْ", ()),
             "c": ((101, 10), " ".join(OTHER), ())}
    conn, report, results = _run({3: other})
    assert results[3]["left"] == {"c": "different_text"} and set(results[3]["marks"]) == {"a", "b"}
    assert {part for (part,) in conn.execute("SELECT part FROM family_word WHERE number = 3")} == {"a", "b"}
    assert (REASONS["different_text"], 1) in conn.execute("SELECT text, count FROM gap WHERE what = 'family_word'").fetchall()


def test_the_store_words_each_place_from_config_and_drops_a_mark_the_text_no_longer_holds(built, tmp_path, monkeypatch):
    from backend.services.usul import store

    conn, _, results = built
    conn.commit()
    target = tmp_path / "usul.db"
    disk = sqlite3.connect(target)
    conn.backup(disk)
    disk.close()
    monkeypatch.setattr(store, "data_path", lambda key: target)
    monkeypatch.setattr(store.loader, "collection_name", lambda collection: "Sahih Muslim")
    places = store.family_places("muslim", 1, 3)
    assert places["heading"] == "Narrators at each place, across Sahih Muslim's 3 narrations of no. 1"
    assert [(p["label"], p["count"], p["alone"]) for p in places["places"]] == [
        ("Companion", 3, ""), ("Place 2", 1, "one narrator here in all 3 narrations"), ("Place 3", 2, ""), ("Place 4", 3, "")]
    assert store.family_places("muslim", 99, 3) is None
    text = {"arabic": _chain([NAMES[104], NAMES[11]])[0] + THREE["b"][1]}
    monkeypatch.setattr(store.loader, "numbered", lambda collection, number: (number, [("muslim", 1, number, "b", text["arabic"], "", "")]))
    words = store.family_words("muslim", 1)
    assert [m["kind"] for m in words["b"]["marks"]] == ["only"] and words["b"]["matn"] == " ".join(results[1]["matns"]["b"])
    text["arabic"] = text["arabic"].replace("لِيَسْكُتْ", "غَيْرُهُ")
    assert store.family_words("muslim", 1) == {}


def test_the_compilers_own_teachers_named_together_stand_before_the_chain_and_leave_the_picture_whole():
    # b: Qutayba and Yahya, both the compiler's teachers (حدثنا A وB), then al-Layth and the Companion.
    _, _, results = _run({3: {"a": ((101, 102, 10), BASE_TEXT, ()), "b": ((101, 104, 102, 10), BASE_TEXT, (1,))}})
    assert results[3]["why"] == "" and results[3]["chains"]["b"] == [102, 10]
    assert results[3]["places"] == [{10}, {102}]


def test_a_name_after_the_chains_cut_leaves_the_telling_without_places_or_marks():
    # a second chain in what the app shows as the text: its names would be counted short and its words marked as text
    text, spans = _chain([NAMES[101], NAMES[10]])
    second = text + "وَقَالَ "
    mentions = [(s, e, w) for (s, e), w in zip(spans, (101, 10))] + [(len(second), len(second) + len(NAMES[106]), 106)]
    assert family.chain_ids(second + NAMES[106] + " " + BASE_TEXT, mentions, {10: "الأولى"}, {"الأولى"}, FC["joiner"]) == ([], "name_after_cut")


def test_a_chain_of_the_compilers_teachers_alone_has_no_places_and_does_not_stop_the_build():
    text, spans = _chain([NAMES[101], NAMES[104]], joins=(1,))
    mentions = [(s, e, w) for (s, e), w in zip(spans, (101, 104))]
    assert family.chain_ids(text, mentions, {}, {"الأولى"}, FC["joiner"]) == ([], "no_chain")


def test_two_names_with_nothing_between_them_are_not_taken_for_the_compilers_teachers():
    # "عن أبيه، محمد": one man named twice, or a name rijal split; no joiner, so the split is not guessed
    text = "حَدَّثَنَا " + NAMES[101] + "، " + NAMES[105] + " عَنْ " + NAMES[10] + TAIL
    mentions = [(text.find(NAMES[w]), text.find(NAMES[w]) + len(NAMES[w]), w) for w in (101, 105, 10)]
    assert family.chain_ids(text, mentions, {10: "الأولى"}, {"الأولى"}, FC["joiner"]) == ([], "names_joined")


def test_a_word_whose_dotted_twin_the_same_telling_also_says_is_its_own_not_a_dot_difference():
    a = " ".join(BASE[:-3]) + " يَقُولُ تَقُولُ"
    b = " ".join(BASE[:-3]) + " تَقُولُ"
    assert _marks(a=a, b=b)[0] == {"a": [(7, "يَقُولُ", "only", "")]}
