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

from backend.services.arabic_text import bare_letters, strip_diacritics
from backend.services.syntax.book import is_one, words as book_words

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
    "نائب فاعل": ("fail", "fail"),
    "مبتدأ": ("mubtada", "fail"),
    "اسم كان": ("mubtada", "fail"),
    "اسم إن": ("mubtada", "fail"),
    "اسم كاد": ("mubtada", "fail"),
    "خبر": ("khabar", "mafool"),
    "خبر كان": ("khabar", "mafool"),
    "خبر إن": ("khabar", "mafool"),
    "خبر كاد": ("khabar", "mafool"),
    "مفعول به": ("mafool", "mafool"),
    # the other nasb extras (time and place, the called, the excepted) share one colour,
    # and the followers that copy the word before them (عطف، توكيد، بدل) share another
    "مفعول فيه": ("mansub", "mansub"),
    "منادى": ("mansub", "mansub"),
    "مستثنى": ("mansub", "mansub"),
    "معطوف": ("tabi", "tabi"),
    "توكيد": ("tabi", "tabi"),
    "بدل": ("tabi", "tabi"),
    "مفعول مطلق": ("mafool", "mafool"),
    "تمييز": ("mafool", "mafool"),
    "صفة": ("sifah", "rel"),
    "حال": ("haal", "mafool"),
    "مضاف إليه": ("mudaf", "mudaf"),
    "حرف": ("harf", "harf"),
    "حرف جر": ("harf", "harf"),
    "مجرور": ("harf", "mafool"),
    # said only inside a unit the diagram draws, so no card ever shows them
    "مضاف": (None, "mudaf"),
    "موصوف": (None, "fail"),
}


def _entry(role: str | None) -> tuple:
    # a recorded role is fully vowelled (نَائِبُ فَاعِلٍ); it is the same role
    return ROLES.get(strip_diacritics(role or ""), (None, None))


def role_key(role: str | None) -> str | None:
    """The stable name the word grid colours a card by."""
    return _entry(role)[0]


def tone(role: str | None) -> str | None:
    """The colour the bracket diagram draws this role in."""
    return _entry(role)[1]


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


def agrees_with_typed(typed: str, reading: str) -> bool:
    """False when a vowelled reading puts a different vowel on a letter the reader
    vowelled: آفِلًا is not the أَفَلَا typed. A letter either side left bare says
    nothing, and two spellings that do not line up letter for letter are not
    evidence either way."""
    mine, theirs = _letters(typed), _letters(reading)
    if [bare_letters(c) for c, _ in mine] != [bare_letters(c) for c, _ in theirs]:
        return True
    for (_, typed_marks), (_, read_marks) in zip(mine, theirs):
        said = {mark for mark in typed_marks if mark in VOWEL}
        read = {mark for mark in read_marks if mark in VOWEL}
        if said and read and said != read:
            return False
    return True


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


def _kids(token: dict, tokens: list[dict]) -> list[dict]:
    return [t for t in tokens if t["head"] == token["id"]]


def _has_particle(verb: dict, tokens: list[dict], family: str, part: str = "words") -> bool:
    return any(k["pos"] == "PRT" and is_one(k["lemma"], family, part) for k in _kids(verb, tokens))


def _completed_by_present_verb(verb: dict, tokens: list[dict]) -> bool:
    """كاد يموت, أوشك أن ينتهي: a present verb, bare or behind أن, finishes the clause."""
    for kid in _kids(verb, tokens):
        if kid["pos"] == "PRT" and is_one(kid["lemma"], "nasb_mudari"):
            if any(k["pos"] == "VRB" and k.get("asp") == "i" for k in _kids(kid, tokens)):
                return True
        elif kid["pos"] == "VRB" and kid.get("asp") == "i":
            return True
    return False


def _family_of(word: dict, tokens: list[dict]) -> str | None:
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


def completes_kaada(token: dict, tokens: list[dict]) -> bool:
    """The present verb that finishes a كاد-type verb; its clause is that verb's khabar."""
    head = next((t for t in tokens if t["id"] == token["head"]), None)
    return bool(head and _is_verb(token) and _family_of(head, tokens) == "kaada")


