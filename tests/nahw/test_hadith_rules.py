"""The rules the hadith «إنما الأعمال بالنيات» exposed, each held by its sentence and by a sibling the same rule
must leave alone. The whole hadith is held at the end, unit by unit."""
import pytest

from backend.services.text.arabic_text import strip_diacritics
from tests.nahw_helpers import analyze, card, needs_parser, units

HADITH = ("إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى فَمَنْ كَانَتْ هِجْرَتُهُ إِلَى دُنْيَا يُصِيبُهَا"
          " أَوْ إِلَى امْرَأَةٍ يَنْكِحُهَا فَهِجْرَتُهُ إِلَى مَا هَاجَرَ إِلَيْهِ")


def plain(sentence: str) -> list[tuple]:
    """units() with the labels' vowels taken off, so a test reads as the books write."""
    return [(job, strip_diacritics(label)) for job, label in units(sentence)]


def placed(sentence: str) -> list[tuple]:
    """(job, label, place) of every labelled unit, the labels' vowels taken off."""
    found = []
    def walk(node):
        if node.get("label"):
            found.append((node.get("role"), strip_diacritics(node["label"]), node.get("detail")))
        for child in node.get("children", []):
            walk(child)
    walk(analyze(sentence)["tree"]["tree"])
    return found


def role(sentence: str, word: str) -> str:
    """The name the card shows: the finer one where the picture gives one (مبتدأ مؤخر)."""
    said = card(sentence, word)
    return said.get("name") or said["role"]


# ما on إنّ stops it working (كافة): the noun after is a مبتدأ, a jar said first the khabar, the noun after it the مبتدأ.
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("فَإِنَّمَا الْعَدْلُ أَنْ يُسْمَعَ الطَّرَفَانِ", "الْعَدْلُ", "مبتدأ"),
    ("إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ", "الْأَعْمَالُ", "مبتدأ"),
    ("إِنَّمَا فِي الدَّارِ زَيْدٌ", "زَيْدٌ", "مبتدأ مؤخر"),
    ("إِنَّمَا عِنْدَ زَيْدٍ كِتَابٌ", "كِتَابٌ", "مبتدأ مؤخر"),
    ("وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى", "مَا", "مبتدأ مؤخر"),
    ("وَإِنَّمَا لِكُلِّ امْرِئٍ مَا نَوَى", "وَإِنَّمَا", "كافة ومكفوفة"),
    # the ما is كافة wherever the parser hung it (here on the khabar)
    ("إِنَّمَا زَيْدٌ قَائِمٌ وَإِنَّمَا عَمْرٌو قَاعِدٌ", "زَيْدٌ", "مبتدأ"),
    # إنّ with no ما still governs
    ("إِنَّ الْعَدْلَ أَسَاسُ الْمُلْكِ", "الْعَدْلَ", "اسم إن"),
    ("إِنَّ فِي الدَّارِ زَيْدًا", "زَيْدًا", "اسم إن"),
    # a second إنّ after و governs its own pair: the و joins, it is no jar, and إنّ is no إنْ of negation
    ("إِنَّ زَيْدًا قَائِمٌ وَإِنَّ عَمْرًا قَاعِدٌ", "عَمْرًا", "اسم إن"),
    ("زَيْدٌ قَائِمٌ وَإِنَّ عَمْرًا قَاعِدٌ", "عَمْرًا", "اسم إن"),
])
def test_ma_on_inna_stops_it_working(sentence, word, said):
    assert role(sentence, word) == said


# A doer is a verb's or a participle's: a unit hung as a jar's or a noun's subject is its مبتدأ.
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("لَكَ مَا تُرِيدُ", "مَا", "مبتدأ مؤخر"),
    ("يُعْجِبُنِي مَا تَقُولُ", "مَا", "فاعل"),
])
def test_a_jars_subject_is_its_mubtada(sentence, word, said):
    assert role(sentence, word) == said


