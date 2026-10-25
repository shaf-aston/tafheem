"""A word written with ة is a name, never a verb: a name the dictionary lacks (حَفْصَةَ) is not
read off a verb's shape (فَعْلَلَ), since ة is the noun's feminine ending and no root letter."""
from tests.nahw_helpers import cards, needs_parser


@needs_parser
def test_a_name_the_dictionary_lacks_written_with_ta_marbuta_is_the_verbs_object():
    words = cards("طَلَّقَ حَفْصَةَ ثُمَّ رَاجَعَهَا")
    assert [(w["role"], w["case"]) for w in words[:2]] == [("فعل", "mabni"), ("مفعول به", "nasb")]
