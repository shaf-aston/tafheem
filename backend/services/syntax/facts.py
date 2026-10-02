"""The questions (axes) the naming tree splits a word on.

An axis is a small pure test of one token and what hangs round it that answers
with exactly one value from a closed list; the tree (data/nahw_rules/naming_tree.json)
names the axis each branch splits on, walker.py reads the answers.

`is_verb` lives here, not in naming, so facts can be imported by the walker that
naming calls without a loop. Pure: tokens in, names out.
"""
from __future__ import annotations

from typing import Callable

from backend.services.arabic_text import bare_letters, strip_diacritics
from backend.services.nahw_book import book_words, is_one, is_plain_noun
from backend.services.syntax.vowels import (
    CAMEL_CASE, command_shape, has_tanween, past_passive_shape, typed_case, typed_passive)

PRESENT_PREFIX = set("أنيت")
# a root letter is what is left once the letters that come and go are removed
WEAK = set("اويىءأإآئؤة")


def is_verb(token: dict) -> bool:
    if has_tanween(token.get("typed")):
        return False  # a verb never carries tanween, whatever the parser tagged it
    if token["pos"].startswith("VRB"):  # VRB-PASS is a verb too
        return True
    # the word is unknown to the morphology, but the reader typed a passive verb or a
    # hollow command (بِعْ, which CAMeL takes for a name)
    typed = token.get("typed") or ""
    if len(bare_letters(typed)) == 2 and command_shape(typed):
        return token.get("pos_camel") in ("noun", "noun_prop")  # نَمْ is not the noun نَمّ
    return token.get("pos_camel") == "noun_prop" and (
        (strip_diacritics(typed)[:1] in PRESENT_PREFIX and typed_passive(typed, True))
        or past_passive_shape(typed))


def is_passive(token: dict) -> bool:
    if token.get("vox") == "p":
        return True
    typed = token.get("typed")
    present = token.get("asp") == "i" or not (token["pos"].startswith("VRB") or past_passive_shape(typed))
    return typed_passive(typed, present)


def _kind(token: dict, tokens: list[dict]) -> str:
    if token["pos"] == "PRT":
        return "harf"
    # a calling or excepting particle takes a noun, whatever the parser tagged the word
    if _governor(token, tokens) in ("nida", "istithna"):
        return "ism"
    return "fil" if is_verb(token) else "ism"


def case_of(token: dict) -> str | None:
    """What the reader typed first, the parser's guess second."""
    return (typed_case(token.get("typed"), token.get("stuck_on", 0))
            or CAMEL_CASE.get(token.get("cas")))


def children_of(token: dict, tokens: list[dict]) -> list[dict]:
    return [t for t in tokens if t["head"] == token["id"]]


def noun_before(particle: dict, by_id: dict) -> bool:
    """The particle follows a noun it can join to, which an oath و does not."""
    before = by_id.get(particle["head"])
    return bool(before and before["id"] < particle["id"] and before["pos"] in ("NOM", "PROP")
                and not is_verb(before))


