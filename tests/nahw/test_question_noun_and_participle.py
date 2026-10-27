"""ما/مَن heading a verbless sentence, and the active participle the dictionary lacks."""
import pytest

from backend.services.sarf import morphology
from backend.services.sarf import noun_reader
from backend.services.nahw.syntax.facts import Sentence
from tests.nahw_helpers import analyze, needs_parser


def _roles(sentence):
    return [w["role"] for w in analyze(sentence)["words"]]  # by the rules, never a stored record


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("مَا هِيَ", ["مبتدأ", "خبر"]),
    ("مَنْ أَبُوكَ", ["مبتدأ", "خبر"]),
    ("الْقَارِعَةُ مَا الْقَارِعَةُ", ["مبتدأ", "مبتدأ", "خبر"]),
    ("الْحَاقَّةُ مَا الْحَاقَّةُ", ["مبتدأ", "مبتدأ", "خبر"]),
    # متى/كيف stand for a time or state: the khabar brought forward, not the mubtada
    ("مَتَى السَّفَرُ", ["خبر", "مبتدأ"]),
])
def test_question_noun_heads_its_sentence(sentence, roles):
    assert _roles(sentence) == roles


@pytest.mark.parametrize("word, lex, pattern, gen, stt", [
    ("الْحَاقَّةُ", "حاق", "ال1َا2ّة", "f", "d"),
    ("الْقَارِعَةُ", "قارع", "ال1َا2ِ3ة", "f", "d"),
    ("كَاتِبٌ", "كاتب", "1َا2ِ3", "m", "i"),
])
def test_active_participle_read_off_sarf(word, lex, pattern, gen, stt):
    r = noun_reader.reading_of(word)
    assert (r["pos"], r["lex"], r["pattern"], r["gen"], r["stt"]) == ("adj", lex, pattern, gen, stt)


def test_a_reading_spelled_with_other_letters_does_not_fit():
    from backend.services.sarf.morphology import _agreeing
    assert not _agreeing("الْحَاقَّةُ", [{"diac": "إِلْحاقُهُ", "atbtok": "إِلْحاق+ُهُ"}])


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("مَا جَزَاؤُهُ إِلَّا سَجْنُهُ", ["حرف", "مبتدأ", "حرف", "خبر"]),  # إلا hung on the mubtada
    ("إِنْ هَذَا إِلَّا سِحْرٌ", ["حرف", "مبتدأ", "حرف", "خبر"]),  # إلا hung on the negation
    ("مَا مُحَمَّدٌ إِلَّا رَسُولٌ", ["حرف", "مبتدأ", "حرف", "خبر"]),
    # left alone: a verb takes the word after إلا, and لا of the genus keeps its own reading
    ("مَا جَاءَ إِلَّا زَيْدٌ", ["حرف", "فعل", "حرف", "فاعل"]),
    ("لَا إِلَهَ إِلَّا اللَّهُ", ["حرف", "اسم لا", "حرف", "بدل"]),
    ("إِنْ أَنْتُمْ إِلَّا تَكْذِبُونَ", ["حرف", "مبتدأ", "حرف", "فعل"]),  # a verb after إلا is its own sentence
])
def test_after_negation_and_illa_the_noun_is_the_khabar(sentence, roles):
    assert _roles(sentence) == roles


def _tok(id, form, pos, head, rel, **feats):
    return {"id": id, "form": form, "lemma": form, "pos": pos, "head": head, "rel": rel, "token_type": "baseword",
            "ud": "", "pos_camel": "verb" if pos == "VRB" else "noun", "vox": "na", "asp": "p" if pos == "VRB" else "na",
            "stt": "i", "cas": "u", "base": form, **feats}


@pytest.mark.parametrize("with_verb", [False, True])
def test_hasr_khabar_waits_for_a_verbless_clause(with_verb):
    """ما زيدٌ [قالَ] إلا حقٌّ: with a verb before it the word after إلا is that verb's, not a khabar."""
    from backend.services.nahw.syntax.repair.khabar import hasr_khabar
    words = [_tok(1, "ما", "PRT", 0, "---"), _tok(2, "زيد", "PROP", 1, "SBJ")]
    if with_verb:
        words.append(_tok(3, "قال", "VRB", 2, "MOD"))
    n = len(words)
    words += [_tok(n + 1, "إلا", "PRT", 2, "MOD"), _tok(n + 2, "حق", "NOM", n + 1, "OBJ")]
    hasr_khabar(words)
    told = words[-1]
    assert (told["head"], told["rel"]) == ((n + 1, "OBJ") if with_verb else (0, "---"))


