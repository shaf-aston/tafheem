"""The job (`role`) each rule gives a word: one sentence with a sibling that must not change.

Run: python -m pytest tests/nahw/test_word_roles.py
"""
from __future__ import annotations

import pytest
from backend.services.nahw import iraab
from tests.nahw_helpers import analysed, cards, NADA, needs_parser, parsed_as, _read, _role

pytestmark = needs_parser


@pytest.mark.parametrize("sentence, lemma", [("قُمْ يَا وَلَدُ", "قام"), ("اُكْتُبْ الدَّرْسَ", "كتب")])
def test_a_command_is_described_as_one(sentence: str, lemma: str):
    """Not the قَمَّ or أَكْتُبُ CAMeL misread it as: its notes and lemma are the command's."""
    from backend.services.sarf import morphology
    word = morphology.analyze_sentence(sentence)[0]
    assert (word["lemma"], word["features"].startswith("command"), "perfect" in word["features"]) == (lemma, True, False)


@pytest.mark.parametrize("sentence, role", [("جَاءَ عَمِّي", "فاعل"), ("زَارَنِي جَدِّي", "فاعل"),
                                            ("سَمِّ اللَّهَ", "فعل")])  # nearest case: a command typed in full
def test_a_noun_with_its_own_pronoun_is_no_command(sentence: str, role: str):
    """عَمِّي is uncle + my, though its letters also spell the command "be general" to a woman."""
    word = iraab.analyze(sentence)["words"][-1 if role == "فاعل" else 0]
    assert word["role"].startswith(role), word


@pytest.mark.parametrize("sentence, at, want", [
    # a noun read with a sign of the noun is never a command (Ibn Aqil V1 p15: بالجر والتنوين والندا وأل)
    ("الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ", 3, "مضاف إليه"),
    ("الشُّكْرُ لِلَّهِ رَبِّ", 2, "صفة"),  # no sentence of asking describes (V3 p198)
    ("سُبْحَانَ رَبِّ الْعَالَمِينَ", 1, "مضاف إليه"),
    ("يَا رَبِّ", 1, "منادى"),
    ("يَا رَبِّ اغْفِرْ لِي", 1, "منادى"),
    ("رَبِّ ابْنَكَ", 0, "فعل"),  # nearest case: opening the sentence, it is the command "raise"
    ("يَا زَيْدُ رَبِّ ابْنَكَ", 2, "فعل"),  # nearest case: in jarr after زيدُ, it is no صفة of it
    ("أَلَا يَا اسْجُدُوا لِلَّهِ", 2, "فعل"),  # nearest case: after يا, a word read as no noun
])
def test_a_noun_with_a_sign_of_the_noun_is_no_command(sentence: str, at: int, want: str):
    assert cards(sentence)[at]["role"] == want


@pytest.mark.parametrize("sentence, want", [
    # an elative takes no object (Ashmuni V2 p312: أجمعوا على أنه لا ينصب المفعول به): its nasb noun is its تمييز
    ("زَيْدٌ أَكْبَرُ مِنْكَ سِنًّا", "تمييز"),
    ("هُوَ أَكْبَرُ مِنْكَ سِنًّا", "تمييز"),
    ("زَيْدٌ ضَارِبٌ بَكْرًا", "مفعول به"),  # nearest case: a participle works as its verb does
])
def test_an_elative_takes_no_object(sentence: str, want: str):
    assert cards(sentence)[-1]["role"] == want


@pytest.mark.parametrize("sentence, want", [
    # with no vowel typed, the sentence vouches for the command: the dictionary has no reading at all
    ("اكتبي درسك", ["فعل", "مفعول به"]),
    ("يا سعاد اكتبي درسك", ["حرف", "منادى", "فعل", "مفعول به"]),
    # or the parser hung an object on what the dictionary read as an elative, which takes none
    ("ارفعي صوتك", ["فعل", "مفعول به"]),
    ("يا سعاد ارفعي صوتك", ["حرف", "منادى", "فعل", "مفعول به"]),
    ("أخي أكبر مني", ["مبتدأ", "خبر", "حرف جر"]),  # nearest case: an elative with no object stays one
    ("عمي كريم", ["مبتدأ", "خبر"]),  # nearest case: a noun's own pronoun, hung as its مضاف إليه
])
def test_a_bare_command_the_sentence_vouches_for(sentence: str, want: str):
    assert [c["role"] for c in cards(sentence)] == want


@pytest.mark.parametrize("sentence, want", [
    ("سَرَّنِي مَا صَنَعْتَهُ", ["فعل", "فاعل", "فعل"]),  # ما after the verb's own pronoun is its doer
    ("مَا رَأَيْتُهُ", ["حرف", "فعل"]),                    # nearest case: ما opening the sentence negates
    ("هَاتَانِ قِلَادَتَانِ فِضِّيَّتَانِ", ["مبتدأ", "خبر", "صفة"]),  # no ال after a pointer: the khabar
    ("هَذَا الْكِتَابُ جَدِيدٌ", ["مبتدأ", "صفة", "خبر"]),  # nearest case: with ال it follows the pointer
    ("أَهْدَى الْجَدُّ حَفِيدَهُ مِنْظَارًا", ["فعل", "فاعل", "مفعول به", "مفعول به"]),  # its pronoun makes it definite: no حال
    ("جَاءَ زَيْدٌ رَاكِبًا", ["فعل", "فاعل", "حال"]),  # nearest case: indefinite, a حال
    ("كَانَ النَّاسُ أُمَّةً وَاحِدَةً", ["فعل", "اسم كان", "خبر كان", "صفة"]),
    ("إِنَّ مِنَ الْبَيَانِ لَسِحْرًا", ["حرف", "حرف جر", "مجرور", "اسم إن"]),  # the jar-majrur stands first as the khabar
    ("إِنَّ فِي ذَلِكَ لَآيَةً", ["حرف", "حرف جر", "مجرور", "اسم إن"]),  # إنّ has no object: the noun hung as one is its اسم
    ("عَادَ الْوَلَدُ مِنَ الْمَدْرَسَةِ فَرِحاً", ["فعل", "فاعل", "حرف جر", "مجرور", "حال"]),
    ("محمد بن عبد الله نبي كريم", ["مبتدأ", "صفة", "مضاف إليه", "مضاف إليه", "خبر", "صفة"]),
    ("زَيْدٌ ضَارِبٌ بَكْرًا", ["مبتدأ", "خبر", "مفعول به"]),  # no ال after a name: the khabar
    ("زَيْدٌ صَاحِبُ مَالٍ كَثِيرٍ", ["مبتدأ", "خبر", "مضاف إليه", "صفة"]),  # added to an indefinite: still indefinite
    ("زَيْدٌ صَاحِبُ الْمَالِ كَرِيمٌ", ["مبتدأ", "صفة", "مضاف إليه", "خبر"]),  # nearest case: added to a definite, a صفة
    ("زَيْدٌ صَاحِبُ الْمَالِ", ["مبتدأ", "خبر", "مضاف إليه"]),  # both definite: the first the مبتدأ (Ibn Aqil V1 p232: زيد أخوك)
    ("أَنَا ضَارِبٌ زَيْدًا", ["مبتدأ", "خبر", "مفعول به"]),  # the participle works as its verb (V3 p106): no verb read
    ("زيد جالس عمرا", ["مبتدأ", "فعل", "مفعول به"]),  # nearest case: no tanween written, جَالَسَ the verb
    ("جَاءُوا مُسْرِعِينَ", ["فعل", "حال"]),  # the dictionary's past, and the plural read off its ending
    ("قَاتِلُوا مُسْرِعِينَ", ["فعل", "حال"]),  # a command no less
    ("مَرَرْتُ بِرِجَالٍ مُسْرِعِينَ", ["فعل", "مجرور", "صفة"]),  # nearest case: after an indefinite plural, its صفة
    ("إِنَّ الطُّلَّابَ مُسْرِعُونَ", ["حرف", "اسم إن", "خبر إن"]),
    ("حضر الطلاب الا زيدا", ["فعل", "فاعل", "حرف", "مستثنى"]),
    # a command to a woman with its object written on: the ي before هِ is her, no noun's ending
    ("اُكْتُبِيهِ الْآنَ", ["فعل", "مفعول فيه"]),
    # a time word its own verb hangs on is the main verb's ظرف, however the parser links it (as a خبر here)
    ("كُلَّمَا جَاءَ زَيْدٌ أَكْرَمْتُهُ", ["مفعول فيه", "فعل", "فاعل", "فعل"]),  # bare الا is إِلَّا, not the name آلًا
    ("إِنَّ الْمُهَنْدِسَ الْعَجُوزَ نَشِيطٌ", ["حرف", "اسم إن", "صفة", "خبر إن"]),  # ال on both: it follows
    ("ابْتَاعَ الْخَبَّازُ صَاعًا شَعِيرًا", ["فعل", "فاعل", "مفعول به", "تمييز"]),  # after a measure
    ("اشْتَرَيْتُ رِطْلًا كَامِلًا", ["فعل", "مفعول به", "صفة"]),  # nearest case: an adjective after one
    ("الْفِيلُ أَثْقَلُ وَزْنًا مِنَ الْجَمَلِ", ["مبتدأ", "خبر", "تمييز", "حرف جر", "مجرور"]),  # after an elative
    ("أَنْصَتَ الْمُسْتَمِعُونَ تَقْدِيرًا لِلْخَطِيبِ", ["فعل", "فاعل", "مفعول لأجله", "مجرور"]),
    ("أَدْهَشَ الْجُمْهُورَ السَّاحِرُ", ["فعل", "مفعول به", "فاعل"]),  # the object put before the doer
    ("أَكَلَ الْوَلَدُ الصَّغِيرُ", ["فعل", "فاعل", "صفة"]),  # nearest case: the same case, a صفة
    ("يَا سَائِقًا الشَّاحِنَةَ تَمَهَّلْ", ["حرف", "منادى", "مفعول به", "فعل"]),  # tanween: no إضافة
    ("يَا سَائِقَ الشَّاحِنَةِ تَمَهَّلْ", ["حرف", "منادى", "مضاف إليه", "فعل"])])  # nearest case: an إضافة
def test_what_a_word_after_a_verb_noun_or_pointer_is(sentence: str, want: list[str]):
    got = [w["role"] for w in iraab.analyze(sentence)["words"]]
    assert len(got) == len(want) and all(g and g.startswith(x) for g, x in zip(got, want)), got


@pytest.mark.parametrize("sentence, index, role", [
    ("زَيْدٌ ضَارِبٌ بَكْرًا", 2, "مفعول به"),  # the notes' own example of شبه الفعل
    ("لَوْ كُنْتُ آمِرًا أَحَدًا أَنْ يَسْجُدَ لأَحَدٍ", 3, "مفعول به"),  # آمِر: فاعل of a hamza root
    ("هَلْ أَنْتَ فَاهِمٌ الدَّرْسَ", 3, "مفعول به"),  # linked as idafa, but its fatha says object
    ("زَيْدٌ قَادِمٌ مُسْرِعًا", 2, "حال")])  # nearest case: a describing word stays a حال