# أَنْ with its verb is a masdar: as a khabar's subject it is the مبتدأ, and the khabar is named, not dashed.
@needs_parser
@pytest.mark.parametrize("sentence, word, job, said", [
    ("أَنْ تَصْدُقَ خَيْرٌ", "خَيْرٌ", "مبتدأ", "خبر"),
    ("أُرِيدُ أَنْ أَصْدُقَ", "أُرِيدُ", "مفعول به", "فعل"),
])
def test_a_masdar_before_a_khabar_is_its_mubtada(sentence, word, job, said):
    assert (job, "مصدر مؤول") in plain(sentence)
    assert role(sentence, word) == said


# أنْ with its verb is a noun in all but its letters: it describes no noun, so after إنّ's noun (or إنما's) with no
# khabar yet, or after a raf' noun hung on it, it is the khabar, named and placed as its governor's khabar.
@needs_parser
@pytest.mark.parametrize("sentence, job, place", [
    ("فَإِنَّمَا الْعَدْلُ أَنْ يُسْمَعَ الطَّرَفَانِ", "خبر", "رفع"),
    ("إِنَّمَا الْعِلْمُ أَنْ تَعْمَلَ", "خبر", "رفع"),
    ("الْخَيْرُ أَنْ تَصْدُقَ", "خبر", "رفع"),
    ("إِنَّ الْعَدْلَ أَنْ يُسْمَعَ الطَّرَفَانِ", "خبر إن", "رفع"),
    ("كَانَ الْخَيْرُ أَنْ تَصْدُقَ", "خبر كان", "نصب"),
    ("لَيْسَ الْبِرُّ أَنْ تُوَلُّوا وُجُوهَكُمْ", "خبر ليس", "نصب"),
    # a كاد-type verb's khabar is the present verb that finishes it, bare or behind أنْ
    ("عَسَى زَيْدٌ أَنْ يَقُومَ", "خبر عسى", "نصب"),
    ("أَوْشَكَ الْمَطَرُ أَنْ يَنْزِلَ", "خبر أوشك", "نصب"),
    # a verb's masdar is its object, whatever noun stands before it
    ("أُرِيدُ أَنْ أَصْدُقَ", "مفعول به", "نصب"),
    ("أُحِبُّ الْعَدْلَ أَنْ يُسْمَعَ الطَّرَفَانِ", "مفعول به", "نصب"),
])
def test_a_masdar_after_a_noun_told_of_is_its_khabar(sentence, job, place):
    assert (job, "مصدر مؤول", f"في محل {place}") in placed(sentence)


@needs_parser
@pytest.mark.parametrize("sentence, job", [
    ("كَادَ زَيْدٌ يَمُوتُ", "خبر كاد"),
    ("طَفِقَ زَيْدٌ يَكْتُبُ", "خبر طفق"),
    ("كَانَ زَيْدٌ يَكْتُبُ", "خبر كان"),
])
def test_a_kaada_verbs_clause_is_its_khabar(sentence, job):
    assert (job, "جملة فعلية") in plain(sentence)


# A relative after its verb is its doer while the verb has none (Tasheel 2.4.1: a verb has one doer), else its object.
# A verb that takes no object (the book's list) has no other place for it, whoever was named before (يَسْعَدُ); any
# other verb, after a doer named before it (أَحَدُكُمْ، اللَّهُ، الْعِلْمُ), takes it as its object.
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("زَيْدٌ قَالَ يَسْعَدُ مَنْ صَدَقَ", "مَنْ", "فاعل"),
    ("الطَّالِبُ يَسْعَدُ مَنْ يُكْرِمُهُ", "مَنْ", "فاعل"),
    ("نَجَحَتِ الَّتِي ثَابَرَتْ", "الَّتِي", "فاعل"),
    ("زَيْدٌ يُحِبُّ مَنْ صَدَقَ", "مَنْ", "مفعول به"),
    ("الْعِلْمُ يَنْفَعُ مَنْ طَلَبَهُ", "مَنْ", "مفعول به"),
    ("لَا يُؤْمِنُ أَحَدُكُمْ حَتَّى يُحِبَّ لِأَخِيهِ مَا يُحِبُّ لِنَفْسِهِ", "مَا", "مفعول به"),
    ("اللَّهُ الَّذِي خَلَقَكُمْ مِنْ ضَعْفٍ ثُمَّ جَعَلَ مِنْ بَعْدِ ضَعْفٍ قُوَّةً ثُمَّ جَعَلَ مِنْ بَعْدِ قُوَّةٍ ضَعْفًا وَشَيْبَةً"
     " يَخْلُقُ مَا يَشَاءُ وَهُوَ الْعَلِيمُ الْقَدِيرُ", "مَا", "مفعول به"),
])
def test_a_relative_after_its_verb_is_its_doer_or_object(sentence, word, said):
    assert role(sentence, word) == said


