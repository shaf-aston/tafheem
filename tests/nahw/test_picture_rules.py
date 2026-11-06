"""What the drawn picture (the tree the page shows) says for a sentence, per rule.

Run: python -m pytest tests/nahw/test_picture_rules.py
"""
from __future__ import annotations

import pytest
from backend.services.nahw import iraab
from backend.services.sarf import morphology
from backend.services.nahw import syntax
from backend.services.text.arabic_text import words
from backend.services.nahw.book import term_ar
from tests.nahw_helpers import analyze, NADA, needs_parser, tree_roles, _ATTENTION, _read

pytestmark = needs_parser


def _syntax_read(sentence: str) -> dict:
    return syntax.read(sentence, morphology.pick(words(sentence), syntax.disambiguator()))


@pytest.mark.parametrize("sentence, term", [
    ("يَا عَبْدَ اللهِ", "jumlah_nidaiyyah"),
    ("الطُّلَّابُ يَدْرُسُونَ فِي المَكْتَبَةِ", "jumlah_ismiyyah"),  # a مبتدأ before the verb
    ("هَذَا البَيْتُ كَبِيرٌ", "jumlah_ismiyyah"),
    ("قُمْ يَا وَلَدُ", "jumlah_filiyyah"),  # nearest case: a command before the call
    ("إِنْ كُنْتَ تُحِبُّ أَنْ تُطَوَّقَ طَوْقًا مِنْ نَارٍ فَاقْبَلْهَا", "jumlah_shartiyyah"),
    ("إِنْ تَدْرُسْ تَنْجَحْ", "jumlah_shartiyyah"),
    ("مَتَى سَافَرَ الرَّجُلُ", "jumlah_istifhamiyyah")])  # a question, in the picture and above it
def test_summary_and_tree_name_the_sentence_alike(sentence: str, term: str):
    answer = _read(sentence)
    assert (answer["summary"], _syntax_read(sentence)["tree"]["tree"]["label"]) == (term_ar(term), term_ar(term))


def _picture_roles(node: dict) -> list:
    return [node.get("role"), node.get("detail"), *(r for kid in node.get("children", []) + node.get("parts", [])
                                                     for r in _picture_roles(kid))]


def test_an_action_after_illa_is_a_munqati_excepted_and_its_hidden_doer_is_said_either_way():
    shown = _picture_roles(_syntax_read("الصَّلَوَاتِ الْخَمْسَ إِلَّا أَنْ تَطَّوَّعَ شَيْئًا")["tree"]["tree"])
    assert "مستثنى منقطع" in shown and "ضمير مستتر تقديره أنتَ أو هي" in shown


def test_the_same_masdar_with_no_illa_stays_an_object():
    shown = _picture_roles(_syntax_read("أُرِيدُ أَنْ تَطَّوَّعَ")["tree"]["tree"])
    assert "مفعول به" in shown and "مستثنى منقطع" not in shown


def test_the_summary_is_the_pictures_own_label_never_a_second_guess():
    # a hadith whose word the parser misnamed اسم إن once printed "· إنّ" with no إنّ in it
    answer = _read("الظُّهْرَ وَالْعَصْرَ جَمِيعًا بِالْمَدِينَةِ فِي غَيْرِ خَوْفٍ وَلاَ سَفَرٍ")
    assert answer["summary"] == answer["tree"]["tree"]["label"] and "إنّ" not in answer["summary"]


def test_a_relative_and_its_silah_are_one_unit():
    """جاء الذي نجح: the الذي unit does the فاعل's job, made of the relative and its صلة."""
    doer = _syntax_read("جَاءَ الَّذِي نَجَحَ")["tree"]["tree"]["children"][1]
    inside = [(kid.get("role"), kid.get("label")) for kid in doer["children"]]
    assert (doer["role"], doer["label"], inside) == (
        "فاعل", term_ar("mawsool_silah"), [("اسم موصول", None), ("صلة", term_ar("jumlah_filiyyah"))])


def test_the_glossary_explains_every_term_the_page_prints():
    """Every role a card can carry, every tarkeeb term and every label in the book's worked
    examples is in grammar.json, as an entry or named in one's meaning, so the glossary is never short."""
    import json
    from pathlib import Path
    from backend.services.text.arabic_text import strip_diacritics
    from backend.services.nahw.book import role_table
    from backend.services.nahw.syntax.naming import ROLES
    root = Path(__file__).parent.parent.parent
    grammar = json.loads((root / "frontend/src/config/grammar.json").read_text(encoding="utf-8"))
    tarkeeb = json.loads((root / "backend/data/nahw_rules/tarkeeb.json").read_text(encoding="utf-8"))["terms"]
    entries = [*grammar["types"].values(), *grammar["cases"].values(),
               *(t for s in grammar["sections"] for t in s.get("terms", []))]
    names = {t["arabic"] for t in entries}
    meanings = " ".join(t["meaning"] for t in entries)

    def labels(node):
        yield from (node[k] for k in ("role", "label") if node.get(k))
        for child in node.get("children", []) + node.get("parts", []):
            yield from labels(child)

    book = root / "backend/data/tarkeeb/examples"
    worked = {strip_diacritics(label) for f in book.glob("*.json")
              for e in json.loads(f.read_text(encoding="utf-8"))["examples"] for label in labels(e["tree"])}
    printed = set(role_table()) | set(ROLES) | worked | {
        strip_diacritics(t["ar"]) for k, t in tarkeeb.items() if k != "unresolved"}
    assert sorted(label for label in printed - names if label not in meanings) == []


