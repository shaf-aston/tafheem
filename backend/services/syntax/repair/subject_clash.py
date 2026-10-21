"""Repair 2: a word hung on a verb's subject that the typed vowels forbid there is the verb's object."""
from __future__ import annotations

from backend.services.nahw_book import is_mabni
from backend.services.syntax.facts import (
    Sentence, has_added, indefinite_nasb, typed_tanween, is_state_word, is_verb, is_zarf, same_root, typed_case_of, noun_tagged, subject_link, works_as_verb)


def subject_clash(tokens: list[dict]) -> None:
    """A word the parser hung on a verb's subject that the typed vowels forbid there is the verb's object.
    أَعْطَى الرَّجُلُ الْفَقِيرَ دِرْهَمًا، ضَرَبَ زَيْدٌ عَمْرًا: a نعت wears its noun's case (Tasheel 3.10.1),
    so a word in nasb after the subject's damma is no نعت; a hal (جَاءَ زَيْدٌ رَاكِبًا) or the verb's own
    masdar (فَرِحَ الْوَلَدُ فَرَحًا) is left to its own rule.
    ضَرَبَ زَيْدٌ مَرْيَمَ: a noun with tanween is complete, so nothing after it is its مضاف إليه."""
    s = Sentence(tokens)
    for token in tokens:
        head = s.head(token)
        verb = s.head(head) if head else None
        if not (verb and is_verb(verb) and noun_tagged(token) and token["id"] > head["id"]
                and subject_link(head) and not is_verb(token) and typed_case_of(head) == "u"
                and not is_mabni(token.get("pos_camel", "")) and not is_zarf(token, s)):
            continue
        clash = token["rel"] == "MOD" and typed_case_of(token) == "a" and not (indefinite_nasb(token) and (is_state_word(token) or same_root(token, verb)))
        # the parser may hang it there unlabelled (---) rather than as IDF; either way an إضافة is meant
        added = (token["rel"] in ("IDF", "---") and typed_tanween(head)
                 and typed_case_of(token) in ("a", None) and not any(k["rel"] == "OBJ" for k in s.kids(verb)))
        if clash or added:
            token["head"], token["rel"] = verb["id"], "OBJ"
            head["mudaf"] = has_added(head, tokens)
            s = Sentence(tokens)


def doer_after_object(tokens: list[dict]) -> None:
    """أَدْهَشَ الْجُمْهُورَ السَّاحِرُ: the object may come before the doer. A word hung on a verb
    as its subject that the reader typed in nasb, with a raf' word hung on it straight after,
    is the object and that raf' word the doer: a نعت wears its noun's case, and a مضاف إليه is
    in jarr."""
    s = Sentence(tokens)
    for token in tokens:
        verb = s.head(token)
        if not (verb and is_verb(verb) and token["rel"] == "SBJ" and typed_case_of(token) == "a"
                and not is_mabni(token.get("pos_camel", ""))):
            continue
        doer = next((k for k in s.kids(token) if k["id"] == token["id"] + 1 and k["rel"] in ("MOD", "IDF")
                     and noun_tagged(k) and typed_case_of(k) == "u"), None)
        if doer:
            token["rel"] = "OBJ"
            doer["head"], doer["rel"] = verb["id"], "SBJ"
            s = Sentence(tokens)


def object_after_tanween(tokens: list[dict]) -> None:
    """يَا سَائِقًا الشَّاحِنَةَ: a word with tanween is complete, so nothing after it is its
    مضاف إليه; a participle typed so takes the word the parser hung on it that way, in nasb,
    as its object."""
    s = Sentence(tokens)
    for token in tokens:
        head = s.head(token)
        if (head and token["rel"] == "IDF" and works_as_verb(head) and typed_tanween(head)
                and typed_case_of(token) == "a"):
            token["rel"] = "OBJ"


def kana_subject(tokens: list[dict]) -> None:
    """لَيْسَ الشَّدِيدُ بِالصُّرَعَةِ: كان and its sisters put their خبر in nasb (Tasheel 1.9), so
    a word the parser made the خبر that the reader typed in raf', with no اسم beside it, is the
    اسم; what the parser hung on it after it (here بِالصُّرَعَةِ) is the خبر."""
    s = Sentence(tokens)
    for token in tokens:
        verb = s.head(token)
        if not (verb and token["rel"] == "PRD" and s.family(verb) == "kana" and verb["id"] < token["id"]
                and noun_tagged(token) and typed_case_of(token) == "u"
                and not any(subject_link(k) for k in s.kids(verb))):
            continue
        token["rel"] = "SBJ"
        told = next((k for k in s.kids(token) if k["id"] > token["id"] and k["rel"] == "MOD"
                     and (k["pos"] == "PRT" or typed_case_of(k) == "a")), None)
        if told:
            told["head"], told["rel"] = verb["id"], "PRD"
        s = Sentence(tokens)


def zanna_pair(tokens: list[dict]) -> None:
    """حَسِبَ الرَّجُلُ الطَّرِيقَ قَصِيرًا: ظنّ and its sisters enter a مبتدأ and its خبر and put both
    in nasb as their two objects (Alfiyya: انصب بفعل القلب جزأي ابتدا). The parser may keep the pair
    as it was, the first word the subject of the second; with the reader's fatha on both, the first is
    the verb's first object and the second its second. A doer the parser took for the object, typed
    in raf', is the verb's doer."""
    s = Sentence(tokens)
    for first in tokens:
        second = s.head(first)
        verb = second and s.head(second)
        if not (verb and first["rel"] in ("SBJ", "TPC") and s.family(verb) == "zanna" and first["id"] < second["id"]
                and noun_tagged(first) and typed_case_of(first) == typed_case_of(second) == "a"):
            continue
        for doer in s.kids(verb):
            if doer["rel"] == "OBJ" and doer["id"] < first["id"] and typed_case_of(doer) == "u":
                doer["rel"] = "SBJ"
        first["head"], first["rel"] = verb["id"], "OBJ"
        second["rel"] = "OBJ"
        s = Sentence(tokens)
