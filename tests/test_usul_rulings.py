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


def _rulings_for(units, hadith, narrators_of, others=(), **knobs):
    """others: the name forms of narrators no chain here names, who still count for how many men carry a name;
    knobs: match knobs to set."""
    conn = sqlite3.connect(":memory:")
    conn.executescript(build_usul._SCHEMA)
    units_of = {kc["book"]: [] for kc in RULINGS["kinds"].values()} | {"shahin": units}
    everyone = list({tuple(f): f for men in narrators_of.values() for f in men}.values()) + list(others)
    cfg = {**SMALL, "rulings": {**SMALL["rulings"], "match": {**SMALL["rulings"]["match"], **knobs}}}
    build_usul.add_rulings(conn, units_of, hadith, narrators_of, everyone, cfg)
    return conn.execute("SELECT collection, number, part, unit FROM ruling ORDER BY collection, number").fetchall(), conn


def test_a_text_match_with_no_narrator_in_common_gets_no_ruling_and_is_listed_as_rejected():
    hadith = [(("abudawud", 1, ""), _ours(), 1), (("muslim", 2, ""), _ours("حدثنا زيد بن ثابت"), 1)]
    narrators_of = {("abudawud", 1, ""): [[names.words("سفيان بن عيينة")]], ("muslim", 2, ""): [[names.words("زيد بن ثابت")]]}
    found, conn = _rulings_for([_unit(7)], hadith + OTHERS, narrators_of)
    assert found == [("abudawud", 1, "", 7)]   # Muslim's text is the same; its chain names another man
    assert not [row for row in conn.execute("SELECT * FROM gap").fetchall() if row[0] == "ruling_match"]
    # With only Muslim's hadith to hold it, the unit gets nothing and says why.
    found, conn = _rulings_for([_unit(7)], hadith[1:] + OTHERS, narrators_of)
    assert found == []
    assert ("ruling_match", "shahin: rejected", 1) in conn.execute("SELECT * FROM gap").fetchall()


def test_a_shared_kunya_that_many_men_carry_is_not_a_shared_man():
    kunya = "حدثنا أبو عبد الرحمن"   # its words alone are named in thousands of our chains, so only the run counts
    common = {"rare_name": 0}
    hadith = [(("muslim", 2, ""), _ours(kunya), 1)]
    narrators_of = {("muslim", 2, ""): [[names.words("أبو عبد الرحمن السلمي")]]}
    found, _ = _rulings_for([_unit(7, kunya)], hadith + OTHERS, narrators_of, **common)
    assert found == [("muslim", 2, "", 7)]   # one man carries it here
    many = [[names.words(f"أبو عبد الرحمن {n}")] for n in ("الحبلي", "المقرئ", "العمري") * 40]
    found, _ = _rulings_for([_unit(7, kunya)], hadith + OTHERS, narrators_of, many, **common)
    assert found == []   # a hundred and more men are called so


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
    db.executemany("INSERT INTO ruling VALUES ('muslim', 24, ?, ?, ?, ?, ?, ?, ?, ?, ?, 5, 60.0)", [
        (1, "", "ilal_ah", "ilal", "أبو حاتم", "قال أبي: هذا حديث منكر.", "سألت أبي عن حديث رواه سعيد؟", "باب", "no. 5"),
        (2, "a", "ilal_ah", "ilal", "أبو زرعة", "قال: هو باطل.", "", "باب", "no. 6"),
        (2, "a", "shahin", "nasikh_chapter", "ابن شاهين", "", "", "ذكر الناسخ", "p. 9"),
        (3, "", "ghost", "no_longer_in_config", "ابن شاهين", "", "", "باب", "p. 1")])   # a kind the config dropped
    db.commit()
    db.close()
    terms = client.get("/api/usul/terms").json()
    assert [(t["kind"], t["count"]) for t in terms] == [("nasikh_chapter", 1), ("ilal", 2)] and all(t["say"] for t in terms)
    page = client.get("/api/usul/terms/ilal", params={"offset": 1, "limit": 1}).json()
    assert page == {"kind": "ilal", "total": 2, "items": [{"collection": "muslim", "book": 24, "number": 2, "part": "a"}]}
    assert client.get("/api/usul/terms/nonsense").status_code == 404
    chains = client.get("/api/rijal/chains/muslim/24").json()["rulings"]
    assert chains["1"] == [{"kind": "ilal", "label": RULINGS["kinds"]["ilal"]["label"], "quote_label": "", "scholar": "أبو حاتم",
                            "quote": "قال أبي: هذا حديث منكر.", "asked": "سألت أبي عن حديث رواه سعيد؟", "chapter": "باب",
                            "source": rule()["sources"]["ilal_ah"]["label"], "page": "no. 5"}]
    assert [r["kind"] for r in chains["2a"]] == ["nasikh_chapter", "ilal"]
    assert chains["2a"][0]["quote_label"] == RULINGS["kinds"]["nasikh_chapter"]["quote_label"]
    assert "3" not in chains   # a kind the config no longer names is left out, not an error
    assert client.get("/api/usul/terms/ghost").status_code == 404


