"""Repair 2: a word hung on a verb's subject that the typed vowels forbid there is the verb's object."""
from __future__ import annotations

from backend.services.harakat import has_tanween
from backend.services.nahw_book import is_mabni
from backend.services.syntax.facts import (
    Sentence, indefinite_nasb, is_state_word, is_verb, is_zarf, same_root, typed_case_of, noun_tagged, subject_link)


def subject_clash(tokens: list[dict]) -> None:
    """A word the parser hung on a verb's subject that the typed vowels forbid there is the verb's object.
    أَعْطَى الرَّجُلُ الْفَقِيرَ دِرْهَمًا، ضَرَبَ زَيْدٌ عَمْرًا: a نعت wears its noun's case (Tasheel 3.10.1),
    so a word in nasb after the subject's damma is no نعت; a hal (جَاءَ زَيْدٌ رَاكِبًا) or the verb's own
    masdar (فَرِحَ الْوَلَدُ فَرَحًا) is left to its own rule.
    ضَرَبَ زَيْدٌ مَرْيَمَ: a noun with tanween is complete, so nothing after it is its مضاف إليه.
    Written over before the words are read."""
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
        added = (token["rel"] in ("IDF", "---") and has_tanween(head.get("typed") or "")
                 and typed_case_of(token) in ("a", None) and not any(k["rel"] == "OBJ" for k in s.kids(verb)))
        if clash or added:
            token["head"], token["rel"] = verb["id"], "OBJ"
            head["mudaf"] = any(t["head"] == head["id"] and t["rel"] == "IDF" for t in tokens)
            s = Sentence(tokens)