def test_an_active_participle_takes_its_object_as_its_verb_does(sentence: str, index: int, role: str):
    assert _read(sentence)["words"][index]["role"] == role


# One reading per small word (particles.stamp): the card names what the word does here.
PARTICLE_ROLES = [
    ("إِذَا قَالَ الْعَبْدُ لاَ إِلَهَ إِلاَّ اللَّهُ وَاللَّهُ أَكْبَرُ",
     ["مفعول فيه", "فعل", "فاعل", "حرف", "اسم لا", "حرف", "بدل", "مبتدأ", "خبر"]),
    ("لاَ ضَرَرَ وَلاَ ضِرَارَ", ["حرف", "اسم لا", "حرف", "اسم لا"]),
    ("جَاءَ زَيْدٌ لَا خَالِدٌ", ["فعل", "فاعل", "حرف", "معطوف"]),
    ("جَاءَ زَيْدٌ لَا عَمْرٌو", ["فعل", "فاعل", "حرف", "معطوف"]),  # the written و of عمرو hides no case
    ("الْحَلاَلُ بَيِّنٌ وَالْحَرَامُ بَيِّنٌ", ["مبتدأ", "خبر", "مبتدأ", "خبر"]),
    ("أَىُّ الأَعْمَالِ أَفْضَلُ", ["مبتدأ", "مضاف إليه", "خبر"]),
    ("مَتَى السَّفَرُ", ["خبر", "مبتدأ"]),  # nearest case: a built question word takes no مضاف إليه
]


@pytest.mark.parametrize("sentence, expected", PARTICLE_ROLES)
def test_a_small_word_is_read_once_by_what_surrounds_it(sentence: str, expected: list[str]):
    assert [w["role"] for w in iraab.analyze(sentence)["words"]] == expected


@pytest.mark.parametrize("sentence, expected", [
    ("لَا تَعْبُدُوا إِلَّا اللَّهَ", ["حرف", "فعل", "حرف", "مفعول به"]),  # the parser hangs the noun on إلا
    ("لَا تَضْرِبْ إِلَّا زَيْدًا", ["حرف", "فعل", "حرف", "مفعول به"]),
    ("لَا تَقُلْ إِلَّا الْحَقَّ", ["حرف", "فعل", "حرف", "مفعول به"]),
    ("مَا ذَهَبَ إِلَّا إِلَى الْمَدْرَسَةِ", ["حرف", "فعل", "حرف", "حرف جر", "مجرور"]),
    ("لَا إِلَهَ إِلَّا اللَّهُ", ["حرف", "اسم لا", "حرف", "بدل"]),  # control: after a noun in its case, a بدل
])
def test_the_word_after_a_restricting_illa_takes_the_place_the_sentence_leaves(sentence: str, expected: list[str]):
    assert [w["role"] for w in iraab.analyze(sentence)["words"]] == expected


@pytest.mark.parametrize("sentence, expected", [
    ("مَا أَجْمَلَ السَّمَاءَ", ["مبتدأ", "فعل", "مفعول به"]),
    ("ما اجمل السماء", ["مبتدأ", "فعل", "مفعول به"]),  # plain text: the shape is read from the letters
    ("ما اشد الحر", ["مبتدأ", "فعل", "مفعول به"]),  # the doubled root, from the analyser's root
    ("مَا أَطْوَلَ اللَّيْلَ", ["مبتدأ", "فعل", "مفعول به"]),
    ("مَا أَكْرَمَ زَيْدٌ عَمْرًا", ["حرف", "فعل", "فاعل", "مفعول به"]),  # a noun in raf': the ordinary negation
    ("ما أكرم زيد عمرا", ["حرف", "فعل", "فاعل", "مفعول به"]),
    ("مَا أُكْرِمَ زَيْدٌ", ["حرف", "فعل مجهول", "نائب فاعل"]),  # the typed damma says it is not the wonder shape
    ("مَا أَعْطَى الرَّجُلَ كِتَابًا", ["حرف", "فعل", "مفعول به", "مفعول به"]),  # two objects: not the wonder form
    ("ما أنزل الله بها من سلطان", ["حرف", "فعل", "فاعل", "حرف جر", "حرف جر", "مجرور"]),  # أنزل gives no comparative
    ("مَا أَجْمَلَهَا", ["مبتدأ", "فعل"]),  # the pronoun on the verb is its one object
    ("مَا أَعْظَمَكَ", ["مبتدأ", "فعل"]),
    ("ما أحلاها", ["مبتدأ", "فعل"]),
    ("مَا أَجْمَلَهَا مِنْ لَيْلَةٍ", ["مبتدأ", "فعل", "حرف جر", "مجرور"]),  # a preposition after it is no question word
    ("مَا أَعْطَاهَا كِتَابًا", ["حرف", "فعل", "مفعول به"]),  # a second object: not the wonder form
])
def test_the_wonder_form_is_told_by_its_shape_and_its_noun(sentence: str, expected: list[str]):
    assert [w["role"] for w in iraab.analyze(sentence)["words"]] == expected


@pytest.mark.parametrize("sentence, expected", [
    # ما/مَن with a noun after them: the mubtada, that noun the khabar (Sibawayh, as the notes teach,
    # Musnad p12); Tasheel 2.4.7 p47 also allows the khabar brought to the front
    ("مَا اسْمُكَ", ["مبتدأ", "خبر"]),
    ("مَا هَذَا", ["مبتدأ", "خبر"]),
    ("مَا الْإِيمَانُ", ["مبتدأ", "خبر"]),
    ("مَنْ أَنْتَ", ["مبتدأ", "خبر"]),
    ("مَنْ هَذَا؟", ["مبتدأ", "خبر"]),
    ("مَنْ أَبُوكَ", ["مبتدأ", "خبر"]),
    ("أَيُّكُمْ أَحْسَنُ عَمَلًا", ["مبتدأ", "خبر", "تمييز"]),  # أيّ filed with its pronoun unsplit
    ("قَالَ مَا اسْمُكَ", ["فعل", "مبتدأ", "خبر"]),
    ("يَا أَخِي مَا اسْمُكَ", ["حرف", "منادى", "مبتدأ", "خبر"]),
    ("وَمَا أَدْرَاكَ مَا يَوْمُ الدِّينِ", ["مبتدأ", "فعل", "مبتدأ", "خبر", "مضاف إليه"]),  # a verb of informing, its second object a question
    ("مَا أَجْمَلَ السَّمَاءَ", ["مبتدأ", "فعل", "مفعول به"]),
    # not a question: ما الحجازية, a negation, a relative before a ظرف or a verb, من before a preposition
    ("مَا هَذَا بَشَرًا", ["حرف", "اسم كان", "خبر كان"]),
    ("ما زيدٌ قائمًا", ["حرف", "اسم كان", "خبر كان"]),
    ("وَمَا زَيْدٌ قَائِمًا", ["حرف", "اسم كان", "خبر كان"]),  # a وَ or فَ before it leaves it ما الحجازية
    ("فَمَا هَذَا بَشَرًا", ["حرف", "اسم كان", "خبر كان"]),
    ("مَا جَاءَ إِلَّا زَيْدٌ", ["حرف", "فعل", "حرف", "فاعل"]),
    ("مَنْ جَاءَ", ["مبتدأ", "فعل"]),
    ("مَنْ فِي الْبَيْتِ", ["مبتدأ", "حرف جر", "مجرور"]),
    # ما with its khabar first, a جار ومجرور or ظرف, negates and its noun is the مبتدأ مؤخر
    ("مَا فِي الدَّارِ أَحَدٌ", ["حرف", "حرف جر", "مجرور", "مبتدأ"]),
    ("مَا فِيهِ عَيْبٌ", ["حرف", "حرف جر", "مبتدأ"]),
    ("مَا عِنْدِي مَالٌ", ["حرف", "مفعول فيه", "مبتدأ"]),
    ("مَا لَكَ عَلَيَّ سُلْطَانٌ", ["حرف", "حرف جر", "حرف جر", "مبتدأ"]),
    ("وَمَا عِنْدَ اللَّهِ خَيْرٌ", ["مبتدأ", "مفعول فيه", "مضاف إليه", "خبر"]),
    ("الَّذِي فِي الدَّارِ رَجُلٌ", ["مبتدأ", "حرف جر", "مجرور", "خبر"]),
    # the parser hangs خير under the ظرف, which takes no subject: it is the relative's khabar
    ("وَمَا عِنْدَ اللَّهِ خَيْرٌ وَأَبْقَى", ["مبتدأ", "مفعول فيه", "مضاف إليه", "خبر", "معطوف"]),
    # the question hamza on a جار: the noun after it in jarr is its majrur, not a verb's (أَفِي "I fulfil")
    ("أَفِي اللَّهِ شَكٌّ", ["حرف جر", "مجرور", "مبتدأ"]),
    ("أَفِي بِعَهْدِي", ["فعل", "مجرور"]),
    ("إِنَّ مَا عِنْدَ اللَّهِ هُوَ خَيْرٌ لَكُمْ", ["حرف", "اسم إن", "مفعول فيه", "مضاف إليه", "مبتدأ", "خبر إن", "حرف جر"]),
])
def test_a_question_word_heads_the_noun_after_it(sentence: str, expected: list[str]):
    # the rules' own names: وَمَا أَدْرَاكَ مَا يَوْمُ الدِّينِ is an ayah, whose record names its roles vowelled
    assert [w["role"] for w in iraab.analyze(sentence, recorded=False)["words"]] == expected


@pytest.mark.parametrize("sentence, expected", [
    # أَبْقَى reads as the elative and as "and I remain": joined onto an elative, it is that elative
    ("وَالْآخِرَةُ خَيْرٌ وَأَبْقَى", ["مبتدأ", "خبر", "معطوف"]),
    ("هُوَ أَعْلَمُ وَأَحْكَمُ", ["مبتدأ", "خبر", "معطوف"]),
    # one the dictionary lacks, read by sarf's shape once the و is off
    ("الْآخِرَةُ أَبْقَى وَأَدْوَمُ", ["مبتدأ", "خبر", "معطوف"]),
    # the typed vowels still choose (the past verb's fatha, the verb's damma), and a participle takes a verb
    ("زَيْدٌ خَيْرٌ وَأَحْسَنَ إِلَيَّ", ["مبتدأ", "خبر", "فعل", "حرف جر"]),
    ("زَيْدٌ قَائِمٌ وَأَدُومُ", ["مبتدأ", "خبر", "فعل"]),
    ("زَيْدٌ قَائِمٌ وَأَبْقَى عَمْرًا", ["مبتدأ", "خبر", "فعل", "مفعول به"]),
    # a verb is joined onto an active participle, which is like a verb (Ibn Aqil V3 p244)
    ("زَيْدٌ قَائِمٌ وَأَبْقَى", ["مبتدأ", "خبر", "فعل"]),
    ("هُوَ مُقِيمٌ وَأَبْقَى", ["مبتدأ", "خبر", "فعل"]),
])
def test_a_word_joined_onto_an_elative_is_an_elative(sentence: str, expected: list[str]):
    assert [w["role"] for w in cards(sentence)] == expected


