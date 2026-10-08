"""What a scholar said of a hadith (usul phase 2): the reader of each ruling book, the match to our hadith, the endpoints.

The match runs on a tiny index, so its knobs are lowered to that scale (usul.json's are set for 34,005 hadith).
"""
from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.scripts import build_usul
from backend.services.usul import books, match, names, ruling
from backend.services.usul.books import Entry
from backend.services.usul.rule import rule
from tests.test_usul import paths  # noqa: F401  (the fixture: temporary rijal.db and usul.db)

RULINGS = rule()["rulings"]
SMALL = {**rule(), "rulings": {**RULINGS, "match": {**RULINGS["match"], "df_max": 5, "floor": 3.0, "whole_floor": 2.0}}}
MATN = "نهيتكم عن زيارة القبور فزوروها فإن في زيارتها تذكرة للآخرة"
CHAIN = "حدثنا سفيان بن عيينة، عن أبي هريرة"


def test_entries_numbered_by_the_book_skip_page_subheadings_and_drop_the_editors_introduction():
    raw = ("#META#Header#End#\n### | مقدمة المحقق\n### | 1 -\nمقدمة\n### | بيان علل الأحاديث\n### | 1 -\nنص أول\n"
           "### | [ص: 37]\nتتمة\n### | 2 -\nنص ثان\n")
    spec = {"entry": r"^### \| (?P<n>\d+) ?-\s*$", "skip": r"^### \| \[ص: ?\d+\]", "from_heading": "بيان علل"}
    assert [(e.n, e.text) for e in books.entries(raw, spec)] == [(1, "نص أول تتمة"), (2, "نص ثان")]
    # A book that numbers nothing is numbered as it comes.
    assert [e.n for e in books.entries("#META#Header#End#\n# باب أ\n# باب ب\n", {"entry": r"^# (?P<text>باب .*)$"})] == [1, 2]


def test_a_quote_is_the_books_own_sentence_and_goes_on_through_a_qualifier():
    shahin = Entry(5, "حدثنا أحمد، عن أبي هريرة قال: «نهيتكم عن زيارة القبور فزوروها» قال الشيخ والحديث ناسخ للأول.",
                   heading="ذكر زيارة القبور")
    [found], why = ruling.read(shahin, "nasikh_chapter", RULINGS)
    assert (found.quote, found.chapter, why) == ("قال الشيخ والحديث ناسخ للأول.", "ذكر زيارة القبور", "")
    asked = Entry(9, "وسألت أبي عن حديث رواه سعيد، عن قتادة، عن النبي (ص) : من قال كذا دخل الجنة؟ "
                     "قال أبي: هذا حديث منكر، إلا أن يكون عن فلان. وقال أبو زرعة: هو باطل.")
    found, _ = ruling.read(asked, "ilal", RULINGS)
    assert [(r.scholar, r.quote) for r in found] == [("أبو حاتم", "قال أبي: هذا حديث منكر، إلا أن يكون عن فلان."),
                                                      ("أبو زرعة", "وقال أبو زرعة: هو باطل.")]
    judged = Entry(3, 'قال: قال رسول الله صلى الله عليه وسلم: " من فعل كذا فله كذا ". هذا حديث لا يصح، لا أصل له إلا من هذا الوجه.',
                   heading="باب فضل كذا")
    assert ruling.read(judged, "mawdu_listed", RULINGS)[0][0].quote == "هذا حديث لا يصح، لا أصل له إلا من هذا الوجه."


def test_a_unit_with_two_hadith_or_no_verdict_is_not_forced_into_a_ruling():
    two = "حدثنا أ «س» حدثنا ب «ص»"
    assert ruling.read(Entry(1, two, heading="ذكر", breaks=[0, len("حدثنا أ «س» ")]), "nasikh_chapter", RULINGS) == (
        [], "more than one hadith in the unit")
    assert ruling.read(Entry(2, "أنبأنا فلان عن علي: ما أحسن هذا", heading="باب"), "mawdu_listed", RULINGS)[1] == "no verdict sentence"


# Twenty other hadith, so that a phrase in one or two of 22 is rare.
OTHERS = [(("bukhari", i, ""), "حدثنا س قال " + " ".join(chr(0x628 + i) + w for w in ("لكم", "منهم", "عندهم", "إليهم")), 1)
          for i in range(1, 21)]


def _ours(chain_text: str = CHAIN) -> str:
    return f'{chain_text} قال رسول الله صلى الله عليه وسلم ‏ "‏ {MATN} ‏"‏ ‏.‏'


def _unit(n: int, chain_text: str = CHAIN) -> Entry:
    return Entry(n, f"{chain_text} قال: «{MATN}» قال الشيخ والحديث ناسخ.", heading="ذكر زيارة القبور")