@pytest.mark.parametrize("change, moved", [
    (None, True),
    ("not_hasr", False),      # ما زيدٌ في حقٍّ: only إلا restricts; في does not
    ("before_illa", False),   # the khabar is the word after إلا
    ("subject_particle", False),  # a mubtada is a noun
    ("told_verb", False),     # إن أنتم إلا تكذبون: a verb after إلا is a sentence, not this noun khabar
])
def test_hasr_khabar_needs_each_of_its_parts(change, moved):
    from backend.services.nahw.syntax.repair.khabar import hasr_khabar
    words = [_tok(1, "ما", "PRT", 0, "---"), _tok(2, "زيد", "PROP", 1, "SBJ"),
             _tok(3, "إلا", "PRT", 2, "MOD"), _tok(4, "حق", "NOM", 3, "OBJ")]
    told = words[3]
    if change == "not_hasr":
        words[2].update(form="في", lemma="في")
    elif change == "before_illa":
        words[2]["id"], told["id"], words[2]["head"], told["head"] = 4, 3, 2, 4
        words[2], words[3] = words[3], words[2]
    elif change == "told_verb":
        told.update(pos="VRB", pos_camel="verb")
    elif change == "subject_particle":
        words[1].update(pos="PRT", pos_camel="part")
    hasr_khabar(words)
    assert (told["head"] == 0) is moved


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("مَا ذَاهِبٌ الْمُسْلِمُونَ", ["حرف", "مبتدأ", "فاعل"]),
    ("أَذَاهِبٌ زَيْدٌ", ["مبتدأ", "فاعل"]),  # the question hamza written onto the وصف
    ("هَلْ نَاجِحٌ أَخُوكَ", ["حرف", "مبتدأ", "فاعل"]),
    # not a مبتدأ وصف: ما الحجازية with its khabar in nasb, and a question noun before a pronoun
    ("مَا زَيْدٌ ذَاهِبًا", ["حرف", "اسم كان", "خبر كان"]),
    ("مَا هِيَ", ["مبتدأ", "خبر"]),
])
def test_a_wasf_after_negation_or_question_is_the_mubtada(sentence, roles):
    assert _roles(sentence) == roles


@needs_parser
def test_the_doer_of_a_wasf_stands_in_for_the_khabar():
    assert analyze("مَا ذَاهِبٌ الْمُسْلِمُونَ")["words"][2]["reason"].endswith("فاعل سدّ مسدّ الخبر")


def _clause(lead="ما", wasf=None, doer=None, after=None):
    words = [_tok(1, lead, "PRT", 2, "MOD"),
             _tok(2, "ذاهب", "NOM", 0, "---", **{"pos_camel": "adj", "ud": "ADJ", "num": "s", **(wasf or {})}),
             _tok(3, "زيد", "PROP", 2, "SBJ", **(doer or {}))]
    if after:
        words.append(_tok(4, "ذهب", "VRB", 2, "MOD"))
    return words


@pytest.mark.parametrize("kw, found", [
    ({}, True),
    ({"lead": "في"}, False),                      # no negation or question before it
    ({"wasf": {"num": "p"}}, False),             # أقائمون الزيدون: plural, so the khabar
    ({"wasf": {"stt": "d"}}, False),             # with ال it is no وصف at work
    ({"wasf": {"pos_camel": "noun", "ud": "NOUN"}}, False),  # a plain noun describes nothing
    ({"wasf": {"cas": "a", "case": "a"}}, False),  # not in raf'
    ({"doer": {"cas": "g", "case": "i"}}, False),   # the doer is in raf'
    ({"after": True}, False),                     # a verb in the clause
])
def test_described_doer_needs_each_of_its_parts(kw, found):
    s = Sentence(_clause(**kw))
    assert (s.described_doer is not None) is found


@needs_parser
def test_question_hamza_split_only_off_the_first_word_that_needs_it():
    first = morphology.pick(["أَذَاهِبٌ", "زَيْدٌ"])[0]
    assert (first["prc3"], first["atbtok"]) == ("Aa_ques", "أَ+_ذاهِبٌ")
    assert morphology.pick(["أَمِنَ", "زَيْدٌ"])[0].get("prc3") != "Aa_ques"  # read whole, though مِنَ is a word
    assert morphology.pick(["زَيْدٌ", "أَذَاهِبٌ"])[1].get("prc3") != "Aa_ques"  # only a sentence's first word


