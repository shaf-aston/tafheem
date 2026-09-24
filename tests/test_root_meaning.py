"""The classical root book: the three situations it can be in, and the one thing
it must never do, let "not installed" be mistaken for "no such root"."""

import json

import pytest

from backend.services.root_meaning import BROKEN, MISSING, READY, JsonFileProvider


def _provider(tmp_path, payload, *, name="roots.json"):
    path = tmp_path / name
    path.write_text(payload, encoding="utf-8")
    provider = JsonFileProvider(path)
    provider.load()
    return provider


def test_no_file_reads_as_missing_not_as_an_empty_book(tmp_path):
    provider = JsonFileProvider(tmp_path / "not-here.json")
    provider.load()
    assert provider.status() == MISSING
    assert provider.lookup("كتب") is None


def test_unreadable_file_says_broken_rather_than_pretending_to_be_empty(tmp_path):
    assert _provider(tmp_path, "{ not json").status() == BROKEN


def test_a_list_is_refused_because_the_book_is_keyed_by_root(tmp_path):
    assert _provider(tmp_path, json.dumps([{"root": "كتب"}])).status() == BROKEN


def test_a_root_the_book_covers_comes_back_whole(tmp_path):
    provider = _provider(tmp_path, json.dumps({
        "ك ت ب": {"core_meaning": "الجمع", "sarf_pattern": "فَعَلَ", "variances": ["الكتابة", "الفرض"]}
    }, ensure_ascii=False))
    assert provider.status() == READY
    assert provider.lookup("كتب") == {
        "core_meaning": "الجمع",
        "sarf_pattern": "فَعَلَ",
        "variances": ["الكتابة", "الفرض"],
        "body": "",
        "english": "",
    }


@pytest.mark.parametrize("written", ["كتب", "ك ت ب", "ك-ت-ب", " كَتَبَ "])
def test_the_same_root_matches_however_it_is_written(tmp_path, written):
    provider = _provider(tmp_path, json.dumps({"ك-ت-ب": {"core_meaning": "الجمع"}}, ensure_ascii=False))
    assert provider.lookup(written)["core_meaning"] == "الجمع"


def test_a_root_the_book_does_not_cover_is_a_miss_not_an_error(tmp_path):
    provider = _provider(tmp_path, json.dumps({"كتب": {"core_meaning": "الجمع"}}, ensure_ascii=False))
    assert provider.status() == READY
    assert provider.lookup("زقم") is None


def test_a_bad_row_cannot_rewrite_which_root_or_source_is_claimed(tmp_path):
    """The file is data, not instructions: only the three named fields are read."""
    provider = _provider(tmp_path, json.dumps({
        "كتب": {"core_meaning": "الجمع", "root": "ضرب", "source": "verified", "label": "Hans Wehr"}
    }, ensure_ascii=False))
    assert set(provider.lookup("كتب")) == {"core_meaning", "sarf_pattern", "variances", "body", "english"}


def test_blank_rows_are_dropped_rather_than_printed(tmp_path):
    provider = _provider(tmp_path, json.dumps({
        "كتب": {"core_meaning": "الجمع", "variances": ["  ", "الكتابة", None]}
    }, ensure_ascii=False))
    assert provider.lookup("كتب") == {
        "core_meaning": "الجمع", "sarf_pattern": "", "variances": ["الكتابة"], "body": "", "english": "",
    }


@pytest.mark.parametrize("row", [
    {"variances": ["الكتابة"]},                    # no meaning at all
    {"core_meaning": "   "},                       # a meaning that is only spaces
    {"core_meaning": None},
    {"core_meaning": {"ar": "الجمع"}},             # a nested shape, not a line
])
def test_a_row_with_no_readable_meaning_is_a_miss_not_a_blank_entry(tmp_path, row):
    """A blank line under Ibn Faris's name reads as though he had said nothing."""
    provider = _provider(tmp_path, json.dumps({"كتب": row}, ensure_ascii=False))
    assert provider.lookup("كتب") is None


