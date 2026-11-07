"""The entry cut into its words: the model's answer held against the book."""
import json

import pytest

from backend.services.dictionary import root_senses

LINES = [
    "مِنْ ذَلِكَ الرَّطْبُ وَالرَّطِيبُ.",
    "وَالرُّطَبُ مَعْرُوفٌ.",
    "وَيُقَالُ أَرْطَبَ النَّخْلُ إِرْطَابًا.",
    "وَاللَّهُ أَعْلَمُ.",
]


def _answer(**changes):
    senses = [
        {"lines": [1], "word": "الرطب", "say": "al-raṭb", "gloss": "moist"},
        {"lines": [2, 3], "word": "الرطب", "say": "al-ruṭab", "gloss": "ripe dates",
         "examples": [{"line": 3, "arabic": "أرطب النخل إرطابا", "say": "arṭaba", "english": "The palms bore dates."}]},
        {"lines": [4], "word": "", "gloss": "And God knows best."},
    ]
    senses[1].update(changes)
    return {"senses": senses}


def test_the_word_and_sayings_are_printed_as_the_book_spells_them():
    senses = root_senses.check(_answer(), LINES)
    assert senses[0]["word"] == "الرَّطْبُ"
    # The second sense looks in its own lines, so it finds the book's الرُّطَبُ
    assert senses[1]["word"] == "الرُّطَبُ"
    assert senses[1]["examples"][0]["arabic"] == "أَرْطَبَ النَّخْلُ إِرْطَابًا"


def test_a_word_the_lines_do_not_print_is_dropped_with_its_latin():
    senses = root_senses.check(_answer(word="تمر"), LINES)
    assert senses[1]["word"] == "" and senses[1]["say"] == ""


def test_a_saying_from_another_senses_line_is_dropped():
    example = {"line": 1, "arabic": "الرطب", "english": "x"}
    assert root_senses.check(_answer(examples=[example]), LINES)[1]["examples"] == []


def test_a_skipped_or_doubled_line_stays_with_the_word_before_it():
    skipped = root_senses.check(_answer(lines=[3]), LINES)
    assert [s["lines"] for s in skipped] == [[0, 1], [2, 2], [3, 3]]
    assert skipped[1]["examples"]  # still in its own line
    doubled = root_senses.check(_answer(lines=[1, 3]), LINES)
    assert [s["lines"] for s in doubled] == [[0, 0], [1, 2], [3, 3]]
    assert root_senses.check({"senses": _answer()["senses"][:2]}, LINES)[-1]["lines"] == [1, 3]


def test_an_answer_that_misreads_the_entry_is_refused_whole():
    # More than a third of the lines left for check to place: not a slip.
    assert root_senses.check({"senses": _answer()["senses"][:1]}, LINES) is None
    assert root_senses.check(_answer(gloss=""), LINES) is None
    assert root_senses.check({"lines": []}, LINES) is None


def test_cut_asks_once_more_when_the_first_answer_does_not_fit():
    answers = iter([json.JSONDecodeError("cut off", "", 0), {"senses": []}, _answer()])

    def ask(lines):
        answer = next(answers)
        if isinstance(answer, Exception):
            raise answer
        return answer

    assert root_senses.cut(ask, LINES) is None  # two tries, both spent
    assert root_senses.cut(ask, LINES)[1]["word"] == "الرُّطَبُ"


def test_chunks_join_into_one_entry_with_their_lines_moved_along():
    first, second = root_senses.check(_answer(), LINES), root_senses.check(_answer(), LINES)
    joined = root_senses.joined([first, second])
    assert [s["lines"] for s in joined][3:] == [[4, 4], [5, 6], [7, 7]]
    assert joined[4]["examples"][0]["line"] == 6
    assert root_senses.fits(joined, 8)
    assert root_senses.joined([first, None]) is None


def test_kept_senses_must_still_fit_the_book():
    senses = root_senses.check(_answer(), LINES)
    assert root_senses.fits(senses, len(LINES))
    assert not root_senses.fits(senses, len(LINES) + 1)


def test_shown_carries_each_senses_own_lines():
    shown = root_senses.shown(root_senses.check(_answer(), LINES), LINES)
    assert shown[1]["arabic"] == LINES[1:3]
    assert shown[2]["word"] == ""


def test_a_line_that_only_leads_in_joins_the_quote_it_introduces():
    lines = ["قَالَ الشَّاعِرُ:", "صدر البيت ... عجزه", "وَاللَّهُ أَعْلَمُ."]
    answer = {"senses": [
        {"lines": [1], "word": "", "gloss": "The poet said"},
        {"lines": [2], "word": "", "gloss": "A verse"},
        {"lines": [3], "word": "", "gloss": "God knows best"},
    ]}
    senses = root_senses.check(answer, lines)
    assert [s["lines"] for s in senses] == [[0, 1], [2, 2]]
    assert root_senses.fits(senses, 3)


def test_the_model_copies_the_books_explanation_before_it_glosses():
    # The model writes its answer in order: asked for the gloss first, it reached
    # for a word's everyday sense and glossed سَمِعْتُ بِالشَّيْءِ، إِذَا أَشَعْتُهُ "I heard".
    from backend.services.ai import prompts
    shape = prompts.ROOT_ENTRY_SENSES_USER.rsplit('"senses"', 1)[1]
    assert shape.index('"means"') < shape.index('"gloss"')


def test_the_explanation_the_model_copied_is_not_kept():
    answer = _answer(means="معروف")
    assert all("means" not in s for s in root_senses.check(answer, LINES))


def test_a_word_given_wrong_is_a_word_not_given():
    # Its lines fall to the word before it, as a skipped line does.
    for wrong in ({"gloss": ""}, {"lines": "2-3"}, {"lines": []}):
        senses = _answer()["senses"]
        senses.insert(1, {"lines": [2], "word": "الرطب", **wrong})
        senses[2]["lines"] = [3]
        assert [s["lines"] for s in root_senses.check({"senses": senses}, LINES)] == [[0, 1], [2, 2], [3, 3]]
    assert root_senses.check({"senses": ["not a sense", *_answer()["senses"]]}, LINES)


def test_cut_asks_once_more_when_the_call_itself_fails():
    answers = iter([RuntimeError("Error code: 400 json_validate_failed"), _answer()])

    def ask(lines):
        answer = next(answers)
        if isinstance(answer, Exception):
            raise answer
        return answer

    assert root_senses.cut(ask, LINES)[1]["word"] == "الرُّطَبُ"


def test_cut_raises_a_call_that_fails_both_times_and_a_timeout_at_once():

    def broken(lines):
        raise RuntimeError("refused")

    with pytest.raises(RuntimeError):
        root_senses.cut(broken, LINES)
    calls = []

    def slow(lines):
        calls.append(1)
        raise TimeoutError

    with pytest.raises(TimeoutError):
        root_senses.cut(slow, LINES)
    assert len(calls) == 1
