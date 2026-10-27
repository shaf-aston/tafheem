"""A typed verb read back into sarf's table (services/sarf/verb_reader.py)."""
import pytest

from backend.services.sarf import conjugation
from backend.services.sarf import verb_reader


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
    "أَدْرِي",       # I know, as close as "inform!" (f.): the sukun its ي lacks is no mark
    "الكتاب"])
def test_a_word_that_is_not_only_a_command_is_left_alone(word: str):
    assert verb_reader.command(word) is None


def test_the_dictionarys_root_settles_a_tie():
    assert verb_reader.command("اُكْتُبُوا") is None   # also a Form VIII passive of كبو
    cell = verb_reader.command("اُكْتُبُوا", root="كتب")
    assert cell and (cell.person, cell.number) == ("2", "p")


def test_bare_letters_are_read_only_where_the_sentence_vouches_for_a_verb():
    assert verb_reader.command("اكتبي", root="كتب") is None   # without vowels it fits much else
    cell = verb_reader.command("اكتبي", root="كتب", vouched=True)
    assert cell and (cell.person, cell.gender, cell.number) == ("2", "f", "s")
    assert verb_reader.command("أكرم", vouched=True) is None   # also the past أَكْرَمَ: still not only a command


def test_after_a_jazm_or_nasb_particle_it_is_the_present_not_a_command():
    assert verb_reader.command("أَقِمْ", governed=True) is None   # لم أَقِمْ
    assert verb_reader.command("يَرْجِعُوا", governed=True, root="رجع") is None   # لَنْ يَرْجِعُوا
    assert verb_reader.command("يَصْبِرْ", root="صبر") is None   # not the four-letter root يصبر


def test_the_dropped_ta_of_forms_v_and_vi_is_read():
    cells = verb_reader.read("تَحَاسَدُوا")
    assert verb_reader.Cell("حسد", "VI", "jussive", "2", "m", "p") in cells   # لا تَحَاسَدُوا
    assert verb_reader.Cell("نزل", "V", "mudari", "3", "m", "s") not in verb_reader.read("تَنَزَّلُ")  # يَتَنَزَّلُ has no تَتَ


@pytest.mark.parametrize("word, root, form, column, person", [
    ("يَقْرَءُونَ", "قرء", "I-fataha", "mudari", "3"),     # يَقْرَءُونَ الْكِتَابَ: on the line, not on و
    ("قَرَءُوا", "قرء", "I-fataha", "madi", "3"),
    ("اِقْرَءُوا", "قرء", "I-fataha", "amr", "2"),
    ("يَسْتَهْزِءُونَ", "هزء", "X", "mudari", "3"),       # not on ي either
])
def test_a_hamza_before_the_long_waw_may_stand_on_the_line(word, root, form, column, person):
    assert verb_reader.Cell(root, form, column, person, "m", "p") in verb_reader.read(word)


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



@pytest.mark.parametrize("word", ["تَشَأْ", "تَطَأَ", "تَجِئُ", "تَطَأُ"])
def test_a_hamzated_verb_tried_against_a_doubled_hamza_root_is_read_without_failing(word: str):
    # The reader tries roots like شأأ, which sarf shapes down to one letter; the hadith index reads every word of
    # every matn, so one failure here stops the server's whole deploy.
    verb_reader.command(word)


@pytest.mark.parametrize("word", ["حَفْصَةَ", "شَجَرَةَ", "دَحْرَجَةَ"])
def test_a_word_written_with_ta_marbuta_is_no_verb(word: str):
    # ة is the noun's feminine ending; the verb's تاء التأنيث is the ساكنة (قَالَتْ), so no blank of a
    # verb's shape takes it: حَفْصَةَ is no فَعْلَلَ of ح ف ص ة
    assert verb_reader.read(word) == [] and verb_reader.reading_of(word) is None


def test_the_same_shape_with_a_root_letter_in_place_of_the_ta_marbuta_is_still_a_verb():
    assert any(c.root == "دحرج" for c in verb_reader.read("دَحْرَجَ"))


def test_a_madda_carries_a_vowel_so_its_command_is_read_typed():
    # آتِ is أَ + ا: the fatha is written into the letter, so the word is typed, not bare letters
    cell = verb_reader.command("آتِ")
    assert cell and cell.root == "أتي" and (cell.person, cell.number) == ("2", "s")
    assert verb_reader.command("اتِ") is None   # the same letters with no vowel before the last


_KNOWN = {"هَدَى", "أَعْلَنَ", "أَعْلَى", "آتَى"}.__contains__   # the verbs a dictionary's texts use


@pytest.mark.parametrize("word, past", [("اِهْدِنَا", "هَدَى"), ("آتِنَا", "آتَى")])
def test_a_command_the_dictionary_has_with_its_object_written_on_beats_a_verb_it_never_saw(word: str, past: str):
    assert verb_reader.reading_of(word)["num"] == "d"   # alone, the closest cell is a dual of هَدَنَ / آتَنَ
    found = verb_reader.reading_of(word, _KNOWN)
    assert (found["asp"], found["num"], found["lex"], found["enc0"]) == ("c", "s", past, "1p_dobj")
    assert verb_reader.reading_of(word, lambda _: False)["num"] == "d"   # nearest case: it has neither verb


def test_a_word_the_table_has_no_cell_for_is_read_with_its_object_split_off_by_the_dictionary():
    """اِهْدِهِمْ: no cell holds the whole word, so the verb before هِمْ is read, among the verbs the dictionary has."""
    assert verb_reader.reading_of("اِهْدِهِمْ", _KNOWN)["lex"] == "هَدَى"
    assert "lex" not in verb_reader.reading_of("اِهْدِهِمْ")   # nearest case: هَدَى، هَدَا or هَدِيَ


def test_of_the_closest_cells_the_one_the_dictionary_has_names_the_verb():
    assert "lex" not in verb_reader.reading_of("اِهْدِ")   # هَدَى، هَدَا or هَدِيَ: the cells disagree
    assert verb_reader.reading_of("اِهْدِ", _KNOWN)["lex"] == "هَدَى"


def test_a_whole_word_the_dictionary_has_is_not_split():
    found = verb_reader.reading_of("أَعْلِنَا", _KNOWN)   # announce, you two: no أَعْلَى + نا
    assert (found["num"], found["lex"], found.get("enc0")) == ("d", "أَعْلَنَ", None)