def _follows(token: dict, tokens: list[dict]) -> str:
    """Which follower (tabi') the word is, or none: a follower takes its case from the
    word it follows, every other noun from a governor (Tasheel 3.10 p88).

    A word is a follower only on the evidence of both its link and what it hangs on;
    an indefinite word after a definite or construct noun is a khabar or hal, so it
    answers none and the rest of the naming decides it."""
    by_id = {t["id"]: t for t in tokens}
    head = by_id.get(token["head"])
    # the noun pointed at by a demonstrative child: هذا البستانُ
    pointer = next((c for c in children_of(token, tokens) if "dem" in c.get("pos_camel", "")), None)
    if pointer and case_of(pointer) in (None, case_of(token)) and token.get("stt") == "d":
        return "naat"
    if not head:
        return "none"
    # لكن is also an inna sister; it joins only when no clause of its own follows
    if head["pos"] == "PRT" and is_one(head["lemma"], "atf") and not is_one(head["lemma"], "inna")             and noun_before(head, by_id):
        return "atf"
    # الخليفة عمر: a bare name right after a noun with ال is that noun's badal
    if token["pos"] == "PROP" and token["rel"] == "MOD" and head["id"] == token["id"] - 1             and head["pos"] == "NOM" and head["form"].startswith("ال") and not is_verb(head)             and not has_tanween(token.get("typed")):
        return "badal"
    with_pronoun = any(k.get("pos_camel") == "pron" for k in children_of(token, tokens))
    if is_one(token["lemma"], "tawkeed", "with_pronoun" if with_pronoun else "without_pronoun")             and head["id"] < token["id"] and not is_verb(head) and head["pos"] != "PRT":
        return "tawkeed"
    if token["rel"] != "MOD" or is_verb(head):
        return "none"
    mine, theirs = case_of(token), case_of(head)
    if mine and mine == theirs:
        # a na't matches its noun in "the" as well as case, and a word in idafa
        # counts as definite, so an indefinite word after either is the khabar
        return "none" if token.get("stt") == "i" and head.get("stt") in ("d", "c") else "naat"
    # لا رجلَ حاضرٌ (khabar) and a hal or tamyeez in nasb are not followers
    if mine and theirs and head["rel"] in ("SBJ", "TPC") and mine != "a":
        return "none"
    if mine == "a" and token.get("stt") != "d":
        return "none"
    return "naat" if token.get("ud") == "ADJ" else "none"


def _has_particle(verb: dict, tokens: list[dict], family: str, part: str = "words") -> bool:
    return any(k["pos"] == "PRT" and is_one(k["lemma"], family, part) for k in children_of(verb, tokens))


def _completed_by_present_verb(verb: dict, tokens: list[dict]) -> bool:
    """كاد يموت, أوشك أن ينتهي: a present verb, bare or behind أن, finishes the clause."""
    for kid in children_of(verb, tokens):
        if kid["pos"] == "PRT" and is_one(kid["lemma"], "nasb_mudari"):
            if any(k["pos"].startswith("VRB") and k.get("asp") == "i" for k in children_of(kid, tokens)):
                return True
        elif kid["pos"].startswith("VRB") and kid.get("asp") == "i":
            return True
    return False


def family_of(word: dict, tokens: list[dict]) -> str | None:
    """Which family a governing word belongs to: inna, kana, kaada or zanna."""
    lemma = word["lemma"]
    if is_one(lemma, "inna") or is_one(lemma, "la_jins"):
        return "inna"
    if is_one(lemma, "kana") or is_one(lemma, "kana", "like_laysa") \
            or (is_one(lemma, "kana", "needs_negation") and _has_particle(word, tokens, "negation")) \
            or (is_one(lemma, "kana", "needs_ma") and _has_particle(word, tokens, "kana", "like_laysa")):
        return "kana"
    if is_one(lemma, "kaada") and _completed_by_present_verb(word, tokens):
        return "kaada"
    return "zanna" if is_one(lemma, "zanna") else None


def negated_before(word: dict, tokens: list[dict]) -> bool:
    return any(t["pos"] == "PRT" and t["id"] < word["id"] and is_one(t["lemma"], "negation")
               for t in tokens)


def _skeleton(word: str) -> list[str]:
    return [letter for letter in bare_letters(word) if letter not in WEAK]


def is_participle(token: dict) -> bool:
    """An active or passive participle, or an adjective: what a hal is made of.
    A word the morphology does not know (مسرعا) is judged by its مـ and its ending ـا."""
    typed = bare_letters(token.get("typed") or "")
    return (token.get("ud") == "ADJ" or token.get("pos_camel") == "adj"
            or token.get("pattern", "").startswith(tuple(book_words("participle_patterns")))
            or (token.get("pos_camel") == "noun_prop" and typed[:1] == "م" and typed[-1:] == "ا"))


