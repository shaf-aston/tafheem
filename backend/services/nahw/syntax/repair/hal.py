"""Repair 6: a hal or not: و, a raf' pronoun and a verb open a hal clause, the pronoun its mubtada;
a full verb has no خبر, so a word in nasb the parser made one is a hal; a word after the verb's
masdar that agrees with it is its na't."""
from __future__ import annotations

from backend.services.nahw.book import is_one, is_plain_noun, is_subject_pronoun
from backend.services.nahw.syntax.facts import Sentence, describes, indefinite_nasb, is_verb, noun_tagged, same_root, typed_case_of

# the verbs that take a خبر or a second object (closed_words families): any other verb takes neither
_TOLD_BY = (("kana", "words"), ("kana", "needs_negation"), ("kana", "needs_ma"), ("kaada", "words"), ("zanna", "words"))


def hal_clause(bases: list[dict], tokens: list[dict]) -> None:
    """جاء الولدُ وهو يبكي، دخل الوزيرُ والصحفيون ينتظرونه، وَهُمْ ظَاهِرُونَ: the parser may join هو
    to the noun before as a معطوف, or take it with the و; but a verb after it makes the pronoun a
    mubtada and the verb its khabar, the clause a hal (Tasheel 3.7). Hung as the parser hangs a
    clause after و: the verb on the و, the pronoun on the verb. A raf' noun does the same, after a
    clause already said (not as the first word: والله يعلم). A khabar of a noun or pronoun after
    the و that the parser hung on the verb before (SBJ on it, a المبتدأ, its khabar elsewhere)
    hangs on the و as well, so it is the khabar (Tasheel 1.4.4 p11), not a hal on the verb. After a sentence already said
    (الْحَلَالُ بَيِّنٌ وَالْحَرَامُ بَيِّنٌ, typed bare) the parser may hang the noun and the khabar both on the و: the
    و joins a second sentence (عطف الجمل, page unchecked), so the noun is told of that khabar, as above."""
    s = Sentence(tokens)
    for subject, after in zip(bases, bases[1:]):
        waw = s.by_id.get(subject["id"] - 1)
        if not (waw and waw["pos"] == "PRT" and waw["lemma"].strip("+") == "و"):
            continue
        if not (is_subject_pronoun(subject) or (waw["id"] > 1 and _opens_clause(subject))):
            continue
        told = s.head(subject)
        if is_verb(after) and (subject["head"] in (waw["id"], waw["head"]) or after["head"] == subject["id"]):
            after["head"], after["rel"] = waw["id"], "OBJ"
            subject["head"], subject["rel"] = after["id"], "SBJ"
        elif (subject["rel"] == "SBJ" and told and noun_tagged(told) and not is_verb(told)
                and told["id"] > subject["id"] and told["head"] != waw["id"]
                and typed_case_of(told) in (None, "u")):
            told["head"], told["rel"] = waw["id"], "OBJ"
        elif subject["rel"] == "SBJ" and told is waw and (clause := s.head(waw)) and clause["head"] == 0 and clause["id"] < waw["id"]                 and (khabar := next((k for k in s.kids(waw) if k["id"] > subject["id"] and k["rel"] in ("OBJ", "PRD")
                                     and noun_tagged(k) and not is_verb(k) and typed_case_of(k) in (None, "u")), None)):
            subject["head"] = khabar["id"]


def _opens_clause(noun: dict) -> bool:
    """A plain noun of raf' or no case shown, the first word of a clause of its own: not a relative,
    a condition or a question word, whose clause is told of it (والذين يكنزون)."""
    return is_plain_noun(noun) and typed_case_of(noun) in (None, "u") and not (
        is_one(noun["lemma"], "mawsul") or is_one(noun["lemma"], "jazm", "conditional_nouns")
        or is_one(noun["lemma"], "istifham"))


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
