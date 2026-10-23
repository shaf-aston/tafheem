"""Narrators of the hadith chains: where each is named in our Arabic, and his sheet.

Run on trimmed copies of real sunnah.com pages (tests/fixtures/rijal): Sahih
Muslim 1620a and 1625j, and Malik ibn Anas's narrator page. 1625j names Abu
Bakr ibn Abi Shayba twice in one chain, the case a plain "find the name" gets
wrong by landing both on the first.
"""
from __future__ import annotations

import re
import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.main import app  # noqa: E402
from backend.scripts import build_rijal  # noqa: E402
from backend.services.arabic_text import strip_diacritics  # noqa: E402
from backend.services.hadith import loader  # noqa: E402
from backend.services.hadith.rijal import cache, parse, store  # noqa: E402

FIXTURES = Path(__file__).parent / "fixtures" / "rijal"
OURS = json.loads((FIXTURES / "arabic.json").read_text(encoding="utf-8"))
BOOK = (FIXTURES / "book-muslim-24.html").read_text(encoding="utf-8")
MALIK = (FIXTURES / "narrator-6659.html").read_text(encoding="utf-8")


def _placed(ref: str) -> list[tuple[int, int, int]]:
    chain = next(c for c in parse.book_chains(BOOK) if f"{c['number']}{c['part']}" == ref)
    placed, lost = parse.place(OURS[ref], chain["names"])
    assert lost == []
    return placed


def _read(ref: str) -> list[tuple[str, int]]:
    return [(strip_diacritics(OURS[ref][start:end]), who) for start, end, who, _ in _placed(ref)]


def test_offsets_slice_our_arabic_to_the_right_names():
    assert _read("1620a") == [
        ("عبد الله بن مسلمة بن قعنب", 5085), ("مالك بن أنس", 6659), ("زيد بن أسلم", 3122),
        ("أبيه", 549), ("عمر بن الخطاب", 5913),
    ]


def test_a_name_twice_in_one_chain_lands_twice_in_order():
    found = _placed("1625j")
    shayba = [at for at in found if at[2] == 5049]
    assert len(shayba) == 2 and shayba[0][1] < shayba[1][0]
    assert OURS["1625j"][shayba[0][0]:shayba[0][1]] == OURS["1625j"][shayba[1][0]:shayba[1][1]]
    assert [at[0] for at in found] == sorted(at[0] for at in found)


def test_malik_is_graded_first_rank_of_the_seventh_generation():
    malik = parse.narrator(MALIK)
    assert (malik["grade_rank"], malik["generation_ar"]) == (1, "السابعة")
    assert malik["name_ar"] == "مالك بن أنس الأصبحي" and malik["hadith_total"] == 1341


@pytest.fixture()
def built(tmp_path, monkeypatch):
    """The two fixture hadith and Malik's page put through the real build, into a temporary rijal.db."""
    paths = {"rijal_pages_dir": tmp_path / "pages", "rijal_index_path": tmp_path / "rijal.db",
             "rijal_dir": build_rijal.data_path("rijal_dir")}
    for module in (cache, store, build_rijal):
        monkeypatch.setattr(module, "data_path", paths.__getitem__)
    monkeypatch.setattr(loader, "hadiths", lambda *_: [
        {"number": int(ref[:-1]), "part": ref[-1], "arabic": arabic} for ref, arabic in OURS.items()])
    monkeypatch.setattr(loader, "collection_name", {"muslim": "Sahih Muslim"}.get)
    cache.write(cache.book_path("muslim", 24), BOOK)
    cache.write(cache.narrator_path(6659), MALIK)
    build_rijal.build()
    return TestClient(app)


def test_a_classical_text_keeps_its_lines_and_book_letters():
    text = parse.narrator(MALIK)["texts"][0]
    blocks = text[2]
    assert blocks[0]["kind"] == "title" and blocks[0]["runs"][0]["t"].startswith("مالك بن أنس")
    assert any(b["kind"] == "label" for b in blocks)
    page = '<div class="accordion"><div class="accordion-title">T</div><div class="accordion-body"><ul><li>بكر بن وائل '
    page += '<a class="sigla-link" title="Sahih Muslim">م</a> وهو أصغر منه</li></ul><p>وقال <span class="tarjama-scholar">العجلي:</span> '
    page += '<span class="tarjama-verdict">ثقة</span></p></div></div>'
    item, said = parse.narrator(page)["texts"][0][2]
    assert item == {"kind": "item", "runs": [{"t": "بكر بن وائل "}, {"t": "م", "role": "mark", "title": "Sahih Muslim"},
                                             {"t": " وهو أصغر منه"}]}
    assert [r.get("role") for r in said["runs"]] == [None, "scholar", None, "verdict"]