@pytest.mark.parametrize("sentence, roles", [
    # a typed case clash rules out the نعت: the fatha makes الفقير the first object
    ("أَعْطَى الرَّجُلُ الْفَقِيرَ دِرْهَمًا", ["فعل", "فاعل", "مفعول به", "مفعول به"]),
    # آتى takes two objects, so the second is never a حال
    ("لَا يُؤْتُونَ النَّاسَ نَقِيرًا", ["حرف", "فعل", "مفعول به", "مفعول به"]),
    # a command a noun reading had (آتٍ, one coming) is آتَى's: its second object no بدل of the first
    ("آتِ ذَا الْقُرْبَى حَقَّهُ", ["فعل", "مفعول به", "مضاف إليه", "مفعول به"]),
    # nearest case: an indefinite word after one object stays the حال
    ("جَاءَ الرَّجُلُ ضَاحِكًا", ["فعل", "فاعل", "حال"])])
def test_two_objects_of_a_verb_of_giving_are_both_objects_and_a_case_clash_is_no_naat(sentence: str, roles: list[str]):
    assert [w["role"] for w in _read(sentence)["words"]] == roles


@pytest.mark.parametrize("sentence, word, role", [
    ("فَإِنْ آنَسْتُمْ مِنْهُمْ رُشْدًا فَادْفَعُوا إِلَيْهِمْ أَمْوَالَهُمْ", "فَادْفَعُوا", "فعل"),  # the word list has no such command
    ("فَإِنْ آنَسْتُمْ مِنْهُمْ رُشْدًا فَادْفَعُوا إِلَيْهِمْ أَمْوَالَهُمْ", "أَمْوَالَهُمْ", "مفعول به"),
])
def test_a_command_the_word_list_lacks_is_read_by_sarf_under_its_joined_fa(sentence: str, word: str, role: str):
    got = {w["word"]: w for w in analysed(sentence)}
    assert got[word]["role"] == role


def test_a_prayer_noun_after_a_verb_is_a_mubtada_not_its_doer():
    words = iraab.analyze(NADA, recorded=False)["words"]
    assert [w["role"] for w in words] == [
        "فعل", "مجرور", "مضاف إليه", "مبتدأ", "مجرور", "حرف جر", "مجرور", "مفعول مطلق", "حرف", "معطوف"]


def test_a_doer_after_nada_stays_a_doer():
    assert iraab.analyze("نَادَى زَيْدٌ", recorded=False)["words"][1]["role"] == "فاعل"


def test_a_count_of_times_is_the_absolute_object_of_its_verb():
    assert iraab.analyze("ضَرَبْتُهُ مَرَّتَيْنِ", recorded=False)["words"][1]["role"] == "مفعول مطلق"


def test_a_word_added_to_the_count_or_the_masdar_stands_in_for_the_masdar():
    assert iraab.analyze("زُرْتُهُ ثَلَاثَ مَرَّاتٍ", recorded=False)["words"][1]["role"] == "مفعول مطلق"
    assert iraab.analyze("قَرَأْتُ الْكِتَابَ عَشْرَ مَرَّاتٍ", recorded=False)["words"][2]["role"] == "مفعول مطلق"
    assert iraab.analyze("فَرِحْتُ كُلَّ الْفَرَحِ", recorded=False)["words"][1]["role"] == "مفعول مطلق"
    # added to any other noun, the number or كل is the object
    assert iraab.analyze("رَأَيْتُ ثَلَاثَةَ رِجَالٍ", recorded=False)["words"][1]["role"] == "مفعول به"
    assert iraab.analyze("أَكَلْتُ كُلَّ الطَّعَامِ", recorded=False)["words"][1]["role"] == "مفعول به"
    assert iraab.analyze("قَرَأْتُ كُلَّ الدَّرْسِ", recorded=False)["words"][1]["role"] == "مفعول به"


def test_a_doubled_or_hollow_root_still_reads_as_a_masdar_measure():
    # حُبّ is فُعْل with its last radicals in one shadda, قَوْل is فَعْل with its weak middle letter
    assert iraab.analyze("أَحْبَبْتُهُ كُلَّ الْحُبِّ", recorded=False)["words"][1]["role"] == "مفعول مطلق"
    assert iraab.analyze("قُلْتُ بَعْضَ الْقَوْلِ", recorded=False)["words"][1]["role"] == "مفعول مطلق"
    assert iraab.analyze("مَدَدْتُ كُلَّ الْحَبْلِ", recorded=False)["words"][1]["role"] == "مفعول به"


def test_a_prayer_noun_is_the_said_only_after_a_verb_of_saying():
    assert _role("فَقَالَ وَيْلٌ لَهُ", 1) == "مبتدأ"  # the لِ phrase hung on the verb, with a pronoun
    assert _role("جَاءَ عَذَابٌ لِلْكَافِرِينَ", 1) == "فاعل"  # coming is no saying: the doer
    assert _role("جَاءَ سَلَامٌ لِلْقَوْمِ", 1) == "فاعل"


def test_a_verb_of_saying_is_known_by_its_meaning_not_only_by_the_list():
    assert _role("نَطَقَ وَيْلٌ لَهُ", 1) == "مبتدأ"  # نطق is in no list: CAMeL glosses it "utter"


def test_mundhu_before_a_noun_is_a_preposition():
    assert [w["role"] for w in iraab.analyze("مَا زُرْتُهُ مُذْ شَهْرٍ", recorded=False)["words"]][-2:] == ["حرف جر", "مجرور"]


def test_idha_past_a_jussive_particle_still_opens_a_condition():
    words = iraab.analyze("إِذَا لَمْ تَدْرُسْ فَلَنْ تَنْجَحَ", recorded=False)["words"]
    assert words[0]["role"] == "مفعول فيه"


@pytest.mark.parametrize("sentence, want", [
    # a command and its object pronoun the dictionary has no reading of: اِهْدِنَا is هَدَى + نا
    ("اِهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ", ["فعل", "مفعول به", "صفة"]),
    ("أَعْطِنَا كِتَابًا", ["فعل", "مفعول به"]),
    ("زِدْنِي عِلْمًا", ["فعل", "مفعول به"]),
])
def test_a_command_with_its_object_pronoun_written_on(sentence: str, want: list):
    assert [c["role"] for c in cards(sentence)] == want


@pytest.mark.parametrize("sentence, at, said, unsaid", [
    ("يَا أَيُّهَا الَّذِينَ آمَنُوا", 2, "definite (معرفة)", "indefinite"),  # a relative is known (Ibn Aqil V1 p86)
    ("هَذَا كِتَابٌ", 0, "definite (معرفة)", "indefinite"),  # a pointer
    ("جَاءَ زَيْدٌ", 1, "definite (معرفة)", "indefinite"),  # a name
    ("هَذَا كِتَابٌ", 1, "indefinite (نكرة)", "definite (معرفة)"),  # nearest case: a noun with no ال
    ("جَاءَ زَيْدٌ", 0, "perfect (ماضٍ)", "indicative"),  # the past is built, no mood (V1 p35)
])
def test_a_card_note_says_what_the_word_is(sentence: str, at: int, said: str, unsaid: str):
    notes = cards(sentence)[at]["notes"]
    assert said in notes and unsaid not in notes, notes


def test_a_word_opening_before_no_command_may_be_the_command():
    card = cards("رَبِّ الْوَلَدَ")[0]  # nearest case: رَبَّى's command, its object after it
    assert (card["role"], card["aspect"]) == ("فعل", "c")


@pytest.mark.parametrize("sentence, aspect", [
    ("جَاءُوا مُسْرِعِينَ", "p"),  # the dictionary's past, never a command spelled جَاِئُوا it left a mark off
    ("قُومُوا مُسْرِعِينَ", "c"),  # nearest case: the command typed in full
])
def test_a_past_verb_read_with_its_vowels_stays_past(sentence: str, aspect: str):
    assert cards(sentence)[0]["aspect"] == aspect


@pytest.mark.parametrize("sentence, at, aspect", [
    ("كُلُوا وَاشْرَبُوا", 1, "c"),  # the hamzat al-wasl after a joined وَ: not the past أَشْرَبُوا
    ("وَاسْتَغْفِرُوا اللَّهَ", 0, "c"),
    ("وَأَشْرَبُوا فِي قُلُوبِهِمُ الْعِجْلَ", 0, "p"),  # nearest case: its hamza written, the past أَشْرَبَ (2:93)
])
def test_hamzat_al_wasl_after_a_joined_letter_is_still_the_command(sentence: str, at: int, aspect: str):
    assert cards(sentence)[at]["aspect"] == aspect


@pytest.mark.parametrize("sentence, at, want", [
    ("أُمِّ اسْمَعِي", 0, "منادى"),  # its damma is the noun أُمّ the dictionary read, not the particle أَمْ
    ("أُمُّ زَيْدٍ كَرِيمَةٌ", 0, "مبتدأ"),
    ("أَزَيْدٌ عِنْدَكَ أَمْ عَمْرٌو", 2, "حرف"),  # nearest case: the particle typed with its fatha
    ("جَاءَ زَيْدٌ ثُمَّ عَمْرٌو", 2, "حرف"),  # nearest case: ثُمَّ, read as an adverb, keeps its damma rule
])
def test_a_noun_typed_with_its_vowels_is_no_joining_particle(sentence: str, at: int, want: str):
    assert cards(sentence)[at]["role"] == want


def test_a_kasra_with_tanween_is_no_dropped_ya():
    assert cards("زَيْدٍ اذْهَبْ")[0]["role"] != "منادى"  # nearest case: the tanween stands on no ياء المتكلم


@pytest.mark.parametrize("sentence, want", [
    # an adjective on فَعِل the dictionary lacks, in its sound plural, is a describing word: a hal after the doer
    ("جَاءَ الطُّلَّابُ فَرِحِينَ", "حال"),
    ("رَجَعَ الْمُسَافِرُونَ حَزِنِينَ", "حال"),
    ("جَاءَ الطُّلَّابُ لَاعِبِينَ", "حال"),  # nearest case: the dictionary knows it, same shape of sentence
    ("رَأَيْتُ الطُّلَّابَ", "مفعول به"),  # nearest case: with no describing word the noun stays the object
])
def test_a_sound_plural_adjective_the_dictionary_lacks_is_a_hal(sentence: str, want: str):
    assert cards(sentence)[-1]["role"] == want


