"""The tarkeeb tree must group real ayahs correctly, and admit what it cannot.

Every case below runs on the real corpus, so a rule that only works on invented
tags fails here.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
import pytest

from backend.services import arabic_text, quran_corpus, tarkeeb

needs_corpus = pytest.mark.skipif(
    not quran_corpus.is_loaded(), reason="corpus.db not built"
)

TERMS = tarkeeb._rules()["terms"]


def ayah(surah: int, number: int) -> dict:
    return tarkeeb.tree_for(quran_corpus.tags_for_ayah(surah, number))


def spans(node: dict, at: int = 0) -> list[tuple[int, int, str]]:
    """Every unit in the tree as (first word, last word, what it is or does)."""
    if "word" in node:
        return [(node["word"], node["word"], node["role"])]
    found, start = [], at
    for child in node["children"]:
        found += spans(child, start)
        start = found[-1][1] + 1
    return found + [(found[0][0], found[-1][1], node.get("label") or node["role"])]


def named(tree: dict, key: str) -> list[tuple[int, int]]:
    return [(lo, hi) for lo, hi, name in spans(tree) if name == TERMS[key]["ar"]]


@needs_corpus
def test_adjectives_bind_to_the_noun_before_the_annexation():
    # بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ, the two names describe اللَّهِ, so they must
    # sit inside the annexation, not beside it.
    tree = ayah(1, 1)["tree"]
    assert named(tree, "murakkab_tawsifi") == [(1, 3)]
    assert named(tree, "murakkab_idafi") == [(0, 3)]


@needs_corpus
def test_a_name_is_not_taken_as_a_mudaf():
    # اَلْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ, لِلَّهِ رَبِّ has the shape of an annexation and
    # is not one. رَبِّ الْعَالَمِينَ is. The corpus cannot tell how the two relate.
    result = ayah(1, 2)
    assert named(result["tree"], "murakkab_idafi") == [(2, 3)]
    assert named(result["tree"], "mubtada") == [(0, 0)]
    assert named(result["tree"], "khabar") == [(1, 1)]


@needs_corpus
def test_what_the_rules_cannot_place_is_drawn_as_a_gap():
    result = ayah(1, 2)
    gaps = [node for node in result["tree"]["children"] if node.get("gap")]
    assert len(gaps) == 1
    assert gaps[0]["role"] == TERMS["unresolved"]["ar"]
    # Two of the four words placed, and the number says so rather than hiding it.
    assert result["coverage"] == 0.5


@needs_corpus
def test_a_preposition_takes_the_whole_annexation_after_it():
    # اِقْرَأْ بِاسْمِ رَبِّكَ, the glued بِ governs اسم رب, not اسم alone.
    tree = ayah(96, 1)["tree"]
    assert named(tree, "murakkab_idafi") == [(1, 2)]
    # ٱقْرَأْ, and خَلَقَ in the relative clause after it.
    assert named(tree, "fil") == [(0, 0), (4, 4)]


@needs_corpus
def test_a_join_inside_one_written_word_is_named():
    # رَبِّكَ is two pieces in one word: مضاف and مضاف إليه.
    word = ayah(96, 1)["tree"]["children"][1]["children"][1]
    assert [part["role"] for part in word["parts"]] == [
        TERMS["mudaf"]["ar"], TERMS["mudaf_ilayhi"]["ar"]
    ]


@needs_corpus
def test_a_definite_noun_and_a_predicate_are_not_read_as_a_description():
    # ذَٰلِكَ الْكِتَابُ, الْكِتَابُ is not a description of ذَٰلِكَ.
    tree = ayah(2, 2)["tree"]
    assert named(tree, "murakkab_tawsifi") == []


@needs_corpus
def test_every_word_appears_exactly_once():
    """A tree that dropped or repeated a word would be wrong however it looked."""
    for surah, number in ((1, 1), (1, 2), (1, 5), (2, 2), (2, 255), (96, 1), (112, 1)):
        result = ayah(surah, number)
        leaves = [lo for lo, hi, _ in spans(result["tree"]) if lo == hi]
        assert sorted(leaves) == list(range(len(result["words"])))


@needs_corpus
def test_a_pronoun_is_never_treated_as_an_ordinary_noun():
    # إِيَّاكَ نَعْبُدُ, the corpus tags إِيَّاكَ only as a pronoun, with no case, so
    # the rules must leave it open instead of inventing a role for it.
    tree = ayah(1, 5)["tree"]
    assert tree["children"][0]["role"] == TERMS["unresolved"]["ar"]
    assert tree["children"][2]["role"] == TERMS["unresolved"]["ar"]
    # Each verb opens its own clause, so both are named.
    assert named(tree, "fil") == [(1, 1), (3, 3)]


@needs_corpus
def test_a_standalone_connective_gets_its_own_role_not_a_gap():
    # هُوَ ... ثُمَّ ٱسْتَوَىٰ, ثُمَّ (word 8) joins two clauses and governs
    # nothing. It used to fall through to the unresolved gap; it must not.
    tree = ayah(2, 29)["tree"]
    thumma = next(n for n in tree["children"] if n.get("word") == 8)
    assert thumma["role"] == TERMS["harf_atf"]["ar"]
    assert thumma["tone"] == TERMS["harf_atf"]["tone"] == "ghair_aamil"
    assert thumma.get("ghair_aamil") is True
    assert not thumma.get("gap")


@needs_corpus
def test_a_glued_atf_prefix_is_named_as_its_own_piece():
    # فَسَوَّىٰهُنَّ (word 12), the فَ is a separate join from سَوَّىٰ, so it is
    # named as its own piece with its own text, not swallowed into the word.
    word = next(n for n in ayah(2, 29)["tree"]["children"] if n.get("word") == 12)
    assert word["parts"][0]["role"] == TERMS["harf_atf"]["ar"]
    assert word["parts"][0]["ghair_aamil"] is True
    assert word["prefix_arabic"] == "فَ"


@needs_corpus
def test_a_resumptive_faa_is_named_instead_of_dropped():
    # فَبِمَا رَحْمَةٍ, the REM-tagged فَ (a فاء استئنافية) used to go entirely
    # unread because only CONJ was checked. It must be named, not silently lost.
    word = ayah(3, 159)["tree"]["children"][0]
    assert word["parts"][0]["role"] == TERMS["harf_istinaf"]["ar"]
    assert word["parts"][0]["ghair_aamil"] is True
    assert word["prefix_arabic"] == "فَ"


# ── Governing words ─────────────────────────────────────────────────────────

def roles(result: dict) -> dict[int, list[str]]:
    """Every role on a unit, filed under the unit's first word, pieces included."""
    found: dict[int, list[str]] = {}

    def walk(node: dict) -> list[int]:
        words = [node["word"]] if "word" in node else sum((walk(c) for c in node["children"]), [])
        if node.get("role"):
            found.setdefault(min(words), []).append(node["role"])
        found.setdefault(min(words), []).extend(p["role"] for p in node.get("parts", ()))
        return words

    walk(result["tree"])
    return found