def test_a_classical_text_keeps_the_space_between_two_quotes_and_reads_a_nested_block_once():
    page = '<div class="accordion"><div class="accordion-title">T</div><div class="accordion-body"><p>قال '
    page += '<span class="tarjama-scholar">أحمد:</span> <span class="tarjama-verdict">ثقة</span> '
    page += '<span class="tarjama-scholar">يحيى:</span> <span class="tarjama-verdict">صدوق</span></p>'
    page += '<ul><li><p>روى عن نافع</p></li></ul></div></div>'
    said, item = parse.narrator(page)["texts"][0][2]
    assert "".join(r["t"] for r in said["runs"]) == "قال أحمد: ثقة يحيى: صدوق"
    assert item == {"kind": "item", "runs": [{"t": "روى عن نافع"}]}


def test_a_name_is_placed_on_a_whole_word_not_inside_a_longer_one():
    placed, lost = parse.place("حدثنا مَعْمَر عن عمر", [(1, "عمر", 6, True)])
    assert placed == [(17, 20, 1, True)] and not lost
    placed, _ = parse.place("حدثنا شعبة وعمر", [(2, "عمر", 10, True)])
    assert placed == [(12, 15, 2, True)]


def test_only_the_english_has_its_ayn_set_and_the_arabic_is_untouched():
    page = '<h1 class="hero-title">`Urwa</h1><h1 class="hero-title arabic">عروة — `</h1>'
    found = parse.narrator(page)
    assert (found["name_en"], found["name_ar"]) == ("ʿUrwa", "عروة — `")


def test_the_book_endpoint_gives_slices_that_read_as_names(built):
    reply = built.get("/api/rijal/chains/muslim/24").json()
    assert reply["ready"] is True and reply["source"]["key"] == "rijal"
    text = OURS["1620a"]
    assert [(strip_diacritics(text[a:b]), who) for a, b, who in reply["chains"]["1620a"]][3] == ("أبيه", 549)
    assert built.get("/api/rijal/chains/nosuchbook/1").status_code == 404
    assert built.get("/api/rijal/chains/muslim/999").json()["chains"] == {}   # a book of a known collection with no chains


def test_a_narrator_sheet_carries_grade_generation_and_his_circle(built):
    sheet = built.get("/api/rijal/narrators/6659").json()
    assert (sheet["grade_rank"], sheet["generation_ar"]) == (1, "السابعة")
    assert sheet["teachers"] and sheet["students"] and sheet["verdicts"]
    city = next(f for f in sheet["facts"] if f["label_ar"] == "بلد الإقامة")
    assert city["label_en"] == "Cities/Regions" and city["en"] and city["ar"] == sheet["city_ar"]
    assert all(b["en"] and b["ar"] for b in sheet["books"])
    assert built.get("/api/rijal/narrators/1").status_code == 404
    assert built.get("/api/rijal/narrators/6659/hadith").json() == [{"collection": "muslim", "book": 24, "number": 1620, "part": "a", "opening": ""}]


def test_search_finds_a_narrator_by_unpointed_arabic_or_english(built):
    assert [n["id"] for n in built.get("/api/rijal/search", params={"q": "مالك أنس"}).json()["narrators"]] == [6659]
    assert [n["id"] for n in built.get("/api/rijal/search", params={"q": "malik"}).json()["narrators"]] == [6659]
    # The ayn (ʿAisha, al-ʿAdawi) is not typed: plain letters still find the name.
    assert [n["id"] for n in built.get("/api/rijal/search", params={"q": "aisha"}).json()["narrators"]] == [4049]
    assert 5913 in [n["id"] for n in built.get("/api/rijal/search", params={"q": "adawi"}).json()["narrators"]]