@pytest.mark.parametrize("sentence, role", [
    # typed bare, a plain noun read in nasb after the doer is no نعت (a نعت is made of a describing word): the object
    ("شرب الطفل اللبن", "مفعول به"),
    ("شرب الولد الماء", "مفعول به"),
    ("جاء الرجل الكريم", "صفة"),  # nearest case: a describing word after the doer stays its نعت
    ("حضر الطلاب أنفسهم", "توكيد"),  # a word of emphasis after the doer stays its توكيد
    ("حضر الملك عينه", "توكيد"),
])
def test_a_bare_plain_noun_in_nasb_after_the_doer_is_the_object(sentence: str, role: str):
    assert cards(sentence)[-1]["role"] == role


@pytest.mark.parametrize("sentence, at, role", [
    # a relative after a known noun describes it, unless the verb owes an object (كافأ), which it then is
    ("جَاءَ الرَّجُلُ الَّذِي رَأَيْتُهُ أَمْسِ", 2, "صفة"),
    ("نَجَا الْمُتَسَلِّقُ الَّذِي سَقَطَ", 2, "صفة"),
    ("كَافَأَ الْمُدِيرُ الَّذِي نَجَحَ", 2, "مفعول به"),
    ("اقْرَأْ بِاسْمِ رَبِّكَ الَّذِي خَلَقَ", 3, "صفة"),  # known by its pronoun, not by ال
    # إِلَّا opening the sentence governs the noun after it, however the parser hung the pair
    ("إِلَّا الَّذِينَ آمَنُوا وَعَمِلُوا الصَّالِحَاتِ", 1, "مستثنى"),
])
def test_a_relative_after_a_known_noun_is_its_sifa_and_after_illa_the_excepted(sentence, at, role):
    assert _role(sentence, at) == role


@pytest.mark.parametrize("rel", [None, "OBJ", "SBJ"])
def test_a_negation_is_a_particle_even_when_the_parser_hangs_its_verb_under_it(rel):
    sentence = "مَا وَدَّعَكَ رَبُّكَ وَمَا قَلَىٰ"
    with parsed_as("قلى", 7, rel):  # token 7 is the negation: the verb under it, by MOD or another relation
        assert _role(sentence, 3) == "حرف"  # not the و's majrur


def test_a_noun_with_no_case_shown_after_a_preposition_is_its_majrur():
    assert _role("وَالضُّحَىٰ وَاللَّيْلِ إِذَا سَجَىٰ", 0) == "مجرور"


def test_a_noun_after_the_jar_khabar_of_la_is_a_second_khabar():
    assert _role("ذَلِكَ الْكِتَابُ لَا رَيْبَ فِيهِ هُدًى لِلْمُتَّقِينَ", 5) == "خبر لا"


def test_a_noun_with_a_pair_under_it_is_the_mubtada_not_the_khabar():
    assert _role("اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ", 0) == "مبتدأ"


def test_how_asked_before_its_verb_is_the_state_of_that_verb():
    assert _role("أَلَمْ تَرَ كَيْفَ فَعَلَ رَبُّكَ بِأَصْحَابِ الْفِيلِ", 2) == "حال"  # not the object of تَرَ


def test_a_plain_noun_in_nasb_after_a_working_participle_is_its_object():
    assert _role("وَإِذْ قَالَ رَبُّكَ لِلْمَلَائِكَةِ إِنِّي جَاعِلٌ فِي الْأَرْضِ خَلِيفَةً", 8) == "مفعول به"


def test_a_defective_noun_ending_in_a_bare_ya_wears_its_nouns_case():
    assert _role("سَمِعْتُ صَوْتَ الطِّفْلِ الْبَاكِي فِي اللَّيْلِ", 3) == "صفة"


def test_a_word_with_its_mubtada_before_it_is_a_khabar_not_a_describer():
    assert _role("رَأَيْتُ رَجُلًا وَجْهُهُ مُنِيرٌ يَمْشِي فِي السُّوقِ", 3) == "خبر"


def test_the_noun_with_al_after_a_pronoun_follows_it_as_badal():
    assert _role("اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ", 5) == "بدل"


def test_a_noun_in_nasb_after_kana_is_its_khabar_and_what_follows_is_its_ism():
    assert _role("لَيْسَ الْبِرَّ أَنْ تُوَلُّوا وُجُوهَكُمْ", 1) == "خبر كان"


@pytest.mark.parametrize("at, role", [(2, "اسم إن"), (7, "خبر إن")])
def test_a_relative_ma_is_the_ism_of_anna_and_a_raf_noun_after_its_clause_the_khabar(at, role):
    assert _role("وَلَوْ أَنَّ مَا فِي الْأَرْضِ مِنْ شَجَرَةٍ أَقْلَامٌ", at) == role


@pytest.mark.parametrize("sentence, at, role", [
    ("حضر الضيوف غير بكر", 1, "فاعل"),  # the parser read the guests as the object and غير as the doer
    ("حضر الضيوف سوى بكر", 3, "مضاف إليه"),
])
def test_an_excepting_noun_after_the_doer_is_excepted_and_adds_the_noun_after_it(sentence, at, role):
    assert _role(sentence, at) == role


def test_a_verb_of_two_objects_owes_the_noun_after_its_doer_as_object():
    assert _role("مَنَحَ المدير المعلم كتابا", 2) == "مفعول به"


def test_a_detached_pronoun_after_kana_is_its_ism():
    assert _role("كَانَ أَنْتَ مُسَافِرًا", 1) == "اسم كان"


def test_the_noun_after_a_fronted_jar_majrur_is_the_mubtada_though_bare():
    assert _role("لله الحمد", 1) == "مبتدأ"


def test_a_mudaf_to_a_known_noun_before_an_indefinite_one_is_the_mubtada():
    assert _role("يوم الجمعة يوم مبارك", 0) == "مبتدأ"


def test_a_relative_typed_bare_after_a_preposition_is_not_read_as_a_command():
    assert _role("مررت بالذي ساعدني", 1) == "مجرور"


@pytest.mark.parametrize("sentence, at, role", [
    ("مَنْ حَلَفَ عَلَى مَالِ امْرِئٍ مُسْلِمٍ", 3, "مجرور"),  # مَالِ typed in jarr after على, not the command مِلْ
    ("لَا خَيْرَ فِي قَرَارٍ يُتَّخَذُ دُونَ دِرَاسَةٍ", 5, "مفعول فيه"),  # دُونَ is the book's ظرف, not a verb
])
def test_a_noun_with_the_noun_s_sign_is_never_read_as_the_command_its_letters_spell(sentence, at, role):
    assert _role(sentence, at) == role


def test_khilal_is_a_noun_of_place_not_the_preposition_camel_files_it_as():
    assert _role("انْخَفَضَتِ الصَّادِرَاتُ انْخِفَاضًا حَادًّا خِلَالَ الْأَشْهُرِ الثَّلَاثَةِ", 4) == "مفعول فيه"


def test_a_verb_after_the_question_hamza_the_dictionary_lacks_is_read_off_the_table():
    assert [_role("أَيَعْجِزُ أَحَدُكُمْ أَنْ يَقْرَأَ", i) for i in (0, 1)] == ["فعل", "فاعل"]  # the dictionary has يَعْجَزُ, not يَعْجِزُ


def test_a_verb_spelled_alike_in_the_active_and_the_passive_is_read_as_the_active():
    assert _role("هَلْ تُضَارُّونَ فِي رُؤْيَةِ الشَّمْسِ", 1) == "فعل"


def test_a_command_with_a_joined_fa_the_dictionary_lacks_is_a_verb():
    assert _role("إِذَا دَعَوْتُمُ اللَّهَ فَاعْزِمُوا", 3) == "فعل"


def test_a_noun_with_tanween_is_described_by_the_tanween_noun_after_it_not_added_to_it():
    assert _role("إِذَا كَانَ يَوْمٌ صَحْوٌ", 3) == "صفة"


def test_a_ya_typed_as_a_marked_maqsura_is_the_pronoun_of_the_speaker():
    assert _role("وَغَيْرُهُ أَحَبُّ إِلَىَّ مِنْهُ", 2) == "حرف جر"  # إِلَىَّ is إِلَيَّ


def test_a_conditional_noun_the_analyser_files_as_a_particle_is_a_noun():
    assert _role("لَنْ نَتَرَاجَعَ مَهْمَا طَالَ الزَّمَنُ", 2) in ("مبتدأ", "مفعول فيه")


def test_a_jar_before_an_and_its_verb_is_a_harf_jarr():
    assert _role("يَسْعَى الْمَسْؤُولُونَ إِلَى أَنْ يُوَفِّرُوا فُرَصًا", 2) == "حرف جر"


@pytest.mark.parametrize("sentence, at, role", [
    # واو الحال: the و brings a sentence, its raf' noun the mubtada, the word told of it the khabar
    ("لاَ يَزَالُ نَاسٌ مِنْ أُمَّتِي ظَاهِرِينَ حَتَّى يَأْتِيَهُمْ أَمْرُ اللَّهِ وَهُمْ ظَاهِرُونَ", 11, "خبر"),
    ("دَخَلَ الْوَزِيرُ الْقَاعَةَ مُبْتَسِمًا وَالصَّحَفِيُّونَ يَنْتَظِرُونَهُ بِفَارِغِ الصَّبْرِ", 4, "مبتدأ"),
    ("مَنْ حَلَفَ عَلَى مَالِ امْرِئٍ مُسْلِمٍ بِغَيْرِ حَقِّهِ لَقِيَ اللَّهَ وَهُوَ عَلَيْهِ غَضْبَانُ", 12, "خبر"),
    # ما before a fronted phrase and a raf' noun is the negation, not a relative
    ("مَا بَيْنَ خَلْقِ آدَمَ إِلَى قِيَامِ السَّاعَةِ خَلْقٌ أَكْبَرُ مِنَ الدَّجَّالِ", 0, "حرف"),
    # ما after a مضاف or a preposition, with its عائد inside a jar, is the relative
    ("سَأُنَبِّئُكَ بِتَأْوِيلِ مَا لَمْ تَسْتَطِعْ عَلَيْهِ صَبْرًا", 2, "مضاف إليه"),
    # a و that opens a clause is no joiner: the two khabars of the two mubtadas
    ("الْيَدُ الْعُلْيَا خَيْرٌ مِنَ الْيَدِ السُّفْلَى وَالْيَدُ الْعُلْيَا الْمُنْفِقَةُ وَالسُّفْلَى السَّائِلَةُ", 8, "خبر"),
    ("يَا عَبْدَ الرَّحْمَنِ بْنَ سَمُرَةَ لاَ تَسْأَلِ الإِمَارَةَ", 3, "صفة"),
    # the oath: the relative is sworn by, its صلة is the nominal sentence
    ("وَالَّذِي نَفْسِي بِيَدِهِ لاَ تَدْخُلُونَ الْجَنَّةَ حَتَّى تُؤْمِنُوا", 0, "مجرور"),
    ("وَالَّذِي نَفْسِي بِيَدِهِ لاَ تَدْخُلُونَ الْجَنَّةَ حَتَّى تُؤْمِنُوا", 1, "مبتدأ"),
    # أمّا: the noun after it is the mubtada, the فاء answer its khabar
    ("فَأَمَّا الَّذِي يَرَى النَّاسُ أَنَّهَا النَّارُ فَمَاءٌ بَارِدٌ", 6, "خبر"),
    ("وَأَمَّا مَنْ كَانَ مِنْ أَهْلِ الشَّقَاءِ فَيُيَسَّرُ لِعَمَلِ أَهْلِ الشَّقَاوَةِ", 1, "مبتدأ"),
    # كان: the اسم, the name added to بنو, a relative as the khabar, a noun joined after وَلَا
    ("كَانَ الْمُهَنْدِسُونَ يَعْمَلُونَ لَيْلًا وَنَهَارًا حَتَّى اكْتَمَلَ الْجِسْرُ قَبْلَ الْمَوْعِدِ الْمُحَدَّدِ", 1, "اسم كان"),
    ("كَانَتْ بَنُو إِسْرَائِيلَ يَغْتَسِلُونَ عُرَاةً", 2, "مضاف إليه"),
    ("لَيْسَ الْمِسْكِينُ الَّذِي تَرُدُّهُ التَّمْرَةُ وَالتَّمْرَتَانِ وَلاَ اللُّقْمَةُ وَلاَ اللُّقْمَتَانِ", 2, "خبر كان"),
    ("لَيْسَ الْمِسْكِينُ الَّذِي تَرُدُّهُ التَّمْرَةُ وَالتَّمْرَتَانِ وَلاَ اللُّقْمَةُ وَلاَ اللُّقْمَتَانِ", 7, "معطوف"),
    # the light لكن after a و opens a sentence: the noun after it is its mubtada
    ("لاَ هِجْرَةَ بَعْدَ الْفَتْحِ وَلَكِنْ جِهَادٌ وَنِيَّةٌ وَإِذَا اسْتُنْفِرْتُمْ فَانْفِرُوا", 5, "مبتدأ"),
    # a verb has one doer: the second raf' noun is the khabar of a left-out mubtada
    ("إِنَّ فِيكَ لَخَصْلَتَيْنِ يُحِبُّهُمَا اللَّهُ الْحِلْمُ وَالأَنَاةُ", 5, "خبر"),
])
def test_clause_structure_of_hadith_matn(sentence, at, role):
    assert _role(sentence, at) == role