def _book(key: str, markup: str) -> list[Entry]:
    """The entries of `markup`, written as the OpenITI file of book `key` writes them."""
    return books.entries("#META#Header#End#\n" + markup, rule()["books"][key])


def _ilal(body: str) -> list[ruling.Ruling]:
    [entry] = _book("ilal_ah", f"### | بيان علل الأحاديث\n### | 1 -\n{body}\n")
    return ruling.read(entry, "ilal", RULINGS)[0]


ASKED = "سألت أبي عن حديث رواه سعيد، عن قتادة، عن النبي (ص) : من قال كذا دخل الجنة؟"


def test_a_bang_ends_a_sentence_only_at_a_paragraph_end_or_another_speaker_and_not_in_the_middle_of_an_answer():
    whole = _ilal(f"# {ASKED} قال أبي: ما أدري ما هذا! لا أعرف لقتادة هذا ولا لسعيد، وهذا من تخاليط فلان.")
    assert [r.quote for r in whole] == ["قال أبي: ما أدري ما هذا! لا أعرف لقتادة هذا ولا لسعيد، وهذا من تخاليط فلان."]
    cut = _ilal(f"# {ASKED} قال أبي: هذا خطأ! وقال أبو زرعة: بل هو صحيح.")
    assert [(r.scholar, r.quote) for r in cut] == [("أبو حاتم", "قال أبي: هذا خطأ!"), ("أبو زرعة", "وقال أبو زرعة: بل هو صحيح.")]
    paragraph = _ilal(f"# {ASKED} قال أبي: هذا خطأ!\n# ثم ذكرت له حديثا آخر.")
    assert paragraph[0].quote == "قال أبي: هذا خطأ!"


def test_an_ilal_unit_with_two_questions_is_left_out_with_its_reason():
    [entry] = _book("ilal_ah", f"### | بيان علل الأحاديث\n### | 1 -\n# {ASKED} قال أبي: منكر.\n# {ASKED} قال أبي: باطل.\n")
    assert ruling.read(entry, "ilal", RULINGS) == ([], "2 questions in the unit")


def test_a_bare_qal_after_a_follow_up_question_is_the_scholar_asked_and_each_answer_keeps_its_own_question():
    found = _ilal("# سألت أبي وأبا زرعة عن حديث رواه سعيد، عن قتادة، عن النبي (ص) : من قال كذا؟ قال أبي: هذا حديث منكر.\n"
                  "# قلت لأبي زرعة: فما تقول؟ قال: هو باطل.\n# قلت لأبي: فما علته؟ قال: تفرد به سعيد.")
    assert [(r.scholar, r.quote) for r in found] == [("أبو حاتم", "قال أبي: هذا حديث منكر."), ("أبو زرعة", "قال: هو باطل."),
                                                     ("أبو حاتم", "قال: تفرد به سعيد.")]   # two answers of Abu Hatim, two rulings
    assert found[0].asked == "سألت أبي وأبا زرعة عن حديث رواه سعيد، عن قتادة، عن النبي (ص) : من قال كذا؟"
    assert found[1].asked.endswith("قلت لأبي زرعة: فما تقول؟") and "منكر" not in found[1].asked   # an earlier answer is no part of the question
    assert found[2].asked.endswith("قلت لأبي: فما علته؟")
    # The chain the unit is matched on starts after the asker, so أبي and أبا زرعة are not chain names.
    assert found[0].head.startswith("سعيد، عن قتادة")


