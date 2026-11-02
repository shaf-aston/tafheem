"""مَنْ فِي البيتِ: an opening مَنْ with no verb to be the صلة of asks a question.

The analyser often reads it as the relative; a relative needs its صلة, and with no verb
in the sentence there is none, so it is the question word, the مبتدأ, and what follows (a
jar-majroor, a ظرف, a noun) is told of it (Tasheel, أسماء الاستفهام)."""
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
        if held is None or typed_case_of(held) != "a":
            return
        held["head"], held["rel"] = verb["id"], "OBJ"
    man["head"], man["rel"] = 0, "---"
    verb["head"], verb["rel"] = man["id"], "MOD"


def asked_before_verb(tokens: list[dict]) -> None:
    """كَمْ طَالِبًا نَجَحَ، مَاذَا حَدَثَ، كَمْ بَلَدٍ زُرْتُ: a question noun that asks for the object (closed_words
    istifham before_verb) next to the verb after it, whichever of the two the parser hung on the other. A verb
    with a doer of its own holds no pronoun back to the question noun, and a مبتدأ's khabar needs one (كَمْ كِتَابًا
    قَرَأْتَهُ), so with no object of its own, active and not one the book lists as taking none, it has the question
    noun as its fronted object (man_before_verb reads مَنْ the same); a verb holding no doer of its own holds the pronoun back to it, so
    the question noun is the مبتدأ and the verb its khabar, as مَنْ جَاءَ reads."""
    s = Sentence(tokens)
    for token in tokens:
        if book_map("istifham", "before_verb").get(strip_diacritics(token["form"])) != "object":
            continue
        verb = _verb_beside(token, s)
        if verb is None:
            continue
        kids = [k for k in s.kids(verb) if k is not token]
        if holds_doer(verb, kids):
            if (token["rel"] != "OBJ" and not is_passive(verb) and not is_one(verb["lemma"], "intransitive_verbs")
                    and not any(k["rel"] == "OBJ" for k in kids)):
                _hang_under(token, verb, "OBJ")
        elif is_passive(verb) or not takes_object(verb["lemma"]) or is_one(verb["lemma"], "intransitive_verbs"):
            if s.head(token) is verb:
                _hang_under(verb, token, "MOD")
        s = Sentence(tokens)


def _verb_beside(token: dict, s: Sentence) -> dict | None:
    """The verb after the question noun that holds it, or that it holds as its MOD."""
    head = s.head(token)
    if head and is_verb(head) and token["id"] < head["id"] and token["rel"] in ("SBJ", "OBJ", "MOD"):
        return head
    return next((k for k in s.kids(token) if is_verb(k) and k["id"] > token["id"] and k["rel"] == "MOD"), None)


def _hang_under(low: dict, high: dict, rel: str) -> None:
    """Swap two words: `high` takes `low`'s place in the sentence and `low` hangs on it as `rel`."""
    if high["head"] == low["id"]:
        high["head"], high["rel"] = low["head"], low["rel"]
    low["head"], low["rel"] = high["id"], rel


def _man(token: dict) -> bool:
    return token.get("pos_camel") == "pron_rel" and strip_diacritics(token["form"]) == "من"
