"""مَنْ فِي البيتِ: an opening مَنْ with no verb to be the صلة of asks a question.

The analyser often reads it as the relative; a relative needs its صلة, and with no verb
in the sentence a jar-majroor or ظرف after it is told of it, so it is the question word,
the مبتدأ (Tasheel, أسماء الاستفهام)."""
from __future__ import annotations

from backend.services.text.arabic_text import strip_diacritics
from backend.services.nahw.book import book_map, is_one, takes_object
from backend.services.nahw.syntax.facts import Sentence, holds_doer, is_passive, is_verb, subject_link, typed_case_of


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


def asked_before_doer_verb(tokens: list[dict]) -> None:
    """كَمْ طَالِبًا نَجَحَ، مَاذَا حَدَثَ: a question noun that asks for the object (closed_words istifham
    before_verb) is the object only of a verb that takes one; before a verb that takes none it is the
    مبتدأ, and the verb, holding the pronoun back to it, its khabar, as مَنْ جَاءَ reads (man_before_verb). A verb
    with a doer of its own (كَمْ بَلَدٍ زُرْتُ) holds no pronoun back to it, so it stays the object."""
    s = Sentence(tokens)
    for token in tokens:
        verb = s.head(token)
        if (verb and is_verb(verb) and token["id"] < verb["id"] and token["rel"] in ("SBJ", "OBJ", "MOD")
                and book_map("istifham", "before_verb").get(strip_diacritics(token["form"])) == "object"
                and not holds_doer(verb, [k for k in s.kids(verb) if k is not token])
                and (is_passive(verb) or not takes_object(verb["lemma"]) or is_one(verb["lemma"], "intransitive_verbs"))):
            token["head"], token["rel"] = verb["head"], verb["rel"]
            verb["head"], verb["rel"] = token["id"], "MOD"
            s = Sentence(tokens)


def _man(token: dict) -> bool:
    return token.get("pos_camel") == "pron_rel" and strip_diacritics(token["form"]) == "من"