def _shape(node: dict) -> tuple:
    """A picture as the book draws it: each unit's label and job, each leaf's role."""
    from backend.services.text.arabic_text import strip_diacritics
    if node.get("word") is not None:
        return (strip_diacritics(node["role"]),)
    return (strip_diacritics(node.get("label") or ""), strip_diacritics(node.get("role") or ""),
            *(_shape(kid) for kid in node["children"]))


def test_the_wonder_form_is_drawn_as_the_books_own_example():
    """ما أحسن زيدًا (Tasheel 1.4.2 p8): ما the مبتدأ, the verb's clause its khabar, the verb with its hidden doer."""
    import json
    from backend.services.nahw.book import RULES
    book = next(e for e in json.loads((RULES.parent / "tarkeeb" / "examples" / "tasheel-al-nahw.json")
                                      .read_text(encoding="utf-8"))["examples"] if e["id"] == "1.4.2-taajjub")
    ours = _syntax_read(book["sentence"])
    assert _shape(ours["tree"]["tree"]) == _shape(book["tree"])
    assert "ضمير مستتر وجوبًا تقديره هو يعود على ما" in _picture_roles(ours["tree"]["tree"])
    card = _read(book["sentence"])["words"][1]
    assert card["role"] == "فعل" and "فعل ماضٍ جامد للتعجب مبني على الفتح" in card["reason"]


@pytest.mark.parametrize("sentence, negations", [
    ("مَا أَنْتَ إِلَّا بَشَرٌ", 1),
    ("قَالُوا مَا أَنْتُمْ إِلَّا بَشَرٌ", 1),  # quoted speech: a verb of saying does not take the ما as its object
    ("ما قلت لهم إلا ما أمرتني به", 1),  # the first ما negates, the second is the relative
    ("لَا يَعْلَمُ مَا فِي الْغَيْبِ إِلَّا اللَّهُ", 0),  # the verb takes the ما as its object
    ("قَرَأْتُ مَا كَتَبَ الطُّلَّابُ إِلَّا زَيْدًا", 0),
])
def test_only_a_ma_that_opens_its_clause_is_the_negation_before_illa(sentence: str, negations: int):
    shown = _picture_roles(_syntax_read(sentence)["tree"]["tree"])
    assert shown.count("ما النافية") == negations


def test_a_relative_before_a_zarf_and_its_verb_is_no_question():
    words = iraab.analyze("مَا عِنْدَكُمْ يَنْفَدُ")["words"]
    assert words[0]["role"] == "مبتدأ" and words[-1]["role"] == "فعل" and "اسْتِفْهَامِيَّةٌ" not in _sentence_label("مَا عِنْدَكُمْ يَنْفَدُ")


def _sentence_label(sentence: str) -> str:
    return _syntax_read(sentence)["tree"]["tree"].get("label") or ""


@pytest.mark.parametrize("sentence", ["هَلْ أَنْتَ تَكْتُبُ", "ما أنت إلا بشر", "هَلِ الْوَلَدُ نَائِمٌ", "يَا أَخِي مَا اسْمُكَ",
                                      "مَنْ أَنْتَ فِي هَذِهِ الْمَدِينَةِ"])
def test_the_picture_keeps_the_order_the_words_were_typed(sentence: str):

    def leaves(node: dict) -> list[int]:
        return ([node["word"]] if node.get("word") is not None else []) + [i for kid in node.get("children", []) for i in leaves(kid)]
    order = leaves(_syntax_read(sentence)["tree"]["tree"])
    assert order == sorted(order)


@pytest.mark.parametrize("sentence, name", [
    ("مَا هَذَا بَشَرًا", "ما الحجازية"),  # a particle that works like ليس is no فعل ناقص
    ("كَانَ زَيْدٌ قَائِمًا", "فعل ناقص"),
])
def test_the_picture_names_the_governor_of_kana(sentence: str, name: str):

    def roles(node: dict) -> list[str]:
        return [node.get("role")] + [r for kid in node.get("children", []) for r in roles(kid)]
    assert name in roles(_syntax_read(sentence)["tree"]["tree"])


