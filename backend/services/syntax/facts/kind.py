"""Axis `kind`: is the word a harf, a fi'l or an ism. Also what a called, excepted,
asked or negating word is, which the other axes read."""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics
from backend.services.harakat import letters
from backend.services.nahw_book import book_map, is_one
from backend.services.syntax.facts.word import is_called_alone, is_called_noun, is_object_pronoun, is_suffix, is_verb, read_as
from backend.services.syntax.facts.sentence import Sentence, verb_above


def calling_head(token: dict, s: Sentence) -> str | None:
    """nida or istithna when the word is called or excepted: it is a noun called alone
    (اللهمّ), or it hangs on the listed particle (the excepting one only when no negation came before it), or it is a listed
    excepting noun (غير، سوى) under a verb."""
    if is_called_alone(token):
        return "nida"
    head = s.head(token)
    if head and head["pos"] == "PRT":
        if is_one(head["lemma"], "nida") and "interrog" not in head.get("pos_camel", ""):
            return "nida"
        if read_as(head, "istithna") and not s.negated_before(head):
            return "istithna"
    # غير، سوى after a complete clause: hung on its verb beside the group it is taken from
    # (جاء غيرُك، رأيتُ غيرَك: غير is the doer, the object), or on a definite noun under it
    # (an indefinite one takes غير as its صفة: رجلٌ غيرُ كريم)
    if head and is_one(token["lemma"], "istithna", "nouns") and not s.negated_before(token) and (
            (is_verb(head) and any(k["rel"] in ("SBJ", "OBJ") and k["id"] < token["id"] for k in s.kids(head)))
            or (head.get("stt") == "d" and verb_above(token, s))):
        return "istithna"
    return None


def owns_pronoun(token: dict, s: Sentence) -> bool:
    """أُمُّكَ: a pronoun written onto it as its مضاف إليه makes it a noun, never the particle
    spelled like it (أَمْ، ثُمَّ); a particle's pronoun (إِنَّهُ، لَكَ) is its اسم or its مجرور."""
    return any(is_suffix(t) and t["head"] == token["id"] and t["rel"] == "IDF" for t in s.tokens)


def joins_clauses(token: dict, s: Sentence) -> bool:
    """ثم is a noun to the parser, but a listed joining word between two nouns, or bare
    before a verb, is the particle, as is any typed with its damma: the place-word is ثَمَّ."""
    if not read_as(token, "atf") or owns_pronoun(token, s):
        return False
    marked = letters(token.get("typed") or "")
    if marked and "ُ" in marked[0][1]:
        return True
    if s.noun_before(token) and any(k["rel"] == "OBJ" for k in s.kids(token)):
        return True
    typed = token.get("typed") or ""
    follower = s.by_id.get(token["id"] + 1)
    return bool(typed and typed == strip_diacritics(typed) and follower and is_verb(follower))


def asked_verb(s: Sentence) -> dict | None:
    """ماذا فرض الله: the verb a question word stands as the object of, when it has no object of
    its own (data: istifham `before_verb`). A reply later in the text answers for that object."""
    asking = book_map("istifham", "before_verb")
    for question in s.tokens:
        if asking.get(strip_diacritics(question["form"])) != "object":
            continue
        verb = next((t for t in s.tokens if t["id"] > question["id"] and is_verb(t)), None)
        if verb and not any(k["rel"] == "OBJ" and k is not question and not is_verb(k) for k in s.kids(verb)):  # قال after it is the reply
            return verb
    return None


def negates(token: dict, s: Sentence) -> bool:
    """ما رأيتُه: ما straight before a verb that has its object already can only negate it
    (a relative or question ما would be that object). Straight after a verb with no object
    of its own it is that object, the relative (قرأتُ ما كتبتُه); hung on that verb as its doer it is
    the doer (سَرَّنِي ما صنعتَه), the verb's own pronouns stuck on before it."""
    verb, before = s.by_id.get(token["id"] + 1), s.by_id.get(token["id"] - 1)
    while before and before.get("token_type") == "enc0":
        before = s.by_id.get(before["id"] - 1)
    if before and is_verb(before) and (token["head"] == before["id"] and token["rel"] == "SBJ"
                                       or not any(k["rel"] == "OBJ" and k is not token for k in s.kids(before))):
        return False
    return bool(token["lemma"] == "ما" and token["pos"] != "PRT" and verb and is_verb(verb)
                and any(k["rel"] == "OBJ" for k in s.kids(verb)))


def _kind(token: dict, s: Sentence) -> str:
    """Particle, verb or noun. A word a calling or excepting particle takes is a noun,
    whatever the parser tagged it, so that test comes before the verb test."""
    if is_called_noun(token) or is_object_pronoun(token):
        return "ism"
    if token.get("reading"):
        return token["reading"]["kind"]  # إذا before a verb is a ظرف, أَلَا a حرف
    if negates(token, s):
        return "harf"
    if token["pos"] == "PRT" or joins_clauses(token, s) or (s.hijazi and token is s.hijazi[0]):
        return "harf"
    if calling_head(token, s):
        return "ism"
    return "fil" if is_verb(token) else "ism"