def test_a_field_that_is_not_text_is_never_printed_as_arabic(tmp_path):
    """str() on a list would put ['a', 'b'] on screen in Arabic type."""
    provider = _provider(tmp_path, json.dumps({
        "كتب": {"core_meaning": "الجمع", "sarf_pattern": ["فَعَلَ"], "variances": [["الكتابة"], 7]}
    }, ensure_ascii=False))
    assert provider.lookup("كتب") == {
        "core_meaning": "الجمع", "sarf_pattern": "", "variances": [], "body": "", "english": "",
    }


def test_a_folder_instead_of_a_file_reads_as_missing_not_as_unreadable(tmp_path):
    """The likeliest way to mistype the one setting is to point it at the folder."""
    provider = JsonFileProvider(tmp_path)
    provider.load()
    assert provider.status() == MISSING


def test_a_book_that_fails_to_load_says_broken_never_not_installed(tmp_path, monkeypatch):
    """Otherwise a bad drive or a permissions error tells the reader to install
    a file that is already sitting there."""
    provider = _provider(tmp_path, json.dumps({"كتب": {"core_meaning": "الجمع"}}, ensure_ascii=False))
    monkeypatch.setattr(
        type(provider),
        "_read",
        lambda self: iter(()).throw(RuntimeError("disk gone")),
    )
    provider.load()
    assert provider.status() == BROKEN
    assert provider.lookup("كتب") is None


def test_a_row_that_is_not_an_object_is_dropped_rather_than_crashing_the_book(tmp_path):
    provider = _provider(tmp_path, json.dumps({
        "كتب": "الجمع", "ضرب": {"core_meaning": "الضرب"}
    }, ensure_ascii=False))
    assert provider.status() == READY
    assert provider.lookup("كتب") is None
    assert provider.lookup("ضرب")["core_meaning"] == "الضرب"


def test_the_english_never_merges_into_the_arabic(tmp_path):
    """One field here was read off a photograph and the rest was typed by a
    person. They stay apart so the card can badge them differently, merged,
    the weaker would borrow the standing of the stronger."""
    provider = _provider(tmp_path, json.dumps({
        "كتب": {"core_meaning": "الجمع", "body": "الجمع. ومنه الكتاب", "english": "gathering"}
    }, ensure_ascii=False))
    entry = provider.lookup("كتب")
    assert entry["english"] == "gathering"
    assert entry["core_meaning"] == "الجمع"
    assert "gathering" not in entry["core_meaning"] + entry["body"]


def test_an_entry_with_no_english_says_nothing_rather_than_none(tmp_path):
    """The card renders on truthiness; a None would print the word "None"."""
    provider = _provider(tmp_path, json.dumps({"كتب": {"core_meaning": "الجمع"}}, ensure_ascii=False))
    assert provider.lookup("كتب")["english"] == ""
    assert provider.lookup("كتب")["body"] == ""


def test_a_body_that_is_not_text_is_dropped_like_every_other_field(tmp_path):
    provider = _provider(tmp_path, json.dumps({
        "كتب": {"core_meaning": "الجمع", "body": ["ومنه الكتاب"], "english": 7}
    }, ensure_ascii=False))
    assert provider.lookup("كتب")["body"] == ""
    assert provider.lookup("كتب")["english"] == ""


# ── The endpoint ────────────────────────────────────────────────────────────
# The rules above only hold if the web layer passes them through: the status the
# card reads, and the source badge, are decided here.

@pytest.fixture()
def client(monkeypatch, tmp_path):
    """The dictionary router alone, so no other data file has to load."""
    from fastapi import FastAPI
    from fastapi.testclient import TestClient

    from backend.routers import dictionary as router_module
    from backend.services import root_meaning as module

    def _install(payload):
        provider = _provider(tmp_path, payload) if payload else JsonFileProvider(tmp_path / "none.json")
        if payload is None:
            provider.load()
        monkeypatch.setattr(module, "get_provider", lambda: provider)
        monkeypatch.setattr(module, "status", provider.status)
        monkeypatch.setattr(module, "lookup", provider.lookup)

    app = FastAPI()
    app.include_router(router_module.router)
    test_client = TestClient(app)
    test_client.install = _install
    return test_client