# A verb of starting (جَعَلَ) governs a noun and a present verb; with an object of its own it is the plain verb
# (جعل: made), and the present verb after it begins afresh.
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("جَعَلَ زَيْدٌ يَكْتُبُ الدَّرْسَ", "زَيْدٌ", "اسم جعل"),
    ("كَادَ الْبَرْقُ يَخْطَفُ أَبْصَارَهُمْ", "الْبَرْقُ", "اسم كاد"),
    ("ثُمَّ جَعَلَ مِنْ بَعْدِ قُوَّةٍ ضَعْفًا وَشَيْبَةً يَخْلُقُ مَا يَشَاءُ وَهُوَ الْعَلِيمُ الْقَدِيرُ", "ضَعْفًا", "مفعول به"),
])
def test_a_verb_of_starting_with_an_object_is_the_plain_verb(sentence, word, said):
    assert role(sentence, word) == said


# ثُمَّ is a حرف عطف, though the parser tag it a noun (ثَمَّ "there"): it is no second object of a verb of the heart before it.
# جَعَلَ مِنْ بَعْدِ ضَعْفٍ قُوَّةً: "made", one object; جَعَلَ اللَّهُ اللَّيْلَ سَكَنًا: a sister of ظن, two.
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("اللَّهُ الَّذِي خَلَقَكُمْ مِنْ ضَعْفٍ ثُمَّ جَعَلَ مِنْ بَعْدِ ضَعْفٍ قُوَّةً ثُمَّ جَعَلَ", "جَعَلَ", "فعل"),
    ("جَعَلَ اللَّهُ اللَّيْلَ سَكَنًا ثُمَّ", "جَعَلَ", "فعل ناسخ من أخوات ظن"),
])
def test_thumma_is_no_object(sentence, word, said):
    assert role(sentence, word) == said


# خَلَقَكُمْ: nothing before the first word puts it in nasb, and with كُمْ on it the fatha before the pronoun is its case,
# so it is the past verb, not the noun خَلَق "worn"; كِتَابَكَ has no verb to read, and is the fronted object.
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("خَلَقَكُمْ ثُمَّ رَزَقَكُمْ", "خَلَقَكُمْ", "فعل"),
    ("كِتَابَكَ قَرَأْتُ", "كِتَابَكَ", "مفعول به"),
])
def test_a_first_word_in_nasb_before_its_pronoun_is_the_past_verb(sentence, word, said):
    assert role(sentence, word) == said


# The sentence a حرف عطف brings is named once, with the حرف in it; a sentence another حرف brings (حتى) keeps its own unit.
@needs_parser
@pytest.mark.parametrize("sentence, sentences", [
    ("ذَهَبَ زَيْدٌ وَجَاءَ عَمْرٌو", 2),
    ("ذَهَبَ زَيْدٌ ثُمَّ جَاءَ عَمْرٌو", 2),
    ("سِرْتُ حَتَّى أَدْخُلَ الْمَدِينَةَ", 3),
])
def test_a_joined_sentence_is_named_once(sentence, sentences):
    assert sum(label == "جملة فعلية" for _, label, _ in placed(sentence)) == sentences


