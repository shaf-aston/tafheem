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

from backend.services import morphology, provenance, rule_engine, syntax, tarkeeb, tarkeeb_store


def analyse(sentence: str) -> dict:
    """{words, summary, source, tree} for one sentence; `tree` is None when nothing joins."""
    tags = morphology.analyze_sentence(sentence)
    result = rule_engine.analyze(sentence, tags)
    recorded = tarkeeb_store.for_sentence(sentence)
    parsed = recorded or syntax.read(sentence)
    result = syntax.with_parser_roles(result, parsed["roles"])
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
        is_verbal=top["label"] == tarkeeb.term_ar("jumlah_filiyyah"),
        is_inna=top.get("role") == tarkeeb.term_ar("harf_nasikh"))