def _get(client, root):
    return client.get("/api/dictionary/root-meaning", params={"root": root}).json()


def test_the_endpoint_reports_missing_so_the_card_can_say_so(client):
    client.install(None)
    body = _get(client, "كتب")
    assert body["status"] == "missing"
    assert body["meaning"] is None and body["source"] is None


def test_a_root_the_book_covers_comes_back_with_its_source(client):
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع"}}, ensure_ascii=False))
    body = _get(client, "كَتَبَ")
    assert body["status"] == "ready"
    assert body["root"] == "كتب"          # the letters searched, echoed back
    assert body["meaning"]["core_meaning"] == "الجمع"
    assert body["source"]["label"]


def test_the_english_carries_its_own_weaker_badge(client):
    """Two sources in one card: the Arabic typed by a person, the English read
    off a scan. A single badge would vouch for both at the stronger level."""
    client.install(json.dumps({
        "كتب": {"core_meaning": "الجمع", "english": "gathering"}
    }, ensure_ascii=False))
    body = _get(client, "كتب")
    assert body["english_source"]["confidence"] == "guessed"
    assert body["source"]["confidence"] != "guessed"


def test_no_english_means_no_english_badge(client):
    """A credit shown for something the card is not displaying reads as though
    the gloss had been consulted and had said nothing."""
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع"}}, ensure_ascii=False))
    assert _get(client, "كتب")["english_source"] is None


def test_a_miss_carries_no_source_because_no_book_answered(client):
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع"}}, ensure_ascii=False))
    body = _get(client, "زقم")
    assert body["status"] == "ready" and body["meaning"] is None
    assert body["source"] is None


def test_letters_that_are_not_arabic_are_refused_loudly(client):
    """422, the same as every other endpoint given non-Arabic where it needs Arabic.

    This asked for 400 while the identical check in the analysis, morphology and
    practice routers answered 422, one condition, two answers, depending on which
    endpoint you happened to hit. They all go through `require_arabic` now.
    """
    client.install(None)
    assert client.get("/api/dictionary/root-meaning", params={"root": "ktb"}).status_code == 422


# ── One root, two spellings ─────────────────────────────────────────────────
# The book writes each root once, the way its editor spelled it. A reader does
# not know which way that was. Matching the two is the search's job, and the one
# thing it may never do is answer with a different root that merely looks alike.

def _spelled(tmp_path, payload, fold=None):
    """A book with its spelling rules beside it, the way it ships."""
    if fold is not None:
        (tmp_path / "spelling.json").write_text(
            json.dumps({"fold": fold}, ensure_ascii=False), encoding="utf-8"
        )
    return _provider(tmp_path, json.dumps(payload, ensure_ascii=False))


def test_a_root_is_found_under_the_other_spelling_of_its_letters(tmp_path):
    """The book prints أمر; nobody types the hamza into a search box."""
    provider = _spelled(tmp_path, {"أمر": {"core_meaning": "الأمر"}}, {"أ": "ا"})
    assert provider.resolve("امر") == "أمر"
    assert provider.lookup("امر")["core_meaning"] == "الأمر"


def test_the_second_spelling_works_in_both_directions(tmp_path):
    """هدي is what the book wrote and هدى is what a reader writes. Folding only
    one way left the reader's spelling reading as "the book has no entry"."""
    provider = _spelled(tmp_path, {"هدي": {"core_meaning": "الهداية"}}, {"ى": "ي"})
    assert provider.resolve("هدى") == "هدي"


def test_two_roots_that_look_alike_never_answer_for_each_other(tmp_path):
    """هنأ and هنا are different roots that fold onto the same letters. Picking
    one would print a real entry under the wrong root, the worst thing this
    card can do, because nothing on screen would look wrong."""
    provider = _spelled(tmp_path, {
        "هنأ": {"core_meaning": "إصابة الخير"}, "هنا": {"core_meaning": "الحرف المعتل"},
    }, {"أ": "ا"})
    assert provider.lookup("هنأ")["core_meaning"] == "إصابة الخير"
    assert provider.lookup("هنا")["core_meaning"] == "الحرف المعتل"
    # A third spelling folding onto the pair is answered by neither.
    assert provider.resolve("هنآ") is None


