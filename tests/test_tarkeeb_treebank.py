"""The recorded tarkeeb, and the checks that decide what is allowed into it.

The importer's job is to turn arrows into brackets, and to refuse when it cannot.
Both halves are tested: the turning, and the refusing.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
import pytest

from backend.scripts import build_tarkeeb
from backend.services import arabic_text, nahw_book, tarkeeb_store

SETTINGS = nahw_book.tarkeeb_rules()["treebank"]
TONE = lambda relation: "default"  # noqa: E731, colour is not what these tests are about

needs_database = pytest.mark.skipif(
    not tarkeeb_store.is_built(), reason="tarkeeb.db not built"
)


def word(text, relation=None, head=None, pos="N", elided=False):
    return {"text": text, "elided": elided, "relation": relation, "head": head,
            "pos": pos, "constituent": "-"}


# ── Arrows into brackets ─────────────────────────────────────────────────────

def test_a_word_and_what_hangs_off_it_becomes_one_bracket():
    # جَلَسَ فِى ٱلْبَيْتِ, البيت hangs off فى, so the two make one unit under the verb.
    words = [word("جَلَسَ", "root", 0, pos="V"), word("فِى", "متعلق", 0, pos="P"),
             word("ٱلْبَيْتِ", "مجرور", 1)]
    tree = build_tarkeeb._tree_of(words, SETTINGS, TONE)
    verb, phrase = tree["children"]
    assert verb["word"] == 0
    assert [child["word"] for child in phrase["children"]] == [1, 2]


def test_crossing_arrows_are_refused_because_no_bracket_can_hold_them():
    # Word 0 governs word 2, reaching over word 1, which belongs to something
    # else. A bracket round 0 and 2 would have to leave a hole in the middle.
    words = [word("أ", "root", 0), word("ب", "فاعل", 3), word("ج", "مفعول به", 0),
             word("د", "root", 3)]
    assert build_tarkeeb._tree_of(words, SETTINGS, TONE) is None


def test_a_sentence_resting_on_two_words_draws_as_two_branches():
    words = [word("أ", "root", 0, pos="V"), word("ب", "root", 1, pos="V")]
    tree = build_tarkeeb._tree_of(words, SETTINGS, TONE)
    assert len(tree["children"]) == 2


def test_the_root_marker_never_reaches_the_reader():
    words = [word("قَالَ", "root", 0, pos="V"), word("زَيْدٌ", "فاعل", 0)]
    tree = build_tarkeeb._tree_of(words, SETTINGS, TONE)
    printed = {tree.get("role"), tree.get("label")}
    printed |= {child.get("role") for child in tree["children"]}
    assert SETTINGS["root"] not in printed
    assert tree["label"] == nahw_book.term("jumlah_filiyyah")["ar"]
    assert tree["children"][0]["role"] == nahw_book.term("fil")["ar"]


def test_a_nominal_sentence_names_its_opening_word_the_mubtada():
    words = [word("زَيْدٌ", "root", 0), word("قَائِمٌ", "خبر", 0)]
    tree = build_tarkeeb._tree_of(words, SETTINGS, TONE)
    assert tree["children"][0]["role"] == nahw_book.term("mubtada")["ar"]


# ── Particles: what the treebank's arrows say about them ─────────────────────

def row(token, word_id, text, pos, pos_ar, relation, ref, constituent="-", segment="STEM"):
    """One treebank row, the columns the importer reads."""
    return {"token_id": str(token), "word_id": str(word_id), "uthmani_token": text,
            "pos": pos, "pos_ar": pos_ar, "rel_label_ar": relation, "ref_token_id": str(ref),
            "constituent_label": constituent, "features": f"{segment}|POS:{pos}"}


# أَفَلَا يَعْلَمُ إِذَا بُعْثِرَ مَا فِى ٱلْقُبُورِ (100:9), as the treebank records it:
# the sentence rests on the question أَ, يَعْلَمُ hangs off لَا with نفي on its arrow.
AL_ADIYAT_9 = [
    row(0, 1, "أَ", "INTG", "حرف استفهام", "root", 0, segment="PREFIX"),
    row(1, 1, "فَ", "SUP", "حرف زائد", "زائد", 2, segment="PREFIX"),
    row(2, 1, "لَا", "NEG", "حرف نفي", "استفهام", 0),
    row(3, 2, "يَعْلَمُ", "V", "فعل", "نفي", 2),
    row(4, 0, "(هُوَ)", "PRON", "ضمير", "فاعل", 3),
    row(5, 3, "إِذَا", "T", "ظرف زمان", "مفعول به", 3, constituent="CS"),
    row(6, 4, "بُعْثِرَ", "V", "فعل", "شرط", 5, constituent="VS"),
    row(7, 5, "مَا", "REL", "اسم موصول", "نائب فاعل", 6),
    row(8, 0, "(*)", "N", "اسم", "صلة", 7),
    row(9, 6, "فِى", "P", "حرف جر", "متعلق", 8, constituent="PP"),
    row(10, 7, "ٱلْ", "DET", "ال التعريف", "NonRel", 10, segment="PREFIX"),
    row(11, 7, "قُبُورِ", "N", "اسم", "مجرور", 9),
]


def drawn(rows):
    words, _ = build_tarkeeb._words_of(rows, SETTINGS)
    tree = build_tarkeeb._tree_of(words, SETTINGS, nahw_book.relation_tone)
    columns = {}

    def walk(node):
        if node.get("children"):
            for child in node["children"]:
                walk(child)
        else:
            columns[words[node["word"]]["text"]] = node
    walk(tree)
    return tree, columns


def term(key):
    return nahw_book.term(key)["ar"]


def test_a_particle_is_named_for_what_it_is_never_as_a_mubtada():
    tree, columns = drawn(AL_ADIYAT_9)
    afala = columns["أَفَلَا"]
    assert afala["role"] == SETTINGS["particle_kinds"]["حرف استفهام"]
    assert [part["role"] for part in afala["parts"]] == [
        SETTINGS["particle_kinds"][kind] for kind in ("حرف استفهام", "حرف زائد", "حرف نفي")]
    assert term("mubtada") not in {afala["role"], tree["role"]}


def test_a_sentence_opening_on_particles_is_named_by_the_verb_under_them():
    tree, _ = drawn(AL_ADIYAT_9)
    assert tree["label"] == term("jumlah_filiyyah")


def test_an_arrow_naming_its_particle_heads_meaning_is_not_the_verbs_job():
    # نفي is what لَا does; يَعْلَمُ is a verb
    _, columns = drawn(AL_ADIYAT_9)
    assert columns["يَعْلَمُ"]["role"] == term("fil")


def test_a_job_the_particles_name_does_not_say_stays_with_the_governed_word():
    _, columns = drawn(AL_ADIYAT_9)
    assert columns["ٱلْقُبُورِ"]["role"] == SETTINGS["relation_terms"]["مجرور"]
    assert columns["مَا"]["role"] == SETTINGS["relation_terms"]["نائب فاعل"]


def test_a_word_heading_a_unit_says_what_it_is_and_the_unit_carries_the_job():
    tree, columns = drawn(AL_ADIYAT_9)
    assert columns["إِذَا"]["role"] == term("zarf_zaman")
    assert columns["بُعْثِرَ"]["role"] == term("fil")
    assert columns["فِى"]["role"] == term("jarr")

    def units(node, found):
        if node.get("children"):
            found.append(node.get("role"))
            for child in node["children"]:
                units(child, found)
        return found
    jobs = units(tree, [])
    for job in ("مفعول به", "شرط", "متعلق"):
        assert SETTINGS["relation_terms"][job] in jobs


def test_ina_is_spelled_the_same_as_the_rules_spell_it():
    assert build_tarkeeb._particle("حرف نصب", SETTINGS)["ar"] == term("harf_nasikh")


# ── The gates ────────────────────────────────────────────────────────────────

def test_a_tree_that_misses_a_word_fails_the_coverage_gate():
    words = [word("أ"), word("ب")]
    tree = {"children": [{"word": 0}]}
    assert build_tarkeeb.gates(words, tree, ["أ", "ب"], set()) == "coverage"


def test_a_relation_the_treebank_does_not_document_fails_the_vocabulary_gate():
    words = [word("أ", "لَيْسَ مِنَ ٱلْمُصْطَلَحَاتِ", 0)]
    tree = {"word": 0}
    assert build_tarkeeb.gates(words, tree, ["أ"], {"فاعل"}) == "vocabulary"


def test_a_different_ayah_fails_the_anchoring_gate():
    words = [word("زَيْدٌ", "root", 0)]
    tree = {"word": 0}
    assert build_tarkeeb.gates(words, tree, ["عَمْرٌو"], {"root"}) == "anchoring"


def test_the_same_ayah_spelled_two_ways_passes_anchoring():
    # The treebank writes الله, the corpus writes ٱللَّهِ. Same word.
    words = [word("الله", "root", 0)]
    tree = {"word": 0}
    assert build_tarkeeb.gates(words, tree, ["ٱللَّهِ"], {"root"}) is None


def test_an_elided_word_takes_a_column_without_breaking_anchoring():
    words = [word("زَيْدٌ", "root", 0), word("—", "خبر", 0, elided=True)]
    tree = {"children": [{"word": 0}, {"word": 1}]}
    assert build_tarkeeb.gates(words, tree, ["زَيْدٌ"], {"root", "خبر"}) is None


def test_folding_treats_quranic_spelling_as_the_same_word():
    assert arabic_text.bare_letters("ورسُوله") == arabic_text.bare_letters("وَرَسُولِهِۦٓ")
    assert arabic_text.bare_letters("زيد") != arabic_text.bare_letters("عمرو")


# ── What was actually built ──────────────────────────────────────────────────

@needs_database
def test_the_recorded_tarkeeb_answers_for_al_fatihah():
    result = tarkeeb_store.for_ayah(1, 2)
    assert result is not None
    # The join the rules could only leave open, رَبِّ standing in for اللَّهِ.
    roles = []

    def walk(node):
        if node.get("role"):
            roles.append(node["role"])
        for child in node.get("children", ()):
            walk(child)

    walk(result["tree"])
    assert SETTINGS["relation_terms"]["بدل"] in roles


@needs_database
def test_an_ayah_that_was_refused_is_absent_rather_than_wrong():
    present = sum(1 for surah in range(1, 6) for ayah in range(1, 20)
                  if tarkeeb_store.for_ayah(surah, ayah) is not None)
    assert present > 0
    assert tarkeeb_store.for_ayah(999, 1) is None


# ── Wording ──────────────────────────────────────────────────────────────────

def test_a_name_the_app_knows_is_spelled_the_app_way():
    assert nahw_book.relation_wording("فاعل") == (SETTINGS["relation_terms"]["فاعل"], False)


def test_khabar_plus_its_governing_word_is_spelled_out_when_both_are_known():
    said, raw = nahw_book.relation_wording("خبر كان")
    assert said == "خَبَرُ كَانَ" and raw is False


def test_a_conjugated_governor_keeps_the_treebanks_spelling_and_says_so():
    # The frame is the app's; يكون is left exactly as the treebank wrote it.
    said, raw = nahw_book.relation_wording("خبر يكون")
    assert said == "خَبَرُ يكون" and raw is True


def test_a_name_nobody_has_checked_is_used_but_not_passed_off_as_checked():
    said, raw = nahw_book.relation_wording("شيء غريب")
    assert said == "شيء غريب" and raw is True


@needs_database
def test_the_recorded_tarkeeb_marks_every_unchecked_wording():
    """Nothing may print the treebank's raw wording without being flagged as such."""
    checked = set(SETTINGS["relation_terms"].values()) | {""}
    checked |= {build_tarkeeb._particle(kind, SETTINGS)["ar"] for kind in SETTINGS["particle_kinds"]}
    frames = tuple(SETTINGS["relation_frames"].values())
    unflagged = []

    def walk(node):
        role = node.get("role") or ""
        known = role in checked or role.startswith(frames) or not role
        if not known and not node.get("raw_wording") and not node.get("ghair_aamil"):
            unflagged.append(role)
        for child in node.get("children", ()):
            walk(child)

    for surah, ayah in [(2, 2), (2, 29), (1, 5), (3, 7), (18, 10)]:
        if (found := tarkeeb_store.for_ayah(surah, ayah)):
            walk(found["tree"])
    assert not set(unflagged) - {
        nahw_book.tarkeeb_rules()["terms"][key]["ar"]
        for key in nahw_book.tarkeeb_rules()["terms"]
    }