def test_a_time_name_is_the_maful_fihi_though_the_list_never_named_it():
    assert _role("هَلْ رَأَى أَحَدٌ مِنْكُمُ الْبَارِحَةَ رُؤْيَا", 4) == "مفعول فيه"


def test_a_time_word_in_nasb_after_a_verb_that_takes_no_object_is_the_maful_fihi():
    assert _role("مَنْ يَقُمْ لَيْلَةَ الْقَدْرِ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ", 2) == "مفعول فيه"


@pytest.mark.parametrize("sentence, at", [
    ("هَلْ سَتَنْجَحُ الْجُهُودُ الدِّبْلُومَاسِيَّةُ فِي وَقْفِ التَّصْعِيدِ بَيْنَ الطَّرَفَيْنِ", 7),
    ("لاَ هِجْرَةَ بَعْدَ الْفَتْحِ وَلَكِنْ جِهَادٌ وَنِيَّةٌ", 2),
])
def test_a_time_or_place_word_in_nasb_hung_on_a_noun_or_on_la_is_the_maful_fihi(sentence, at):
    assert _role(sentence, at) == "مفعول فيه"


def test_a_pointer_with_a_time_word_in_nasb_after_it_is_the_maful_fihi():
    assert _role("أَعْلَنَتِ الشَّرِكَةُ أَنَّ أَرْبَاحَهَا ارْتَفَعَتْ بِنِسْبَةِ عَشَرَةٍ فِي الْمِئَةِ هَذَا الْعَامَ", 9) == "مفعول فيه"


def test_a_single_act_masdar_with_a_weak_radical_is_the_maful_mutlaq():
    assert _role("لَمْ يَخْطُ خَطْوَةً إِلاَّ رُفِعَ بِهَا دَرَجَةً", 2) == "مفعول مطلق"


def test_an_amount_word_after_a_verb_is_the_maful_mutlaq_not_a_hal():
    assert _role("وَاللَّهِ لَوْ تَعْلَمُونَ مَا أَعْلَمُ لَبَكَيْتُمْ كَثِيرًا", 6) == "مفعول مطلق"


def test_a_describing_word_of_the_doer_shape_with_ta_marbuta_is_a_hal():
    assert _role("كَانَتْ بَنُو إِسْرَائِيلَ يَغْتَسِلُونَ عُرَاةً", 4) == "حال"


def test_a_masdar_after_a_passive_verb_whose_object_became_its_deputy_is_a_hal():
    assert _role("لاَ يُقْتَلُ قُرَشِيٌّ صَبْرًا بَعْدَ هَذَا الْيَوْمِ إِلَى يَوْمِ الْقِيَامَةِ", 3) == "حال"
    assert _role("لَمْ يَخْطُ خَطْوَةً إِلاَّ رُفِعَ بِهَا دَرَجَةً", 6) == "مفعول به"  # a noun of a single act names a thing


def test_a_masdar_of_the_heart_after_the_verb_is_the_maful_li_ajlih():
    assert _role("مَنْ يَقُمْ لَيْلَةَ الْقَدْرِ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ", 4) == "مفعول لأجله"


def test_a_heart_masdar_added_to_an_plus_verb_is_the_maful_li_ajlih():
    assert _role("وَغَيْرُهُ أَحَبُّ إِلَيَّ مِنْهُ خَشْيَةَ أَنْ يُكَبَّ فِي النَّارِ عَلَى وَجْهِهِ", 4) == "مفعول لأجله"


def test_a_numeral_after_a_passive_participle_noun_is_its_naat():
    assert _role("شَارَكَ جَمِيعُ الْمُرَشَّحِينَ فِي الْمُنَاظَرَةِ إِلَّا مُرَشَّحًا وَاحِدًا اعْتَذَرَ لِأَسْبَابٍ صِحِّيَّةٍ", 7) == "صفة"


def test_a_second_describing_word_with_al_describes_the_same_noun():
    assert _role("إِنَّ فِي الْجَنَّةِ لَشَجَرَةً يَسِيرُ الرَّاكِبُ الْجَوَادَ الْمُضَمَّرَ السَّرِيعَ مِائَةَ عَامٍ", 8) == "صفة"


def test_an_indefinite_word_after_an_construct_of_an_unknown_noun_is_its_naat():
    assert _role("يَسْعَى الْمَسْؤُولُونَ إِلَى أَنْ يُوَفِّرُوا فُرَصَ عَمَلٍ جَدِيدَةً لِلشَّبَابِ الْعَاطِلِينَ", 7) == "صفة"


def test_a_noun_showing_no_case_after_an_elative_is_its_tamyeez():
    assert _role("أَعْظَمُ النَّاسِ أَجْرًا فِي الصَّلاَةِ أَبْعَدُهُمْ فَأَبْعَدُهُمْ مَمْشًى", 7) == "تمييز"


def test_a_masdar_added_to_its_doer_governs_the_object_after_it():
    assert _role("أَدَّى إِهْمَالُ الْمَسْؤُولِينَ صِيَانَةَ الْجُسُورِ الْقَدِيمَةِ إِلَى انْهِيَارِ أَحَدِهَا الْأُسْبُوعَ الْمَاضِيَ", 3) == "مفعول به"


def test_the_noun_after_lawla_is_its_mubtada():
    assert _role("كَادَتِ الْمُفَاوَضَاتُ تَنْهَارُ لَوْلَا تَدَخُّلُ الْوَسِيطِ الدَّوْلِيِّ فِي اللَّحْظَةِ الْأَخِيرَةِ", 4) == "مبتدأ"


def test_a_noun_after_illa_is_no_badal_of_a_noun_in_another_clause():
    assert _role("لاَ يَعْلَمُ مَا تَغِيضُ الأَرْحَامُ إِلاَّ اللَّهُ", 6) == "فاعل"


def test_a_relative_ma_that_is_the_one_object_of_a_passive_verb_is_its_deputy():
    assert _role("مَنْ يَقُمْ لَيْلَةَ الْقَدْرِ إِيمَانًا وَاحْتِسَابًا غُفِرَ لَهُ مَا تَقَدَّمَ مِنْ ذَنْبِهِ", 8) == "نائب فاعل"


def test_kayfa_before_a_verb_in_a_recorded_ayah_is_the_hal():
    # the treebank tags كيف a particle; the books name it the حال of the verbal clause after it (not before a noun)
    assert iraab.analyze("أَلَمْ تَرَ كَيْفَ فَعَلَ رَبُّكَ بِأَصْحَابِ الْفِيلِ")["words"][2]["role"] == "حَالٌ"


def test_a_built_or_unseen_case_zarf_word_is_not_the_maful_fihi_of_a_nominal_sentence():
    assert _role("أَيْنَ الْكِتَابُ", 0) == "خبر"
    assert _role("الْيَدُ الْعُلْيَا خَيْرٌ مِنَ الْيَدِ السُّفْلَى", 1) == "صفة"


def test_an_indefinite_word_after_a_construct_with_no_verb_above_is_the_khabar():
    assert _role("خَاتَمُ فِضَّةٍ جَمِيلٌ", 2) == "خبر"


def test_an_amount_word_after_a_verb_that_takes_an_object_is_left_to_the_other_rules():
    assert _role("الَّذِي يَقْرَأُ كَثِيرًا يَزْدَادُ عِلْمُهُ", 2) == "حال"


def test_a_number_counting_a_time_word_is_the_maful_fihi_and_that_word_its_tamyeez():
    # Awdah al-Masalik V2 p231: the numbers specified by a time or place name stand in for the zarf
    assert _role("إِنَّ خَلْقَ أَحَدِكُمْ يُجْمَعُ فِي بَطْنِ أُمِّهِ أَرْبَعِينَ لَيْلَةً", 7) == "مفعول فيه"
    assert _role("إِنَّ خَلْقَ أَحَدِكُمْ يُجْمَعُ فِي بَطْنِ أُمِّهِ أَرْبَعِينَ لَيْلَةً", 8) == "تمييز"


def test_a_hundred_added_to_a_time_word_is_the_maful_fihi_though_hung_as_an_object():
    assert _role("إِنَّ فِي الْجَنَّةِ لَشَجَرَةً يَسِيرُ الرَّاكِبُ الْجَوَادَ الْمُضَمَّرَ السَّرِيعَ مِائَةَ عَامٍ", 9) == "مفعول فيه"


def test_inna_with_a_noun_in_nasb_is_no_negation_and_ila_excepts_from_its_ism():
    # إِنَّ is not the إن that denies: تِسْعَةً is its اسم and the word after إِلاَّ the مستثنى
    assert _role("إِنَّ لِلَّهِ تِسْعَةً وَتِسْعِينَ اسْمًا مِائَةً إِلاَّ وَاحِدًا", 2) == "اسم إن"
    assert _role("إِنَّ لِلَّهِ تِسْعَةً وَتِسْعِينَ اسْمًا مِائَةً إِلاَّ وَاحِدًا", 7) == "مستثنى"