def test_the_spelling_the_reader_typed_is_answered_before_any_other(tmp_path):
    """بدأ and بدو are both in the book. بدأ must never be served the entry of
    whichever root happens to fold onto it."""
    provider = _spelled(tmp_path, {
        "بدا": {"core_meaning": "الظهور"}, "بدأ": {"core_meaning": "الافتتاح"},
    }, {"أ": "ا"})
    assert provider.lookup("بدأ")["core_meaning"] == "الافتتاح"
    assert provider.lookup("بدا")["core_meaning"] == "الظهور"


def test_without_the_spelling_file_only_the_books_own_spelling_is_found(tmp_path):
    """Optional data, so its absence thins the search rather than breaking it; 
    but it must not quietly look like the book having no such root."""
    provider = _spelled(tmp_path, {"أمر": {"core_meaning": "الأمر"}})
    assert provider.status() == READY
    assert provider.resolve("أمر") == "أمر"
    assert provider.lookup("امر") is None


def test_a_spelling_file_that_is_nonsense_does_not_break_the_book(tmp_path):
    (tmp_path / "spelling.json").write_text("{ not json", encoding="utf-8")
    provider = _provider(tmp_path, json.dumps({"أمر": {"core_meaning": "الأمر"}}, ensure_ascii=False))
    assert provider.status() == READY
    assert provider.lookup("أمر")["core_meaning"] == "الأمر"


def test_the_card_is_told_when_the_book_spells_the_root_differently(client, tmp_path):
    """Otherwise an entry about بدأ reads as an answer about the بدا typed in."""
    (tmp_path / "spelling.json").write_text(
        json.dumps({"fold": {"أ": "ا"}}, ensure_ascii=False), encoding="utf-8"
    )
    client.install(json.dumps({"أمر": {"core_meaning": "الأمر"}}, ensure_ascii=False))
    assert _get(client, "امر")["book_root"] == "أمر"


def test_no_note_when_the_spelling_searched_is_the_one_printed(client):
    """Naming the same letters back reads as a correction that never happened."""
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع"}}, ensure_ascii=False))
    assert _get(client, "كتب")["book_root"] is None


@pytest.mark.parametrize("shape", ['{"fold": ["أ", "ا"]}', '{"fold": "أا"}', '{"fold": 5}', '{"fold": null}'])
def test_a_fold_of_the_wrong_shape_thins_the_search_and_never_hides_the_book(tmp_path, shape):
    """An optional sidecar must not be able to report the book as unreadable.

    Every unusable shape has to land in the same place: searches match only the
    spelling the book uses, and the entries are still there. A "fold" that is a
    list has no .items(), and that one shape used to escape to the catch-all and
    blame a roots.json that was perfectly fine.
    """
    (tmp_path / "spelling.json").write_text(shape, encoding="utf-8")
    provider = _provider(tmp_path, json.dumps({"أمر": {"core_meaning": "الأمر"}}, ensure_ascii=False))
    assert provider.status() == READY
    assert provider.lookup("أمر")["core_meaning"] == "الأمر"
    assert provider.lookup("امر") is None


# ── The entry retold in English ─────────────────────────────────────────────
# A separate endpoint because it is a separate kind of answer: the entry is the
# book's, this is a machine reading it. The rules here are that it never invents
# a reason to call the model, never claims a whole entry it only saw part of,
# and never blames the model for something the book is missing.

def _english(client, root):
    return client.get("/api/dictionary/root-meaning/english", params={"root": root})


@pytest.fixture(autouse=True)
def kept(monkeypatch, tmp_path):
    """A fresh store of English readings per test, in a directory of its own."""
    from backend.services import root_english

    monkeypatch.setattr(root_english, "STORE_FILE", tmp_path / "english_entries.json")
    monkeypatch.setattr(root_english, "_entries", None)
    monkeypatch.setattr(root_english, "LINES_FILE", tmp_path / "english_lines.json")
    monkeypatch.setattr(root_english, "_line_entries", None)
    return root_english


