"""The one reading of a small word with several (لا، إلا، ألا، إذا), decided once per sentence.

A word on more than one list (لا is a joining word, the لا of genus, a negation and a
prohibition) used to be read by whichever list a caller asked first, so the card, the
picture and the case rules could each read it apart. Here the book's tests decide it
once (data/nahw_rules/particle_tree.json, walked like the naming tree) and the answer is
stamped on the token as `reading`; facts, naming, the picture and the card all read that.
Pure: tokens in, readings stamped.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Callable

from backend.services.arabic_text import strip_diacritics
from backend.services.harakat import SHADDA, SUKUN, five_verb_nun, has_tanween, letters
from backend.services.nahw_book import book_file, book_map
from backend.services.syntax import facts, walker


def _attached(token: dict) -> bool:
    return token["form"].startswith("+")


def _next(token: dict, s: facts.Sentence) -> dict | None:
    """The word after it, past a pronoun written onto it."""
    return next((t for t in s.tokens if t["id"] > token["id"] and not _attached(t)), None)


def _word(token: dict, s: facts.Sentence) -> str:
    lemma = strip_diacritics(token["lemma"]).strip("+")
    return lemma if lemma in _words() else "other"


def _what_follows(token: dict, s: facts.Sentence) -> str:
    """A verb in jazm (its last letter stilled or the nun of the five verbs gone), any other
    verb, an indefinite noun (no ال, no name, no pronoun on it: رجلَ، عدوى), a definite one,
    a particle, or nothing."""
    after = _next(token, s)
    if after is None:
        return "none"
    typed = after.get("typed") or ""
    if facts.is_verb(after):
        own = letters(typed)
        stilled = bool(own) and SUKUN in own[-1][1]
        return "verb_jazm" if stilled or five_verb_nun(typed) == "dropped" else "verb"
    if after["pos"] == "PRT":
        return "particle"
    bare = strip_diacritics(typed or after["form"])
    pronoun = any(t["head"] == after["id"] and _attached(t) for t in s.tokens)
    # a name is definite unless CAMeL itself read it indefinite (ضِرَارَ of لا ضرارَ, tagged a name)
    named = after["pos"] == "PROP" and after.get("stt") != "i"
    definite = bare.startswith("ال") or named or after.get("stt") == "d" or pronoun
    return "noun" if definite else "indefinite_noun"


def _negated(token: dict, s: facts.Sentence) -> str:
    return "yes" if s.negated_before(token) else "no"


def _joins(token: dict, s: facts.Sentence) -> str:
    """The noun after it wears the case of the noun before it: جاء زيدٌ لا عمرٌو, ما جاء
    الطلابُ إلا زيدٌ. Nothing to share a case with (ما جاء إلا زيدٌ) or a case apart
    (لا إلهَ إلا اللهُ) says no."""
    before, after = facts.previous_noun(token, s), _next(token, s)
    if not (before and after and after["pos"] in ("NOM", "PROP")):
        return "no"
    mine = facts.typed_or_parsed_case(after)
    return "yes" if mine and mine == facts.place_case(before, s) else "no"


def _raf(token: dict, s: facts.Sentence) -> str:
    """The noun after it is typed in raf' (damma or tanween with damma): the noun of لا of the
    genus is never raf', so this لا is a plain negation and the noun is a مبتدأ."""
    after = _next(token, s)
    return "yes" if after and facts.typed_case_of(after) == "u" else "no"


def _told(token: dict, s: facts.Sentence) -> str:
    """What stands straight after the noun that follows: a noun (its khabar) or anything else."""
    noun = _next(token, s)
    told = _next(noun, s) if noun else None
    return "noun" if told and told["pos"] in ("NOM", "PROP") and not facts.is_verb(told) else "other"


def _opens(token: dict, s: facts.Sentence) -> str:
    """The noun after it opens a sentence of its own: a definite noun in raf' with an
    indefinite one in raf' after it that does not describe it, its khabar (واللهُ أكبرُ)."""
    noun = _next(token, s)
    told = _next(noun, s) if noun else None
    if not (noun and told and noun["pos"] in ("NOM", "PROP") and told["pos"] in ("NOM", "PROP")) or facts.is_verb(told):
        return "no"
    definite = noun.get("stt") == "d" or noun["pos"] == "PROP"
    return "yes" if definite and facts.typed_or_parsed_case(noun) == "u" \
        and facts.typed_or_parsed_case(told) == "u" and told.get("stt") != "d" else "no"


AXES: dict[str, tuple[tuple[str, ...], Callable[[dict, facts.Sentence], str]]] = {
    "next": (("verb_jazm", "verb", "indefinite_noun", "noun", "particle", "none"), _what_follows),
    "negated": (("yes", "no"), _negated),
    "joins": (("yes", "no"), _joins),
    "opens": (("yes", "no"), _opens),
    "raf": (("yes", "no"), _raf),
    "told": (("noun", "other"), _told),
}


@lru_cache(maxsize=1)
def _tree() -> dict:
    tree = book_file("particle_tree.json")["tree"]
    words = tuple(child["is"] for child in tree["children"]) + ("other",)
    walker.validate(tree, {"word": (words, _word), **AXES}, book_file("closed_words.json")["families"])
    return tree


@lru_cache(maxsize=1)
def _words() -> frozenset[str]:
    return frozenset(child["is"] for child in _tree()["children"])


@lru_cache(maxsize=None)
def _judged(word: str) -> frozenset[str]:
    """The families the tree decides for this word: every role at a leaf of its branch."""
    def roles(node: dict) -> set[str]:
        return {node["role"]} if "role" in node else set().union(*map(roles, node.get("children", [])))
    return frozenset(roles(next(c for c in _tree()["children"] if c["is"] == word)))


def _merged(tokens: list[dict]) -> None:
    """أَلَّا (shadda on the lam) is أنْ with its nun merged into لا (data: nasb_mudari `merges`):
    the word is the nasb particle, and the لا the parser split off it a plain negation."""
    for word, merged in book_map("nasb_mudari", "merges").items():
        for token, tail in zip(tokens, tokens[1:]):
            if strip_diacritics(token["lemma"]) == word and SHADDA in (token.get("typed") or "") and _attached(tail):
                token["reading"] = {"family": "nasb_mudari", "named": merged["named"], "kind": "harf", "book": None}
                tail["reading"] = {"family": merged["tail"], "named": None, "kind": "harf", "book": None}


def stamp(tokens: list[dict]) -> None:
    """Stamp each listed word's reading on its token: {family, named, kind, book}, and the
    families the tree judges for it as `judged`. A word no leaf took (a و that opens no
    sentence) is read by its other lists as before, never as one of those families."""
    s = facts.Sentence(tokens)
    for token in tokens:
        token.pop("reading", None)
        token.pop("judged", None)
        if (word := _word(token, s)) == "other":
            continue
        token["judged"] = _judged(word)
        values = {"word": word, **{axis: answer(token, s) for axis, (_, answer) in AXES.items()}}
        if found := walker.walk(values, _tree()):
            token["reading"] = {"family": found.role, "named": found.leaf.get("named"),
                                "kind": found.leaf.get("kind", "harf"), "book": found.book}
    _merged(tokens)
