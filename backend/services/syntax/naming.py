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
from backend.services.nahw_book import book_path, is_mabni, is_one, named_roles, role_table
from backend.services.syntax import facts, walker
from backend.services.syntax.facts import PRESENT_PREFIX
from backend.services.syntax.vowels import (
    CASE_NAME, SUKUN, command_shape, letters, paused, typed_case)

# Every role this module can name, with its card colour key and bracket tone
# (data/nahw_rules/roles.json); a role missing there is left uncoloured.
ROLES = role_table()
NAMED = named_roles()


def _entry(role: str | None) -> tuple:
    # a recorded role is fully vowelled (نَائِبُ فَاعِلٍ); it is the same role
    return ROLES.get(strip_diacritics(role or ""), (None, None))


def role_key(role: str | None) -> str | None:
    """The stable name the word grid colours a card by."""
    return _entry(role)[0]


def roles_keyed(*keys: str) -> tuple[str, ...]:
    """Every role the card colours by one of these keys (`fail` is فاعل and نائب فاعل)."""
    return tuple(role for role in ROLES if role_key(role) in keys)


def tone(role: str | None) -> str | None:
    """The colour the bracket diagram draws this role in."""
    return _entry(role)[1]


def base_tokens(words: list[str], tokens: list[dict]) -> list[dict]:
    """The parser's tokens that are the words the reader typed, clitics aside.
    Fewer or more than `words` means the split does not line up."""
    bases = [t for t in tokens if t.get("token_type") == "baseword"]
    if len(bases) != len(words):
        # a reader who writes بِ or وَ apart types as many words as the parser splits
        bases = [t for t in tokens if not t["form"].startswith("+")]
    return bases


def roles(words: list[str], tokens: list[dict]) -> list[dict]:
    """One {role, case, aspect, book} per typed word, in the order they were typed;
    `book` is the proof line, the tree's branches that named it.

    The parser splits بِ and ـه off as their own tokens; the words a reader types
    are the base words, so only those are named and the vowels are carried over.
    The case is given only when the reader typed it, since the parser never sees
    a harakah and a guessed case would look like a read one.
    """
    bases = base_tokens(words, tokens)
    if len(bases) != len(words):
        return [{"role": None, "case": None} for _ in words]  # the split does not line up
    for i, (word, token) in enumerate(zip(words, bases)):
        token["typed"] = word
        # اُكْتُبْ، أَكْرِمْ: the typed command is the tense, whatever reading the parser had
        after = words[i + 1] if i + 1 < len(words) else ""
        if command_shape(paused(word, after), i > 0 and is_one(strip_diacritics(words[i - 1]), "jazm", "before_a_present_verb")):
            token["asp"] = "c"
        # letters at the end that belong to an attached pronoun, not to the word
        token["stuck_on"] = sum(len(bare_letters(t["form"].strip("+"))) for t in tokens
                                if t["head"] == token["id"] and t["form"].startswith("+"))
    answers = {t["id"]: a for t, a in zip(tokens, facts.of_sentence(tokens))}
    # the book's tree has no leaf for some answers: that word stays unnamed
    walked = [walker.walk(answers[token["id"]]) for token in bases]
    named = [found.role if found else None for found in walked]
    # a particle with a مجرور under it is a حرف جر: the one name, for card and picture
    for index, token in enumerate(bases):
        if token["pos"] == "PRT" and any(
                named[j] == NAMED.majroor for j, kid in enumerate(bases) if kid["head"] == token["id"]):
            named[index] = NAMED.harf_jarr
    # the parser's tense goes with a فعل, so a card CAMeL took for a noun (ضُرِبَ) still says ماضٍ
    return [{"role": role, "case": _ending(role, token, bases[i - 1] if i else None,
                                           words[i + 1] if i + 1 < len(words) else ""),
             "aspect": token.get("asp") if role == NAMED.fil else None,
             "book": book_path(found.path, found.book) if found else None}
            for i, (role, token, found) in enumerate(zip(named, bases, walked))]


def opens_with_verb(roles: list[str | None]) -> bool:
    """Verbal unless a مبتدأ (or the اسم of إنّ) comes before the first verb. A particle,
    a fronted adverb or a fronted object leaves it verbal (لم يكتب، متى سافر، القرآنَ قرأ):
    the book judges a sentence by the word it rests on, not the one put first."""
    for role in roles:
        if role == NAMED.fil:
            return True
        if role in (NAMED.mubtada, NAMED.ism_inna, NAMED.khabar):
            return False
    return False


def _ending(role: str | None, token: dict, before: dict | None, after: str) -> str | None:
    """What to print under the word: a case for a noun or a present verb, else mabni."""
    if role == NAMED.fil:
        # not bare_letters: it folds the أ of أَجْلِسُ into an alef
        present = strip_diacritics(token["typed"])[:1] in PRESENT_PREFIX and token.get("asp") == "i"
        return _mood(paused(token["typed"], after), before) if present else "mabni"
    if role in (NAMED.harf, NAMED.harf_jarr):
        return "mabni"
    # يَا وَلَدُ، يا أيها: a single called noun is built on the damma (in the place of nasb)
    if role == NAMED.munada and (typed_case(token["typed"]) == "u" or facts.is_called_noun(token)):
        return "mabni"
    # a question word, a demonstrative, a relative or a pronoun never changes its
    # ending, so the vowel on it is part of the word and not a case
    if is_mabni(token):
        return "mabni"
    return CASE_NAME.get(facts.typed_case_of(token))


def _mood(typed: str, before: dict | None) -> str:
    """A present verb's case: the ending the reader typed, else the particle straight
    before it when the book's list says that particle settles it (لم يكتب، لن يذهب),
    else raf'. `typed` is the word as paused on (vowels.paused)."""
    last = letters(typed)[-1][1] if letters(typed) else set()
    shown = typed_case(typed)
    if SUKUN in last:
        return "jazm"
    if shown in ("u", "a"):
        return CASE_NAME[shown]
    particle = strip_diacritics(before["typed"]) if before else ""
    for family, case in (("jazm", "jazm"), ("nasb_mudari", "nasb")):
        if is_one(particle, family, "before_a_present_verb"):
            return case
    return "raf'"
