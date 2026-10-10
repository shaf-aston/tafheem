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
    return [(strip_diacritics(OURS[ref][start:end]), who) for start, end, who in _placed(ref)]


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
    cache.write(cache.book_path("muslim", 24), BOOK)
    cache.write(cache.narrator_path(6659), MALIK)
    build_rijal.build()
    return TestClient(app)


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
    assert built.get("/api/rijal/narrators/6659/hadith").json() == [{"collection": "muslim", "book": 24, "number": 1620, "part": "a"}]


def test_search_finds_a_narrator_by_unpointed_arabic_or_english(built):
    assert [n["id"] for n in built.get("/api/rijal/search", params={"q": "مالك أنس"}).json()["narrators"]] == [6659]
    assert [n["id"] for n in built.get("/api/rijal/search", params={"q": "malik"}).json()["narrators"]] == [6659]


def test_a_link_ending_in_a_space_still_lands_before_the_next_word():
    page = ('<div class="actualHadithContainer"><table class="hadith_reference"><a href="/bukhari:6481">r</a></table>'
            '<div class="arabic_hadith_full">عَنْ <a href="/narrator/3260">أَبِي سَعِيدٍ ـ </a>رضى الله عنه</div></div>')
    names = parse.book_chains(page)[0]["names"]
    placed, lost = parse.place("عَنْ أَبِي سَعِيدٍ ـ رضى الله عنه", names)
    assert lost == [] and placed == [(5, 20, 3260)]


def test_a_name_said_again_in_the_story_lands_where_sunnah_links_it():
    text = "سَمِعْتُ الْحَسَنَ يَقُولُ وَلَقَدْ سَمِعْتُ أَبَا بَكْرَةَ يَقُولُ إِنَّ ابْنِي هَذَا سَيِّدٌ يَعْنِي الْحَسَنَ"
    later = len(re.sub(r"\s", "", text[:text.rindex("الْحَسَنَ")]))
    placed, _ = parse.place(text, [(1281, "الْحَسَنَ", later)])
    assert placed == [(text.rindex("الْحَسَنَ"), len(text), 1281)]


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