def _listed(token: dict, *families: str) -> bool:
    """On a book list by its lemma or by the form as typed: the list holds صباحا
    and يوم, while the parser lemmatises the first to صباح."""
    return any(is_one(spelling, family) for family in families
               for spelling in (token["lemma"], strip_diacritics(token["form"])))


def _place_time(token: dict, tokens: list[dict]) -> bool:
    """A listed time or place word that is a verb's مفعول فيه (Tasheel 3.2 p67): it
    modifies the verb with no vowel or fatha, or it stands before its verb with the
    verb hanging off it (مَتَى سافر), whichever way this CAMeL/onnx build drew the link."""
    if token["pos"] == "PRT" or not _listed(token, "zarf_zaman", "zarf_makan"):
        return False
    head = next((t for t in tokens if t["id"] == token["head"]), None)
    if head and is_verb(head):
        return token["rel"] == "MOD" and typed_case(token.get("typed"), token.get("stuck_on", 0)) in (None, "a")
    return case_of(token) in (None, "a") and any(
        is_verb(k) and k["id"] > token["id"] for k in children_of(token, tokens))


def _verb_slot(token: dict, tokens: list[dict]) -> str:
    """The place a word fills under the verb that governs it (Tasheel 3.1 p60, 3.2 p67),
    decided in this order, `none` where the book names it elsewhere:

    a listed time or place word is a مفعول فيه; before a plain verb a TPC is a mubtada
    (none) and a SBJ or TPC in nasb the object; an indefinite word after a verb that has
    its doer is a tamyeez (after a tamyeez verb, not a participle) or a hal (a participle);
    then the argument itself, by the vowel the reader typed (damma subject, fatha object),
    else by the link; an OBJ or TMZ the parser hung elsewhere keeps its link's place;
    last, an indefinite word in nasb modifying a verb or the noun under it is an absolute
    object (same root), a hal (participle or مـ) or a tamyeez (never before its head)."""
    if _place_time(token, tokens):
        return "place_time"
    by_id = {t["id"]: t for t in tokens}
    head = by_id.get(token["head"])
    rel = token["rel"]
    typed = typed_case(token.get("typed"), token.get("stuck_on", 0))
    if head and is_verb(head):
        family = family_of(head, tokens)
        before = token["id"] < head["id"]
        siblings = [t for t in children_of(head, tokens) if t is not token]
        if family is None:
            if before and rel in ("SBJ", "TPC") and typed == "a":
                return "object"  # القرآنَ قرأ الطالبُ: the reader's own fatha marks the fronted object
            if before and rel == "TPC":
                return "none"  # a doer never comes first: the noun opens the sentence
            if rel in ("OBJ", "MOD", "TMZ") and typed in (None, "a") and not before \
                    and token.get("stt") == "i" and any(t["rel"] in ("SBJ", "TPC", "OBJ") for t in siblings):
                if is_one(head["lemma"], "tamyeez_verbs") and not is_participle(token):
                    return "specification"
                if is_participle(token):
                    return "state"
        if (rel in ("SBJ", "TPC", "OBJ") or (rel == "IDF" and typed != "i")
                or (rel == "MOD" and typed == "u" and is_plain_noun(token))
                # بِعْ الكِتَابَ: hung on the verb as a modifier, but a definite word is never a
                # hal or tamyeez, so its fatha makes it the object (unless it is the verb's own masdar)
                or (rel == "MOD" and typed == "a" and token.get("stt") == "d" and is_plain_noun(token)
                    and family is None and _skeleton(token["lemma"]) != _skeleton(head["lemma"]))):
            if typed in ("u", "a"):  # damma stands for the doer (or its deputy), fatha is the done-to
                return "subject" if typed == "u" else "object"
            if is_passive(head):
                # a passive verb has no doer to take an object from: its first noun
                # stands in for the doer, and only a second one is an object
                if rel != "OBJ":
                    return "subject"
                first = min((t for t in (*siblings, token) if t["rel"] in ("SBJ", "TPC", "OBJ")),
                            key=lambda t: (t["rel"] == "OBJ", t["id"]))
                return "subject" if token is first else "object"
            # the parser reads letters only, so a nominative "object" with no subject is the subject
            return "object" if rel == "OBJ" and (
                case_of(token) != "u" or any(s["rel"] == "SBJ" for s in siblings)) else "subject"
    if rel == "TMZ":
        return "specification"
    if rel == "OBJ":
        return "object"
    if rel == "MOD" and head:
        mine, theirs = case_of(token), case_of(head)
        # an indefinite nasb word after a definite noun is that noun's hal, not the verb's
        after_definite = (mine == theirs and not is_verb(head) and token.get("stt") == "i"
                          and head.get("stt") in ("d", "c"))
        if mine == "a" and token.get("stt") != "d" and not after_definite:
            verb = head if is_verb(head) else by_id.get(head["head"])
            if verb and is_verb(verb):
                if _skeleton(token["lemma"]) == _skeleton(verb["lemma"]):
                    return "absolute"  # same root as its verb: فَرِحَ فَرَحًا
                if is_participle(token) or bare_letters(token.get("typed") or "")[:1] == "م":
                    return "state"
                return "specification" if token["id"] > head["id"] else "none"
    return "none"


