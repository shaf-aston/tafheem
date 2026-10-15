"""Axis `governor`: which word works its case on this one (a harf jarr, the mudaf, the verb,
inna, kana, kaada, zanna, the called or the excepting particle)."""
from __future__ import annotations

from backend.services.harakat import has_tanween
from backend.services.nahw_book import is_plain_noun
from backend.services.syntax.facts.word import is_participle, is_verb, shows_jarr, told_of_subject, typed_case_of, typed_or_parsed_case, unlike
from backend.services.syntax.facts.sentence import Sentence, jarr_takes, verb_above
from backend.services.syntax.facts.kind import calling_head
from backend.services.syntax.facts.follows import with_waw
from backend.services.syntax.facts.slot import place_time, verb_place


def _governor(token: dict, s: Sentence) -> str:
    """The governor's kind; the governing word itself is kept in s.governed_by."""
    kind, word = _governing(token, s)
    if word:
        s.governed_by[token["id"]] = word["id"]
    return kind


def _governing(token: dict, s: Sentence) -> tuple[str, dict | None]:
    """What gives this word its case, and which word that is (Tasheel 3.3 p79). A word has
    one governor and the nearest wins, so the tests run nearest first: a particle straight
    before it, then the noun it is the idafa of, then a family or verb it is an argument of,
    then a number or measure, then any verb that reaches it, and last the family whose
    khabar it is."""
    head = s.head(token)
    rel = token["rel"]
    typed = typed_case_of(token)
    if s.asked_of(token):
        return "none", None
    if s.hijazi and token in s.hijazi[1:]:
        return "kana", s.hijazi[0]  # ما الحجازية: its ism and khabar, as ليس's
    if place_time(token, s):
        if head and (is_verb(head) or is_participle(head)):
            return "verb", head
        return "verb", next((k for k in s.kids(token) if is_verb(k)), None)  # مَتَى سافر
    if calling := calling_head(token, s):
        return calling, head
    if with_waw(token, s):
        return "verb", verb_above(head, s)  # the verb before واو المعية works on the noun after it
    if jarr_takes(token, s):
        return "harf_jarr", head
    under_verb = bool(head) and is_verb(head)
    # كنتُ آمرًا أحدًا: the participle governs its object as its verb would; asked before
    # the idafa, since a مضاف إليه is never منصوب (فاهمٌ الدرسَ)
    if head and not under_verb and verb_place(token, s) == "object":
        return "verb", head
    if rel == "IDF" and not (under_verb and typed != "i"):
        return "idafa", head
    # ذائقةُ الموتِ: the noun in jarr straight after a noun in construct is its mudaf ilayh
    if head and head.get("stt") == "c" and head["id"] == token["id"] - 1 and typed == "i" and not under_verb:
        return "idafa", head
    # a noun with tanween is complete (ضَرَبَ زَيْدٌ مَرْيَمَ), so nothing after it is its مضاف إليه
    if rel == "---" and head and is_plain_noun(head) and head["id"] == token["id"] - 1 \
            and not has_tanween(head.get("typed") or "") \
            and (typed_or_parsed_case(token) == "i" or shows_jarr(token)) and not any(c["rel"] in ("SBJ", "TPC") for c in s.kids(token)) \
            and not ("dem" in token.get("pos_camel", "") and s.verbless):
        return "idafa", head
    # ظن الولد الأمر سهلا: a modifier after the first object is the verb's second
    second = (rel == "MOD" and under_verb and typed in (None, "a") and s.family(head) == "zanna"
              and any(k["rel"] == "OBJ" and k["id"] < token["id"] for k in s.kids(head)))
    # كان الطفلُ يلعب: the parser may hang كان's noun on it as a modifier
    named_by_kana = rel == "MOD" and under_verb and typed != "a" and s.family(head) == "kana" \
        and head["id"] == token["id"] - 1
    if head and (second or named_by_kana or rel in ("SBJ", "TPC", "OBJ", "PRD") or (rel == "IDF" and typed != "i")):
        family = s.family(head)
        if family:
            return family, head
    if rel in ("TMZ", "OBJ") and head and not under_verb and head["pos"] != "PRT":
        return "noun", head  # عشرون كتابًا: a number or measure
    if verb_place(token, s) != "none":
        return "verb", verb_above(token, s) or head  # مسافرٌ غدًا: a participle works like its verb
    if rel == "MOD" and head and not is_verb(token):
        if unlike(token, head) or told_of_subject(token, head):
            above = s.head(head)
            family = s.family(above) if above else None
            if family in ("kana", "inna"):
                return family, above
    return "none", None