def governed(relation: str) -> str:
    return tarkeeb.relation_wording(relation)[0]


def typed(*words: tuple[str, str, str]) -> list[dict]:
    """A typed sentence as the rules read it: (text, part of speech, tags), the
    definite article split off as the corpus splits it. No harakat, no case."""
    out = []
    for text, pos, features in words:
        segments = [{"arabic": text, "pos": pos, "features": features}]
        if text.startswith("ال"):
            segments.insert(0, {"arabic": "ال", "pos": "P", "features": "DET|PREF"})
        out.append({"arabic": text, "pos": pos, "features": features, "root": "",
                    "lemma": text, "segments": segments})
    return out


@needs_corpus
def test_inna_takes_its_ism_and_its_khabar():
    # إِنَّ ٱلْإِنسَٰنَ لَفِى خُسْرٍ, the ism is mansoob and the khabar a jar-majroor.
    found = roles(ayah(103, 2))
    assert found[0] == [TERMS["harf_nasikh"]["ar"]]
    assert found[1] == [governed("اسم إن")]
    assert governed("خبر إن") in found[2]


@needs_corpus
def test_inna_with_a_noun_khabar():
    # إِنَّ ٱللَّهَ غَفُورٌ رَّحِيمٌ, the khabar is the marfoo' noun after the ism.
    words = [w["arabic"] for w in quran_corpus.tags_for_ayah(2, 173)]
    at = len(words) - 4
    assert arabic_text.strip_diacritics(words[at]) == "إن"
    found = roles(ayah(2, 173))
    assert found[at + 1] == [governed("اسم إن")]
    assert governed("خبر إن") in found[at + 2]


@needs_corpus
def test_kana_takes_its_ism_and_its_khabar():
    # وَكَانَ ٱللَّهُ عَلِيمًا حَكِيمًا, the reverse of inna: ism marfoo', khabar mansoob.
    found = roles(ayah(4, 17))
    assert TERMS["fil_naqis"]["ar"] in found[16]
    assert found[17] == [governed("اسم كان")]
    assert governed("خبر كان") in found[18]