def _governor(token: dict, tokens: list[dict]) -> str:
    """What gives this noun its case (Tasheel 3.3 p79), decided in this order:
    a calling or excepting particle it hangs on (the excepting one only when no
    negation came before it), any other particle it is the object of (harf jarr),
    a noun it is the idafa of (a verb takes an idafa-linked word as its argument
    unless the reader typed kasra), the inna/kana/kaada/zanna family or plain verb it
    is an argument of, else a verb that governs it by any other place (_verb_slot), else none. A bare noun with kasra straight after a plain noun
    and no particle between is idafa too (يا عبدَ اللهِ)."""
    head = next((t for t in tokens if t["id"] == token["head"]), None)
    rel = token["rel"]
    typed = typed_case(token.get("typed"), token.get("stuck_on", 0))
    if _place_time(token, tokens):
        return "verb"
    if head and head["pos"] == "PRT":
        if is_one(head["lemma"], "nida") and "interrog" not in head.get("pos_camel", ""):
            return "nida"
        if is_one(head["lemma"], "istithna") and not negated_before(head, tokens):
            return "istithna"
    if head and is_verb(head) and is_one(token["lemma"], "istithna", "nouns")             and not negated_before(token, tokens):
        return "istithna"
    if rel == "OBJ" and head and head["pos"] == "PRT":
        return "harf_jarr"
    under_verb = bool(head) and is_verb(head)
    if rel == "IDF" and not (under_verb and typed != "i"):
        return "idafa"
    if rel == "---" and head and is_plain_noun(head) and head["id"] == token["id"] - 1             and case_of(token) == "i" and not any(c["rel"] in ("SBJ", "TPC") for c in children_of(token, tokens))             and not ("dem" in token.get("pos_camel", "") and not any(is_verb(t) for t in tokens)):
        return "idafa"
    # ظن الولد الأمر سهلا: a modifier after the first object is the verb's second
    second = (rel == "MOD" and under_verb and typed in (None, "a") and family_of(head, tokens) == "zanna"
              and any(k["rel"] == "OBJ" and k["id"] < token["id"] for k in children_of(head, tokens)))
    if head and (second or rel in ("SBJ", "TPC", "OBJ", "PRD") or (rel == "IDF" and typed != "i")):
        family = family_of(head, tokens)
        if family:
            return family
    return "verb" if _verb_slot(token, tokens) != "none" else "none"