@pytest.fixture()
def ai(monkeypatch):
    """A stand-in AI. Records what it was handed; answers what it is told to."""
    from backend.routers import dictionary as router_module

    state = {"available": True, "answer": {"english": "gathering one thing to another"}, "seen": None}

    def _explain(root, entry):
        state["seen"] = (root, entry)
        return state["answer"]

    monkeypatch.setattr(router_module.ai_service, "is_ai_available", lambda: state["available"])
    monkeypatch.setattr(router_module.ai_service, "explain_root_entry", _explain)
    return state


def test_a_reading_made_on_the_spot_is_badged_a_guess(client, ai):
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "الجمع. ومن ذلك الكتاب"}},
                              ensure_ascii=False))
    body = _english(client, "كتب").json()
    assert body["english"] == "gathering one thing to another"
    # Made in the second the button was pressed, checked by nobody.
    assert body["source"]["confidence"] == "guessed"
    assert body["source"]["key"] == "ai"
    assert body["truncated"] is False


def test_the_model_is_handed_the_book_never_what_was_typed(client, ai):
    """The only Arabic that reaches the model is the app's own copy of the entry."""
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "نص الكتاب"}},
                              ensure_ascii=False))
    _english(client, "كَتَبَ")
    assert ai["seen"] == ("كتب", "نص الكتاب")


def test_an_entry_the_book_leaves_blank_is_not_reported_as_an_ai_failure(client, ai):
    client.install(json.dumps({"كسا": {"core_meaning": "", "body": ""}}, ensure_ascii=False))
    assert _english(client, "كسا").status_code == 404


def test_a_root_the_book_does_not_have_is_a_miss_not_a_model_error(client, ai):
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "نص"}}, ensure_ascii=False))
    assert _english(client, "قرأ").status_code == 404


def test_no_ai_is_said_plainly_rather_than_answered_with_nothing(client, ai):
    ai["available"] = False
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "نص"}}, ensure_ascii=False))
    response = _english(client, "كتب")
    assert response.status_code == 503
    assert "Arabic" in response.json()["detail"]


def test_the_book_not_being_loaded_is_not_the_models_fault_either(client, ai):
    client.install(None)
    assert _english(client, "كتب").status_code == 503


def test_an_empty_answer_is_a_failure_not_an_entry_with_no_meaning(client, ai):
    ai["answer"] = {"english": "   "}
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "نص"}}, ensure_ascii=False))
    assert _english(client, "كتب").status_code == 502


def test_an_entry_longer_than_the_model_sees_says_so(client, ai, monkeypatch):
    """Otherwise a retelling that stops early reads as the whole entry."""
    from backend.routers import dictionary as router_module

    settings = router_module.get_settings()
    monkeypatch.setattr(settings, "root_entry_truncate_chars", 10, raising=False)
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "ا" * 50}},
                              ensure_ascii=False))
    assert _english(client, "كتب").json()["truncated"] is True


def test_letters_that_are_not_arabic_never_reach_the_model(client, ai):
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "نص"}}, ensure_ascii=False))
    assert _english(client, "ktb").status_code == 422
    assert ai["seen"] is None


# ── Reading an entry once ───────────────────────────────────────────────────
# Putting an entry into English costs a call and gives the same answer every
# time, so it is done once and kept. The rules are that a kept reading is used
# instead of a second call, and that failing to keep one never costs the reader
# the answer they already have.

def test_the_same_entry_is_never_put_into_english_twice(client, ai, kept):
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "نص"}}, ensure_ascii=False))
    assert _english(client, "كتب").json()["english"] == "gathering one thing to another"

    ai["seen"] = None
    ai["answer"] = {"english": "a second, different answer"}
    again = _english(client, "كتب").json()
    assert again["english"] == "gathering one thing to another"
    assert ai["seen"] is None, "the model was asked again for an entry already read"


def test_a_kept_reading_answers_even_with_no_ai_at_all(client, ai, kept):
    kept.put("كتب", "gathering one thing to another")
    ai["available"] = False
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "نص"}}, ensure_ascii=False))
    assert _english(client, "كتب").json()["english"] == "gathering one thing to another"


