"""Names each word's i'raab role from the links the parser drew.

The parser says which word hangs off which and how (subject, object, idafa
and so on), but it says it in CATiB's short tags and it never sees the harakat,
because it is fed the letters alone. This module turns those links into the
words a nahw book uses. Two things decide a name: the link, and the vowels the
reader typed, which are the only evidence for case and for a passive verb.

Nothing here reaches the network or a model. Given the same tokens it always
answers the same, which is why the roles it writes may be shown as derived.

Scored by `backend/scripts/score_iraab.py`; the numbers are quoted once, in this
package's `__init__.py`.
"""
from __future__ import annotations

from backend.services.arabic_text import bare_letters

# Hamza matters in these two lists: كأن folds onto كان once it is dropped,
# so the lemmas are compared as the parser writes them.
KANA = set("كان ليس صار أمسى أصبح أضحى ظل بات زال ما".split())
INNA = set("إن أن لكن كأن ليت لعل لا".split())

VOWEL = {"ً": "a", "ٌ": "u", "ٍ": "i", "َ": "a", "ُ": "u", "ِ": "i"}
TANWEEN = {"ً", "ٌ", "ٍ"}
SHADDA_SUKUN = "ّْ"
# a root letter is what is left once the letters that come and go are removed
WEAK = set("اويىءأإآئؤة")
PRESENT_PREFIX = set("أنيت")
# case shown by an ending, not by a vowel: the plural and the dual
HIDDEN_CASE = ("ين", "ون", "ان")


CASE_NAME = {"u": "raf'", "a": "nasb", "i": "jarr"}

# Every role this module can name, and how each one is drawn: the card's colour
# key (the contract's, `schemas.ROLE_KEYS`) and the bracket diagram's tone. The
# two are different vocabularies over the same roles, so they are one table:
# two tables drift the moment a role is added to only one of them. A role
# missing here is left uncoloured rather than given a plausible colour.
ROLES = {
    #              card key,    bracket tone
    "فعل": ("fil", "fil"),
    "فاعل": ("fail", "fail"),
    "نائب الفاعل": ("fail", "fail"),
    "مبتدأ": ("mubtada", "fail"),
    "اسم كان": ("mubtada", "fail"),
    "اسم إن": ("mubtada", "fail"),
    "خبر": ("khabar", "mafool"),
    "خبر كان": ("khabar", "mafool"),
    "خبر إن": ("khabar", "mafool"),
    "مفعول به": ("mafool", "mafool"),
    "مفعول مطلق": ("mafool", "mafool"),
    "تمييز": ("mafool", "mafool"),
    "صفة": ("sifah", "rel"),
    "حال": ("haal", "mafool"),
    "مضاف إليه": ("mudaf", "mudaf"),
    "حرف": ("harf", "harf"),
    "مجرور": ("harf", "mafool"),
    # said only inside a unit the diagram draws, so no card ever shows them
    "مضاف": (None, "mudaf"),
    "موصوف": (None, "fail"),
}


def role_key(role: str | None) -> str | None:
    """The stable name the word grid colours a card by."""
    return ROLES.get(role or "", (None, None))[0]


def tone(role: str | None) -> str | None:
    """The colour the bracket diagram draws this role in."""
    return ROLES.get(role or "", (None, None))[1]


def _letters(word: str) -> list[tuple[str, set]]:
    """The typed word as (letter, its marks) pairs."""
    out: list[tuple[str, set]] = []
    for char in word or "":
        if char in VOWEL or char in SHADDA_SUKUN:
            if out:
                out[-1][1].add(char)
        elif char.isalpha():
            out.append((char, set()))
    return out


def typed_case(word: str, stuck_on: int = 0) -> str | None:
    """Case read off the last typed vowel, or None when the reader left it bare.

    `stuck_on` is how many letters at the end belong to an attached pronoun, whose
    own vowel says nothing about the word: the fatha of حَالُكَ is the kaf's, and
    the case is the damma before it.
    """
    marked = _letters(word)
    if stuck_on:
        marked = marked[:-stuck_on]
    if len(marked) < 2 or "".join(letter for letter, _ in marked[-2:]) in HIDDEN_CASE:
        return None
    last = marked[-1]
    if last[0] in "اى" and marked[-2][1] & TANWEEN:
        last = marked[-2]  # the alef of رَجُلًا carries nothing; the tanween is before it
    return next((VOWEL[mark] for mark in last[1] if mark in VOWEL), None)


