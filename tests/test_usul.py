"""Weak points on the chains: a narrator's level from his grade, and the notes built from it.

Run on a tiny rijal.db made here: four narrators, two hadith, one mention
written twice at the same place (the case that must not double a note).
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.main import app  # noqa: E402
from backend.scripts import build_rijal, build_usul  # noqa: E402
from backend.services.rijal import store as rijal_store  # noqa: E402
from backend.services.usul import store as usul_store  # noqa: E402
from backend.services.usul.level import level_of  # noqa: E402
from backend.services.usul.rule import rule  # noqa: E402

LEVELS = rule()["levels"]
CHECK_PAGES = build_usul.check_pages   # the fixture below turns the check off; the tests of it turn it back on


@pytest.mark.parametrize("grade, level", [
    ("مجهول الحال", 7),  # the longer term first: not 9
    ("صدوق سيئ الحفظ", 5),  # سيئ and سيء are one word
    ("ضعيف سيء الحفظ", 8),
    ("ثقة ثقة", 2),
    ("متروك متهم بالكذب", 11),
    ("صدوق حسن الحديث", 4),
    ("صدوق رمي بالقدر", 5),
    ("ثقة رمي بالتشيع", 3),  # level 5 falls short of صدوق; a ثقة stays a ثقة
    ("ثقة ثبت قد يخطئ في حديث الثوري", 3),
    ("انفرد بتوثيقه ابن حبان", None),
])
def test_a_grade_reads_to_the_highest_level_its_words_name(grade, level):
    assert level_of(grade, LEVELS)[0] == level


def test_the_words_no_term_took_come_back_as_they_are():
    assert level_of("صدوق حسن الحديث", LEVELS) == (4, ["صدوق"], "حسن الحديث")
    assert level_of("انفرد بتوثيقه ابن حبان", LEVELS) == (None, [], "انفرد بتوثيقه ابن حبان")


# id -> grade; ids 1..4 are ثقة, ضعيف, صدوق سيئ الحفظ, and a grade no term reads.
GRADES = {1: "ثقة", 2: "ضعيف", 3: "صدوق سيئ الحفظ", 4: "انفرد بتوثيقه ابن حبان"}
# (number, part, start, narrator, ord) in muslim book 24; the second row for narrator 2 is a repeat.
MENTIONS = [(1, "", 0, 1, 0), (1, "", 10, 2, 1), (1, "", 10, 2, 2), (1, "", 20, 3, 3), (2, "a", 0, 4, 0), (2, "a", 8, 2, 1)]


@pytest.fixture()
def paths(tmp_path, monkeypatch):
    """A tiny rijal.db, and every module that opens a database pointed at temporary files."""
    books_dir = tmp_path / "books"
    books_dir.mkdir()
    for key in rule()["books"]:
        (books_dir / f"{key}.txt").write_text("#META#Header#End#\n", encoding="utf-8")   # four books with no entries
    where = {"rijal_index_path": tmp_path / "rijal.db", "usul_index_path": tmp_path / "usul.db", "usul_books_dir": books_dir,
             "usul_dir": build_usul.data_path("usul_dir"), "rijal_dir": build_usul.data_path("rijal_dir")}
    # The exemptions name real narrators (al-A'mash, Shu'ba ...), none of whom the four here are.
    monkeypatch.setattr(build_usul, "check_pages", lambda cfg, texts: [])   # the four books here hold none of the quotes
    monkeypatch.setattr(build_usul, "rule", lambda: {**rule(), "tadlis": {**rule()["tadlis"], "unless": []}})
    for module in (rijal_store, usul_store, build_usul):
        monkeypatch.setattr(module, "data_path", where.__getitem__)
    conn = sqlite3.connect(where["rijal_index_path"])
    conn.executescript(build_rijal._SCHEMA)
    conn.executemany("INSERT INTO narrator (id, name_ar, grade_ar) VALUES (?, ?, ?)",
                     [(who, f"راو {who}", grade) for who, grade in GRADES.items()])
    conn.executemany("INSERT INTO mention VALUES ('muslim', 24, ?, ?, ?, ?, ?, ?)",
                     [(number, part, start, start + 5, who, i) for number, part, start, who, i in MENTIONS])
    conn.commit()
    conn.close()
    return where


# The chains rijal.db would send for muslim book 24, built from the same mentions.
CHAINS = {f"{n}{p}": [[start, start + 5, who] for n2, p2, start, who, _ in MENTIONS if (n2, p2) == (n, p)]
          for n, p, *_ in MENTIONS}


def test_notes_are_keyed_by_hadith_and_placed_by_where_the_name_starts(paths):
    build_usul.build()
    found = usul_store.notes("muslim", 24, CHAINS)
    assert found == {
        "1": [{"at": 10, "id": 2, "level": 8, "kind": "weak", "grade": "ضعيف"},
              {"at": 20, "id": 3, "level": 5, "kind": "memory", "grade": "صدوق سيئ الحفظ"}],
        "2a": [{"at": 8, "id": 2, "level": 8, "kind": "weak", "grade": "ضعيف"}],
    }
    assert usul_store.notes("muslim", 25, {}) == {}


def test_a_note_rijal_no_longer_places_there_is_dropped(paths):
    build_usul.build()
    moved = {**CHAINS, "1": [[11, 16, 2], [20, 25, 3]]}  # rijal.db rebuilt: narrator 2 now starts at 11
    assert [n["id"] for n in usul_store.notes("muslim", 24, moved)["1"]] == [3]


def test_a_grade_no_term_reads_is_listed_never_marked(paths):
    build_usul.build()
    db = sqlite3.connect(paths["usul_index_path"])
    assert db.execute("SELECT what, text, count FROM gap WHERE what IN ('left', 'none')").fetchall() == [("none", GRADES[4], 1)]
    assert db.execute("SELECT COUNT(*) FROM narrator_level WHERE narrator_id = 4").fetchone()[0] == 0


def test_a_rebuild_that_swings_the_notes_keeps_the_old_file(paths):
    build_usul.build()
    before = paths["usul_index_path"].read_bytes()
    conn = sqlite3.connect(paths["rijal_index_path"])
    conn.execute("UPDATE narrator SET grade_ar = 'ثقة' WHERE id IN (2, 3)")
    conn.commit()
    conn.close()
    with pytest.raises(SystemExit):
        build_usul.build()
    assert paths["usul_index_path"].read_bytes() == before


def test_the_chains_endpoint_carries_notes_and_the_scale(paths):
    build_usul.build()
    reply = TestClient(app).get("/api/rijal/chains/muslim/24").json()
    assert [n["id"] for n in reply["notes"]["1"]] == [2, 3]
    scale = reply["scale"]
    assert [row["level"] for row in scale] == list(range(1, 13))
    assert [row["weak"] for row in scale] == [False] * 4 + [True] * 8
    assert scale[10]["lift"]["lying"]["lifts"] is False and scale[4]["lift"].keys() == {"memory"}
    assert scale[7]["lift"] == {} and scale[0]["source"] == rule()["sources"]["taqrib"]["label"]


def test_the_chains_endpoint_is_as_before_where_usul_db_is_missing(paths):
    reply = TestClient(app).get("/api/rijal/chains/muslim/24").json()
    assert reply["notes"] == {} and reply["scale"] == [] and reply["ready"] is True
    assert reply["chains"]["1"][1] == [10, 15, 2]


# ---- the narrator books: entries, the year, and the join to a narrator ---------------------------------------------

from backend.services.usul import books, jami, mukhtalitin, names, rung, taqrib, tarif  # noqa: E402
from backend.services.usul.books import Entry  # noqa: E402

TAQRIB = rule()["taqrib"]

SAMPLE_BOOK = """#META# header line
#META#Header#End#