# After لولا the مبتدأ's khabar is a being always left out (موجود), so a jar after the noun is no second khabar
# (ثابت): it hangs on the noun it follows (حِرْصُ ... عَلَى); with no لولا the jar is the khabar.
@needs_parser
@pytest.mark.parametrize("sentence, hung", [
    ("لَوْلَا حِرْصُ زَيْدٍ عَلَى الدَّرْسِ لَرَسَبَ", "متعلق بـحرص"),
    ("وَلَوْلَا حِرْصُ زَيْدٍ عَلَى الدَّرْسِ لَرَسَبَ", "متعلق بـحرص"),
    ("زَيْدٌ فِي الدَّارِ", "متعلق بـثابت"),
])
def test_a_jar_after_lawlas_noun_is_no_khabar(sentence, hung):
    hangs = [label for _, label, _ in placed(sentence) if label.startswith("متعلق")]
    assert hangs == [hung]


def groups(sentence: str) -> list[str]:
    """The jobs of the drawn groups (no word of their own), in order."""
    found = []
    def walk(node):
        if node.get("word") is None and node.get("role"):
            found.append(node["role"])
        for child in node.get("children", []):
            walk(child)
    walk(analyze(sentence)["tree"]["tree"])
    return found


# A khabar with a word joined on it (خَيْرٌ وَأَحَبُّ) is the khabar as a whole; only a whole sentence begun afresh
# (its own مبتدأ under it) does no job.
@needs_parser
@pytest.mark.parametrize("sentence", [
    "الْمُؤْمِنُ الْقَوِيُّ خَيْرٌ وَأَحَبُّ إِلَى اللَّهِ مِنَ الْمُؤْمِنِ الضَّعِيفِ",
    "الطَّالِبُ مُجْتَهِدٌ وَذَكِيٌّ",
])
def test_a_joined_khabar_keeps_its_job(sentence):
    assert "خبر" in groups(sentence)


# A nominal sentence joined after a khabar is joined to the whole sentence: it stands beside the first, in no خبر
# unit; one joined inside a صلة stays in it, and a حال stays with the khabar whose doer it tells the state of.
@needs_parser
@pytest.mark.parametrize("sentence, beside", [
    ("زَيْدٌ قَائِمٌ وَعَمْرٌو قَاعِدٌ", True),
    ("زَيْدٌ قَائِمٌ وَإِنَّمَا عَمْرٌو قَاعِدٌ", True),
    ("إِنَّمَا زَيْدٌ قَائِمٌ وَإِنَّمَا عَمْرٌو قَاعِدٌ", True),
    ("إِنَّ زَيْدًا قَائِمٌ وَإِنَّ عَمْرًا قَاعِدٌ", True),
    ("زَيْدٌ قَائِمٌ وَإِنَّ عَمْرًا قَاعِدٌ", True),
    ("زَيْدٌ فِي الدَّارِ وَهُوَ نَائِمٌ", True),
    ("أَنْتَ صَادِقٌ وَأَنْتَ تَعْلَمُ", True),
    ("إِنَّ زَيْدًا قَائِمٌ وَعَمْرٌو قَاعِدٌ", True),
    ("إِنَّمَا زَيْدٌ قَائِمٌ وَعَمْرٌو قَاعِدٌ", True),
    ("جَاءَ الَّذِي أُمُّهُ قَائِمَةٌ وَأَخُوهُ قَاعِدٌ", False),
    ("زَيْدٌ يَجِيءُ وَهُوَ يَضْحَكُ", False),
    # a khabar that is a sentence: the sentence joined after it joins it (books: معطوفة على جملة فأعذبهم)
    ("فَأَمَّا الَّذِينَ كَفَرُوا فَأُعَذِّبُهُمْ عَذَابًا شَدِيدًا وَمَا لَهُمْ مِنْ نَاصِرِينَ", False),
])
def test_a_joined_nominal_sentence_stands_beside_the_first(sentence, beside):
    tree = analyze(sentence)["tree"]
    top, waw = tree["tree"]["children"], max(i for i, word in enumerate(tree["words"]) if strip_diacritics(word) == "و")
    last = top[-1]
    joined = last.get("word") is None and not last.get("role") and strip_diacritics(last.get("label") or "") == "جملة اسمية"
    assert any(kid.get("word") == waw for kid in top + (last["children"] if joined else [])) == beside
    assert not beside or joined and top[0].get("word") is not None  # the first sentence stays the top's own