def test_a_kept_reading_is_badged_as_a_translation(client, ai, kept):
    """A kept reading was translated against the Arabic and read back first."""
    kept.put("كتب", "gathering one thing to another")
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "نص"}}, ensure_ascii=False))
    assert _english(client, "كتب").json()["source"]["confidence"] == "translated"


def test_a_store_that_cannot_be_read_costs_time_not_correctness(client, ai, kept):
    kept.STORE_FILE.write_text("{ not json", encoding="utf-8")
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "نص"}}, ensure_ascii=False))
    assert _english(client, "كتب").json()["english"] == "gathering one thing to another"


def test_nothing_blank_is_ever_kept(kept):
    kept.put("كتب", "   ")
    kept.put("", "something")
    assert kept.count() == 0


def test_a_store_written_by_something_else_is_ignored_not_trusted(kept):
    kept.STORE_FILE.write_text(json.dumps(["كتب"]), encoding="utf-8")
    assert kept.get("كتب") is None


def test_a_reading_never_drops_what_another_writer_kept(kept):
    """What wiped it once: another writer rewrote the file from its own copy.

    A reading made from a stale copy carries over whatever the file has gained
    since, so the store only ever grows.
    """
    kept.put("كتب", "gathering")
    kept.put("علم", "knowing")
    kept._entries = {"كتب": "gathering"}      # a stale copy, as an outside writer would have

    kept.put("جعل", "making")

    assert set(json.loads(kept.STORE_FILE.read_text(encoding="utf-8"))) == {"كتب", "علم", "جعل"}


def test_two_roots_that_fold_together_each_answer_for_themselves(tmp_path):
    """حدا and حدأ are different entries whose folded spelling is the same.

    The fold index deliberately holds neither, so only the literal spelling can
    tell them apart. If resolve() were ever simplified to fold first, حدأ would
    quietly come back with حدا's meaning, which reads perfectly plausible and
    would be caught by nobody. Four such pairs exist, and three of them are
    entries recovered from headings the book's contents page leaves out.
    """
    pairs = [("حدا", "حدأ"), ("دفأ", "دفا"), ("لما", "لمأ"), ("هنا", "هنأ")]
    book = _provider(tmp_path, json.dumps({
        root: {"core_meaning": f"the meaning of {root}"}
        for pair in pairs for root in pair
    }, ensure_ascii=False))
    for pair in pairs:
        for root in pair:
            assert book.resolve(root) == root
            assert book.lookup(root)["core_meaning"] == f"the meaning of {root}"


# Which of the two English glosses wins, and which badge it earns. This used to
# be decided inside the web handler, where the only way to reach it was over
# HTTP and so the decision itself was never tested. It lives beside the book now.

@pytest.fixture()
def book(monkeypatch, tmp_path):
    """The book installed, and `entry_for` called directly, no web layer at all."""
    from backend.services import root_meaning as module

    def _install(payload):
        provider = _provider(tmp_path, payload)
        monkeypatch.setattr(module, "get_provider", lambda: provider)
        monkeypatch.setattr(module, "lookup", provider.lookup)
        monkeypatch.setattr(module, "resolve", provider.resolve)
        return module

    return _install


def test_a_root_the_book_does_not_have_is_none_not_an_empty_entry(book):
    module = book(json.dumps({"كتب": {"core_meaning": "الجمع"}}, ensure_ascii=False))
    assert module.entry_for("زقم") is None


def test_english_read_off_the_scan_carries_the_weaker_badge(book):
    """Nothing has been translated from the Arabic, so all there is to show is
    what a model read off a photograph of the page. It says so."""
    module = book(json.dumps(
        {"كتب": {"core_meaning": "الجمع", "english": "to gather"}}, ensure_ascii=False))
    entry = module.entry_for("كتب")
    assert entry.meaning["english"] == "to gather"
    assert entry.english_source_key == "maqayees_english"