def test_only_a_kind_whose_config_keeps_the_question_stores_it():
    [entry] = _book("shahin", "### | ذكر زيارة القبور\n### | 5 -\n# حدثنا أحمد، عن أبي هريرة قال: «نهيتكم» قال الشيخ هذا ناسخ للأول.\n")
    assert [r.asked for r in ruling.read(entry, "nasikh_chapter", RULINGS)[0]] == [""]


def _mawduat(markup: str) -> list[ruling.Ruling]:
    found = []
    for entry in _book("mawduat", markup):
        found += ruling.read(entry, "mawdu_listed", RULINGS)[0]
    return found


def test_a_bab_splits_at_any_ordinal_hadith_and_at_a_bare_ordinal_with_a_colon():
    markup = ("# باب ذكر فضل كذا\n"
              '# حدثنا أحمد عن سفيان عن جابر قال قال رسول الله صلى الله عليه وسلم: " من فعل كذا فله كذا " هذا حديث لا يصح.\n'
              '# الثاني: حدثنا بكر عن عمرو عن أنس قال قال رسول الله صلى الله عليه وسلم: " من قال كذا غفر له " هذا حديث موضوع.\n'
              '# الحديث السادس: حدثنا زيد عن خالد عن علي قال قال رسول الله صلى الله عليه وسلم: " من صام كذا " هذا حديث باطل.\n'
              '# الحديث الحادي عشر: حدثنا سالم عن نافع عن عمر قال قال رسول الله صلى الله عليه وسلم: " من صلى كذا " لا أصل له.\n')
    found = _mawduat(markup)
    assert [r.quote for r in found] == ["هذا حديث لا يصح.", "هذا حديث موضوع.", "هذا حديث باطل.", "لا أصل له."]
    assert [r.head.split()[0] for r in found] == ["باب", "الثاني:", "الحديث", "الحديث"]   # each verdict sits with its own hadith


def test_a_bare_bab_line_opens_a_unit_and_a_joint_verdict_covers_the_hadith_waiting_for_one():
    markup = ("# باب ذكر فضل كذا\n"
              '# حدثنا أحمد عن سفيان عن جابر قال قال رسول الله: " من فعل كذا " هذا حديث لا يصح.\n'
              "# باب\n"
              '# ما ذكر أن الله قرأ طه ويس قبل خلق آدم حدثنا يعقوب عن بكر قال قال رسول الله: " إن الله قرأ طه "\n'
              '# الثاني: حدثنا زيد عن خالد عن علي قال قال رسول الله: " إن الله قرأ يس "\n'
              "# هذان حديثان موضوعان.\n")
    units = _book("mawduat", markup)
    assert len(units) == 2   # the bare باب line opened the second
    first, second = (ruling.read(u, "mawdu_listed", RULINGS)[0] for u in units)
    assert [r.quote for r in first] == ["هذا حديث لا يصح."]   # not the verdict of the next bab
    assert [r.quote for r in second] == ["هذان حديثان موضوعان."] * 2
    assert [r.head.split()[0] for r in second] == ["باب", "الثاني:"]
    assert second[0].chapter == "باب ما ذكر أن الله قرأ طه ويس قبل خلق آدم"


