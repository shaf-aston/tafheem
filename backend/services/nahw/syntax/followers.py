"""التوابع: the صفة, معطوف, توكيد and بدل, in one place.

A follower takes its case from the word it follows, every other noun from a governor
(Tasheel 3.10 p88). Which follower a word is stays a question the evidence answers
(`facts.follows`); this module owns what comes of that answer:

    FOLLOWERS            the roles that are followers
    followed()           the typed word a follower follows, past the و of a معطوف
    chain_first()        the first word of a chain of معطوفات, the معطوف عليه
    take_their_ending()  each follower wears the case of the word it follows

naming, teacher, tree and card_wording all ask here, so a card, a check and the picture
cannot each find a different word a follower follows.
"""
from __future__ import annotations

from collections.abc import Callable, Hashable
from typing import TypeVar

from backend.services.nahw.book import is_one, is_subject_pronoun, named_roles, roles_keyed
from backend.services.nahw.syntax import facts

FOLLOWERS = roles_keyed("tabi", "sifah")
NAMED = named_roles()
# a صفة or a توكيد is never itself described or stressed: a word linked onto one follows that one's noun
# (إِنَّ اللَّهَ غَفُورٌ لِعِبَادِهِ الْمُؤْمِنِينَ التَّائِبِينَ: both are صفة of عباده); a معطوف or a بدل is a noun of its own
LEANING = tuple(role for role in FOLLOWERS if role not in (NAMED.matoof, NAMED.badal))

Key = TypeVar("Key", bound=Hashable)


def followed(token: dict, bases: list[dict], tokens: list[dict], named: list | None = None) -> int | None:
    """The typed word a follower follows, reached through the و of a معطوف: a particle is climbed past,
    never أيها, the called noun tagged one (يا أيها الذين آمنوا: الذين follows أيّ).

    Given the roles (`named`), a صفة, توكيد or بدل is held to what a تابع can follow (Tasheel 3.10)
    rather than wherever the parser hung it: a noun, never a verb; never a صفة or توكيد (`LEANING`);
    and the noun whose case it wears (`_matboo`). A معطوف follows the word before its و as linked."""
    at = {t["id"]: i for i, t in enumerate(bases)}
    by_id = {t["id"]: t for t in tokens}
    head = by_id.get(token["head"])
    while head and (head["id"] not in at or facts.is_particle(head)):
        head = by_id.get(head["head"])
    if head is None:
        return None
    i = at.get(token["id"])
    if named is None or i is None or named[i] not in LEANING + (NAMED.badal,):
        return at[head["id"]]
    return _matboo(i, at[head["id"]], bases, tokens, named)


def _matboo(i: int, on: int, bases: list[dict], tokens: list[dict], named: list) -> int:
    """The noun the صفة/توكيد/بدل at `i`, linked onto the word at `on`, follows."""
    token = bases[i]
    # ما جاء أحدٌ من الضيوف إلا زيدٌ: a بدل after إلا follows the noun it is excepted from (Tasheel 3.8.7)
    illa = next((t for t in tokens if t["id"] == token["id"] - 1), None)
    if illa and illa["pos"] == "PRT" and facts.read_as(illa, "istithna") \
            and (excepted := facts.excepted_from(illa, facts.Sentence(tokens))):
        return next((n for n, base in enumerate(bases) if base["id"] == excepted["id"]), on)
    # قرأتُ الكتابَ نصفَه، أعجبني المعلمُ علمُه: hung on the verb, it follows the noun straight before it;
    # a detached pronoun there (ذهبتُ أنا) repeats the doer the verb holds, so it stays on the verb
    if facts.is_verb(bases[on]) and not is_subject_pronoun(token) and i \
            and facts.noun_tagged(bases[i - 1]) and not facts.is_verb(bases[i - 1]):
        on = i - 1
    mine, seen = facts.shown_cases(token), {i}
    while on not in seen:
        seen.add(on)
        word = bases[on]
        if named[on] in LEANING:
            # نجح الطالبان المجتهدان كلاهما: the توكيد stresses الطالبان, not the صفة it was hung on; but the noun a
            # pointer points at (هذا البستانُ الجميلُ) is a noun, named صفة of the pointer, and is itself described
            up = followed(word, bases, tokens, named)
            up = None if up is not None and "dem" in bases[up].get("pos_camel", "") else up
        elif named[on] == NAMED.mudaf_ilayh and mine and not mine & facts.shown_cases(word):
            # مدرسةُ البلدِ الكبيرةُ: wearing its مضاف's case, not the مضاف إليه's, it describes the مضاف
            up = followed(word, bases, tokens)
            up = up if up is not None and mine & facts.shown_cases(bases[up]) else None
        else:
            break
        if up is None:
            break
        on = up
    return on


def chain_first(start: Key, joined_on: Callable[[Key], Key | None]) -> Key:
    """The first word of a chain of معطوفات (وَإِقَامِ الصَّلَاةِ وَإِيتَاءِ الزَّكَاةِ وَالْحَجِّ): each معطوف is joined
    on the one before it, so the chain is climbed until a word joined on nothing. `joined_on` gives the
    word a معطوف is joined on, or None for any other word; whatever the words are (token ids, card
    places), a chain that loops back stops at the word it would meet again."""
    seen = {start}
    while (up := joined_on(start)) is not None and up not in seen:
        seen.add(start := up)
    return start


def take_their_ending(named: list, cases: list, bases: list[dict], tokens: list[dict]) -> None:
    """In order, so a chain follows too. A follower with no vowel typed wears the case of the word it follows
    (اليدُ العليا); its kasra on ـات is also nasb, a diptote's fatha also jarr. A present verb showing nothing,
    joined (atf `joins_mood`) to a verb in nasb or jazm, is in that mood too (أَنْ تَبَرُّوا وَتَتَّقُوا); any other is raf'."""
    for i, (role, token) in enumerate(zip(named, bases)):
        head = followed(token, bases, tokens, named) if role in FOLLOWERS else None
        if head is not None and cases[head] != "mabni" and (cases[i] is None or (cases[head] == "nasb" and facts.shows_nasb_by_kasra(token))
                                                             or (cases[head] == "jarr" and facts.shows_jarr(token))):
            cases[i] = cases[head]
    by_id = {t["id"]: t for t in tokens}
    for i, (role, token) in enumerate(zip(named, bases)):  # the verbs after every noun, as they were two passes
        if role == NAMED.fil and cases[i] is None:
            joiner = by_id.get(token["head"])
            head = followed(token, bases, tokens) if joiner and joiner["pos"] == "PRT" and is_one(joiner["lemma"], "atf", "joins_mood") else None
            cases[i] = cases[head] if head is not None and named[head] == NAMED.fil and cases[head] in ("nasb", "jazm") else "raf'"
