"""The entry cut into its words: the model's answer held against the book."""
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


def test_lines_out_of_order_or_missing_are_refused_whole():
    assert root_senses.check(_answer(lines=[3]), LINES) is None
    assert root_senses.check({"senses": _answer()["senses"][:2]}, LINES) is None
    assert root_senses.check(_answer(gloss=""), LINES) is None
    assert root_senses.check({"lines": []}, LINES) is None


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


def test_pieces_keep_whole_lines_and_never_end_on_a_lead_in():
    lines = ["a" * 300, "قَالَ:", "b" * 300, "c" * 300]
    pieces = root_senses.cut(lines, 320)
    # The lead-in fits the first piece, so the verse it introduces comes too
    assert [len(p) for p in pieces] == [3, 1]
    assert sum(pieces, []) == lines
    assert root_senses.covered(lines, 320, most=1) == 3


def test_a_long_entry_is_asked_for_in_pieces_with_its_numbers_moved_along():
    asked = []

    def ask(piece):
        asked.append(len(piece))
        return {"senses": [{"lines": list(range(1, len(piece) + 1)), "word": "", "gloss": "x",
                            "examples": [{"line": 1, "arabic": piece[0][:3], "english": "e"}]}]}

    lines = ["مِنْ ذَلِكَ"] * 5
    senses, done = root_senses.make(lines, ask, budget=25)
    assert asked == [2, 2, 1] and done == 5
    assert [s["lines"] for s in senses] == [[0, 1], [2, 3], [4, 4]]
    assert [s["examples"][0]["line"] for s in senses] == [0, 2, 4]
    assert root_senses.fits(senses, 5)
    # Only the pieces asked for while a reader waits
    asked.clear()
    assert root_senses.make(lines, ask, budget=25, most=1)[1] == 2


def test_a_piece_that_will_not_fit_twice_fails_the_whole():
    assert root_senses.make(["مِنْ ذَلِكَ"], lambda piece: {"senses": []}, budget=100) == (None, 0)