@needs_corpus
def test_a_governing_verbs_own_ending_is_its_ism():
    # كُنتُمْ فِى رَيْبٍ, the تُمْ is the ism, so no word after it is.
    found = roles(ayah(2, 23))
    assert found[1] == [TERMS["fil_naqis"]["ar"],
                        TERMS["fil_naqis"]["ar"], governed("اسم كان")]
    assert governed("خبر كان") in found[2]


@needs_corpus
def test_innama_governs_nothing():
    # قَالُوٓا۟ إِنَّمَا نَحْنُ مُصْلِحُونَ, the attached ما stops إِنَّ governing.
    found = roles(ayah(2, 11))
    named_roles = {role for listed in found.values() for role in listed}
    assert TERMS["harf_nasikh"]["ar"] not in named_roles
    assert governed("اسم إن") not in named_roles


@needs_corpus
def test_a_passive_verbs_subject_is_its_naib_fail():
    # فَقُطِعَ دَابِرُ ٱلْقَوْمِ
    assert TERMS["naib_fail"]["ar"] in roles(ayah(6, 45))[1]


@needs_corpus
def test_a_verb_carrying_its_subject_takes_the_next_noun_as_object():
    # يُخَٰدِعُونَ ٱللَّهَ, the ونَ is the subject; ٱللَّهَ is the object, not a فاعل.
    found = roles(ayah(2, 9))
    assert TERMS["fail"]["ar"] in found[0]
    assert found[1] == [TERMS["mafool"]["ar"]]


def test_typed_arabic_without_harakat_is_read_by_place():
    # كان الجو جميلا, no case on any word, so the ism and khabar come from order.
    found = roles(tarkeeb.tree_for(typed(
        ("كان", "V", "PERF|FAM:كَان|3MS"), ("الجو", "N", "M"), ("جميلا", "N", "M"),
    )))
    assert found == {0: [TERMS["fil_naqis"]["ar"]], 1: [governed("اسم كان")],
                     2: [governed("خبر كان")]}


def test_typed_harakat_outrank_place():
    # كان الجوَّ جميلٌ, the harakat say the khabar comes first; place does not overrule them.
    found = roles(tarkeeb.tree_for(typed(
        ("كان", "V", "PERF|FAM:كَان|3MS"), ("الجوَّ", "N", "M|ACC"), ("جميلٌ", "N", "M|NOM|INDEF"),
    )))
    assert found[1] == [governed("خبر كان")]
    assert found[2] == [governed("اسم كان")]


def test_a_relative_after_a_noun_describes_it_and_is_not_the_khabar():
    noun = roles(tarkeeb.tree_for(typed(("الكتاب", "N", "M"), ("الذي", "N", "REL|MS"))))
    assert noun[0] == [TERMS["mubtada"]["ar"]]
    assert TERMS["khabar"]["ar"] not in noun[1]
    # هو الذي, after a pronoun the relative is the khabar.
    pronoun = roles(tarkeeb.tree_for(typed(("هو", "N", "PRON|3MS"), ("الذي", "N", "REL|MS"))))
    assert pronoun == {0: [TERMS["mubtada"]["ar"]], 1: [TERMS["khabar"]["ar"]]}


@needs_corpus
def test_a_my_ending_hides_the_case_so_place_decides():
    # قُلْ إِنَّ رَبِّى يَقْذِفُ, the corpus tags رَبِّى nominative; after إِنَّ it is the ism.
    found = roles(ayah(34, 48))
    assert found[2][0] == governed("اسم إن")
    assert found[3] == [governed("خبر إن")]


@needs_corpus
def test_a_khabar_verb_with_nothing_pointing_back_has_a_hidden_subject():
    # إِنَّ رَبِّى يَقْذِفُ بِٱلْحَقِّ عَلَّٰمُ ٱلْغُيُوبِ, the subject is هُوَ, not عَلَّٰمُ.
    named_roles = {role for listed in roles(ayah(34, 48)).values() for role in listed}
    assert TERMS["fail"]["ar"] not in named_roles


@needs_corpus
def test_a_khabar_verb_takes_a_subject_when_the_clause_points_back():
    # فَأُو۟لَٰٓئِكَ يَتُوبُ ٱللَّهُ عَلَيْهِمْ, the هِمْ links the clause to أُو۟لَٰٓئِكَ.
    found = roles(ayah(4, 17))
    assert found[13] == [TERMS["khabar"]["ar"]]
    assert found[14] == [TERMS["fail"]["ar"]]
