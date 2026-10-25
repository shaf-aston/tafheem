"""هاء السكت (Awdah al-Masalik, الوقف; data: closed_words haa_sakt): a sakin ه after a word built
on its vowel, kept in a pause. The word is read as said joined to the next (Mufassal: إذا أدرجت
قلت مالي), and its card shows it as written with a line for the ه. On a word that takes i'rab
(كِتَابَهْ) the ه is a pronoun."""
from __future__ import annotations

import pytest

from backend.services.nahw import iraab
from backend.services.nahw.book import sakt_off, sakt_said
from backend.services.nahw.syntax import disambiguator
from backend.services.sarf import morphology
from tests.nahw_helpers import analyze, needs_parser


@pytest.mark.parametrize("word, said", [
    ("هِيَهْ", "هِيَ"), ("مَالِيَهْ", "مَالِيَ"), ("لِمَهْ", "لِمَ"),
    ("كِتَابَهْ", "كِتَابَ"),  # the shape alone: whether it is one is the reading's
    ("كِتَابُهْ", None), ("كِتَابَهُ", None), ("هِيَ", None), ("هْ", None),  # no fatha before it, a moved ه, none
])
def test_the_shape_is_a_sakin_ha_after_a_fatha(word, said):
    assert sakt_off(word) == said


def test_as_said_takes_the_picks_word_else_the_typed():
    assert morphology.as_said(["مَا", "هِيَهْ"], [{}, {"said": "هِيَ"}]) == ["مَا", "هِيَ"]


@needs_parser
@pytest.mark.parametrize("sentence, at, said", [
    ("وَمَا أَدْرَاكَ مَا هِيَهْ", 3, "هِيَ"),  # a pronoun
    ("هَلَكَ عَنِّي سُلْطَانِيَهْ", 2, "سُلْطَانِيَ"),  # a noun with ياء المتكلم
    ("لِمَهْ", 0, "لِمَ"),  # ما of question under جر
    ("عَلَامَهْ", 0, "عَلَامَ"),  # the same, read as a particle
    ("نَحْنَهْ", 0, None),  # نَحْنُ is built on damma: no reading is the vowels typed
    ("أَخَذْتُ كِتَابَهْ", 1, None),  # takes i'rab: its ه is the pronoun
])
def test_pick_reads_the_word_without_it_only_when_built(sentence, at, said):
    typed = sentence.split()
    assert morphology.pick(typed, disambiguator())[at].get("said") == said


@needs_parser
def test_the_card_shows_the_word_written_and_reads_it_said():
    found = analyze("هَلَكَ عَنِّي سُلْطَانِيَهْ")
    word = found["words"][2]
    assert (word["word"], word["role"]) == ("سُلْطَانِيَهْ", "فاعل")  # not a passive verb, not مفعول به
    assert sakt_said() in word["reason"]
    assert "".join(found["tree"]["words"][-2:]) == "سُلْطَانِيَهْ"  # the picture shows it as typed too


@needs_parser
def test_a_pronoun_is_built_on_its_own_vowel_not_on_the_ha():
    word = analyze("وَمَا أَدْرَاكَ مَا هِيَهْ")["words"][-1]
    assert (word["word"], word["role"], word["sign"]) == ("هِيَهْ", "خبر", "مبني على الفتح")


@needs_parser
def test_a_pronoun_ha_keeps_its_place():
    word = analyze("أَخَذْتُ كِتَابَهْ")["words"][-1]
    assert word["role"] == "مفعول به" and sakt_said() not in word["reason"]


@pytest.mark.parametrize("sentence, case", [
    ("جَاءَ سُلْطَانِيَ", None), ("جَاءَ حَالُكَ", "raf'"),
    ("ٱذْكُرُوا۟ نِعْمَتِىَ", None),  # the Quran's ى: its kasra before is the ya's, no جر
    ("سَلَّمْتُ عَلَى أَخِيكَ", None),  # the six nouns' ي is the sign, not the kaf's fatha
    ("إِلَى عِنْدِهِمْ", "jarr"),  # the kasra before the pronoun
    ("أَلَا إِنَّهُمْ", None),  # a particle's: نّ's fatha is its own build, no case
])
def test_an_attached_pronouns_vowel_is_not_the_nouns_case(sentence, case):
    """The fatha of سُلْطَانِيَ is the ya's own: the case before it is unseen. A recorded ayah
    names the word and leaves its case to this reading, so a fatha here was a wrong نصب."""
    assert morphology.analyze_sentence(sentence)[-1]["case"] == case


@pytest.mark.parametrize("recorded, case", [("فَاعِلٌ", "raf'"), ("مَفْعُوْلٌ بِهِ", "nasb")])
def test_a_recorded_name_on_the_ya_brings_its_case(recorded, case):
    """On ياء المتكلم the case is always unseen (مقدرة), so a recorded ayah's name, vowelled as
    the treebank writes it, is all that shows it."""
    tags = morphology.analyze_sentence("هَلَكَ عَنِّي سُلْطَانِيَ")
    roles = [{"role": None, "case": None}] * 2 + [{"role": recorded, "case": None}]  # tarkeeb_store's shape
    assert iraab.cards(tags, roles)[-1]["case"] == case


def test_a_recorded_name_brings_no_case_off_the_ya():
    """إِنَّهُمْ named مبتدأ by its pronoun: a built word, so the name gives it no case."""
    tags = morphology.analyze_sentence("أَلَا إِنَّهُمْ")
    roles = [{"role": None, "case": None}, {"role": "مُبْتَدَأٌ", "case": None}]
    assert iraab.cards(tags, roles)[-1]["case"] is None
