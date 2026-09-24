"""The library: many books, one shape, one passage however many ayahs it covers.

The thing worth testing is the join. A tafsir commonly comments on a run of
ayahs in one passage, and the library stores that passage once. So the two ways
of getting it wrong are: asking about the middle of a run and getting nothing,
and asking about a run and being told it was written about one ayah.

Also covered: no HTML reaches the app. What arrives from Quran.com and from QUL
is marked up, and a page that renders it as text would show the tags; worse, a
page that rendered it as HTML would be running markup from somebody else.

And that adding a book stays free. Every check below is written over whatever
editions happen to be installed rather than over a named one, because a test
that names Ibn Kathir would have to be edited every time a book arrives, which
is exactly the cost this design exists to remove.

Run: python -m pytest tests/test_quran_library.py
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import quran_library
from backend.services.markup import as_text

client = TestClient(app)

CONFIDENCES = {"verified", "derived", "translated", "guessed"}
# asbab is the third: reports on why an ayah came down, which the Timelines tab
# asks for by id rather than offering in the tafsir picker.
KINDS = {"tafsir", "translation", "asbab"}

needs_library = pytest.mark.skipif(
    not quran_library.is_built(),
    reason="library.db not imported, run backend/scripts/import_quran_editions.py",
)


def first_passage() -> dict | None:
    """A passage covering a run of ayahs, from whichever book has one.

    An-Naba' opens with a run in every tafsir this app is likely to hold, but a
    library holding only translations legitimately has no runs at all, and that
    is a skip rather than a failure.
    """
    return next(
        (
            hit
            for hit in quran_library.for_ayah(78, 1)
            if len(hit["covers"]) > 1
        ),
        None,
    )


@needs_library
def test_a_passage_written_about_a_run_says_so() -> None:
    first = first_passage()
    if first is None:
        pytest.skip("no installed book comments on a run of ayahs")
    assert first["covers"] == sorted(first["covers"])

    same = [
        hit
        for hit in quran_library.for_ayah(78, first["covers"][-1])
        if hit["edition"] == first["edition"]
    ]
    assert same, "the last ayah of the run fell out of it"
    assert same[0]["text"] == first["text"], "one passage, reached from either end"
    assert same[0]["covers"] == first["covers"]


@needs_library
def test_every_ayah_of_a_run_is_reachable() -> None:
    first = first_passage()
    if first is None:
        pytest.skip("no installed book comments on a run of ayahs")
    for ayah in first["covers"]:
        reached = {hit["edition"] for hit in quran_library.for_ayah(78, ayah)}
        assert first["edition"] in reached, f"78:{ayah} fell out of its run"


@needs_library
def test_no_markup_reaches_the_app() -> None:
    for surah, ayah in ((1, 1), (2, 255), (78, 1), (112, 1)):
        for hit in quran_library.for_ayah(surah, ayah):
            where = f"{hit['edition']} on {surah}:{ayah}"
            assert "<" not in hit["text"], f"{where} still carries markup"
            assert "&amp;" not in hit["text"], f"{where} still carries entities"


@needs_library
def test_every_installed_book_can_be_credited() -> None:
    """A book with no name, licence or badge word could not be shown honestly."""
    for book in quran_library.editions():
        for field in ("id", "name", "author", "licence", "origin", "credit"):
            assert str(book[field]).strip(), f"{book['id']} has no {field}"
        assert book["kind"] in KINDS, book["id"]
        assert book["confidence"] in CONFIDENCES, book["id"]
        assert book["passages"] > 0 and book["ayahs"] > 0, book["id"]


@needs_library
def test_narrowing_to_one_book_returns_only_that_book() -> None:
    every = quran_library.for_ayah(2, 255)
    if not every:
        pytest.skip("no installed book has anything on 2:255")
    one = every[0]["edition"]
    assert [hit["edition"] for hit in quran_library.for_ayah(2, 255, [one])] == [one]


@needs_library
def test_asking_for_a_book_nobody_installed_is_empty_not_an_error() -> None:
    """A reader's saved choice must not break the page after a book is removed."""
    assert quran_library.for_ayah(2, 255, ["no-such-book"]) == []


@needs_library
def test_the_endpoint_returns_passages_and_a_source_each() -> None:
    body = client.get("/api/quran/editions/2/255").json()
    assert body["surah"] == 2 and body["ayah"] == 255
    for passage in body["passages"]:
        assert passage["text"].strip()
        assert passage["covers"]
        assert passage["source"]["label"] == passage["name"], "the badge names the book"
        assert passage["source"]["confidence"] in CONFIDENCES


@needs_library
def test_an_ayah_a_book_is_silent_on_is_empty_not_a_404() -> None:
    """Absent commentary is not a missing page, and must not read as one.

    Asked of one book, because a library holding a full translation has
    something for every ayah of the Qur'an: what has to stay true is that a book
    with nothing to say about an ayah answers "nothing", not "no such page".
    Ibn Kathir reaches 6,011 of the 6,236, and 20:32 is one he passes over.
    """
    response = client.get("/api/quran/editions/20/32?ids=ibn-kathir-en")
    assert response.status_code == 200
    assert response.json()["passages"] == []


def test_an_ayah_number_that_cannot_exist_is_refused() -> None:
    """Runs without the library. There is no surah 200 and no ayah 9,999, and
    an unbounded number reached SQLite and came back a 500."""
    assert client.get("/api/quran/editions/2/9999").status_code == 422
    assert client.get("/api/quran/editions/200/1").status_code == 422
    assert client.get("/api/quran/editions/surah/200?id=x").status_code == 422


@needs_library
def test_a_whole_surah_is_translations_only() -> None:
    """A commentary sent a surah at a time repeats each passage once per ayah of
    its run, so the reading-view endpoint takes translations and says so."""
    tafsirs = client.get("/api/quran/editions?kind=tafsir").json()
    if not tafsirs:
        pytest.skip("no commentary installed")
    assert client.get(f"/api/quran/editions/surah/1?id={tafsirs[0]['id']}").status_code == 404


@needs_library
def test_the_editions_list_can_be_narrowed_by_kind() -> None:
    every = client.get("/api/quran/editions").json()
    tafsirs = client.get("/api/quran/editions?kind=tafsir").json()
    assert {book["id"] for book in tafsirs} <= {book["id"] for book in every}
    assert all(book["kind"] == "tafsir" for book in tafsirs)


def test_an_unknown_kind_is_refused() -> None:
    """Runs without the library: the route's own guard, not the data."""
    assert client.get("/api/quran/editions?kind=poetry").status_code == 422


def test_stripping_markup_keeps_the_paragraphs() -> None:
    """Runs without the library, the rule itself, not the imported data."""
    stripped = as_text("<h1>Title</h1><p>One &amp; two<br>same line</p><div>Next</div>")
    assert stripped == "Title\n\nOne & two\nsame line\n\nNext"
