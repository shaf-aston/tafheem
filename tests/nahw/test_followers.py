"""followers.chain_first: the first word of a chain of معطوفات, for any kind of word key."""
from backend.services.nahw.book import named_roles
from backend.services.nahw.syntax.followers import FOLLOWERS, chain_first, followed

NAMED = named_roles()


def test_a_chain_climbs_to_its_first_word():
    # وَإِقَامِ الصَّلَاةِ وَإِيتَاءِ الزَّكَاةِ وَالْحَجِّ: each معطوف joined on the one before
    joined = {3: 2, 2: 1}
    assert chain_first(3, joined.get) == 1


def test_a_word_joined_on_nothing_is_its_own_first():
    assert chain_first(5, {}.get) == 5


def test_a_chain_that_loops_back_stops_instead_of_spinning():
    assert chain_first(1, {1: 2, 2: 1}.get) == 2
    assert chain_first(4, {4: 4}.get) == 4


def test_the_four_followers_are_named():
    assert set(FOLLOWERS) == {"معطوف", "توكيد", "بدل", "صفة"}


def _w(i, typed, pos, head, **kw):
    return {"id": i, "form": typed, "typed": typed, "base": typed, "pos": pos, "lemma": typed, "head": head, **kw}


SIFAH, BADAL, ATF = NAMED.sifah, NAMED.badal, NAMED.matoof
TAWKEED = next(r for r in FOLLOWERS if r not in (SIFAH, BADAL, ATF))


def test_a_badal_hung_on_the_verb_follows_the_noun_before_it():
    # أَعْجَبَنِي الْمُعَلِّمُ عِلْمُهُ: a تابع follows a noun, never the verb the parser hung it on
    words = [_w(1, "أَعْجَبَ", "VRB", 0), _w(2, "الْمُعَلِّمُ", "NOM", 1, stt="d"), _w(3, "عِلْمُ", "NOM", 1, stt="c")]
    named = [NAMED.fil, NAMED.fail, BADAL]
    assert followed(words[2], words, words, named) == 1
    assert followed(words[2], words, words) == 0  # the parser's link, when no roles are given


def test_a_pronoun_tawkeed_stays_on_the_verb_whose_doer_it_repeats():
    # أَكْرَمْتُ زَيْدًا أَنَا: أنا repeats the تاء the verb holds, not the noun straight before it
    words = [_w(1, "أَكْرَمْتُ", "VRB", 0), _w(2, "زَيْدًا", "PROP", 1), _w(3, "أَنَا", "NOM", 1, pos_camel="pron")]
    named = [NAMED.fil, NAMED.mafool_bih, TAWKEED]
    assert followed(words[2], words, words, named) == 0
    # a noun there that is no pronoun does follow that noun (أعجبني المعلمُ علمُه)
    words[2] = _w(3, "نَفْسُهُ", "NOM", 1, stt="c")
    assert followed(words[2], words, words, named) == 1


def test_a_second_sifah_or_a_tawkeed_follows_the_noun_not_the_sifah_before_it():
    # لِعِبَادِهِ الْمُؤْمِنِينَ التَّائِبِينَ، الطَّالِبَانِ الْمُجْتَهِدَانِ كِلَاهُمَا
    words = [_w(1, "عِبَادِ", "NOM", 0), _w(2, "الْمُؤْمِنِينَ", "NOM", 1, stt="d"), _w(3, "التَّائِبِينَ", "NOM", 2, stt="d")]
    for role in (SIFAH, TAWKEED):
        assert followed(words[2], words, words, [NAMED.majroor, SIFAH, role]) == 0


def test_a_sifah_of_a_mudaf_follows_the_mudaf_whose_case_it_wears():
    # مَدْرَسَةُ الْبَلَدِ الْكَبِيرَةُ: raf' like مدرسة, not jarr like البلد
    words = [_w(1, "مَدْرَسَةُ", "NOM", 0, stt="c"), _w(2, "الْبَلَدِ", "NOM", 1, stt="d"), _w(3, "الْكَبِيرَةُ", "NOM", 2, stt="d")]
    assert followed(words[2], words, words, [NAMED.mubtada, NAMED.mudaf_ilayh, SIFAH]) == 0
    # الْبَلَدِ الْكَبِيرِ: jarr like البلد, so it describes البلد
    words[2] = _w(3, "الْكَبِيرِ", "NOM", 2, stt="d")
    assert followed(words[2], words, words, [NAMED.mubtada, NAMED.mudaf_ilayh, SIFAH]) == 1


def test_the_noun_a_pointer_points_at_is_itself_described():
    # هَذَا الْبُسْتَانُ الْجَمِيلُ: البستان (named صفة of هذا) is the noun الجميل describes
    words = [_w(1, "هَذَا", "NOM", 0, pos_camel="pron_dem"), _w(2, "الْبُسْتَانُ", "NOM", 1, stt="d"),
             _w(3, "الْجَمِيلُ", "NOM", 2, stt="d")]
    assert followed(words[2], words, words, [NAMED.mubtada, SIFAH, SIFAH]) == 1


def test_a_matoof_follows_across_its_waw_as_linked():
    words = [_w(1, "زَيْدٌ", "PROP", 0), _w(2, "وَ", "PRT", 1), _w(3, "عَمْرٌو", "PROP", 2)]
    bases = [words[0], words[2]]
    assert followed(words[2], bases, words, [NAMED.fail, ATF]) == 0