def test_a_translation_of_the_arabic_beats_the_scan_and_says_so(book, kept):
    """The same sentence, put into English properly from the typed Arabic. It
    replaces the scanned gloss and carries the better badge; showing the weaker
    one here would undersell an answer that was actually made from the book."""
    module = book(json.dumps(
        {"كتب": {"core_meaning": "الجمع", "english": "to gather"}}, ensure_ascii=False))
    kept.put("كتب", "The letters kaf, ta and ba point to gathering. And of that is the book.")

    entry = module.entry_for("كتب")
    assert entry.meaning["english"] == "The letters kaf, ta and ba point to gathering."
    assert entry.english_source_key == "maqayees_translation"


def test_no_english_at_all_earns_no_badge(book):
    """A credit with nothing above it reads as though something had been said."""
    module = book(json.dumps({"كتب": {"core_meaning": "الجمع"}}, ensure_ascii=False))
    assert module.entry_for("كتب").english_source_key is None


def test_the_translation_is_looked_up_under_the_books_own_spelling(book, kept, tmp_path):
    """Kept readings are filed under the spelling the book prints, so looking
    one up by what the reader typed would find nothing and silently fall back
    to the weaker gloss."""
    (tmp_path / "spelling.json").write_text(
        json.dumps({"fold": {"أ": "ا"}}, ensure_ascii=False), encoding="utf-8"
    )
    module = book(json.dumps({"أمر": {"core_meaning": "الأمر"}}, ensure_ascii=False))
    kept.put("أمر", "The letters hamza, mim and ra point to command.")

    entry = module.entry_for("امر")
    assert entry.book_root == "أمر"
    assert entry.english_source_key == "maqayees_translation"


def test_the_typed_spelling_is_never_named_back(book):
    module = book(json.dumps({"كتب": {"core_meaning": "الجمع"}}, ensure_ascii=False))
    assert module.entry_for("كتب").book_root is None


# ── The entry lined up, English under each Arabic line ──────────────────────
# The one rule that matters here: English is only ever shown under the line it
# translates. An answer that cannot be paired exactly is refused, whatever it
# says, because a mispairing is a false claim about the book.

def _lined(client, root):
    return client.get("/api/dictionary/root-meaning/english/lines", params={"root": root})


@pytest.fixture()
def line_ai(monkeypatch):
    """A stand-in for the line-by-line model call. Counts how often it is asked."""
    from backend.routers import dictionary as router_module

    state = {"available": True, "answer": None, "seen": None, "asked": 0}

    def _explain(root, lines):
        state["asked"] += 1
        state["seen"] = (root, list(lines))
        return state["answer"] if state["answer"] is not None else {
            "lines": [f"English {i + 1}" for i in range(len(lines))]
        }

    monkeypatch.setattr(router_module.ai_service, "is_ai_available", lambda: state["available"])
    monkeypatch.setattr(router_module.ai_service, "explain_root_entry_lines", _explain)
    return state


_LINED_BODY = "الجمع.\nومن ذلك الكتاب.\nوقال الشاعر:\nصدر البيت ... عجزه"


def test_each_arabic_line_comes_back_with_its_own_english(client, line_ai):
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": _LINED_BODY}},
                              ensure_ascii=False))
    body = _lined(client, "كتب").json()
    # The origin sense is not among the lines: it has its own English higher up
    # the card, and the panel this feeds shows only what follows it.
    assert [pair["arabic"] for pair in body["lines"]] == [
        "ومن ذلك الكتاب.", "وقال الشاعر:", "صدر البيت ... عجزه",
    ]
    assert [pair["english"] for pair in body["lines"]] == ["English 1", "English 2", "English 3"]
    assert body["source"]["key"] == "ai"
    assert body["truncated"] is False


def test_a_verse_is_handed_over_as_one_line_not_two_halves(client, line_ai):
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": _LINED_BODY}},
                              ensure_ascii=False))
    _lined(client, "كتب")
    assert line_ai["seen"][1][-1] == "صدر البيت ... عجزه"


def test_a_miscounted_answer_is_refused_and_never_kept(client, line_ai, kept):
    line_ai["answer"] = {"lines": ["only one line for three"]}
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": _LINED_BODY}},
                              ensure_ascii=False))
    response = _lined(client, "كتب")
    assert response.status_code == 502
    assert "lined up" in response.json()["detail"]
    assert kept.get_lines("كتب") is None


