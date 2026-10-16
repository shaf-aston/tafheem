"""Repair 4b: a praying noun with its لِ phrase after a verb is a clause of its own."""
from __future__ import annotations

from backend.services.nahw_book import is_one
from backend.services.syntax.facts import Sentence, is_preposition, is_verb, listed, typed_case_of


def dua_clause(tokens: list[dict]) -> None:
    """نَادَى وَيْلٌ لِلأَعْقَابِ: a noun of prayer (closed_words dua_nouns) in raf' with a لِ phrase
    straight after it after a verb of saying (closed_words saying_verbs) is the mubtada of what was said, not the verb's doer; the لِ phrase is its khabar.
    So it stands as a sentence of its own. Written over before the words are read."""
    s = Sentence(tokens)
    for token, after in zip(tokens, tokens[1:]):
        head = s.head(token)
        if (head and is_verb(head) and is_one(head["lemma"], "saying_verbs") and is_one(token["lemma"], "dua_nouns")
                and typed_case_of(token) == "u" and after["head"] in (token["id"], head["id"]) and after["pos_camel"] == "prep" and after["lemma"].strip("+") == "ل"):
            token["head"], token["rel"] = 0, "---"
            after["head"], after["rel"] = token["id"], "PRD"  # the khabar, as the parser hangs it on a mubtada


def counted_times(tokens: list[dict]) -> None:
    """نَادَى بِصَوْتِهِ مَرَّتَيْنِ: the count of times belongs to the verb it counts (closed_words
    times_counted); the parser hangs it on the jar-majrur before it. Written over before the words are read."""
    s = Sentence(tokens)
    for token in tokens:
        head = s.head(token)
        verb = next((t for t in reversed(tokens[:token["id"] - 1]) if is_verb(t)), None)
        if verb and head and is_preposition(head) and token["rel"] == "MOD" and listed(token, "times_counted"):
            token["head"] = verb["id"]