# إِنَّمَا: ما الكافة leaves إنّ working on nothing, so the مبتدأ after it stands beside its khabar in the إنّ's own
# sentence (as اسم إنّ does), in no sentence box of its own, wherever the إنما stands
@needs_parser
@pytest.mark.parametrize("sentence, subject", [
    ("إِنَّمَا الْمُؤْمِنُونَ إِخْوَةٌ", "الْمُؤْمِنُونَ"),
    ("إِنَّمَا زَيْدٌ قَائِمٌ وَعَمْرٌو قَاعِدٌ", "زَيْدٌ"),
    ("زَيْدٌ قَائِمٌ وَإِنَّمَا عَمْرٌو قَاعِدٌ", "عَمْرٌو"),
])
def test_the_pair_after_inama_is_the_inna_sentence(sentence, subject):
    tree = analyze(sentence)["tree"]
    inna, at = [i for i, word in enumerate(tree["words"]) if strip_diacritics(word) == "إن"][0], tree["words"].index(subject)
    def holder(node: dict) -> dict | None:
        if any(kid.get("word") == at for kid in node.get("children", [])):
            return node
        return next(filter(None, (holder(kid) for kid in node.get("children", []))), None)
    assert any(kid.get("word") == inna for kid in holder(tree["tree"])["children"])


# A past verb's sentence after و is a حال only with قد (Ibn Aqil, باب الحال: الجملة الحالية; page unchecked); after a
# sentence begun with قد too, it is a second one joined to it, no حال; nor is one أمّا brings (a part of a detailing).
@needs_parser
@pytest.mark.parametrize("sentence, hal", [
    ("جَاءَ زَيْدٌ وَقَدْ تَعِبَ", True),
    ("قَدْ أَفْلَحَ مَنْ زَكَّاهَا وَقَدْ خَابَ مَنْ دَسَّاهَا", False),
    ("جَاءَ زَيْدٌ وَتَعِبَ", False),
    ("أَمَّا الْمَشْرُوعُ فَقَدْ تَعَثَّرَ وَأَمَّا الْعَمَلُ فَقَدْ نَجَحَ", False),
    ("جَاءَ زَيْدٌ وَهُوَ يَضْحَكُ", True),
])
def test_a_past_verb_after_waw_is_a_hal_only_with_qad(sentence, hal):
    assert ("حال" in groups(sentence)) == hal


# The واو الحال and its حال stand beside the verb's other words, in no unnamed sentence of their own.
@needs_parser
@pytest.mark.parametrize("sentence", ["جَاءَ زَيْدٌ وَقَدْ تَعِبَ", "لِمَ تُؤْذُونَنِي وَقَدْ تَعْلَمُونَ أَنِّي رَسُولُ اللَّهِ"])
def test_a_hal_sentence_is_no_joined_sentence(sentence):
    top = analyze(sentence)["tree"]["tree"]
    sentences = [kid for kid in top["children"] if kid.get("word") is None and "جُمْلَةٌ" in (kid.get("label") or "")]
    assert [kid.get("role") for kid in sentences] == ["حال"]