def _slot(token: dict, tokens: list[dict]) -> str:
    """Which place the word fills under the inna/kana/kaada/zanna word it hangs on.

    A khabar (PRD) is the predicate, except that after a fronted jar-wa-majroor under
    إن the noun is the subject, and a verb under كاد or إن stays a verb (none).
    Under كان or كاد every argument but an OBJ is the subject; under إن a SBJ or TPC
    is. Under an active ظن a nominative word is the subject, a word in nasb the
    object, and an object or modifier after an earlier object the second. A passive
    ظن has no such places (none). A word a plain verb governs takes its place from
    _verb_slot: subject is the doer or its deputy, object the done-to."""
    if _governor(token, tokens) == "verb":
        return _verb_slot(token, tokens)
    head = next((t for t in tokens if t["id"] == token["head"]), None)
    family = family_of(head, tokens) if head else None
    rel = token["rel"]
    if not family:
        return "none"
    if rel == "PRD":
        if family == "inna" and token["pos"] != "PRT" and any(
                t["head"] == head["id"] and t["rel"] == "PRD" and t["pos"] == "PRT" and t["id"] < token["id"]
                for t in tokens):
            return "subject"  # إن في البيت رجلا
        return "none" if is_verb(token) and family in ("kaada", "inna") else "predicate"
    typed = typed_case(token.get("typed"), token.get("stuck_on", 0))
    if family in ("kana", "kaada"):
        if rel in ("SBJ", "TPC") or (rel == "IDF" and is_verb(head) and typed != "i"):
            return "subject"
        return "object" if rel == "OBJ" else "none"
    if family == "inna":
        return "subject" if rel in ("SBJ", "TPC") else "object" if rel == "OBJ" else "none"
    if is_passive(head) or not (rel in ("SBJ", "TPC", "OBJ", "MOD") or (rel == "IDF" and typed != "i")):
        return "none"
    if rel in ("OBJ", "MOD") and typed in (None, "a") and any(
            k["rel"] == "OBJ" and k["id"] < token["id"] for k in children_of(head, tokens)):
        return "second_object"
    if typed:
        return "subject" if typed == "u" else "object"
    if rel == "OBJ":
        others = [t for t in children_of(head, tokens) if t is not token]
        return "object" if case_of(token) != "u" or any(s["rel"] == "SBJ" for s in others) else "subject"
    return "none" if rel == "MOD" else "subject"


def _voice(token: dict, tokens: list[dict]) -> str:
    """Whether the verb that governs the word is active or passive: under a passive
    verb the subject is the deputy of the doer. none where no verb heads the word."""
    head = next((t for t in tokens if t["id"] == token["head"]), None)
    if head and is_verb(head) and _governor(token, tokens) == "verb":
        return "passive" if is_passive(head) else "active"
    return "none"


# Each axis is one question the book asks of a word, with a closed list of answers
# and a function that gives exactly one. Siblings in the tree split on one axis
# and each takes one answer, so they cannot overlap.
AXES: dict[str, tuple[tuple[str, ...], Callable[[dict, list[dict]], str]]] = {
    "kind": (("harf", "fil", "ism"), _kind),
    "follows": (("naat", "atf", "tawkeed", "badal", "none"), _follows),
    "governor": (("harf_jarr", "idafa", "verb", "inna", "kana", "kaada", "zanna", "nida", "istithna", "none"),
                 _governor),
    "slot": (("subject", "predicate", "object", "second_object", "absolute", "place_time", "state",
              "specification", "none"), _slot),
    "voice": (("active", "passive", "none"), _voice),
}


def of(token: dict, tokens: list[dict]) -> dict[str, str]:
    """The word's answer on every axis."""
    values = {}
    for axis, (allowed, answer) in AXES.items():
        values[axis] = answer(token, tokens)
        if values[axis] not in allowed:
            raise ValueError(f"axis {axis} answered {values[axis]!r}, not one of {allowed}")
    return values
