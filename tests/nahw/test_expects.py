"""After a word that wants a verb (هل، لن، لم، a relative ...), a bare word that reads as a verb as well as a
noun is the verb; typed vowels that only a noun fits keep the noun (data/nahw_rules/expects.json)."""
from backend.scripts.nahw.score_iraab import routed
from tests.nahw_helpers import needs_parser

pytestmark = needs_parser


def roles(sentence: str) -> list[str]:
    return [card["role"] for card in routed(sentence, None)["words"]]


def test_a_bare_word_after_hal_is_the_verb_and_its_doer_follows():
    assert roles("هل نضج التين") == ["حرف", "فعل", "فاعل"]
    assert roles("لن نضج التين")[1] == "فعل"


def test_vowels_only_a_noun_fits_keep_the_noun_after_hal():
    assert roles("هل نُضْجُ التِّينِ مُبَكِّرٌ") == ["حرف", "مبتدأ", "مضاف إليه", "خبر"]


def test_a_noun_after_kayfa_stays_a_noun():
    assert roles("كيف حالك")[1] == "مبتدأ"
