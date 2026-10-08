"""A typed verb read back into sarf's table (services/verb_reader.py)."""
import pytest

from backend.services import conjugation, verb_reader


@pytest.mark.parametrize("radicals", ["كتب", "قول", "سير", "دعو", "رمي", "وعد", "مدد", "وقي", "أمر", "أخذ", "سأل", "قرأ", "دخل", "صبر", "ثبت", "سكن", "وهب"])
def test_every_word_sarf_builds_reads_back_to_its_own_cell(radicals: str):
    for form in conjugation.forms(3):
        try:
            table = conjugation.cells(radicals, form)
        except ValueError:
            continue
        for row, column, word in table:
            name = {"nahy": "jussive"}.get(column, column)
            if name == "amr" and not conjugation.addressed(row):
                continue
            mine = verb_reader.Cell(radicals, form, name, *conjugation.person_features(row))
            assert mine in verb_reader.read(word.split(" ")[-1]), (word, form, column)


@pytest.mark.parametrize("word, root, person", [
    ("اِجْلِسِي", "جلس", ("2", "f", "s")),   # the dictionary has no command: it offered a name
    ("ارْحَمُوا", "رحم", ("2", "m", "p")),
    ("أَفْشُوا", "فشو", ("2", "m", "p")),    # Form IV of a weak-ended root, not the past أَفْشَوْا
    ("سَمِّ", "سمو", ("2", "m", "s")),
    ("قُمْ", "قوم", ("2", "m", "s")),        # hollow: the middle letter is gone
    ("أَقِمْ", "قوم", ("2", "m", "s")),       # Form IV hollow, not أَقِّمْ with its shadda left off
    ("اتَّقِ", "وقي", ("2", "m", "s")),
])
def test_a_command_is_named_by_sarf(word: str, root: str, person: tuple):
    cell = verb_reader.command(word)
    assert cell and cell.root == root and (cell.person, cell.gender, cell.number) == person


@pytest.mark.parametrize("word", [
    "كَتَبُوا", "يَكْتُبُونَ", "أَكْتُبُ", "اِجْتَمَعُوا",
    "تَحَاسَدُوا",   # also the past: the dictionary keeps its say
    "أَحْمَدْ",      # a name paused on: no command has this fatha
    "الكتاب"])
def test_a_word_that_is_not_only_a_command_is_left_alone(word: str):
    assert verb_reader.command(word) is None


def test_the_dictionarys_root_settles_a_tie():
    assert verb_reader.command("اُكْتُبُوا") is None   # also a Form VIII passive of كبو
    cell = verb_reader.command("اُكْتُبُوا", root="كتب")
    assert cell and (cell.person, cell.number) == ("2", "p")


def test_after_a_jazm_or_nasb_particle_it_is_the_present_not_a_command():
    assert verb_reader.command("أَقِمْ", governed=True) is None   # لم أَقِمْ
    assert verb_reader.command("يَرْجِعُوا", governed=True, root="رجع") is None   # لَنْ يَرْجِعُوا
    assert verb_reader.command("يَصْبِرْ", root="صبر") is None   # not the four-letter root يصبر


def test_the_dropped_ta_of_forms_v_and_vi_is_read():
    cells = verb_reader.read("تَحَاسَدُوا")
    assert verb_reader.Cell("حسد", "VI", "jussive", "2", "m", "p") in cells   # لا تَحَاسَدُوا


def test_the_dictionary_form_is_sarfs_own_past():
    assert verb_reader.past(verb_reader.command("أَقِمْ")) == "أَقَامَ"


@pytest.mark.parametrize("word, root, form", [
    ("يَسْتَعْفِفْ", "عفف", "X"),        # the pair written apart, as the Qur'an writes it
    ("يَرْتَدِدْ", "ردد", "VIII"),
    ("يَمْدُدْ", "مدد", "I-nasara"),
    ("يَمُدِّ", "مدد", "I-nasara"),      # the kasra the book also allows
    ("يَمُدُّ", "مدد", "I-nasara"),      # the damma, where the letter before carries one
])
def test_a_doubled_verb_ending_a_jussive_is_read_in_every_spelling_the_book_allows(word: str, root: str, form: str):
    assert any(c.root == root and c.form == form and c.column == "jussive" for c in verb_reader.read(word))


def test_a_word_the_dictionary_lacks_is_spelled_as_the_table_prints_it_with_its_joined_letters_kept():
    assert verb_reader.known_as("فَلْيَسْتَعْفِفْ") == "فَلْيَسْتَعِفَّ"
    assert verb_reader.known_as("الكتاب") is None  # without its vowels a word fits too much