def test_a_teacher_known_only_from_lists_is_marked_as_not_fetched(built):
    assert built.get("/api/rijal/narrators/6659").json()["fetched"] is True
    assert built.get("/api/rijal/narrators/4049").json()["fetched"] is False


def test_a_link_ending_in_a_space_still_lands_before_the_next_word():
    page = ('<div class="actualHadithContainer"><table class="hadith_reference"><a href="/bukhari:6481">r</a></table>'
            '<div class="arabic_hadith_full">عَنْ <a href="/narrator/3260">أَبِي سَعِيدٍ ـ </a>رضى الله عنه</div></div>')
    names = parse.book_chains(page)[0]["names"]
    placed, lost = parse.place("عَنْ أَبِي سَعِيدٍ ـ رضى الله عنه", names)
    assert lost == [] and placed == [(5, 20, 3260, True)]


def test_a_name_said_again_in_the_story_lands_where_sunnah_links_it():
    text = "سَمِعْتُ الْحَسَنَ يَقُولُ وَلَقَدْ سَمِعْتُ أَبَا بَكْرَةَ يَقُولُ إِنَّ ابْنِي هَذَا سَيِّدٌ يَعْنِي الْحَسَنَ"
    later = len(re.sub(r"\s", "", text[:text.rindex("الْحَسَنَ")]))
    placed, _ = parse.place(text, [(1281, "الْحَسَنَ", later, True)])
    assert placed == [(text.rindex("الْحَسَنَ"), len(text), 1281, True)]


def test_family_meets_the_viewed_chain():
    from backend.services.hadith.rijal.family import meet
    viewed = [1, 2, 3, 4]
    assert meet([9, 2], viewed) == ([9], 2, [3, 4])  # stops early, borrows the rest
    assert meet([7, 8], viewed) == ([7, 8], None, [])  # fully its own
    assert meet([5, 5, 3], [1, 3, 3, 4]) == ([5, 5], 3, [3, 4])  # a repeated narrator


def test_the_family_endpoint_lays_each_narration_against_the_viewed_one_and_one_narration_is_404(built, monkeypatch):
    chain = lambda *ids: [{"id": i, "name": f"n{i}"} for i in ids]  # noqa: E731
    monkeypatch.setattr(store, "family", lambda c, n: [
        {"part": "a", "book": 24, "narrators": chain(5085, 6659, 3122, 549, 5913), "said": "x"},
        {"part": "b", "book": 24, "narrators": chain(777, 3122, 5913), "said": "y"}] if n == 1620 else chain(1)[:0])
    reply = built.get("/api/rijal/family/muslim/1620", params={"part": "a"}).json()
    ids = lambda people: [p["id"] for p in people]  # noqa: E731
    a, b = reply["parts"]
    assert reply["viewed"] == "a" and (ids(a["own"]), a["meet"]["id"], ids(a["borrowed"])) == ([], 5085, [6659, 3122, 549, 5913])
    assert (ids(b["own"]), b["meet"]["id"], ids(b["borrowed"])) == ([777], 3122, [549, 5913])
    assert "narrators" not in b
    assert built.get("/api/rijal/family/muslim/99999999").status_code == 404
    monkeypatch.setattr(store, "family", lambda c, n: [{"part": "", "book": 24, "narrators": chain(1), "said": ""}])
    assert built.get("/api/rijal/family/muslim/1620").status_code == 404


def test_the_narrator_list_ranks_by_hadith_and_filters_by_generation(built):
    page = built.get("/api/rijal/narrators").json()
    counts = [n["hadith_count"] for n in page["items"]]
    assert page["total"] == len(counts) >= 2 and counts == sorted(counts, reverse=True)
    top = next(n for n in page["items"] if n["id"] == 6659)
    assert top["hadith_count"] == 1 and top["generation_ar"] == "السابعة"
    assert [g["key"] for g in page["generations"]][0] == "companions"
    mine = built.get("/api/rijal/narrators", params={"generation": "students"}).json()
    assert 6659 in [n["id"] for n in mine["items"]] and mine["total"] < page["total"]
    assert built.get("/api/rijal/narrators", params={"offset": page["total"]}).json()["items"] == []


