"""مَنْ فِي البيتِ: an opening مَنْ with no verb to be the صلة of asks a question.

The analyser often reads it as the relative; a relative needs its صلة, and with no verb
in the sentence a jar-majroor or ظرف after it is told of it, so it is the question word,
the مبتدأ (Tasheel, أسماء الاستفهام)."""
from __future__ import annotations

from backend.services.text.arabic_text import strip_diacritics
from backend.services.nahw.syntax.facts import Sentence, is_verb, subject_link, typed_case_of


def asked_man(bases: list[dict], tokens: list[dict]) -> None:
    if not bases or any(is_verb(t) for t in tokens):
        return
    first = bases[0]
    if _man(first) and first["head"] == 0:
        first["pos_camel"] = "pron_interrog"


def man_before_verb(bases: list[dict], tokens: list[dict]) -> None:
    """مَنْ أَكْرَمَ ضَيْفًا، مَنْ أَكْرَمْتَ: an opening مَنْ the parser hung loose on the verb after
    it is a noun with a job. A verb whose doer is the hidden هو holds the pronoun back to it, so
    مَنْ is the مبتدأ and the verb its khabar, as مَنْ جَاءَ reads; a verb with a doer of its own
    has مَنْ as its fronted object (Ibn Yaʿish on the Mufassal: a verb that has its object takes no
    other), so one that has its object already (مَنْ يُرِدِ اللَّهُ بِهِ خَيْرًا) leaves مَنْ the مبتدأ."""
    if len(bases) < 2 or not (_man(man := bases[0]) and man["rel"] == "MOD" and is_verb(verb := bases[1])):
        return
    s = Sentence(tokens)
    own_object = any(k["rel"] == "OBJ" and k is not man for k in s.kids(verb))
    if not own_object and (verb.get("per") in ("1", "2") or any(subject_link(k) for k in s.kids(verb))):
        man["head"], man["rel"] = verb["id"], "OBJ"
        return
    if (held := s.head(man)) is not verb:  # مَنْ نَصَرَ بَكْرًا: a منصوب has no عامل but the verb
        if typed_case_of(held) != "a":
            return
        held["head"], held["rel"] = verb["id"], "OBJ"
    man["head"], man["rel"] = 0, "---"
    verb["head"], verb["rel"] = man["id"], "MOD"


def _man(token: dict) -> bool:
    return token.get("pos_camel") == "pron_rel" and strip_diacritics(token["form"]) == "من"