def test_a_number_before_its_counted_noun_is_the_object_not_a_state():
    assert _role("اشْتَرَتِ الْمَكْتَبَةُ خَمْسَةً وَعِشْرِينَ كِتَابًا نَادِرًا مِنْ مَزَادٍ عَلَنِيٍّ", 2) == "مفعول به"


def test_the_doer_of_an_outer_verb_comes_last_after_the_relative_clause():
    sentence = "شَارَكَتْ فِي الْقِمَّةِ الَّتِي اسْتَضَافَتْهَا الْعَاصِمَةُ إِحْدَى عَشْرَةَ دَوْلَةً إِفْرِيقِيَّةً"
    assert _role(sentence, 5) == "فاعل"
    assert _role(sentence, 6) == "فاعل"


def test_an_oath_answer_with_the_emphatic_nun_is_a_verb_and_the_place_word_after_it_a_maful_fihi():
    sentence = "وَالَّذِي نَفْسِي بِيَدِهِ لأَقْضِيَنَّ بَيْنَكُمَا بِكِتَابِ اللَّهِ"
    assert _role(sentence, 3) == "فعل"
    assert _role(sentence, 4) == "مفعول فيه"


def test_bare_al_umm_is_a_noun_not_the_particle_am():
    # a joining word takes no ال (Ibn Aqil V1 p15): الأم typed bare is the noun
    assert _role("كانت الأم تطبخ", 1) == "اسم كان"
    assert _role("الأم تطبخ الطعام", 0) == "مبتدأ"


def test_bare_nima_before_a_noun_with_al_is_the_verb_of_praise_with_its_doer():
    assert [_role("نعم الرجل زيد", i) for i in range(3)] == ["فعل", "فاعل", "مبتدأ"]


def test_bare_noun_after_kana_with_a_verb_after_it_is_its_ism():
    assert _role("كان الطفل يلعب", 1) == "اسم كان"


def test_a_relative_after_the_ism_of_kana_describes_it_and_is_no_object():
    # كان works on an اسم and a خبر (Tasheel 1.9), so the relative stays the ism's صفة
    assert _role("كان الطالب الذي نجح في الامتحان يدرس ليلا ونهارا", 2) == "صفة"


def test_bare_noun_after_illa_with_the_doer_before_it_is_its_badal():
    assert _role("ما جاء أحد إلا زيد", 4) == "بدل"


def test_bare_noun_straight_after_the_six_noun_in_nasb_is_the_doer():
    # no verb keeps two objects but a verb of two (Ibn Aqil V1 p184): the alif of أباه shows the nasb
    assert [_role("أكرم أباه الولد", i) for i in (1, 2)] == ["مفعول به", "فاعل"]


def test_bare_noun_after_a_called_noun_with_no_damma_is_its_mudaf_ilayh():
    assert _role("يا عبد الله اجتهد", 2) == "مضاف إليه"


def test_bare_tanween_alif_of_a_called_participle_makes_the_noun_after_it_its_object():
    # a word with tanween is complete, so nothing is added to it; the six nouns' alif is not tanween (يا أخا العرب)
    assert _role("يا سائقا الشاحنة تمهل", 2) == "مفعول به"
    assert _role("يا أخا العرب تعال", 2) == "مضاف إليه"


def test_bare_part_noun_with_a_pronoun_back_to_the_noun_before_it_is_its_badal():
    # the sameness of case is not tested when no case is typed (Tasheel 3.10.4 p95: بدل البعض والاشتمال)
    assert _role("قرأت الكتاب نصفه", 2) == "بدل"
    assert _role("أعجبني البستان جماله", 2) == "بدل"


def test_bare_second_noun_after_the_doer_of_a_verb_of_two_objects_is_its_first_object():
    assert [_role("أعطى المعلم الطالب كتابا", i) for i in (1, 2, 3)] == ["فاعل", "مفعول به", "مفعول به"]


def test_bare_emphasis_words_stay_tawkeed():
    assert _role("رأيت الصديقين كليهما", 2) == "توكيد"
    assert _role("حضر الضيوف أجمعون", 2) == "توكيد"
    assert _role("حضر الخليفة عمر", 2) == "بدل"


def test_bare_noun_before_a_verb_with_its_own_doer_and_no_pronoun_back_is_its_fronted_object():
    # a مبتدأ needs a pronoun back to it in the verb's clause; the doer of الطلاب نجحوا is that pronoun
    assert _role("الكتاب قرأ الطالب", 0) == "مفعول به"
    assert _role("الحق نقول", 0) == "مفعول به"
    assert _role("الطلاب نجحوا", 0) == "مبتدأ"


def test_bare_lakin_with_one_word_after_it_joins_that_word():
    # no khabar can follow a single word, so the light لكن is meant (Tasheel 1.8 p20); with a khabar after, it stays the inna sister
    assert _role("ما جاء زيد لكن عمرو", 4) == "معطوف"
    assert _role("لا تصحب الأحمق لكن العاقل", 4) == "معطوف"
    assert _role("لكن الطالب مجتهد", 1) == "اسم إن"


def test_bare_describing_word_after_its_noun_is_its_sifa_whatever_ending_the_parser_guessed():
    # no case is shown for the two to disagree in, and ين is a dual or a plural alike (Tasheel 3.10.1: the na't follows its noun)
    assert _role("سمعت صوت الطفل الباكي في الليل", 3) == "صفة"
    assert _role("رحبت بالزائرين اللطيفين", 2) == "صفة"
    assert _role("الدين النصيحة", 1) == "خبر"


def test_bare_noun_with_a_pronoun_back_to_a_doer_whose_verb_owes_an_object_is_that_object():
    assert _role("ارتدى المحارب درعه", 2) == "مفعول به"


def test_bare_describing_word_after_an_indefinite_idafa_under_a_verb_is_its_sifa_not_a_hal():
    # a hal's owner is known and a describer of a نكرة is its صفة (Tasheel 3.10.1); a bare جديدة shows no nasb for a hal to need
    assert _role("يسعى المسؤولون إلى أن يوفروا فرص عمل جديدة للشباب", 7) == "صفة"
    assert _role("قرأ الطالب كتاب طالب جديدا", 4) == "حال"


def test_bare_word_after_a_pronoun_with_no_case_given_is_its_khabar():
    # a nominal sentence rests on its khabar (Tasheel 1.4 p6); a diptote or a name shows no case to say otherwise
    assert _role("لقي الله وهو غضبان", 3) == "خبر"
    assert _role("لقي الله وهم ظاهرون", 3) == "خبر"


def test_bare_describing_word_after_a_noun_showing_no_case_is_its_sifa():
    assert _role("حلف على مال امرئ مسلم", 4) == "صفة"


def test_bare_plural_without_its_nun_is_the_mudaf_of_the_noun_after_it():
    # Alfiyya: نونا تلي الإعراب أو تنوينا مما تضيف احذف
    assert _role("كانت بنو إسرائيل يغتسلون عراة", 2) == "مضاف إليه"
    assert _role("جاء معلمو المدرسة", 2) == "مضاف إليه"


def test_a_nasb_noun_straight_after_the_ism_of_kana_is_its_khabar():
    # Tasheel 1.9: كان and its sisters put their khabar in nasb; حقا is a masdar word only elsewhere
    assert _role("كَانَ اللَّهُ الصَّمَدَ", 2) == "خبر كان"
    assert _role("كَانَ الْعَيْنُ حَقًّا", 2) == "خبر كان"
    assert _role("كَانَ زَيْدٌ يَوْمًا مُسَافِرًا", 2) == "مفعول فيه"  # a time word beside the khabar stays a ظرف


def test_bare_lam_after_a_relative_is_the_jazm_particle_not_a_verb():
    assert _role("سأنبئك بتأويل ما لم تستطع عليه صبرا", 3) == "حرف"


def test_a_bare_verb_the_dictionary_lacks_is_read_off_sarfs_table_in_a_verb_position():
    # Ibn Aqil V4 p37: the answer of a condition that is a command takes the ف (إن جاء زيد فاضربه); a question hamza and
    # هل want a verb (Tasheel); the root is one the books file, so a name shaped like a verb stays a name
    assert _role("إذا دعوتم الله فاعزموا في الدعاء", 3) == "فعل"
    assert _role("وإذا استنفرتم فانفروا", 2) == "فعل"
    assert _role("أيعجز أحدكم أن يقرأ ثلث القرآن في ليلة", 0) == "فعل"
    assert _role("أيعجز أحدكم أن يقرأ ثلث القرآن في ليلة", 1) == "فاعل"
    assert _role("هل تضارون في رؤية الشمس", 1) == "فعل"
    assert _role("أفاسق أنت", 0) != "فعل"  # a name the dictionary reads is not re-read as a verb


def test_a_bare_place_word_with_its_mudaf_ilayh_is_the_zarf_not_a_follower():
    # Tasheel 3.2 p67: a place word on no other list, added to a noun of its own, is the zarf; a noun's نعت or مضاف إليه is not
    assert _role("لا هجرة بعد الفتح ولكن جهاد", 2) == "مفعول فيه"
    assert _role("هل ستنجح الجهود الدبلوماسية في وقف التصعيد بين الطرفين", 7) == "مفعول فيه"
    assert _role("اللهم فإني أظن أنك قد وضعت الحرب بيننا وبينهم", 7) == "مفعول فيه"


def test_a_bare_noun_after_a_masdar_and_its_doer_is_the_masdars_object():
    # Alfiyya, إعمال المصدر: بفعله المصدر ألحق في العمل مضافا (Ibn Aqil V3, page unchecked)
    assert _role("أدى إهمال المسؤولين صيانة الجسور القديمة إلى انهيار", 3) == "مفعول به"


def test_a_bare_noun_ending_the_sentence_on_an_anna_with_no_khabar_is_its_khabar():
    # Tasheel 1.8: إنّ and its sisters take an اسم and a خبر, so the pair cannot be left without one
    assert _role("ولو أن ما في الأرض من شجرة أقلام", 7) == "خبر إن"


def test_bare_lam_on_the_ism_behind_a_fronted_khabar_of_inna_is_the_lam_of_ibtida():
    # Alfiyya: وتصحب الواسط معمول الخبر والفصل واسما حل قبله الخبر (page unchecked); لسحرا is no verb, and no ism is one
    assert _role("إن من البيان لسحرا", 3) == "اسم إن"


def test_a_second_bare_sentence_after_a_waw_has_its_own_mubtada_and_khabar():
    # عطف الجمل (Ibn Aqil, page unchecked): الحلال بين والحرام بين is two sentences; one khabar after two nouns joined stays one
    assert [_role("الحلال بين والحرام بين", i) for i in (2, 3)] == ["مبتدأ", "خبر"]
    assert _role("الحلال والحرام بين", 1) == "معطوف"