def _has_tanween(word: str) -> bool:
    return any(marks & TANWEEN for _, marks in _letters(word))


def typed_passive(word: str, present: bool) -> bool:
    """فُعِلَ and يُفْعَلُ by their vowels.

    A past verb never opens with a damma unless it is passive, so that one mark
    is enough. A present verb does (يُكَافِئُ is active), so there the fatha
    before the ending is what separates يُكَافَأُ from it. The kasra of كُتِبَتِ
    sits on a root letter, not the last one, which is why the end is not read.
    """
    marked = _letters(word)
    if len(marked) < 3 or "ُ" not in marked[0][1]:
        return False
    return "َ" in marked[-2][1] if present else True


def _skeleton(word: str) -> list[str]:
    return [letter for letter in bare_letters(word) if letter not in WEAK]


def _case(token: dict) -> str | None:
    """What the reader typed first, the parser's guess second."""
    return (typed_case(token.get("typed"), token.get("stuck_on", 0))
            or {"n": "u", "a": "a", "g": "i"}.get(token.get("cas")))


def _is_verb(token: dict) -> bool:
    if _has_tanween(token.get("typed")):
        return False  # a verb never carries tanween, whatever the parser tagged it
    if token["pos"] == "VRB":
        return True
    # the word is unknown to the morphology, but the reader typed a passive present verb
    typed = token.get("typed") or ""
    return (token.get("pos_camel") == "noun_prop" and bare_letters(typed)[:1] in PRESENT_PREFIX
            and typed_passive(typed, True))


def _is_passive(token: dict) -> bool:
    if token.get("vox") == "p":
        return True
    return typed_passive(token.get("typed"), token.get("asp") == "i" or token["pos"] != "VRB")


def _family_of(lemma: str) -> str | None:
    return "inna" if lemma in INNA else "kana" if lemma in KANA else None


def _governor_family(token: dict, by_id: dict) -> str | None:
    """Which family the word this one hangs off belongs to, كان's or إنّ's."""
    head = by_id.get(token["head"])
    return _family_of(head["lemma"]) if head else None


def _predicate(family: str | None) -> str:
    return {"kana": "خبر كان", "inna": "خبر إن"}.get(family, "خبر")


