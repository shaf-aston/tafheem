"""Words the dictionary lacks, read off sarf's shapes instead of split into pieces they are not.

كَفُورًا is فَعُول, a صيغة مبالغة (Ibn Aqil V2 p111; page unchecked), not كَـ + فَوْر. مَنًّا is the فَعْل masdar
of a doubled root (Ibn Aqil V2 p121; page unchecked), not مِنْ + نا. لَأَفْعَلَنْ ends on the light nun of
emphasis (Ibn Aqil V3 p306; page unchecked), so its verb is built on the fatha.
"""
from backend.services.sarf import noun_reader
from backend.services.text.harakat import build_nun
from tests.nahw_helpers import analyze, card, needs_parser


def roles(sentence: str) -> list:
    return [c["role"] for c in analyze(sentence)["words"]]


def test_intensive_shapes_are_read():
    for word, pattern in (("كَفُورًا", "1َ2ُو3"), ("غَفَّارٌ", "1َ2َّا3"), ("مِقْدَامٌ", "مِ1ْ2َا3")):
        reading = noun_reader.reading_of(word)
        assert reading and reading["pattern"] == pattern and reading["pos"] == "adj", word


def test_a_doubled_masdar_of_two_letters_is_read_with_its_root_as_lemma():
    reading = noun_reader.reading_of("مَنًّا")
    assert reading["pattern"] == "1َ2ّ" and reading["cas"] == "a" and reading["lex"] == "منن"
    assert noun_reader.reading_of("رَدٌّ")["cas"] == "n"


def test_two_letters_with_no_doubling_are_no_noun():
    assert noun_reader.reading_of("دَمًا") is None
    assert noun_reader.reading_of("مَنْ") is None


def test_the_light_nun_builds_its_verb_unless_the_nun_is_the_roots():
    assert build_nun("لَأَفْعَلَنْ", lemma="فَعَل") == "emphasis"
    assert build_nun("يَأْمَنْ", lemma="أَمِن") is None
    assert build_nun("لَأَفْعَلَنْ") is None  # no lemma, no telling the nun's
    assert build_nun("لَأَفْعَلَنْهُ", 1, lemma="فَعَل") is None  # the light nun ends its word
    assert build_nun("لَأَفْعَلُنْ", lemma="فَعَل") is None  # a fatha comes before it


@needs_parser
def test_kafuran_is_one_word_joined_by_imma():
    found = roles("إِنَّا هَدَيْنَاهُ السَّبِيلَ إِمَّا شَاكِرًا وَإِمَّا كَفُورًا")
    assert found[-1] == "معطوف" and "حرف جر" not in found


@needs_parser
def test_mannan_is_the_absolute_object_and_badu_the_adverb():
    found = roles("فَإِمَّا مَنًّا بَعْدُ وَإِمَّا فِدَاءً")
    assert found == ["حرف", "مفعول مطلق", "مفعول فيه", "حرف", "معطوف"]


@needs_parser
def test_the_light_nun_verb_is_built_and_lam_yaman_stays_jussive():
    assert card("وَاللَّهِ لَأَفْعَلَنْ", "لَأَفْعَلَنْ")["case"] == "mabni"
    assert card("لَمْ يَأْمَنْ زَيْدٌ", "يَأْمَنْ")["case"] == "jazm"


@needs_parser
def test_the_syntax_names_the_light_nun_verb_built():
    from backend.services.nahw import syntax
    from backend.services.sarf import morphology
    for sentence, case in (("وَاللَّهِ لَأَفْعَلَنْ", "mabni"), ("لَمْ يَأْمَنْ زَيْدٌ", "jazm")):
        words = sentence.split()
        found = syntax.read(sentence, morphology.pick(words, syntax.disambiguator()))["roles"]
        assert found[1]["case"] == case, sentence


def test_a_hollow_present_is_no_intensive():
    for word in ("أَعُوذُ", "تَكُونَ", "يَقُولُ", "نَقُومُ"):
        assert noun_reader.reading_of(word) is None, word
    assert noun_reader.reading_of("الأَكُولُ")["pattern"] == "ال1َ2ُو3"  # ال: no verb, so its letters are the shape's