def test_hayth_hung_as_an_object_is_still_the_maful_fihi():
    # the parser links حيث as the verb's object when a long coordination follows; its damma is its build, no doer's raf'
    assert _role("سَنَبْنِي الْمَصْنَعَ حَيْثُ تَتَوَفَّرُ الْمِيَاهُ وَالْكَهْرَبَاءُ وَالْأَيْدِي الْعَامِلَةُ", 2) == "مفعول فيه"


def test_a_relative_after_a_noun_and_its_describing_word_describes_the_noun():
    # Tasheel 3.10.1: the na't follows its noun, whatever other na't stand between; الذي after التقرير السنوي is a صفة
    assert _role("قَرَأْتُ التَّقْرِيرَ السَّنَوِيَّ الَّذِي أَصْدَرَتْهُ الْوِزَارَةُ", 3) == "صفة"


def test_a_conditional_noun_before_a_verb_that_takes_no_object_is_the_mubtada():
    # Tasheel 1.9: كان takes a khabar, no object; Alfiyya: a verb of cleanliness (توضأ) is لازم; a pronoun on the verb is its object
    assert _role("مَنْ كَانَ يُؤْمِنُ بِاللَّهِ فَلْيَقُلْ خَيْرًا", 0) == "مبتدأ"
    assert _role("مَنْ تَوَضَّأَ فَأَحْسَنَ الْوُضُوءَ خَرَجَتْ خَطَايَاهُ", 0) == "مبتدأ"
    assert _role("فَمَنْ أَخَذَهُ أَخَذَ بِحَظٍّ وَافِرٍ", 0) == "مبتدأ"


def test_a_fa_before_the_oath_waw_leaves_the_oath_its_sworn_by_majrur():
    # Ibn Aqil vol 4 p42 (bab al-qasam): the فاء only ties the oath on; the sworn-by is still the oath's majrur
    assert _role("فَوَاللَّهِ إِنِّي لَأُعْطِي الرَّجُلَ", 0) == "مجرور"
    assert _role("فَوَالَّذِي نَفْسِي بِيَدِهِ لَا يُؤْمِنُ أَحَدُكُمْ", 0) == "مجرور"


def test_qat_and_awd_and_a_cut_off_ba3d_stay_the_adverb_whatever_the_parser_calls_them():
    # Awdah V2 p232: قط وعوض لا يفارقان الظرفية; Ibn Aqil V3 p73: قبل/بعد cut off from their idafa are built on damma, still a zarf
    assert _role("مَا رَأَيْتُهُ قَطُّ", 2) == "مفعول فيه"
    assert _role("لَا أُكَلِّمُهُ عَوْضُ", 2) == "مفعول فيه"
    assert _role("جَاءَ زَيْدٌ بَعْدُ", 2) == "مفعول فيه"
    assert _role("أَمَّا بَعْدُ فَإِنَّ الْعِلْمَ نُورٌ", 1) == "مفعول فيه"
    assert _role("جَاءَ زَيْدٌ بَعْدَ عَمْرٍو", 2) == "مفعول فيه"
    assert _role("اخْتَبَأَ الْقِطُّ خَلْفَ السِّتَارَةِ", 1) == "فاعل"  # with ال it is the noun, the cat


def test_an_elative_read_as_a_verb_is_the_elative_when_a_min_phrase_follows():
    # Tashil V1 p132: the elative's مفضول, in jarr by مِنْ, follows it or what it governs; a doer straight after keeps the verb
    assert _role("مَا كُنْتُ قَطُّ أَقْوَى وَلَا أَيْسَرَ مِنِّي", 5) == "معطوف"
    assert _role("حَتَّى أَكُونَ أَحَبَّ إِلَيْهِ مِنْ وَالِدِهِ", 2) == "خبر كان"  # the doubled shape
    assert _role("فَلْيُبَلِّغِ الشَّاهِدُ الْغَائِبَ فَإِنَّ الشَّاهِدَ عَسَى أَنْ يُبَلِّغَ مَنْ هُوَ أَوْعَى لَهُ مِنْهُ", 10) == "خبر"
    assert _role("مَا أَنْعَمَ اللَّهُ عَلَيَّ مِنْ نِعْمَةٍ", 1) == "فعل"
    assert _role("أَكْرَمَ زَيْدٌ عَمْرًا مِنْ بَيْتِهِ", 0) == "فعل"
    assert _role("أَرْسَلَ إِلَيْهِ فَأَخَذَ مِنْهُ", 0) == "فعل"  # a verb stands before the مِنْ: it is that verb's, not the elative's


def test_an_elative_straight_after_an_indefinite_noun_in_jarr_is_its_sifa():
    # Tasheel 3.10.1: the na't follows its noun; the elative's fatha is a diptote's jarr as well
    assert _role("فَرُبَّ مُبَلَّغٍ أَوْعَى مِنْ سَامِعٍ", 2) == "صفة"
    assert _role("مَا تَقَرَّبَ إِلَيَّ عَبْدِي بِشَيْءٍ أَحَبَّ إِلَيَّ مِمَّا افْتَرَضْتُ عَلَيْهِ", 5) == "صفة"


def test_an_opening_oath_waw_leaves_a_named_sworn_by_majrur_whatever_the_answer_opens_with():
    # Ibn Aqil V4 p42 (bab al-qasam): the sworn-by is the oath's majrur; the answer opens with ما، قد، ل، إن، لا
    assert _role("وَاللَّهِ مَا أَنْعَمَ اللَّهُ عَلَيَّ مِنْ نِعْمَةٍ", 0) == "مجرور"
    assert _role("وَاللَّهِ لَقَدْ بَذَلْنَا كُلَّ مَا نَمْلِكُ مِنْ جُهْدٍ وَمَالٍ", 0) == "مجرور"


def test_a_known_word_then_man_with_its_sila_is_told_by_it():
    # Ibn Aqil V1 p216: the mubtada is known, and man with its sila is one word, the khabar; man never describes a noun
    assert [_role("الْكَيِّسُ مَنْ دَانَ نَفْسَهُ وَعَمِلَ لِمَا بَعْدَ الْمَوْتِ", i) for i in (0, 1)] == ["مبتدأ", "خبر"]
    # after the second و the same: the clause rests on the known word, not on the first man
    assert [_role("الْكَيِّسُ مَنْ دَانَ نَفْسَهُ وَالْعَاجِزُ مَنْ أَتْبَعَ نَفْسَهُ هَوَاهَا", i) for i in (4, 5)] == ["مبتدأ", "خبر"]
    # a word with a khabar of its own keeps man's clause as its na't-less relative: nothing owed
    assert _role("جَاءَ الرَّجُلُ مَنْ نَجَحَ", 2) != "خبر"
    # the الذي family only after a particle that cannot govern the noun
    assert [_role("لَيْسَ الشَّدِيدُ بِالصُّرَعَةِ إِنَّمَا الشَّدِيدُ الَّذِي يَمْلِكُ نَفْسَهُ عِنْدَ الْغَضَبِ", i) for i in (4, 5)] == ["مبتدأ", "خبر"]
    assert _role("الشَّدِيدُ الَّذِي يَمْلِكُ نَفْسَهُ", 1) == "صفة"


def test_man_asks_before_a_noun_though_a_preposition_or_a_relative_clause_follows():
    # man never negates, so the preposition after the khabar (ما أنت بعالم) shows nothing; a relative's sila is no clause of its own
    assert [_role("مَنْ أَحَقُّ النَّاسِ بِحُسْنِ صَحَابَتِي", i) for i in (0, 1)] == ["مبتدأ", "خبر"]
    assert [_role("مَنِ الَّذِي يَضْمَنُ لِلْمُسْتَثْمِرِ", i) for i in (0, 1)] == ["مبتدأ", "خبر"]
    assert _role("مَا أَنْتَ بِعَالِمٍ", 1) != "مبتدأ"  # ما can negate: the preposition keeps it from asking


def test_a_conditional_noun_before_a_verb_with_no_doer_of_its_own_is_the_mubtada():
    # the verb's hidden doer goes back to the noun (asked.man_before_verb): ذبح has none written, so man is its mubtada
    assert _role("مَنْ ذَبَحَ قَبْلَ الصَّلَاةِ فَإِنَّمَا يَذْبَحُ لِنَفْسِهِ وَمَنْ ذَبَحَ بَعْدَ الصَّلَاةِ فَقَدْ تَمَّ نُسُكُهُ", 7) == "مبتدأ"
    assert _role("مَنْ تَشَرَّفَ لَهَا تَسْتَشْرِفْهُ", 0) == "مبتدأ"
    # with a doer written, the verb needs no pronoun back and the noun is its object
    assert _role("مَنْ يَضْرِبْ زَيْدٌ يَضْرِبْ", 0) == "مفعول به"


def test_a_passive_verbs_relative_is_its_deputy_though_a_doer_was_said_before():
    # Ibn Aqil V2 (the passive): the verb that is not told of its doer raises the done-to; a doer said in an earlier clause is no pronoun for it
    assert _role("شَارَكَ فِي الْحَمْلَةِ الْجَمِيعُ فَجُمِعَ مِنَ التَّبَرُّعَاتِ مَا يَكْفِي لِبِنَاءِ مُسْتَشْفًى", 7) == "نائب فاعل"
    # a verb that is not passive keeps the relative as the object the doer said before has left it
    assert _role("شَارَكَ الْجَمِيعُ فَجَمَعَ مِنَ التَّبَرُّعَاتِ مَا يَكْفِي لِبِنَاءِ مُسْتَشْفًى", 5) == "مفعول به"


def test_a_noun_after_a_fa_verb_clause_with_a_waw_noun_before_it_is_still_joined():
    # Tasheel 3.7: a hal clause opens with the waw alone; a fa before its verb ties it to the sentence before
    assert _role("شَارَكَ الْجَمِيعُ حَتَّى الْأَطْفَالُ وَالشُّيُوخُ فَجُمِعَ مِنَ التَّبَرُّعَاتِ مَا يَكْفِي", 4) == "معطوف"


def test_a_ma_the_parser_calls_the_doer_of_a_passive_verb_is_its_deputy():
    # Ibn Aqil V2 (the passive): the one raised in the doer's place is the deputy, however the parser linked the ما
    assert _role("وَاللَّهِ لَقَدْ أُنْجِزَ فِي هَذَا الْمَشْرُوعِ مَا يَزِيدُ عَلَى ثَلَاثِمِئَةٍ وَخَمْسِينَ كِيلُومِتْرًا", 6) == "نائب فاعل"