def _governor_family(token: dict, by_id: dict, tokens: list[dict]) -> str | None:
    """Which family the word this one hangs off belongs to."""
    head = by_id.get(token["head"])
    return _family_of(head, tokens) if head else None


_PREDICATE = {"kana": "خبر كان", "inna": "خبر إن"}
_SUBJECT = {"kana": "اسم كان", "inna": "اسم إن", "kaada": "اسم كاد"}


def _predicate(family: str | None) -> str:
    return _PREDICATE.get(family, "خبر")


def _listed(token: dict, *families: str) -> bool:
    """On a book list by its lemma or by the form as typed: the list holds صباحا
    and يوم, while the parser lemmatises the first to صباح."""
    return any(is_one(spelling, family) for family in families
               for spelling in (token["lemma"], strip_diacritics(token["form"])))


def _noun_before(particle: dict, by_id: dict) -> bool:
    """The particle follows a noun it can join to, which an oath و does not."""
    before = by_id.get(particle["head"])
    return bool(before and before["id"] < particle["id"] and before["pos"] in ("NOM", "PROP")
                and not _is_verb(before))


def _negated_before(word: dict, tokens: list[dict]) -> bool:
    return any(t["pos"] == "PRT" and t["id"] < word["id"] and is_one(t["lemma"], "negation")
               for t in tokens)


def _by_book(token: dict, tokens: list[dict], by_id: dict, head: dict | None,
             family: str | None) -> str | None:
    """Roles the book decides by a closed word list, before the links are read.

    Each test pairs a listed word with the shape round it (what it hangs on, what
    hangs on it, what the reader typed), because most listed words have a second
    life: و swears, كل is a noun, يوم can be a subject.
    """
    lemma = token["lemma"]
    if token["pos"] == "PRT":
        return None
    kids = _kids(token, tokens)
    # ثم is a noun to the parser; between two nouns it is the joining particle
    if is_one(lemma, "atf") and _noun_before(token, by_id) and any(k["rel"] == "OBJ" for k in kids):
        return "حرف"
    if not head:
        return None
    if head["pos"] == "PRT":
        if is_one(head["lemma"], "nida") and "interrog" not in head.get("pos_camel", ""):
            return "منادى"
        # لكن is also an inna sister; it joins only when no clause of its own follows
        if is_one(head["lemma"], "atf") and not is_one(head["lemma"], "inna") \
                and _noun_before(head, by_id):
            return "معطوف"
        if is_one(head["lemma"], "istithna") and not _negated_before(head, tokens):
            return "مستثنى"
    if is_one(lemma, "istithna", "nouns") and _is_verb(head) and not _negated_before(token, tokens):
        return "مستثنى"
    # الخليفة عمر: a bare name right after a noun with ال is that noun's badal
    if token["pos"] == "PROP" and token["rel"] == "MOD" and head["id"] == token["id"] - 1 and head["pos"] == "NOM" \
            and head["form"].startswith("ال") and not _is_verb(head):
        return "بدل"
    case = typed_case(token.get("typed"), token.get("stuck_on", 0))
    tawkeed = "with_pronoun" if any(k.get("pos_camel") == "pron" for k in kids) else "without_pronoun"
    if is_one(lemma, "tawkeed", tawkeed) and head["id"] < token["id"] and not _is_verb(head) \
            and head["pos"] != "PRT":
        return "توكيد"
    if token["rel"] == "MOD" and _is_verb(head) and case in (None, "a"):
        if _listed(token, "zarf_zaman", "zarf_makan"):
            return "مفعول فيه"
        # ظن الولد الأمر سهلا: a first object before it makes it the second
        if family == "zanna" and any(k["rel"] == "OBJ" and k["id"] < token["id"]
                                     for k in _kids(head, tokens)):
            return "مفعول به"
    return None