def name(token: dict, tokens: list[dict]) -> str | None:
    """The role for one word, or None when the links do not say."""
    by_id = {t["id"]: t for t in tokens}
    head = by_id.get(token["head"])
    family = _family_of(head["lemma"]) if head else None
    rel = token["rel"]
    children = [t for t in tokens if t["head"] == token["id"]]
    verbless = not any(_is_verb(t) for t in tokens)

    asking = any("interrog" in t.get("pos_camel", "") for t in tokens) and verbless
    if asking:
        # كيف حالك: the question word is the khabar, brought to the front
        if "interrog" in token.get("pos_camel", ""):
            return "خبر"
        if (token["pos"] == "NOM" and _case(token) == "u" and rel != "IDF") or \
                (head and "interrog" in head.get("pos_camel", "")):
            return "مبتدأ"
    if token["pos"] == "PRT":
        return "حرف"
    if "dem" in token.get("pos_camel", "") and verbless and rel not in ("IDF", "OBJ"):
        return "مبتدأ"
    pointer = next((c for c in children if "dem" in c.get("pos_camel", "")), None)
    if pointer and _case(pointer) in (None, _case(token)) and token.get("stt") == "d":
        return "صفة"  # the noun pointed at: هذا البستانُ
    if rel == "PRD":
        return _predicate(family)
    if _is_verb(token):
        return "فعل"
    if head and _is_verb(head) and rel in ("SBJ", "TPC", "OBJ", "IDF"):
        siblings = [t for t in tokens if t["head"] == head["id"] and t is not token]
        if family == "kana" and rel != "OBJ":
            return "اسم كان"
        # the parser reads letters only, so a nominative "object" with no subject is the subject
        if rel == "OBJ" and (_case(token) != "u" or any(s["rel"] == "SBJ" for s in siblings)):
            return "مفعول به"
        return "نائب الفاعل" if _is_passive(head) else "فاعل"
    if rel in ("SBJ", "TPC"):
        return {"kana": "اسم كان", "inna": "اسم إن"}.get(family, "مبتدأ")
    if rel == "---":
        # the word the sentence hangs on, with its subject under it, is the khabar
        if any(c["rel"] in ("SBJ", "TPC") for c in children):
            return "خبر"
        if token["pos"] == "NOM" and verbless:
            # the parser sometimes leaves a nominal sentence as two loose halves:
            # the first is the mubtada it starts with, the second its khabar
            loose = [t for t in tokens if t["rel"] == "---" and t["pos"] == "NOM"]
            return "مبتدأ" if not loose or token is loose[0] else "خبر"
    if rel == "OBJ":
        return "مجرور" if head and head["pos"] == "PRT" else "مفعول به"
    if rel == "IDF":
        return "مضاف إليه"
    if rel == "TMZ":
        return "تمييز"
    if rel == "MOD" and head:
        mine, theirs = _case(token), _case(head)
        if mine and mine == theirs and not _is_verb(head):
            # a na't matches its noun in "the" as well as case, and a word in idafa
            # counts as definite, so an indefinite word after either is the khabar
            if token.get("stt") == "i" and head.get("stt") in ("d", "c"):
                return _predicate(_governor_family(head, by_id))
            return "صفة"
        # لا رجلَ حاضرٌ: hung off the noun, but its case says it is the noun's khabar
        if mine and theirs and head["rel"] in ("SBJ", "TPC") and mine != "a":
            return _predicate(_governor_family(head, by_id))
        if mine == "a" and token.get("stt") != "d":
            verb = head if _is_verb(head) else by_id.get(head["head"])
            if verb and _is_verb(verb) and _skeleton(token["lemma"]) == _skeleton(verb["lemma"]):
                return "مفعول مطلق"  # same root as its verb: فَرِحَ فَرَحًا
            if token.get("ud") == "ADJ" or token.get("pos_camel") == "adj" \
                    or bare_letters(token.get("typed", ""))[:1] == "م":
                return "حال"
            return "تمييز"
        if token.get("ud") == "ADJ":
            return "صفة"
    return None


def roles(words: list[str], tokens: list[dict]) -> list[dict]:
    """One {role, case} per typed word, in the order they were typed.

    The parser splits بِ and ـه off as their own tokens; the words a reader types
    are the base words, so only those are named and the vowels are carried over.
    The case is given only when the reader typed it, since the parser never sees
    a harakah and a guessed case would look like a read one.
    """
    bases = [t for t in tokens if t.get("token_type") == "baseword"]
    if len(bases) != len(words):
        # a reader who writes بِ or وَ apart types as many words as the parser splits
        bases = [t for t in tokens if not t["form"].startswith("+")]
    if len(bases) != len(words):
        return [{"role": None, "case": None} for _ in words]  # the split does not line up
    for word, token in zip(words, bases):
        token["typed"] = word
        # letters at the end that belong to an attached pronoun, not to the word
        token["stuck_on"] = sum(len(bare_letters(t["form"].strip("+"))) for t in tokens
                                if t["head"] == token["id"] and t["form"].startswith("+"))
    named = [name(token, tokens) for token in bases]
    return [{"role": role, "case": _ending(role, token)} for role, token in zip(named, bases)]


def _ending(role: str | None, token: dict) -> str | None:
    """What to print under the word: a case for a noun, mabni or raf' for a verb."""
    if role == "فعل":
        # only the present tense takes a case, and only when nothing jazms it
        present = bare_letters(token["typed"])[:1] in PRESENT_PREFIX and token.get("asp") == "i"
        return "raf'" if present and typed_case(token["typed"]) == "u" else "mabni"
    if role == "حرف":
        return "mabni"
    # a question word, a demonstrative, a relative or a pronoun never changes its
    # ending, so the vowel on it is part of the word and not a case
    if any(kind in token.get("pos_camel", "") for kind in ("interrog", "dem", "rel", "pron")):
        return "mabni"
    return CASE_NAME.get(typed_case(token["typed"], token["stuck_on"]))
