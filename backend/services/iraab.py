"""A typed sentence's i'raab, by the book's rules alone (no AI, no network).

1. CAMeL reads each word (morphology).
2. The rule engine gives every word a card from its vowels (rule_engine).
3. An ayah the Quranic Treebank recorded is read from that record (tarkeeb_store);
   anything else goes to the parser and the book's tree (syntax). Their names win
   wherever they have one and the rule engine's cards fill the rest, so the cards
   and the picture come from one reading. A word no rule settles stays a gap.

The Analyse page and the practice questions both read sentences through here.
"""
from __future__ import annotations

from backend.services import morphology, provenance, rule_engine, signs, syntax, tarkeeb_store
from backend.services.harakat import CASE_NAME
from backend.services.nahw_book import case_of, reason, teacher_rules, term_ar
from backend.services.syntax import teacher
from backend.services.syntax.naming import NAMED, opens_with_verb, role_key


def analyse(sentence: str) -> dict:
    """{words, summary, source, tree} for one sentence; `tree` is None when nothing joins."""
    tags = morphology.analyze_sentence(sentence)
    result = rule_engine.analyze(sentence, tags)
    recorded = tarkeeb_store.for_sentence(sentence)
    parsed = recorded or syntax.read(sentence)
    result = with_parser_roles(result, parsed["roles"])
    summary = (_recorded_summary(recorded) if recorded else None) or result.get("summary")
    return {
        "words": result.get("words", []),
        "summary": summary,
        "source": provenance.of("treebank" if recorded else "nahw"),
        "tree": _drawn(recorded) if recorded else parsed["tree"],
    }


def _drawn(recorded: dict) -> dict:
    """The recorded tree, in the shape the page draws a typed sentence's in."""
    keep = ("surah", "ayah", "words", "tree", "coverage", "unwritten")
    return {**{key: recorded[key] for key in keep}, "source": provenance.of("treebank")}


def _recorded_summary(recorded: dict) -> str | None:
    """The sentence type the record names, in the words the rules use for it."""
    top = recorded["tree"]
    if not top.get("label"):
        return None
    return rule_engine.sentence_type(
        is_verbal=top["label"] == term_ar("jumlah_filiyyah"),
        is_inna=top.get("role") == term_ar("harf_nasikh"))


def with_parser_roles(rule_result: dict, parser_roles: list[dict]) -> dict:
    """The rule engine's answer with every role the parser could name written over it."""
    entries = rule_result.get("words", [])
    if len(parser_roles) != len(entries) or not any(found["role"] or found.get("gap") for found in parser_roles):
        return rule_result
    for entry, found in zip(entries, parser_roles):
        if not found["role"] and not found.get("gap") and (
                why := teacher.fallback_gap(entry.get("role"), found)):
            found = {**found, "gap": why}  # the rule engine's name clashes with the typed vowel
        if found.get("gap"):
            # the teacher caught the parser's name breaking a rule; the rule engine's
            # guess must not stand in for it, so the card shows the no-role dash and why
            entry.update(role="–", role_key=None, case=found["case"], sign=None, gap=True,
                         reason=found["gap"]["ar"], notes=found["gap"]["en"])
        elif found["role"]:
            renamed = found["role"] != entry.get("role")
            entry["role"] = found["role"]
            entry["book"] = found.get("book")  # the branches of the book that named it
            entry["family"] = found.get("family")  # كان، إنّ: named by what they govern (signs.settle)
            # the colour must follow the new name, never the one it replaced
            entry["role_key"] = role_key(found["role"])
            if found["role"] != "فعل" and entry.get("type") == "fi'l":
                # لَسِحْرًا: CAMeL's verb is the parser's noun, so the verb's case goes with it
                entry.update(type="harf" if found["role"] in (NAMED.harf, NAMED.harf_jarr) else "ism", case=None, aspect=None)
            moved = found["case"] and found["case"] != entry.get("case")
            # أَقِمْ: the root made it a command; the parser, seeing only a sukun, says jazm
            if entry.get("type") == "fi'l" and entry.get("case") == "mabni" and found["case"] == "jazm":
                moved = False
            if found["role"] == "فعل":
                # a word CAMeL took for a noun (ضُرِبَ، كان) or a mood the particle before
                # settled (لن يذهب): the card is the verb's own, by the parser's tense
                if entry.get("type") != "fi'l" or moved:
                    aspect = found.get("aspect") or ("i" if found["case"] != "mabni" else None)
                    entry.update(type="fi'l", **rule_engine.verb_card(entry["camel"]["base"], aspect, found["case"]))
            else:
                if renamed:
                    entry["reason"] = reason(found["role"])  # the reason must explain the new name
                    # رأيتُ أخي: no vowel shows, so a new name brings its own case (case_of_role)
                    if not found["case"] and entry.get("case") != "mabni" and (own := case_of(found["role"])):
                        moved = CASE_NAME[own] != entry.get("case")
                        found = {**found, "case": CASE_NAME[own]}
                if moved and _stands_for_own(entry, found):
                    moved = False  # رأيت المعلماتِ: the kasra is the object's own nasb
                if moved:
                    entry["case"] = found["case"]  # signs.settle writes the sign for it
                if entry["case"] == "mabni" and entry.get("type") != "harf":
                    entry["reason"] = reason(found["role"], mabni=True)  # الذي، هذا: in the place of a case
    summary = _sentence_type(parser_roles) or rule_result.get("summary")
    return {**rule_result, "words": signs.settle(entries), "summary": summary}


def _stands_for_own(entry: dict, found: dict) -> bool:
    """The typed vowel is the sign of the role's own case for this kind of word (a sound
    feminine plural's kasra in nasb, a diptote's fatha in jarr), so the role's case stands."""
    own = case_of(found["role"])
    typed = next((letter for letter, name in CASE_NAME.items() if name == found["case"]), None)
    stands = teacher_rules()["signs"]["stands_for"].get(signs.kind_of(entry["camel"]), {})
    if own and stands.get(typed) == own:
        entry["case"] = CASE_NAME[own]
        return True
    return False


def _sentence_type(parser_roles: list[dict]) -> str | None:
    """The type the parser's names give, or None when it named nothing."""
    names = [found["role"] for found in parser_roles if found["role"]]
    if not names:
        return None
    if "منادى" in names and not opens_with_verb(names):
        return term_ar("jumlah_nidaiyyah")  # يا عبدَ الله: a call, the same words the tree uses
    return rule_engine.sentence_type(is_verbal=opens_with_verb(names), is_inna="اسم إن" in names)