def name(token: dict, tokens: list[dict]) -> str | None:
    """The role for one word, or None when the links do not say."""
    by_id = {t["id"]: t for t in tokens}
    head = by_id.get(token["head"])
    family = _family_of(head, tokens) if head else None
    rel = token["rel"]
    children = _kids(token, tokens)
    verbless = not any(_is_verb(t) for t in tokens)

    by_book = _by_book(token, tokens, by_id, head, family)
    if by_book:
        return by_book
    # a question particle (هل، أ) only asks; it leaves the rest a plain sentence
    asking = verbless and any("interrog" in t.get("pos_camel", "") and t["pos"] != "PRT" for t in tokens)
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
    if rel == "PRD" and not (family == "kaada" and _is_verb(token)):
        return _predicate(family)  # كاد يموت: the present verb stays a verb, the clause is the khabar
    if _is_verb(token):
        return "فعل"
    if head and _is_verb(head) and rel in ("SBJ", "TPC", "OBJ", "IDF"):
        siblings = [t for t in tokens if t["head"] == head["id"] and t is not token]
        if family in ("kana", "kaada") and rel != "OBJ":
            return _SUBJECT[family]
        if _is_passive(head):
            # a passive verb has no doer to take an object from: its first noun
            # stands in for the doer, and only a second one is an object
            standing = [t for t in (*siblings, token) if t["rel"] in ("SBJ", "TPC", "OBJ")]
            first = min(standing, key=lambda t: (t["rel"] == "OBJ", t["id"]))
            return "نائب فاعل" if token is first or rel != "OBJ" else "مفعول به"
        # the parser reads letters only, so a nominative "object" with no subject is the subject
        if rel == "OBJ" and (_case(token) != "u" or any(s["rel"] == "SBJ" for s in siblings)):
            return "مفعول به"
        return "فاعل"
    if rel in ("SBJ", "TPC"):
        return _SUBJECT.get(family, "مبتدأ")
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
                return _predicate(_governor_family(head, by_id, tokens))
            return "صفة"
        # لا رجلَ حاضرٌ: hung off the noun, but its case says it is the noun's khabar
        if mine and theirs and head["rel"] in ("SBJ", "TPC") and mine != "a":
            return _predicate(_governor_family(head, by_id, tokens))
        if mine == "a" and token.get("stt") != "d":
            verb = head if _is_verb(head) else by_id.get(head["head"])
            if verb and _is_verb(verb) and _skeleton(token["lemma"]) == _skeleton(verb["lemma"]):
                return "مفعول مطلق"  # same root as its verb: فَرِحَ فَرَحًا
            if token.get("ud") == "ADJ" or token.get("pos_camel") == "adj" \
                    or bare_letters(token.get("typed", ""))[:1] == "م":
                return "حال"
            # a tamyeez clarifies what came before it and never goes first
            return "تمييز" if token["id"] > head["id"] else None
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
    # a particle with a مجرور under it is a حرف جر: the one name, for card and picture
    for index, token in enumerate(bases):
        if token["pos"] == "PRT" and any(
                named[j] == "مجرور" for j, kid in enumerate(bases) if kid["head"] == token["id"]):
            named[index] = "حرف جر"
    return [{"role": role, "case": _ending(role, token)} for role, token in zip(named, bases)]


def _ending(role: str | None, token: dict) -> str | None:
    """What to print under the word: a case for a noun, mabni or raf' for a verb."""
    if role == "فعل":
        # only the present tense takes a case, and only when nothing jazms it
        present = bare_letters(token["typed"])[:1] in PRESENT_PREFIX and token.get("asp") == "i"
        return "raf'" if present and typed_case(token["typed"]) == "u" else "mabni"
    if role in ("حرف", "حرف جر"):
        return "mabni"
    # a question word, a demonstrative, a relative or a pronoun never changes its
    # ending, so the vowel on it is part of the word and not a case
    if any(kind in token.get("pos_camel", "") for kind in ("interrog", "dem", "rel", "pron")):
        return "mabni"
    return CASE_NAME.get(typed_case(token["typed"], token["stuck_on"]))