@needs_parser
@pytest.mark.parametrize("words, verb", [
    (["نصر", "زيد", "بكرا"], True),        # the written alif of nasb tanween needs an عامل
    (["نصر", "زيد"], False),               # nothing in nasb: نَصْرُ زيدٍ stands
    (["نَصْرُ", "زَيْدٍ", "بَكْرًا"], False),  # typed vowels choose, not this rule
    (["ما", "زيد", "ذاهبا"], False),       # a particle is there to work the nasb
    (["يا", "نصر", "بكرا"], False),        # يا works it (منادى), nothing else need be a verb
    (["نصر", "عصا"], False),               # the alif is عصا's own letter, no nasb to work
    (["زَيْدٌ", "فَاهِمٌ", "الدَّرْسَ"], False),  # a typed tanween is a sign of the noun: no فَأَهِم
    (["زَيْدٌ", "فَاهِمْ", "الدَّرْسَ"], True),   # nearest case: no tanween, the verb reading stands
])
def test_a_bare_first_word_is_the_verb_a_written_nasb_needs(words, verb):
    assert ("verb" in [r.get("pos") for r in morphology.pick(words)]) is verb


@needs_parser
def test_the_verb_is_the_plainest_reading_before_the_nasb():
    assert [r.get("pos") for r in morphology.pick(["زيد", "نصر", "بكرا"])][:2] == ["noun_prop", "verb"]
    assert [r.get("pos") for r in morphology.pick(["نصر", "نصر", "بكرا"])][:2] == ["verb", "noun_prop"]  # one عامل


@needs_parser
@pytest.mark.parametrize("word, diac", [
    ("زيدا", "زَيْدًا"),  # the name adds no letter; the verb زَيَّدَا adds a shadda (الأصل عدم الزيادة)
    ("جدا", "جِدّاً"),   # nearest case: جِدًّا's shadda is the stem's too, so the ranked reading stays
])
def test_a_bare_word_is_read_adding_the_fewest_letters(word, diac):
    assert morphology.pick([word])[0].get("diac") == diac


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("نصر زيد بكرا", ["فعل", "فاعل", "مفعول به"]),  # typed bare: the nasb alif is written
    ("ضرب زيد عمرا", ["فعل", "فاعل", "مفعول به"]),
    ("جئت بكرة", ["فعل", "مفعول فيه"]),            # بُكْرَة keeps its ة: still the time word
    ("جاء زيد راكبا", ["فعل", "فاعل", "حال"]),       # a state word stays the hal
    ("ضربوا زيدا", ["فعل", "مفعول به"]),             # not the verb زَيَّدَا: its shadda is no letter written
    ("رأيت زيدا", ["فعل", "مفعول به"]),
])
def test_bare_text_reads_its_written_nasb(sentence, roles):
    assert _roles(sentence) == roles


@pytest.mark.parametrize("typed, diac, case", [
    ("بكرا", "بَكْراً", "a"),
    ("عصا", "عَصا", None),        # the alif is the word's own
    ("بكرًا", "بَكْراً", None),    # a typed vowel speaks for itself (typed_case)
    ("بكر", "بَكْرٌ", None),       # no alif written
    ("بكرة", "بُكْرَةً", None),    # the tanween sits on the ة, nothing written shows it
])
def test_written_nasb_is_the_alif_of_tanween(typed, diac, case):
    from backend.services.nahw.syntax.facts.word import written_nasb
    assert written_nasb({"typed": typed, "diac": diac}) == case


@pytest.mark.parametrize("form, lemma, found", [
    ("بكرا", "بكرة", False),   # بَكَرًا: no ة, another word
    ("البكر", "بكرة", False),  # nor with the article
    ("سنين", "سنة", True),     # a plural drops it
    ("بكرة", "بكرة", True),
    ("ساعات", "ساعة", True),   # its ة written ت in the plural
    ("يوما", "يوم", True),
    ("الساعة", "ساعة", True),  # by its lemma, the ة written
])
def test_a_listed_word_keeps_its_ta(form, lemma, found):
    from backend.services.nahw.syntax.facts.word import listed
    assert listed({"form": form, "lemma": lemma, "typed": form}, "zarf_zaman") is found


@pytest.mark.parametrize("head_typed, rel, moved", [
    ("زيد", "---", True),     # bare subject: raf' by its place
    ("زيد", "IDF", True),     # nasb is no مضاف إليه
    ("زيد", "MOD", True),     # nor a نعت
    ("زيد", "IDF-diptote", False),  # عُمَرَ typed: a diptote's fatha is its jarr
    ("زيدًا", "---", False),  # the subject typed in nasb is no raf' subject
])
def test_a_written_nasb_after_the_subject_is_the_object(head_typed, rel, moved):
    from backend.services.nahw.syntax.repair.subject_clash import subject_clash
    last = dict(typed="عمرا", diac="عَمْراً") if rel != "IDF-diptote" else dict(typed="عُمَرَ", diac="عُمَرَ")
    words = [_tok(1, "ضرب", "VRB", 0, "---"), _tok(2, "زيد", "PROP", 1, "SBJ", typed=head_typed),
             _tok(3, "عمر", "PROP", 2, rel.removesuffix("-diptote"), **last)]
    subject_clash(words)
    assert ((words[2]["head"], words[2]["rel"]) == (1, "OBJ")) is moved
