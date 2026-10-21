"""Repair 6: و, a raf' pronoun and a verb open a hal clause; the pronoun is its mubtada."""
from __future__ import annotations

from backend.services.nahw_book import is_subject_pronoun
from backend.services.syntax.facts import Sentence, is_verb


def hal_clause(bases: list[dict], tokens: list[dict]) -> None:
    """جاء الولدُ وهو يبكي: the parser may join هو to the noun before as a معطوف, or take it
    with the و; but a verb after it makes the pronoun a mubtada and the verb its khabar,
    the clause a hal (Tasheel 3.7). Hung as the parser hangs a clause after و: the verb
    on the و, the pronoun on the verb."""
    s = Sentence(tokens)
    for pronoun, verb in zip(bases, bases[1:]):
        waw = s.by_id.get(pronoun["id"] - 1)
        if (waw and waw["pos"] == "PRT" and waw["lemma"].strip("+") == "و" and is_subject_pronoun(pronoun)
                and is_verb(verb) and pronoun["head"] in (waw["id"], waw["head"])):
            verb["head"], verb["rel"] = waw["id"], "OBJ"
            pronoun["head"], pronoun["rel"] = verb["id"], "SBJ"