# The clause after a relative is its صلة, with no place, though the relative be a مبتدأ; a word only the tagger
# calls relative (كم) has none, and its clause is its خبر.
@needs_parser
@pytest.mark.parametrize("sentence, job, label", [
    ("لَهُمْ مَا يَشَاءُونَ", "صلة", "جملة فعلية"),
    ("مَرَرْتُ بِالَّذِي نَجَحَ", "صلة", "جملة فعلية"),
    ("كَمْ مِنْ كِتَابٍ قَرَأْتُهُ فَلَمْ أَفْهَمْ مِنْهُ شَيْئًا", "خبر", "جملة فعلية"),
    ("مَرَرْتُ بِرَجُلٍ نَجَحَ", "صفة", "جملة فعلية"),
])
def test_a_relatives_clause_is_its_silah(sentence, job, label):
    assert (job, label) in plain(sentence)


# A jar after a relative is its صلة, hung on a word no one writes; after another noun it is not, nor after a relative
# that has its clause already (a relative has one صلة).
@needs_parser
@pytest.mark.parametrize("sentence, silah", [
    ("جَاءَ الَّذِي فِي الدَّارِ", True),
    ("مَرَرْتُ بِالَّذِي فِي الدَّارِ", True),
    ("الَّذِي فِي الدَّارِ زَيْدٌ", True),
    ("زَيْدٌ فِي الدَّارِ", False),
    ("فَأُولَئِكَ مَعَ الَّذِينَ أَنْعَمَ اللَّهُ عَلَيْهِمْ مِنَ النَّبِيِّينَ وَالصِّدِّيقِينَ وَالشُّهَدَاءِ", False),
])
def test_a_jar_after_a_relative_is_its_silah(sentence, silah):
    assert (("صلة", "متعلق بمحذوف") in plain(sentence)) == silah


# A nominal sentence inside another is one unit: a khabar, a صفة, a حال, what is said, an answer.
# On its own, or under إنما, its halves stand side by side.
@needs_parser
@pytest.mark.parametrize("sentence, job", [
    ("زَيْدٌ أَبُوهُ عَالِمٌ", "خبر"),
    ("زَيْدٌ عِنْدَهُ كِتَابٌ", "خبر"),
    ("زَيْدٌ عِنْدَهُ الْكِتَابُ", "خبر"),
    ("زَيْدٌ لَهُ أَخٌ", "خبر"),
    ("الطَّالِبُ فِي يَدِهِ الْقَلَمُ", "خبر"),
    ("جَاءَ رَجُلٌ أَبُوهُ كَرِيمٌ", "صفة"),
    ("جَاءَ الرَّجُلُ فِي يَدِهِ كِتَابٌ", "حال"),
    ("قَالَ زَيْدٌ لَهُ أَجْرٌ", "مقول القول"),
    ("مَنْ يَتَّقِ اللَّهَ فَهُوَ حَسْبُهُ", "جواب الشرط"),
    ("مَنْ عَمِلَ صَالِحًا فَلَهُ أَجْرٌ", "جواب الشرط"),
    ("فِي الدَّارِ رَجُلٌ", None),
    ("إِنَّمَا فِي الدَّارِ زَيْدٌ", None),
    ("زَيْدٌ فِي الدَّارِ", None),
])
def test_a_nominal_sentence_inside_another_is_one_unit(sentence, job):
    inner = [found for found, label in plain(sentence)[1:] if label == "جملة اسمية"]
    assert inner == ([job] if job else [])


# A word the parser calls a verb with no tense, read as a noun (أَسْرَعُ: أفعل التفضيل), is no verb for the noun before
# it to carry: هو is its مبتدأ, it the خبر, and the sentence begun afresh after و does no job; typed أَسْرَعَ it is the verb.
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("أَلَا لَهُ الْحُكْمُ وَهُوَ أَسْرَعُ الْحَاسِبِينَ", "وَهُوَ", "مبتدأ"),
    ("أَلَا لَهُ الْحُكْمُ وَهُوَ أَسْرَعُ الْحَاسِبِينَ", "أَسْرَعُ", "خبر"),
    ("زَيْدٌ أَسْرَعَ إِلَى الْمَسْجِدِ", "أَسْرَعَ", "فعل"),
])
def test_a_tenseless_verb_read_as_a_noun_is_a_khabar(sentence, word, said):
    assert role(sentence, word) == said


