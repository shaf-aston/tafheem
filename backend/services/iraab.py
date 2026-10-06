"""A typed sentence's i'raab, by the book's rules alone (no AI, no network).

1. CAMeL reads each word (morphology).
2. An ayah the Quranic Treebank recorded is read from that record (tarkeeb_store);
   anything else goes to the parser and the book's tree (syntax), which alone name
   each word's job and its case. A word the tree leaves unnamed stays a gap.
3. Each card is built once (cards): what the word is (rule_engine), the tree's name
   on it, then its sign. The summary is the picture's top label, so the cards, the
   line above them and the picture all come from one reading.

The Analyse page and the practice questions both read sentences through here.
"""
from __future__ import annotations

from backend.services import morphology, provenance, rule_engine, signs, syntax, tarkeeb_store
from backend.services.harakat import CASE_NAME
from backend.services.nahw_book import case_of, reason, teacher_rules
from backend.services.syntax.naming import NAMED, role_key


def analyse(sentence: str) -> dict:
    """{words, summary, source, tree} for one sentence; `tree` is None when nothing joins.
    The summary is the picture's own top label, so the line above the cards and the
    picture can never name the sentence apart; with no picture there is no summary."""
    tags = morphology.analyze_sentence(sentence)
    recorded = tarkeeb_store.for_sentence(sentence)
    parsed = recorded or syntax.read(sentence)
    tree = _drawn(recorded) if recorded else parsed["tree"]
    return {
        "words": cards(tags, parsed["roles"]),
        "summary": tree["tree"].get("label") if tree else None,
        "source": provenance.of("treebank" if recorded else "nahw"),
        "tree": tree,
    }


def _drawn(recorded: dict) -> dict:
    """The recorded tree, in the shape the page draws a typed sentence's in."""
    keep = ("surah", "ayah", "words", "tree", "coverage", "unwritten")
    return {**{key: recorded[key] for key in keep}, "source": provenance.of("treebank")}


def cards(tags: list[dict], roles: list[dict]) -> list[dict]:
    """One card per word, built once: what the word is (rule_engine), the job the book's
    tree names on it, then its sign from the final case (signs.settle). A word the tree
    left unnamed keeps the no-role dash; a name the teacher took back shows why."""
    entries = rule_engine.cards(tags)
    if len(roles) == len(entries):
        for entry, found in zip(entries, roles):
            if found.get("gap"):
                entry.update(role=rule_engine.UNNAMED, role_key=None, case=found["case"], sign=None, gap=True,
                             reason=found["gap"]["ar"], notes=found["gap"]["en"])
            elif found["role"]:
                _named(entry, found)
    words = signs.settle(entries)
    return rule_engine.mark_condition(words, roles) if len(roles) == len(words) else words


def _named(entry: dict, found: dict) -> None:
    """One card takes the tree's name; the case is naming's (syntax.naming._ending)."""
    renamed = found["role"] != entry.get("role")
    entry.update(role=found["role"], book=found.get("book"), role_key=role_key(found["role"]),
                 family=found.get("family"),  # كان، إنّ: named by what they govern (signs.settle)
                 governor=found.get("governor"), follows=found.get("follows"))
    if found["role"] != NAMED.fil and entry.get("type") == "fi'l":
        # لَسِحْرًا: CAMeL's verb is the parser's noun, so the verb's case goes with it
        entry.update(type="harf" if found["role"] in (NAMED.harf, NAMED.harf_jarr) else "ism", case=None, aspect=None)
    if not found["case"] and entry.get("case") != "mabni" and (own := case_of(found["role"])):
        found = {**found, "case": CASE_NAME[own]}  # a recorded ayah's name brings its own case
    moved = found["case"] and found["case"] != entry.get("case")
    if found["role"] == NAMED.fil:
        # أَقِمْ: the root made it a command; the parser, seeing only a sukun, says jazm
        if entry.get("case") == "mabni" and found["case"] == "jazm":
            moved = False
        # a word CAMeL took for a noun (ضُرِبَ، كان) or a mood the particle before settled
        # (لن يذهب): the card is the verb's own, by the parser's tense
        if entry.get("type") != "fi'l" or moved:
            aspect = found.get("aspect") or ("i" if found["case"] != "mabni" else None)
            entry.update(type="fi'l", **rule_engine.verb_card(entry["camel"]["base"], aspect, found["case"]))
        return
    if renamed:
        entry["reason"] = reason(found["role"])  # the reason must explain the new name
    if not _stands_for_own(entry, found) and moved:
        entry["case"] = found["case"]  # signs.settle writes the sign for it
    if entry["case"] == "mabni" and entry.get("type") != "harf":
        entry["reason"] = reason(found["role"], mabni=True)  # الذي، هذا: in the place of a case


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