def test_a_blank_line_in_the_answer_is_a_miscount_too(client, line_ai):
    """Three strings, one empty, still pairs English with the wrong claim."""
    line_ai["answer"] = {"lines": ["a", "   ", "c"]}
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": _LINED_BODY}},
                              ensure_ascii=False))
    assert _lined(client, "كتب").status_code == 502


def test_a_kept_reading_never_asks_the_model_again(client, line_ai):
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": _LINED_BODY}},
                              ensure_ascii=False))
    first = _lined(client, "كتب").json()
    second = _lined(client, "كتب").json()
    assert line_ai["asked"] == 1
    assert first == second


def test_a_kept_reading_that_no_longer_fits_the_entry_is_remade(client, line_ai, kept):
    """The book file can be rebuilt under a kept reading. A count that no
    longer matches would pair old English with new Arabic, so it is remade."""
    kept.put_lines("كتب", ["stale one", "stale two"])
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": _LINED_BODY}},
                              ensure_ascii=False))
    body = _lined(client, "كتب").json()
    assert line_ai["asked"] == 1
    assert [pair["english"] for pair in body["lines"]] == ["English 1", "English 2", "English 3"]


def test_a_long_entry_is_cut_at_whole_lines_and_says_so(client, line_ai, monkeypatch):
    from backend.routers import dictionary as router_module

    settings = router_module.get_settings()
    monkeypatch.setattr(settings, "root_entry_truncate_chars", 20, raising=False)
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": _LINED_BODY}},
                              ensure_ascii=False))
    body = _lined(client, "كتب").json()
    assert body["truncated"] is True
    # Whole lines only: nothing the model saw was half a line.
    assert all(pair["arabic"] in _LINED_BODY.split("\n") for pair in body["lines"])
    assert len(body["lines"]) < 3


def test_an_entry_that_is_all_origin_sense_has_nothing_to_line_up(client, line_ai):
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": "الجمع."}},
                              ensure_ascii=False))
    assert _lined(client, "كتب").status_code == 404


def test_no_ai_for_lines_is_said_plainly(client, line_ai):
    line_ai["available"] = False
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": _LINED_BODY}},
                              ensure_ascii=False))
    assert _lined(client, "كتب").status_code == 503


# ── How finely the entry is cut ──────────────────────────────────────────────
# A paragraph of Ibn Faris runs to hundreds of characters, so pairing at the
# printing's own breaks put a wall of Arabic beside a wall of English. The cut
# is now a claim at a time; a verse is still never cut.

def test_a_paragraph_is_cut_at_its_full_stops(client, line_ai):
    body = "الجمع.\nومن ذلك الكتاب. وقالوا: كتب القوم. ومنه الكتيبة."
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": body}},
                              ensure_ascii=False))
    answer = _lined(client, "كتب").json()
    assert [pair["arabic"] for pair in answer["lines"]] == [
        "ومن ذلك الكتاب.", "وقالوا: كتب القوم.", "ومنه الكتيبة.",
    ]


def test_a_comma_is_not_a_cut(client, line_ai):
    """The book's commas and its ؛ separate clauses inside one claim. Cutting
    there would put half a thought beside half an English sentence."""
    body = "الجمع.\nومن ذلك الكتاب، وهو معروف ؛ ومنه الكتيبة."
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": body}},
                              ensure_ascii=False))
    answer = _lined(client, "كتب").json()
    assert [pair["arabic"] for pair in answer["lines"]] == ["ومن ذلك الكتاب، وهو معروف ؛ ومنه الكتيبة."]


def test_a_verse_stays_whole_even_with_a_full_stop_in_it(client, line_ai):
    body = "الجمع.\nصدر البيت. تمامه ... عجز البيت"
    client.install(json.dumps({"كتب": {"core_meaning": "الجمع", "body": body}},
                              ensure_ascii=False))
    answer = _lined(client, "كتب").json()
    assert [pair["arabic"] for pair in answer["lines"]] == ["صدر البيت. تمامه ... عجز البيت"]