@needs_parser
def test_a_sentence_begun_afresh_after_waw_does_no_job():
    assert plain("أَلَا لَهُ الْحُكْمُ وَهُوَ أَسْرَعُ الْحَاسِبِينَ") == [(None, "جملة اسمية"), (None, "متعلق بـثابت"), (None, "جملة اسمية")]


# The word told of comes after the second word's phrase, so زيدٌ عنده كتابٌ: عنده كتاب is the khabar; and a verb
# hung as the object of the answer's verb is no object (صالحًا stays the object)
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("زَيْدٌ عِنْدَهُ الْكِتَابُ", "الْكِتَابُ", "مبتدأ مؤخر"),
    ("زَيْدٌ لَهُ أَخٌ", "أَخٌ", "مبتدأ مؤخر"),
    ("مَنْ عَمِلَ صَالِحًا فَلَهُ أَجْرٌ", "صَالِحًا", "مفعول به"),
    ("دَخَلَ الضَّيْفُ مُبْتَسِمًا", "مُبْتَسِمًا", "حال"),
])
def test_a_khabar_said_first_tells_of_the_noun_after_its_phrase(sentence, word, said):
    assert role(sentence, word) == said


# نفس، كل with a pronoun back to the noun before, and a khabar that fits that noun, are its توكيد;
# when the khabar fits only نفس/كل itself, they are a مبتدأ of their own.
@needs_parser
@pytest.mark.parametrize("sentence, word, said", [
    ("زَيْدٌ نَفْسُهُ حَاضِرٌ", "نَفْسُهُ", "توكيد"),
    ("الْقَوْمُ كُلُّهُمْ حَاضِرُونَ", "كُلُّهُمْ", "توكيد"),
    ("زَيْدٌ نَفْسُهُ طَيِّبَةٌ", "نَفْسُهُ", "مبتدأ"),
    ("الْقَوْمُ كُلُّهُمْ حَاضِرٌ", "كُلُّهُمْ", "مبتدأ"),
])
def test_tawkeed_before_a_khabar(sentence, word, said):
    assert role(sentence, word) == said


# A condition's answer that is a nominal sentence is drawn as one; a verbal one stays verbal.
@needs_parser
@pytest.mark.parametrize("sentence, label", [
    ("مَنْ يَتَّقِ اللَّهَ فَهُوَ حَسْبُهُ", "جملة اسمية"),
    ("مَنْ يَدْرُسْ يَنْجَحْ", "جملة فعلية"),
])
def test_the_answer_is_the_sentence_its_first_word_is_in(sentence, label):
    assert ("جواب الشرط", label) in plain(sentence)


# The whole hadith: كان with a jar on its known اسم is ناقصة; a diptote (دُنْيَا) shows no case and still takes
# a صفة; the jar after أو is معطوف on the one before, on the word no one writes; the فَ of فَمَنْ stands before
# the condition; the answer is a nominal sentence; ما after إلى is a relative with its صلة.
@needs_parser
def test_the_whole_hadith():
    found = plain(HADITH)
    for unit in [("فعل الشرط", "جملة فعلية"), ("صفة", "جملة فعلية"), ("معطوف", "متعلق بـثابت"),
                 ("جواب الشرط", "جملة اسمية"), ("مجرور", "اسم موصول وصلته"), ("صلة", "جملة فعلية")]:
        assert unit in found
    assert found.count(("صفة", "جملة فعلية")) == 2
    assert role(HADITH, "كَانَتْ") == "فعل ناقص"
    assert role(HADITH, "هِجْرَتُهُ") == "اسم كان"
    assert role(HADITH, "مَا") in ("مبتدأ مؤخر", "مجرور")
    assert [role(HADITH, word) for word in ("إِنَّمَا", "وَإِنَّمَا")] == ["كافة ومكفوفة"] * 2
