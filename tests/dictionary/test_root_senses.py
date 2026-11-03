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