def test_a_hadith_opens_where_its_chain_ends_not_after_a_name_in_its_story():
    text = "حدثنا مالك، عن نافع، عن ابن عمر، أن رسول الله صلى الله عليه وسلم قال: لا يبع بعضكم على بيع الحسن"
    # الحسن at the very end is a linked name too; the last mention is not where the chain stops.
    assert store._said(text, len(text)).startswith("أن رسول الله")


def test_a_name_in_the_story_is_told_from_the_chain_by_the_pages_own_markup():
    page = ('<div class="actualHadithContainer"><table class="hadith_reference"><tr><td><a href="/muslim:7">x</a></td></tr></table>'
            '<div class="arabic_hadith_full"><span class="arabic_sanad">حدثنا <a href="/narrator/1">يحيى</a> قال</span> '
            '<span class="arabic_text_details">ذكر <a href="/narrator/2">الحسن</a></span></div></div>')
    names = parse.book_chains(page)[0]["names"]
    assert [(who, in_chain) for who, _, _, in_chain in names] == [(1, True), (2, False)]
    plain = page.replace("arabic_sanad", "x").replace("arabic_text_details", "y")
    assert all(n[3] for n in parse.book_chains(plain)[0]["names"])  # not wrapped: nothing is guessed to be story


def test_a_name_is_placed_whichever_order_its_marks_are_written_in():
    name = "\u0627\u0644\u062e\u0637{}\u0627\u0628"  # الخطّاب, its ط carrying shadda and fatha
    ours = "\u0633\u0645\u0639\u062a " + name.format("\u0651\u064e")  # shadda then fatha, as our text has it
    placed, lost = parse.place(ours, [(5913, name.format("\u064e\u0651"), 4, True)])  # the page: fatha then shadda
    assert lost == [] and ours[placed[0][0]:placed[0][1]] == name.format("\u0651\u064e")


def test_two_names_never_take_the_same_place_and_a_particle_may_be_attached():
    placed, lost = parse.place("حدثنا عمر وعمر", [(1, "عمر", 0, True), (2, "عمر", 0, True)])
    assert [(a, b) for a, b, *_ in placed] == [(6, 9), (11, 14)] and lost == []
    placed, lost = parse.place("قال بمالك ولعمر", [(1, "مالك", 3, True), (2, "عمر", 8, True)])
    assert len(placed) == 2 and lost == []


def test_a_fact_one_language_lacks_does_not_shift_the_others():
    assert parse._paired(["a", "b"], ["x", "y"]) == [("a", "x"), ("b", "y")]
    assert parse._paired(["a", "b"], ["x"]) == [("a", None), ("b", None), (None, "x")]


def test_the_pages_warning_flags_and_alternate_name_are_kept():
    page = ('<h1 class="hero-title">A</h1><p class="hero-alt-name">(Abu B)</p><h1 class="hero-title arabic">ا</h1>'
            '<p class="hero-alt-name arabic">(أبو ب)</p><span class="pill-flag">Tadlis</span><span class="pill-flag arabic">مدلّس</span>')
    got = parse.narrator(page)
    assert got["flags"] == [{"en": "Tadlis", "ar": "مدلّس"}] and (got["alt_en"], got["alt_ar"]) == ("(Abu B)", "(أبو ب)")


def test_a_build_that_places_no_name_keeps_the_old_file(built, monkeypatch):
    monkeypatch.setattr(loader, "hadiths", lambda *_: [])
    with pytest.raises(SystemExit):
        build_rijal.build()
    assert built.get("/api/rijal/narrators/6659").status_code == 200
    assert not build_rijal.data_path("rijal_index_path").with_suffix(".building.db").exists()


def test_place_finds_a_name_after_a_vowelled_particle():
    """وَمَالِكٌ and لِمَالِكٍ carry their vowel marks between the particle and the name; أَمَالِكٌ is another word."""
    assert parse.place("حَدَّثَنَا وَمَالِكٌ", [(1, "مَالِكٌ", 0, True)])[0] == [(13, 20, 1, True)]
    assert parse.place("لِمَالِكٍ", [(1, "مَالِكٍ", 0, True)])[0] == [(2, 9, 1, True)]
    assert parse.place("أَمَالِكٌ", [(1, "مَالِكٌ", 0, True)])[0] == []
