"""A follower in a long sentence names the word it follows, as the card says: a بدل after إلا
the noun excepted from (out of its جار ومجرور), a صفة the noun it describes when the parser hung it
elsewhere, and a معطوف that carries its own توكيد stays a معطوف (Tasheel 3.8.7, 3.10)."""
import pytest

from tests.nahw_helpers import cards, needs_parser


def follows(sentence: str, word: str) -> tuple[str, str | None]:
    """The role on `word`'s card and the word it follows."""
    words = cards(sentence)
    card = next(c for c in words if c["word"] == word)
    at = card.get("follows")
    return card["role"], words[at]["word"] if isinstance(at, int) else None


@needs_parser
@pytest.mark.parametrize("sentence, word, role, on", [
    # the مستثنى منه is أحد, not the الضيوف its من adds to it, nor the verb
    ("مَا جَاءَ أَحَدٌ مِنَ الضُّيُوفِ إِلَّا زَيْدٌ", "زَيْدٌ", "بدل", "أَحَدٌ"),
    ("مَا رَأَيْتُ أَحَدًا مِنَ الطُّلَّابِ إِلَّا زَيْدًا", "زَيْدًا", "بدل", "أَحَدًا"),
    ("مَا جَاءَ أَحَدٌ إِلَّا زَيْدٌ", "زَيْدٌ", "بدل", "أَحَدٌ"),
    ("مَا مَرَرْتُ بِأَحَدٍ إِلَّا زَيْدٍ", "زَيْدٍ", "بدل", "بِأَحَدٍ"),
    # a describing word with ال after a known noun in its case is its صفة, not a second object
    ("أَطْعَمَ الْغَنِيُّ الْفَقِيرَ الْجَائِعَ خُبْزًا", "الْجَائِعَ", "صفة", "الْفَقِيرَ"),
    ("رَأَيْتُ زَيْدًا الْكَرِيمَ", "الْكَرِيمَ", "صفة", "زَيْدًا"),
    ("مَرَرْتُ بِأَحْمَدَ الْكَرِيمِ", "الْكَرِيمِ", "صفة", "بِأَحْمَدَ"),
    # a known word after the و's noun stresses it (جميعهم is known by its pronoun): no new sentence
    ("دَخَلَ الْمُدِيرُ وَالطُّلَّابُ جَمِيعُهُمْ", "وَالطُّلَّابُ", "معطوف", "الْمُدِيرُ"),
])
def test_a_follower_names_the_word_it_follows(sentence, word, role, on):
    assert follows(sentence, word) == (role, on)


@needs_parser
@pytest.mark.parametrize("sentence, roles", [
    ("مَا جَاءَ إِلَّا زَيْدٌ", ["حرف", "فعل", "حرف", "فاعل"]),  # no noun excepted from: a حصر
    ("مَا أَنْتَ إِلَّا بَشَرٌ", ["حرف", "مبتدأ", "حرف", "خبر"]),
    ("أَعْطَيْتُ الطَّالِبَ الْكِتَابَ", ["فعل", "مفعول به", "مفعول به"]),  # الكتاب describes nothing
    ("خَرَجَ زَيْدٌ وَاللَّهُ أَكْبَرُ", ["فعل", "فاعل", "مبتدأ", "خبر"]),  # an unknown khabar: a new sentence
    ("جَاءَ زَيْدٌ وَأَخُوهُ رَاكِبٌ", ["فعل", "فاعل", "مبتدأ", "خبر"]),  # أخوه is known by its pronoun
])
def test_the_rules_leave_what_they_do_not_reach(sentence, roles):
    assert [c["role"] for c in cards(sentence)] == roles