def _rulings_for(units, hadith, narrators_of):
    conn = sqlite3.connect(":memory:")
    conn.executescript(build_usul._SCHEMA)
    units_of = {kc["book"]: [] for kc in RULINGS["kinds"].values()} | {"shahin": units}
    build_usul.add_rulings(conn, units_of, hadith, narrators_of, SMALL)
    return conn.execute("SELECT collection, number, part, unit FROM ruling ORDER BY collection, number").fetchall(), conn


def test_a_text_match_with_no_narrator_in_common_gets_no_ruling_and_is_listed_as_rejected():
    hadith = [(("abudawud", 1, ""), _ours(), 1), (("muslim", 2, ""), _ours("حدثنا زيد بن ثابت"), 1)]
    narrators_of = {("abudawud", 1, ""): [[names.words("سفيان بن عيينة")]], ("muslim", 2, ""): [[names.words("زيد بن ثابت")]]}
    found, conn = _rulings_for([_unit(7)], hadith + OTHERS, narrators_of)
    assert found == [("abudawud", 1, "", 7)]   # Muslim's text is the same; its chain names another man
    assert ("ruling_match", "shahin: rejected", 0) not in conn.execute("SELECT * FROM gap").fetchall()


def test_the_same_report_in_two_collections_gets_the_ruling_in_both_and_a_repeated_unit_counts_once():
    hadith = [(("abudawud", 1, ""), _ours(), 1), (("nasai", 9, ""), _ours(), 4)]
    narrators_of = {key: [[names.words("سفيان بن عيينة")]] for key, *_ in hadith}
    found, conn = _rulings_for([_unit(7), _unit(7)], hadith + OTHERS, narrators_of)   # the book prints the unit twice
    assert found == [("abudawud", 1, "", 7), ("nasai", 9, "", 7)]
    assert conn.execute("SELECT hbook FROM ruling ORDER BY collection").fetchall() == [(1,), (4,)]


def test_a_rarer_shared_phrase_scores_more_and_a_phrase_in_too_many_hadith_counts_for_nothing():
    docs = {i: ["شيء", "مشترك", "جدا", f"فريد{i}"] for i in range(6)} | {6: ["عبارة", "نادرة", "في", "حديث", "واحد"]}
    index = match.Index(docs, 3)
    assert index.scores(["شيء", "مشترك", "جدا"], df_max=5) == {}   # in 6 hadith: formula
    assert index.scores(["شيء", "مشترك", "جدا"], df_max=6).keys() == set(range(6))
    assert index.scores(["عبارة", "نادرة", "في", "حديث"], df_max=5) == {6: pytest.approx(2 * 1.9459, rel=1e-3)}


def test_the_terms_endpoint_lists_the_kinds_and_pages_their_hadith_and_the_chains_carry_the_quote(paths):  # noqa: F811
    client = TestClient(app)
    assert client.get("/api/usul/terms").json() == []   # usul.db is not built
    build_usul.build()
    db = sqlite3.connect(paths["usul_index_path"])
    db.executemany("INSERT INTO ruling VALUES ('muslim', 24, ?, ?, ?, ?, ?, ?, ?, ?, 5, 60.0)", [
        (1, "", "ilal_ah", "ilal", "أبو حاتم", "قال أبي: هذا حديث منكر.", "باب", "no. 5"),
        (2, "a", "ilal_ah", "ilal", "أبو زرعة", "قال: هو باطل.", "باب", "no. 6"),
        (2, "a", "shahin", "nasikh_chapter", "ابن شاهين", "", "ذكر الناسخ", "p. 9")])
    db.commit()
    db.close()
    terms = client.get("/api/usul/terms").json()
    assert [(t["kind"], t["count"]) for t in terms] == [("nasikh_chapter", 1), ("ilal", 2)] and all(t["say"] for t in terms)
    page = client.get("/api/usul/terms/ilal", params={"offset": 1, "limit": 1}).json()
    assert page == {"kind": "ilal", "total": 2, "items": [{"collection": "muslim", "book": 24, "number": 2, "part": "a"}]}
    assert client.get("/api/usul/terms/nonsense").status_code == 404
    chains = client.get("/api/rijal/chains/muslim/24").json()["rulings"]
    assert chains["1"] == [{"kind": "ilal", "label": RULINGS["kinds"]["ilal"]["label"], "scholar": "أبو حاتم", "quote": "قال أبي: هذا حديث منكر.", "chapter": "باب",
                            "source": rule()["sources"]["ilal_ah"]["label"], "page": "no. 5"}]
    assert [r["kind"] for r in chains["2a"]] == ["nasikh_chapter", "ilal"]
