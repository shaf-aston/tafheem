"""Repair 6: a hal or not: و, a raf' pronoun and a verb open a hal clause, the pronoun its mubtada;
a full verb has no خبر, so a word in nasb the parser made one is a hal; a word after the verb's
masdar that agrees with it is its na't."""
from __future__ import annotations

from backend.services.nahw.book import is_one, is_subject_pronoun
from backend.services.nahw.syntax.facts import Sentence, describes, indefinite_nasb, is_verb, noun_tagged, same_root

# the verbs that take a خبر or a second object (closed_words families): any other verb takes neither
_TOLD_BY = (("kana", "words"), ("kana", "needs_negation"), ("kana", "needs_ma"), ("kaada", "words"), ("zanna", "words"))


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


def no_khabar_on_full_verb(tokens: list[dict]) -> None:
    """جاء زيد كريما: only كان, كاد and ظنّ and their sisters are told of (Tasheel 1.9, 1.10, 1.12);
    an indefinite word in nasb the parser hung on any other verb as its خبر (PRD) is a modifier
    of it, as the parser hangs a hal. A raf' word there is left to the nominal sentence it heads."""
    s = Sentence(tokens)
    for token in tokens:
        verb = s.head(token)
        if token["rel"] == "PRD" and verb and is_verb(verb) and indefinite_nasb(token) \
                and not any(is_one(verb["lemma"], family, part) for family, part in _TOLD_BY):
            token["rel"] = "MOD"


def naat_beside_its_noun(tokens: list[dict]) -> None:
    """ضَلَّ ضَلَالًا بَعِيدًا، ضَرَبَ ضَرْبًا شَدِيدًا: the verb's own masdar (one root with it, its مفعول
    مطلق) with an indefinite word after it that agrees with it (facts.describes, which reads a bare
    مضاف as indefinite) is told of by it: the word is the masdar's na't, giving the kind of the doing
    (المفعول المطلق المبيّن للنوع, Tasheel 3.2), not a hal. So where the parser hung both on the verb,
    the word hangs on the masdar. Any other noun keeps the hal the parser gave (قتل زيد عمرا ظالما)."""
    s = Sentence(tokens)
    for token in tokens:
        verb, noun = s.head(token), s.by_id.get(token["id"] - 1)
        if (token["rel"] == "MOD" and verb and is_verb(verb) and noun and noun["head"] == verb["id"]
                and noun_tagged(noun) and same_root(noun, verb) and token.get("stt") == "i" and describes(token, noun)):
            token["head"] = noun["id"]