# PageV01P010
### | باب الأول
### $ 1 أحمد بن إبراهيم صدوق من العاشرة
~~مات سنة ست وثلاثين PageV01P011 د
### $ 2 ms003 أحمد بن علي ثقة من
~~الثامنة
# PageV00P000
### $ 3 زيد بن عمرو ثقة
### || تقسيم
# هذا ليس من مدخل
### | باب الثاني
### $ 4 خالد بن سعد مقبول
"""


def test_entries_keep_the_page_each_stands_on_and_drop_the_markers():
    found = books.entries(SAMPLE_BOOK, {"entry": r"^### \$ (?P<n>\d+) ?(?P<text>.*)$"})
    assert [e.n for e in found] == [1, 2, 3, 4]
    assert found[0].text == "أحمد بن إبراهيم صدوق من العاشرة مات سنة ست وثلاثين د"
    # A marker ends its page: entry 1's words before PageV01P011 are on p. 11 (the P010 before them closed the
    # page before); its last word, and entry 2, end at PageV00P000, a page the book lost.
    assert found[0].page_at(0) == "PageV01P011" and found[0].page_at(found[0].text.rindex("د")) == ""
    assert found[1].text == "أحمد بن علي ثقة من الثامنة" and found[1].page_at(0) == ""
    assert found[2].text == "زيد بن عمرو ثقة" and found[2].end_page == ""   # no marker closes it: no page known
    assert found[3].heading == "باب الثاني"
    assert books.page_label("PageV01P073") == "p. 73" and books.page_label("") == ""


def test_a_marker_in_a_heading_or_on_the_next_entrys_line_ends_the_page_of_the_entry_before():
    raw = ("#META#Header#End#\n### $ 1 أول\n### | باب PageV01P020\n### $ 2 ثان\n### $ 3 PageV01P021 ثالث\n"
           "# تتمة PageV02P005\n")
    first, second, third = books.entries(raw, {"entry": r"^### \$ (?P<n>\d+) ?(?P<text>.*)$"})
    assert first.where() == "p. 20" and second.where() == "p. 21"
    assert third.where() == "v2 p. 5" and third.page_at(len(third.text) - 1) == "PageV02P005"


def test_entries_can_be_kept_to_a_chapter_and_cut_where_the_list_ends():
    spec = {"entry": r"^### \$ (?P<n>\d+) ?(?P<text>.*)$", "in_heading": "الثاني", "stop": "مقبول"}
    assert [(e.n, e.text) for e in books.entries(SAMPLE_BOOK, spec)] == [(4, "خالد بن سعد")]


def test_a_numbered_entry_printed_mid_line_opens_only_when_it_is_the_next_number():
    # The Ta'rif prints "(81)" inside entry 80's last line; "(5)" there is not the next number and stays text.
    raw = "#META#Header#End#\n# (80) المحاربي وصفه (5) العقيلي\n~~بالتدليس (81) عبد العزيز القرشي (82) الجدعاني\n"
    spec = {"entry": r"^# \((?P<n>[1-9]\d*)\) ?(?P<text>.*)$", "inline": r"\((?P<n>[1-9]\d*)\)"}
    assert [(e.n, e.text) for e in books.entries(raw, spec)] == [
        (80, "المحاربي وصفه (5) العقيلي بالتدليس"), (81, "عبد العزيز القرشي"), (82, "الجدعاني")]


@pytest.mark.parametrize("text, year, why", [
    ("ثقة من الثالثة مات سنة تسع وعشرين ومائة د", 129, ""),
    ("ثقة من العاشرة مات سنة ثلاث عشرة خ", 13, ""),
    ("مات سنة اثنتين وأربعين وقد نيف على التسعين ع", 42, ""),
    ("مات سنة خمسين ق", 50, ""),
    ("مات سنة تسع وستين ومائتين د", 269, ""),
    ("مات سنة سبع عشرة أو بعدها خ", None, "doubt"),     # the book itself is not sure
    ("مات سنة 197 خ ت ق", None, "digits"),
    ("مات سنة بضع وخمسين خ", None, "unreadable"),
    ("مات بعد الخمسين ق", None, "no_clause"),
])
def test_the_death_year_is_read_only_in_its_plain_form(text, year, why):
    assert taqrib.death_year(text, TAQRIB["death"]["doubt"]) == (year, why)


def test_a_year_without_hundreds_takes_them_from_the_generation_the_preface_names_except_where_it_cannot():
    bands = TAQRIB["death"]["bands"]
    assert [taqrib.hijri(36, g, bands) for g in (2, 5, 8, 10)] == [36, 136, 136, 236]
    assert taqrib.hijri(129, 3, bands) == 129 and taqrib.hijri(269, 12, bands) == 269
    assert taqrib.hijri(95, 3, bands) is None and taqrib.hijri(56, 4, bands) is None   # first or second century: not read


def _row(who, lineage, generation, grade, nisba="", name=None):
    return {"id": who, "name_ar": name or lineage, "lineage_ar": lineage, "nisba_ar": nisba, "kunya_ar": "",
            "grade_ar": grade, "generation_ar": generation}


def _joined(rows, *entry_texts):
    parsed = {i: taqrib.parse(t, TAQRIB) for i, t in enumerate(entry_texts)}
    return taqrib.join(parsed, [names.person(r) for r in rows], TAQRIB, 3)


def test_the_taqrib_join_wants_name_generation_and_grade_to_agree():
    rows = [_row(1, "الحسين بن واقد", "السابعة", "ثقة"), _row(2, "حسين بن واقد", "السادسة", "ثقة"),
            _row(3, "خالد بن سعد", "الثالثة", "صدوق")]
    joined, gaps = _joined(rows,
                           "الحسين بن واقد المروزي ثقة من السابعة مات سنة تسع وخمسين د",   # 1: name, generation, grade
                           "خالد بن سعد الكوفي ثقة من الثالثة م",                          # grade differs: not joined
                           "خالد بن سعد الكوفي صدوق من الرابعة م")                         # generation differs: not joined
    assert joined == {0: 1} and gaps == {1: "none", 2: "none"}


def test_the_taqrib_join_rejects_two_candidates():
    rows = [_row(1, "محمد بن عبد الله", "السابعة", "ثقة"), _row(2, "محمد بن عبد الرحمن", "السابعة", "ثقة"),
            _row(3, "محمد بن عبد الله", "السابعة", "ثقة")]   # the same man twice: nothing says which is meant
    joined, gaps = _joined(rows, "محمد بن عبد الله بن زيد ثقة من السابعة د")
    assert joined == {} and gaps == {0: "many"}


def test_two_entries_never_share_one_narrator():
    rows = [_row(1, "أحمد بن علي", "الثامنة", "ثقة")]
    joined, gaps = _joined(rows, "أحمد بن علي بن ثابت ثقة من الثامنة د", "أحمد بن علي بن زيد ثقة من الثامنة س")
    assert joined == {} and gaps == {0: "shared", 1: "shared"}


def test_an_entry_with_no_generation_is_listed_not_guessed():
    joined, gaps = _joined([_row(1, "أبي بن كعب", "الأولى", "صحابي")], "أبي بن كعب بن قيس صحابي سيد القراء")
    assert joined == {} and gaps == {0: "no_generation"}


def test_a_name_keeps_its_compound_words_whole_so_abd_allah_and_abd_al_rahman_differ():
    assert names.words("محمد بن عبد الله") == ("محمد", "بن", "عبد الله")
    assert names.words("محمد بن عبد الله")[:3] != names.words("محمد بن عبد الرحمن")[:3]
    assert names.words("أبا بكر بن عياش")[0] == names.words("أبو بكر بن عياش")[0]   # أبا and أبو are one word, with its next


# ---- Ta'rif: a name joins only with a nisba of his beside it -------------------------------------------------------

def _people(*rows):
    return [names.person(r) for r in rows]


def test_the_tarif_join_wants_a_nisba_and_one_narrator():
    people = _people(_row(1, "قتادة بن دعامة", "الرابعة", "ثقة", nisba="السدوسي، البصري"),
                     _row(2, "عمرو بن عبد الله", "الثالثة", "ثقة", nisba="السبيعي، الكوفي"),
                     _row(3, "عمرو بن عبد الله", "السادسة", "ثقة", nisba="النخعي، الكوفي"))
    joined, gaps = tarif.join({
        10: names.words("قتادة بن دعامة السدوسي تابعي مشهور"),   # joins narrator 1
        11: names.words("قتادة بن دعامة تابعي مشهور"),           # no nisba of his beside it
        12: names.words("عمرو بن عبد الله كوفي"),                # the nisba كوفي is shared by two men
        13: names.words("عمرو بن عبد الله سبيعي"),               # would be narrator 2, but entry 12 also reached him
    }, people, 3, 12)
    assert joined == {10: 1} and gaps == {11: "none", 12: "many", 13: "shared"}
    assert tarif.join({13: names.words("عمرو بن عبد الله سبيعي")}, people, 3, 12)[0] == {13: 2}


def test_the_tarif_lineage_it_writes_tells_men_of_one_short_name_apart():
    people = _people(_row(1, "محمد بن مسلم بن عبيد الله بن عبد الله بن شهاب", "الرابعة", "ثقة", nisba="الزهري، المدني", name="ابن شهاب"),
                     _row(2, "محمد بن مسلم بن السائب بن خباب", "الخامسة", "مقبول", nisba="المدني"),
                     _row(3, "محمد بن مسلم بن السائب بن أبي بكر", "الخامسة", "مقبول", nisba="المدني"),
                     _row(4, "محمد بن مسلم بن تدرس", "الرابعة", "صدوق", nisba="المدني"))
    one = {10: names.words("محمد بن مسلم بن عبيد الله بن شهاب الزهري المدني الفقيه")}   # one man's lineage (a book may skip an ancestor)
    assert tarif.join(one, people, 3, 12) == ({10: 1}, {})
    assert tarif.join({13: names.words("محمد بن مسلم بن السائب بن خباب المدني")}, people, 3, 12)[0] == {13: 2}
    # the nearest case: the lineage written fits two men, or none is written, so nothing tells them apart
    assert tarif.join({11: names.words("محمد بن مسلم بن السائب المدني مشهور")}, people, 3, 12) == ({}, {11: "many"})
    assert tarif.join({12: names.words("محمد بن مسلم المدني مشهور")}, people, 3, 12) == ({}, {12: "many"})


# ---- a chain's links: a possible tadlis, a scholar's "did not hear" ------------------------------------------------

MUSADDAD, YAHYA, QATADA, ANAS, SHUBA, LAYTH, ABU_ZUBAIR, JABIR = range(1, 9)
TADLIS = rule()["tadlis"]
JAMI = rule()["jami"]


def _rungs(text, *who):
    """The rungs of a chain written in `text`, each (name, narrator id) found in order."""
    found, at = [], 0
    for name, narrator in who:
        start = text.index(name, at)
        found.append((start, start + len(name), narrator))
        at = start + len(name)
    return rung.rungs(text, found)[0]


def _tadlis_of(word, collection="abudawud", level=3, exempt=(), strand="يحيى"):
    """What the rung Qatada -> Anas gets when Qatada says `word` and `strand` is the narrator below Qatada."""
    below = {"يحيى": YAHYA, "شعبة": SHUBA}[strand]
    text = f"حدثنا مسدد حدثنا {strand} عن قتادة {word} أنس قال قال رسول الله صلى الله عليه وسلم كذا"
    last = _rungs(text, ("مسدد", MUSADDAD), (strand, below), ("قتادة", QATADA), ("أنس", ANAS))[-1]
    assert (last.student, last.teacher, last.word) == (QATADA, ANAS, word)
    return rung.tadlis(last, collection, level, TADLIS, list(exempt))


def test_a_level_3_teller_saying_an_in_abu_dawud_gets_a_tadlis_note():
    assert _tadlis_of("عن") == ("tadlis", "")
    assert _tadlis_of("عن", level=4) == ("tadlis", "")


def _said(word):
    return rung.Rung(student=QATADA, teacher=ANAS, at=30, word=word, below=frozenset())


def test_a_level_3_teller_saying_anna_gets_the_unclear_note_and_qala_the_same_as_an():
    # chain_of ends a chain at أن and قال unless a word of passing on follows, so a chain's own text gives neither
    # as a rung's last word; the rule is read on the rung itself.
    assert rung.tadlis(_said("أن"), "abudawud", 3, TADLIS, []) == ("tadlis_unclear", "")
    assert rung.tadlis(_said("قال"), "abudawud", 4, TADLIS, []) == ("tadlis", "")


def test_anna_then_a_word_of_hearing_after_the_name_is_hearing():
    # Abu Dawud 73: قتادة أن محمد بن سيرين حدثه عن أبي هريرة. حدثه is Ibn Sirin telling Qatada; أن is no rung word.
    text = "حدثنا مسدد حدثنا يحيى عن قتادة أن أنس حدثه عن جابر قال قال رسول الله صلى الله عليه وسلم كذا"
    found = _rungs(text, ("مسدد", MUSADDAD), ("يحيى", YAHYA), ("قتادة", QATADA), ("أنس", ANAS), ("جابر", JABIR))
    assert [(r.student, r.teacher, r.word) for r in found[-2:]] == [(QATADA, ANAS, "حدثه"), (ANAS, JABIR, "عن")]
    assert rung.tadlis(found[-2], "abudawud", 3, TADLIS, []) == (None, "heard")


@pytest.mark.parametrize("word", ["حدثنا", "أخبرنا", "سمعت"])
def test_a_word_of_hearing_gets_no_note(word):
    assert _tadlis_of(word) == (None, "heard")


def test_no_note_in_bukhari_or_muslim_and_none_for_a_teller_the_tarif_tolerates():
    assert _tadlis_of("عن", collection="bukhari") == (None, "sahih")
    assert _tadlis_of("عن", collection="muslim") == (None, "sahih")
    assert _tadlis_of("عن", level=2) == (None, "tolerated")
    assert _tadlis_of("عن", level=None) == (None, "not_mudallis")


def test_no_note_when_shuba_stands_below_the_teller_and_one_when_another_does():
    shuba = [{"tellers": {QATADA}, "via": SHUBA, "teacher": None}]
    assert _tadlis_of("عن", exempt=shuba, strand="شعبة") == (None, "exempt")
    assert _tadlis_of("عن", exempt=shuba, strand="يحيى") == ("tadlis", "")


def test_no_note_when_al_layth_is_below_abu_al_zubair_and_the_teacher_is_jabir():
    layth = [{"tellers": {ABU_ZUBAIR}, "via": LAYTH, "teacher": JABIR}]
    text = "حدثنا مسدد حدثنا الليث عن أبي الزبير عن جابر قال قال رسول الله صلى الله عليه وسلم كذا"
    who = [("مسدد", MUSADDAD), ("الليث", LAYTH), ("أبي الزبير", ABU_ZUBAIR), ("جابر", JABIR)]
    last = _rungs(text, *who)[-1]
    assert rung.tadlis(last, "abudawud", 3, TADLIS, layth) == (None, "exempt")
    other = [{"tellers": {ABU_ZUBAIR}, "via": LAYTH, "teacher": ANAS}]   # the same man below, a different teacher
    assert rung.tadlis(last, "abudawud", 3, TADLIS, other) == ("tadlis", "")


def test_a_ruling_name_must_stand_for_exactly_one_narrator():
    people = _people(_row(1, "عمرو بن عبد الله", "الثالثة", "ثقة", nisba="السبيعي، الكوفي"),
                     _row(2, "عمرو بن عبد الله", "السادسة", "ثقة", nisba="النخعي، الكوفي"))
    assert tarif.resolve("عمرو بن عبد الله السبيعي", people, 3, 12) == 1
    with pytest.raises(ValueError):
        tarif.resolve("عمرو بن عبد الله الكوفي", people, 3, 12)


ANAS_FORMS = (names.flat("أنس بن مالك"), names.flat("أنس"))
JAMI_ENTRY = Entry(n=1, end_page="PageV01P150",
                   text="قتادة بن دعامة السدوسي قال أبو حاتم لم يسمع من أنس بن مالك وقال شعبة لم يسمع من أنس إلا حديثا "
                        "وقال أحمد لم يسمع من سعيد بن المسيب")


def test_a_not_heard_pair_is_made_only_from_the_narrators_own_teachers():
    found, left = jami.pairs([(QATADA, JAMI_ENTRY, [(ANAS, ANAS_FORMS)])], JAMI)
    assert [(p.student, p.teacher, p.kind, p.scholar, p.quote, p.page) for p in found] == [
        (QATADA, ANAS, "not_heard", "أبو حاتم", "قال أبو حاتم لم يسمع من أنس بن مالك", "p. 150")]
    # "إلا حديثا" qualifies the no, so it is left out; سعيد is no teacher of his in tie: listed, not guessed.
    assert left == {("not_heard", "qualified"): 1, ("not_heard", "none"): 1}


def test_a_name_that_goes_on_past_the_teachers_is_another_man_not_a_prefix_of_him():
    entry = Entry(n=3, text="وهب بن منبه قال ابن معين لم يلق جابر بن سمرة إنما هو كتاب")
    jabir = [(8, (names.flat("جابر بن عبد الله الأنصاري"),))]
    vocab = frozenset(names.flat("جابر بن عبد الله سمرة منبه"))
    found, left = jami.pairs([(9, entry, jabir)], JAMI, vocab)
    assert found == [] and left == {("not_met", "longer"): 1}
    found, _ = jami.pairs([(9, Entry(n=3, text="وهب بن منبه قال ابن معين لم يلق جابر بن عبد الله إنما هو كتاب"), jabir)], JAMI, vocab)
    assert [(p.teacher, p.quote) for p in found] == [(8, "قال ابن معين لم يلق جابر بن عبد الله")]


def test_an_entry_the_book_repeats_does_not_double_a_pair():
    found, _ = jami.pairs([(QATADA, JAMI_ENTRY, [(ANAS, ANAS_FORMS)]), (QATADA, JAMI_ENTRY, [(ANAS, ANAS_FORMS)])], JAMI)
    assert len(found) == 1


def test_a_scholar_is_named_only_from_name_words_that_follow_qala_directly():
    teachers = [(ANAS, ANAS_FORMS)]
    vocab = frozenset(names.flat("أبو حاتم قتادة بن دعامة أنس بن مالك"))   # the words of names, folded as names are
    for said, scholar in (("قال أبو حاتم لم يسمع من أنس", "أبو حاتم"),
                          ("قال أبو حاتم رأى فلانا ولم يسمع من أنس", ""),    # the statement is not what he said
                          ("قال فيه أبو حاتم لم يسمع من أنس", "")):          # فيه is no name word
        found, _ = jami.pairs([(QATADA, Entry(n=9, text="قتادة بن دعامة " + said), teachers)], JAMI, vocab)
        assert [p.scholar for p in found] == [scholar], said


def test_a_scholar_is_named_only_where_the_clause_does_not_mix_in_the_mans_own_name():
    entry = Entry(n=2, text="عبد الكريم بن مالك قال الدارقطني عبد الكريم لم يدرك المستورد")   # no page: the entry's number stands
    found, _ = jami.pairs([(9, entry, [(8, (names.flat("المستورد بن شداد"),))])], JAMI)
    assert [(p.kind, p.scholar, p.page) for p in found] == [("not_reached", "", "no. 2")]   # the quote still carries the words


def test_a_mukhtalitin_heading_must_agree_in_nisba_where_it_goes_past_the_name():
    people = _people(_row(1, "إبراهيم بن العباس", "العاشرة", "ثقة", nisba="الحجازي"),
                     _row(2, "أبان بن صمعة", "السابعة", "صدوق", nisba="الأنصاري"))
    entries = {1: Entry(n=1, text="x", head="إبراهيم بن العباس السامري"), 2: Entry(n=2, text="y", head="أبان بن صمعة")}
    assert mukhtalitin.join(entries, people, 3, 12) == ({2: 2}, {1: "none"})


# ---- the endpoints --------------------------------------------------------------------------------------------------

def test_the_chains_endpoint_carries_links_where_rijal_still_places_them(paths):
    build_usul.build()
    db = sqlite3.connect(paths["usul_index_path"])
    db.executemany("INSERT INTO link VALUES ('muslim', 24, ?, ?, ?, ?, '', ?, ?, 'عن', 3, '', '', '', '')",
                   [(1, "", 10, "tadlis", 1, 2), (1, "", 11, "tadlis", 1, 2), (1, "", 20, "tadlis", 9, 3)])
    db.commit()
    db.close()
    reply = TestClient(app).get("/api/rijal/chains/muslim/24").json()
    assert [(link["at"], link["student"], link["teacher"]) for link in reply["links"]["1"]] == [(10, 1, 2)]   # 11 and 9 are placed nowhere
    assert reply["link_rules"]["levels"]["3"]["page"] == books.page_label(rule()["tadlis"]["levels"]["3"]["page"]) and "tadlis_unclear" in reply["link_rules"]["kinds"]
    assert "skip" not in reply["link_rules"]   # no note is ever shown in the Sahihs, so their reason is not sent


def test_a_narrators_page_carries_what_the_books_say_grouped_with_their_book(paths):
    build_usul.build()
    db = sqlite3.connect(paths["usul_index_path"])
    db.executemany("INSERT INTO narrator_fact VALUES (2, ?, ?, ?, ?, ?, ?)", [
        ("habits", "not_heard", "راو 3", "لم يسمع من راو 3", "jami", "p. 150"),
        ("habits", "tadlis", "3", "ترجمته", "tarif", "p. 40"),
        ("life", "death_hundreds", "136", "مات سنة ست وثلاثين", "taqrib", "p. 9")])
    db.commit()
    db.close()
    reply = TestClient(app).get("/api/rijal/narrators/2").json()["usul"]
    assert reply["source"]["confidence"] == "derived"
    assert reply["habits"][0]["ar"] == "راو 3" and reply["habits"][0]["book"] == rule()["sources"]["jami"]["label"]
    assert reply["habits"][1]["rule"]["page"] == books.page_label(rule()["tadlis"]["levels"]["3"]["page"]) and reply["life"][0]["rule"]["quote"] == rule()["taqrib"]["death"]["quote"]
    assert [(line["text"], line["ar"], line["page"]) for line in reply["reliability"]] == [
        ("Level 8 of 12, Weak", "ضعيف", "")]   # no entry joined: his sunnah.com grade, not a Taqrib page
    assert [line["text"] for line in reply["books"]] == [   # narrator 2 is named once in hadith 1 (twice at one place) and in 2a
        "Named in 2 of our hadith", "Part of 2 hadith with a weak point on the chain"]


def test_a_narrator_page_has_empty_groups_where_usul_db_is_missing(paths):
    reply = TestClient(app).get("/api/rijal/narrators/2").json()["usul"]
    assert {k: v for k, v in reply.items() if k != "source"} == {"reliability": [], "habits": [], "life": [], "books": []}


# Page 10 ends at the first marker, 11 at the second: the quote's words stand on the page whose marker follows them.
PAGED = ("#META#Header#End#\n# وقال المصنف ثقة\n~~ثبت ms004 حافظ PageV01P010\n# ومن بعد ذلك مسألة أخرى PageV01P011\n"
         "# تتمة النص كله PageV01P012\n")
VERIFY = rule()["verify"]


@pytest.mark.parametrize("quote, page", [
    ("وَقَالَ المصنف ثقة ثبت", "PageV01P010"),   # across a line wrap, a word-count marker and a diacritic
    ("حافظ ومن بعد ذلك مسألة", "PageV01P010-11"),   # across a page marker: both pages
    ("وقال ... مسألة أخرى", "PageV01P010-11"),   # an elision: each part found in order
    ("تتمة النص", "PageV01P012"),
    ("ليس في الكتاب", None),
])
def test_a_quote_is_located_by_its_letters_and_gets_the_page_or_pages_whose_markers_close_it(quote, page):
    assert books.locate(PAGED, quote, VERIFY) == page


def test_an_elisions_parts_must_lie_close_together_and_a_page_the_book_lost_is_empty_not_missing():
    assert books.locate(PAGED, "وقال ... تتمة", VERIFY) == "PageV01P010-12"
    assert books.locate(PAGED, "وقال ... تتمة", {**VERIFY, "gap": 5}) is None
    assert books.locate("#META#Header#End#\n# نص ضائع PageV00P000\n", "نص ضائع", VERIFY) == ""


def test_the_check_names_each_quote_whose_config_page_is_not_the_books_with_the_page_the_book_gives():
    cfg = {"verify": VERIFY,
           "rule": {"quote": "ثقة ثبت", "book": "k", "page": "PageV01P011"},
           "kept": {"quote": "تتمة النص", "book": "k", "page": "PageV01P012"},
           "gone": {"quote": "ليس في الكتاب", "book": "k", "page": "PageV01P012"}}
    assert CHECK_PAGES(cfg, {"k": PAGED}) == [
        "rule: book k, config 'PageV01P011', derived 'PageV01P010'",
        "gone: book k, config 'PageV01P012', derived not found"]
    cfg["rule"]["page"], cfg["gone"]["page"] = "PageV01P010", "PageV01P011"
    cfg["gone"]["quote"] = "ومن بعد ذلك"
    assert CHECK_PAGES(cfg, {"k": PAGED}) == []


def test_a_build_whose_books_do_not_hold_the_configs_quotes_stops_before_building(paths, monkeypatch):
    monkeypatch.setattr(build_usul, "check_pages", CHECK_PAGES)
    with pytest.raises(SystemExit, match=r"taqrib\.death: book taqrib, config 'PageV01P0\d+', derived not found"):
        build_usul.build()
    assert not paths["usul_index_path"].exists()