def test_a_masdar_the_books_list_as_a_reason_is_the_maful_li_ajlih():
    # Tasheel 3.8.3: the reason masdars (closed_words reason_masdars) answer "why", a masdar of a feeling or a motive; each row is its own case
    assert _role("إِنَّ مُوسَى كَانَ رَجُلًا حَيِيًّا سِتِّيرًا، لَا يُرَى مِنْ جِلْدِهِ شَيْءٌ اسْتِحْيَاءً مِنْهُ", 11) == "مفعول لأجله"
    assert _role("أَغْلَقَتِ الْمَدَارِسُ أَبْوَابَهَا يَوْمَيْنِ حِفَاظًا عَلَى سَلَامَةِ الطُّلَّابِ وَتَجَنُّبًا لِتَفَشِّي الْعَدْوَى بَيْنَ التَّلَامِيذِ", 4) == "مفعول لأجله"
    assert _role("سَارَ الْمُتَظَاهِرُونَ وَالطَّرِيقَ إِلَى الْبَرْلَمَانِ احْتِجَاجًا عَلَى الْقَرَارِ وَسَارَ الصَّحَفِيُّونَ وَالْمُصَوِّرُونَ خَلْفَهُمْ رَغْبَةً فِي نَقْلِ الْحَدَثِ", 5) == "مفعول لأجله"


def test_a_time_or_place_noun_the_books_list_is_the_zarf_though_it_stands_in_nasb():
    # Ibn Aqil V2 (the zarf): طَوَالَ، بِضْعَةَ أَيَّامٍ، دُبُرَ name a stretch of time or a place
    assert _role("شَجَّعَ وَدَعَمَ الْمُدَرِّبُ اللَّاعِبِينَ الشَّبَابَ طَوَالَ الْمَوْسِمِ وَلَمْ يَتَخَلَّ عَنْهُمْ حَتَّى فِي أَصْعَبِ الظُّرُوفِ", 5) == "مفعول فيه"
    assert _role("سَارَ الْمُسَافِرُ وَالنِّيلَ بِضْعَةَ أَيَّامٍ حَتَّى بَلَغَ مَدِينَةَ أَسْوَانَ وَهُوَ مُتْعَبٌ لَكِنَّهُ سَعِيدٌ", 3) == "مفعول فيه"
    assert _role("يَأْتِي الْمَسِيحُ مِنْ قِبَلِ الْمَشْرِقِ، هِمَّتُهُ الْمَدِينَةُ، حَتَّى يَنْزِلَ دُبُرَ أُحُدٍ، ثُمَّ تَصْرِفُ الْمَلَائِكَةُ وَجْهَهُ قِبَلَ الشَّامِ", 9) == "مفعول فيه"


def test_a_time_word_in_nasb_the_parser_hung_as_a_doer_is_the_zarf():
    # a doer is never in nasb (كُلَّ يَوْمٍ), so the word the reader typed in nasb is the zarf of the verb after it
    assert _role("كُلُّ سُلَامَى مِنَ النَّاسِ عَلَيْهِ صَدَقَةٌ كُلَّ يَوْمٍ تَطْلُعُ فِيهِ الشَّمْسُ وَالْكَلِمَةُ الطَّيِّبَةُ صَدَقَةٌ", 6) == "مفعول فيه"


def test_a_noun_on_the_sifa_mushabbaha_measure_after_a_verb_is_its_object_not_a_state():
    # Ibn Aqil: the state is a derived word (a doer, a done-to); فَعِيل names a thing (طَرِيق), and نَبِيّ is no describing word
    assert _role("مَنْ سَلَكَ طَرِيقًا يَلْتَمِسُ فِيهِ عِلْمًا سَهَّلَ اللَّهُ لَهُ طَرِيقًا إِلَى الْجَنَّةِ", 2) == "مفعول به"
    assert _role("مَنْ سَلَكَ طَرِيقًا يَلْتَمِسُ فِيهِ عِلْمًا سَهَّلَ اللَّهُ لَهُ طَرِيقًا إِلَى الْجَنَّةِ", 9) == "مفعول به"
    # a verb the parser hung as the object (إِلَّا رَعَى) is no object, so بَعَثَ still takes the noun
    assert _role("مَا بَعَثَ اللَّهُ نَبِيًّا إِلَّا رَعَى الْغَنَمَ، فَقَالَ أَصْحَابُهُ: وَأَنْتَ؟ فَقَالَ: نَعَمْ، كُنْتُ أَرْعَاهَا عَلَى قَرَارِيطَ لِأَهْلِ مَكَّةَ", 3) == "مفعول به"
    # but a describing word the analyser also calls a noun (غَزِيرَةً) stays the state of the verb
    assert _role("هَاجَمَتِ الْعَاصِفَةُ السَّاحِلَ هُجُومًا عَنِيفًا، وَأَغْلَقَتِ الْمَوَانِئُ أَبْوَابَهَا حِفَاظًا عَلَى السُّفُنِ، وَالْأَمْطَارُ تَهْطِلُ غَزِيرَةً", 13) == "حال"


def test_what_follows_a_verb_of_praise_or_blame_is_its_tamyeez_a_describing_word_too():
    # Ibn Aqil V3 (نِعْمَ وبِئْسَ): نِعْمَ رَجُلًا، and a describing word in the same place (شَرِيكًا، نَاصِحًا) is no state
    sentence = "نِعْمَ شَرِيكًا لِلْمُسْتَثْمِرِينَ الْمَصْرِفُ الَّذِي يَدْعَمُ مَشَارِيعَهُمْ وَبِئْسَ نَاصِحًا مَنْ يُشَجِّعُهُمْ عَلَى الْمُغَامَرَةِ بِلَا دِرَاسَةٍ"
    assert [_role(sentence, i) for i in (1, 8)] == ["تمييز", "تمييز"]


def test_a_masdar_after_a_verb_whose_object_is_already_said_is_its_absolute_object():
    # a verb of one object takes no second: لَا يَقْبِضُ الْعِلْمَ انْتِزَاعًا, the masdar after the object says how
    assert _role("إِنَّ اللَّهَ لَا يَقْبِضُ الْعِلْمَ انْتِزَاعًا يَنْتَزِعُهُ مِنَ الْعِبَادِ، وَلَكِنْ يَقْبِضُ الْعِلْمَ بِقَبْضِ الْعُلَمَاءِ", 5) == "مفعول مطلق"


def test_a_passive_verb_of_two_objects_names_its_deputy_and_the_object_left():
    # Tasheel 1.10 p26 (page unchecked for the passive): the first object is raised to the doer's place, the second stays منصوب
    sentence = "عُلِّمَ الْمُتَدَرِّبُونَ لُغَةَ الْإِشَارَةِ خِلَالَ شَهْرٍ وَاحِدٍ"
    assert [_role(sentence, i) for i in (1, 2)] == ["نائب فاعل", "مفعول به"]


def test_a_noun_with_a_sentence_left_loose_after_it_is_its_mubtada():
    # Tasheel 1.4 p6: the parser hangs the noun on the particle before it and leaves its sentence beside it; the noun is what that sentence tells of
    assert _role("بَيْنَمَا رَجُلٌ يَجُرُّ إِزَارَهُ مِنَ الْخُيَلَاءِ خُسِفَ بِهِ", 1) == "مبتدأ"  # a verb loose after it
    assert [_role("إِنْ تَلْتَزِمِ الدُّوَلُ بِتَعَهُّدَاتِهَا فَالْمُسْتَقْبَلُ أَفْضَلُ لِلْأَجْيَالِ", i) for i in (4, 5)] == ["مبتدأ", "خبر"]  # a describing word loose
    assert _role("الْبَيِّعَانِ بِالْخِيَارِ مَا لَمْ يَتَفَرَّقَا", 0) == "مبتدأ"  # the root noun of a sentence whose verb is in another clause
    # the noun stays what its own place says when it is called, or is a describing word the tagger took for a verb
    assert _role("يَا لَلْعَدَالَةِ لِلْمَظْلُومِينَ وَا حَسْرَتَاهُ عَلَى حَقٍّ ضَاعَ", 4) != "مبتدأ"
    assert _role("تَجِدُونَ مِنْ شَرِّ النَّاسِ ذَا الْوَجْهَيْنِ الَّذِي يَأْتِي هَؤُلَاءِ بِوَجْهٍ وَهَؤُلَاءِ بِوَجْهٍ", 0) != "مبتدأ"


def test_a_pronoun_is_built_so_its_fatha_makes_it_no_hal_or_tamyeez():
    # a fatha on a built word is no sign of nasb (facts.indefinite_nasb)
    assert _role("بَيْنَمَا رَجُلٌ يَجُرُّ إِزَارَهُ مِنَ الْخُيَلَاءِ خُسِفَ بِهِ فَهُوَ يَتَجَلْجَلُ فِي الْأَرْضِ إِلَى يَوْمِ الْقِيَامَةِ", 8) == "مبتدأ"


def test_a_relative_after_a_noun_describes_the_noun_its_idafa_is_added_to():
    # Tasheel 3.10.1: the relative follows the مضاف the parser links it to (أرشيف), not the مضاف إليه nearest it (المكتبة); a name is known
    assert _role("إِنَّ فِي أَرْشِيفِ الْمَكْتَبَةِ الْوَطَنِيَّةِ الَّذِي أُسِّسَ قَبْلَ مِئَةٍ وَخَمْسِينَ عَامًا", 5) == "صفة"
    assert _role("الْحَمْدُ لِلَّهِ الَّذِي أَطْعَمَنَا وَسَقَانَا", 2) == "صفة"


def test_a_conditional_or_relative_noun_that_a_complete_verb_hangs_on_is_its_mubtada():
    assert _role("قَالَ رَسُولُ اللَّهِ: مَنْ لَمْ يُجْمِعِ الصِّيَامَ قَبْلَ الْفَجْرِ فَلَا صِيَامَ لَهُ", 3) == "مبتدأ"
    # a mubtada already before it makes it the khabar (خَيْرُكُمْ مَنْ تَعَلَّمَ), as a sentence that has none does not
    assert _role("خَيْرُكُمْ مَنْ تَعَلَّمَ الْقُرْآنَ وَعَلَّمَهُ", 1) == "خبر"


def test_a_damma_on_a_noun_the_parser_added_to_another_makes_it_no_mudaf_ilayh():
    # a مضاف إليه is never مرفوع: وَفِي كُلٍّ خَيْرٌ, سَتَكُونُ فِتَنٌ الْقَاعِدُ فِيهَا خَيْرٌ
    assert _role("سَتَكُونُ فِتَنٌ الْقَاعِدُ فِيهَا خَيْرٌ مِنَ الْقَائِمِ", 2) == "مبتدأ"


@needs_parser
@pytest.mark.parametrize("sentence", [
    "لَعَلِّي طَالِبٌ",  # the dictionary has only لَعَلَّنِي, so the short ي read as the name عَلِيّ
    "لَيْتِي طَالِبٌ",  # the same short ي on another sister
    "لَعَلَّكَ طَالِبٌ",  # nearest case: a pronoun the dictionary has
])
def test_a_sister_of_inna_with_its_pronoun_is_the_particle_and_its_ism(sentence: str):
    assert [w["role"] for w in iraab.analyze(sentence)["words"]] == ["حرف", "خبر إن"]
