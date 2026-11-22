"""What a ما does in its sentence, asked in one place (مغني اللبيب، باب ما).

A ما is one of several words spelled alike; this module answers which, for the steps that need it:

- ما الكافة, written onto an إنّ sister and stopping it working (إِنَّمَا، كَأَنَّمَا): `kaffa_sister` names the sister
  a typed word is (the parser's lemma of the pair), `stops_sister` says whether the word a cut-off ما is written onto is
  one (book links read it before any word is named);
- a relative ما or ما المصدرية, a verb hung on it after it, told apart by its عائد: `kind`.

The book's lists stay in closed_words.json, read through nahw.book (sarf asks the book directly: it sits below syntax).
"""
from __future__ import annotations

from backend.services.nahw.book import is_one, kaffa_sister as _kaffa_sister
from backend.services.nahw.syntax.facts import Sentence, is_passive, is_preposition, is_suffix, is_verb, listed
from backend.services.text.arabic_text import strip_diacritics

MA = "ما"


def is_ma(token: dict, alone: bool = False) -> bool:
    """The word is ما, or a piece cut off another word is (إِنَّ+مَا، مِمَّا) unless `alone` asks for a word standing alone."""
    form = strip_diacritics(token.get("form", ""))
    return form == MA if alone else form.strip("+") == MA


def cut_off(token: dict) -> bool:
    """The word is a ما cut off the word before it and nothing else (إِنَّ+مَا), as the parser writes the piece."""
    return strip_diacritics(token.get("form", "")) == "+" + MA


def kaffa_sister(lemma: str) -> str | None:
    """إنما → إن: the إن sister a typed word is, with ما الكافة written onto it; none for any other word."""
    return _kaffa_sister(lemma)


def stops_sister(onto: dict) -> bool:
    """The word a cut-off ما is written onto is an إن sister (إِنَّ+مَا زَيْدٌ قَائِمٌ), so the ما is the كافة that stops it."""
    return is_one(onto["lemma"].removesuffix(MA), "inna")


def kind(token: dict, s: Sentence) -> str | None:
    """What a ما with a verb hung on it after it is, by its عائد (مغني اللبيب، ما المصدرية):
    the relative's صلة holds a pronoun going back to it, ما المصدرية's never does. So "relative"
    while the verb has a place one could sit in: a هـ on it or on its jar (أعجبني ما كتبتَه, سأنبئك بتأويل ما لم تستطع عليه صبرا), a hidden هو for
    its doer (ما نفعك), an object it may take and lacks (أكلتُ ما طبختَ, the default when both
    readings stand). "masdar" when every place is taken by another word: its object written
    (أكره ما يهمل الطلابُ دروسَهم), a passive's نائب فاعل written (بما تُرِكَ العملُ), or a verb
    that takes no object (intransitive_verbs) with its doer written (سرّني ما قمتَ). None: no verb."""
    if not is_ma(token, alone=True):
        return None
    verb = next((t for t in s.kids(token) if t["id"] > token["id"] and is_verb(t)), None)
    if not verb:
        return None
    kids = s.kids(verb)
    # the verb's own pronouns, and those of the jar it holds (استطعتَ عليه)
    pronouns = [t for k in kids for t in ([k] if is_suffix(k) else s.kids(k) if is_preposition(k) else []) if is_suffix(t) and t.get("pos_camel") == "pron"]
    if any(strip_diacritics(t["form"]).strip("+") == "ه" for t in pronouns):  # the هـ that goes back to ما
        return "relative"
    named = [t for t in kids if t["rel"] in ("SBJ", "OBJ") and not is_suffix(t) and not is_verb(t)]
    if is_passive(verb):
        return "masdar" if named else "relative"
    if not any(t["rel"] == "SBJ" for t in kids) and (verb.get("per"), verb.get("gen"), verb.get("num")) == ("3", "m", "s"):
        return "relative"
    if any(t["rel"] == "OBJ" for t in kids) or listed(verb, "intransitive_verbs"):
        return "masdar"
    return "relative"