@pytest.mark.parametrize("sentence, doer", [
    ("أَنْتَ تَكْتُبُ", "ضمير مستتر تقديره أنتَ"),  # the khabar's pronoun goes back to its mubtada
    ("هِيَ تَكْتُبُ", "ضمير مستتر تقديره هي"),
    ("أَنْتِ تَكْتُبِينَ", "ضمير متصل (أنتِ)"),  # the ياء is the doer, not a hidden أنتَ أو هي
    ("تَكْتُبِينَ", "ضمير متصل (أنتِ)"),
    ("تَكْتُبُ", "ضمير مستتر تقديره أنتَ أو هي"),  # nothing settles it
])
def test_a_detached_pronoun_is_the_mubtada_and_settles_the_verbs_doer(sentence: str, doer: str):
    shown = _picture_roles(_syntax_read(sentence)["tree"]["tree"])
    assert doer in shown
    if sentence.startswith(("أَنْتَ", "هِيَ", "أَنْتِ")):
        assert [w["role"] for w in iraab.analyze(sentence)["words"]][0] == "مبتدأ" and "خبر" in shown


@pytest.mark.parametrize("sentence, particle, verb", [
    ("وَلَا تَأْكُلُوهَا", "لا الناهية", "فعل مضارع للنهي"),
    ("وَلَا تَأْكُلُوهَآ", "لا الناهية", "فعل مضارع للنهي"),  # the Qur'an's spelling of the same ending
    ("لِيَكْتُبْ زَيْدٌ", "لام الأمر", "فعل مضارع للأمر"),
    ("اكْتُبِ الدَّرْسَ", None, "فعل أمر"),
])
def test_a_verb_that_gives_an_order_is_named_for_it_in_the_picture(sentence: str, particle: str | None, verb: str):
    shown = _picture_roles(_syntax_read(sentence)["tree"]["tree"])
    assert verb in shown and (particle is None or particle in shown)


def _tree_roles(sentence: str) -> list[str | None]:
    """Every role the picture prints, top to bottom, worked out (not read from the treebank)."""
    drawn = iraab.analyze(sentence, recorded=False)["tree"]["tree"]
    out: list[str | None] = []

    def walk(node: dict) -> None:
        out.append(node.get("role"))
        for kid in node.get("parts", []) + node.get("children", []):
            walk(kid)
    walk(drawn)
    return out


def test_a_prayer_noun_with_its_lam_phrase_is_a_mubtada_and_khabar():
    assert [w["role"] for w in iraab.analyze("وَيْلٌ لِلْمُطَفِّفِينَ", recorded=False)["words"]][0] == "مبتدأ"
    roles = _tree_roles("وَيْلٌ لِلْمُطَفِّفِينَ")
    assert "مبتدأ" in roles and "خبر" in roles


def test_the_picture_names_no_particle_a_mawsuf_and_leaves_no_gap():
    roles = _tree_roles(NADA)
    assert "موصوف" not in roles and "معطوف" in roles
    drawn = iraab.analyze(NADA, recorded=False)["tree"]["tree"]
    assert '"gap": true' not in __import__("json").dumps(drawn)


@pytest.mark.parametrize("sentence, said", [
    # أيّ is described only by a noun with ال, a pointer or a relative (Ibn Aqil V3 p268)
    ("يَا أَيُّهَا الَّذِينَ آمَنُوا", "الَّذِينَ"),
    ("يَا أَيُّهَا هَذَا", "هَذَا"),
    ("يَا أَيُّهَا النَّاسُ", "النَّاسُ"),
    ("يَا أَيَّتُهَا النَّفْسُ", "النَّفْسُ"),
])
def test_the_called_ayyu_is_built_on_damma_and_described(sentence: str, said: str):
    read = analyze(sentence)
    called, described = read["words"][1], read["words"][2]
    # أيّ مبني على الضم في محل نصب, its ها of attention written on, a particle with no place
    assert (called["role"], called["sign"]) == ("منادى", "مبني على الضم")
    assert _ATTENTION in called["reason"], called["reason"]
    assert (described["word"], described["role"]) == (said, "صفة")
    # the picture: يا, then أيّ with its صفة, the unit as a whole the منادى
    assert tree_roles(read["tree"]["tree"])[:3] == ["حرف نداء", "منادى", "موصوف"]


@pytest.mark.parametrize("sentence, said", [
    # a command is never a صفة (Ibn Aqil V3 p198: لا تقع الجملة الطلبية صفة): hung on the called noun it is the call's answer
    ("رَبِّ اغْفِرْ لِي", True),
    ("رَبِّ زِدْنِي عِلْمًا", True),
    ("رَأَيْتُ رَجُلًا يَكْتُبُ", False),  # nearest case: a told verb on a noun no one calls is its صفة
])
def test_a_command_hung_on_the_called_noun_is_no_sifah(sentence: str, said: bool):
    tree = analyze(sentence)["tree"]["tree"]
    assert ("صفة" not in tree_roles(tree)) == said, tree_roles(tree)