def test_a_bab_title_runs_to_the_chain_so_a_rawa_inside_it_stays():
    [found] = _mawduat('# باب ما روى أن الله عرج إلى السماء حدثنا أحمد عن سفيان قال قال رسول الله: " عرج بي " هذا حديث موضوع.\n')
    assert found.chapter == "باب ما روى أن الله عرج إلى السماء"


def test_a_shahin_remark_is_paged_where_it_stands_and_loses_the_editors_zeros_and_a_cut_tail():
    markup = ("### | ذكر زيارة القبور\n### | 5 -\n# PageV01P010\n# حدثنا أحمد، عن أبي هريرة قال: «نهيتكم عن زيارة القبور»\n"
              "# PageV01P011\n# قال الشيخ هذا ناسخ للأول 0 وهذا أصح سندا.\n")
    [entry] = _book("shahin", markup)
    [found], _ = ruling.read(entry, "nasikh_chapter", RULINGS)
    assert found.quote == "قال الشيخ هذا ناسخ للأول وهذا أصح سندا."   # the 0 between the two is gone
    assert entry.where(found.at) == "p. 11"   # the remark's page, not the page the unit opens on
    cut = "قال الشيخ هذا حديث صحيح. ومما يدل على ذلك: ما"
    [entry] = _book("shahin", f"### | ذكر زيارة القبور\n### | 6 -\n# حدثنا أحمد، عن أبي هريرة قال: «نهيتكم» {cut}\n")
    assert ruling.read(entry, "nasikh_chapter", RULINGS)[0][0].quote == "قال الشيخ هذا حديث صحيح."   # back to the last full stop
    [entry] = _book("shahin", "### | ذكر زيارة القبور\n### | 7 -\n# حدثنا أحمد، عن أبي هريرة قال: «نهيتكم» هذا الحديث يحتمل أن يكون ناسخا ومما يدل على ذلك: ما\n")
    [found], _ = ruling.read(entry, "nasikh_chapter", RULINGS)
    assert (found.quote, found.chapter) == ("", "ذكر زيارة القبور")   # no full stop to cut back to: no remark, the chapter still shows


def test_a_lower_score_outside_the_tie_ratio_is_dropped_and_a_short_hadith_wholly_held_passes_the_whole_floor():
    knobs = RULINGS["match"]
    chosen, how = match.choose({"a": 100.0, "b": 95.0, "c": 70.0}, 100.0, lambda key: True, knobs)
    assert (sorted(key for key, _ in chosen), how) == (["a", "b"], "matched")   # c is the same text, scoring too far below
    held = (knobs["whole_floor"] + knobs["floor"]) / 2
    assert match.choose({"a": held}, held, lambda key: True, knobs)[1] == "matched"   # all a short matn could score, held
    assert match.choose({"a": held}, held / knobs["whole"] * 2, lambda key: True, knobs)[1] == "below_floor"   # a share of a long one


def test_a_ruling_book_missing_from_disk_stops_the_build_and_a_big_change_in_rows_does_not_pass(paths, tmp_path):  # noqa: F811
    (paths["usul_books_dir"] / "ilal_ah.txt").unlink()
    with pytest.raises(SystemExit, match="ilal_ah.txt"):
        build_usul.build()
    target = tmp_path / "old.db"
    old = sqlite3.connect(target)
    old.executescript(build_usul._SCHEMA)
    old.executemany("INSERT INTO ruling VALUES ('muslim', 24, ?, '', 'shahin', 'nasikh_chapter', '', '', '', '', '', 1, 1.0)",
                    [(i,) for i in range(100)])
    old.commit()
    old.close()
    ratio = rule()["max_change_ratio"]
    build_usul.guard_change(target, "ruling", 100 + int(100 * ratio), ratio)   # within the ratio
    with pytest.raises(SystemExit, match="ruling rows went 100 to 150"):
        build_usul.guard_change(target, "ruling", 150, ratio)
    build_usul.guard_change(tmp_path / "none.db", "ruling", 150, ratio)   # nothing built yet
