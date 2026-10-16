"""Repair 3: ابن between two names is the first name's صفة and مضاف to the second."""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics
from backend.services.harakat import has_tanween, typed_case
from backend.services.syntax.facts import is_name, listed, noun_tagged
from backend.services.syntax.mask import above


def _under(token: dict, ancestor: dict, tokens: list[dict]) -> bool:
    """`ancestor` is one of the words `token` hangs under."""
    return above([t["head"] for t in tokens], token["head"], ancestor["id"])


def nasab(bases: list[dict], tokens: list[dict]) -> None:
    """محمدُ بنُ عبدِ اللهِ: ابن or بنت between a name and the noun after it is the name's صفة,
    in its case, and مضاف to that noun (Tasheel 3.10.1): the three are one name, never a
    mubtada and its khabar, typed vowels or none. A name typed with tanween is complete,
    so ابن after it opens what is told of it (زيدٌ ابنُ عمرٍو) and is left to the parser.
    The name keeps its own place in the sentence, or the one the ابن held when the parser
    hung the name under it. Written over before the words are read."""
    by_id = {t["id"]: t for t in tokens}
    for name, son, after in zip(bases, bases[1:], bases[2:]):
        if not (_names(name, son) and listed(son, "nasab") and noun_tagged(after)
                and not has_tanween(name.get("typed") or "")):
            continue
        # محمدُ بنُ عبدِ اللهِ بنِ عبدِ المطلبِ: the second ابن describes the whole name عبد الله,
        # so it hangs on that name's first word, the مضاف
        while name["rel"] == "IDF" and (head := by_id.get(name["head"])) and head["id"] < name["id"] \
                and not listed(head, "nasab"):
            name = head
        # climb the name out from under the ابن and its noun into the place they held
        while (over := next((w for w in (son, after) if _under(name, w, tokens)), None)):
            name["head"], name["rel"] = over["head"], over["rel"]
        son["head"], son["rel"] = name["id"], "MOD"
        after["head"], after["rel"] = son["id"], "IDF"
        son["mudaf"] = True
        _told_of(name, _name_goes_on(after, bases, tokens), bases, tokens)


def _names(word: dict, son: dict) -> bool:
    """A name, or a bare word before بن written without its alef: the alef drops only between
    two names, so عليُّ بنُ أبي طالبٍ is a name whatever the reading calls عليّ."""
    return is_name(word) or (_bare(word) and strip_diacritics(son.get("typed") or son["form"]) == "بن")


def _bare(word: dict) -> bool:
    """No ال and no tanween: nothing closes the word, so a noun after it can be its مضاف إليه."""
    return not word["form"].startswith("ال") and not has_tanween(word.get("typed") or "")


def _told_of(name: dict, end: dict, bases: list[dict], tokens: list[dict]) -> None:
    """محمدُ بنُ عبدِ اللهِ رسولُ اللهِ، عمرُ بنُ الخطابِ خليفةٌ: a full name opening a sentence
    with no verb is its mubtada and the noun straight after the name its khabar, however
    the parser hung it (as the name's صفة, or a root of its own)."""
    first, at = bases[0], bases.index(end) + 1
    if not (name is first or _under(name, first, tokens)) or at >= len(bases) \
            or any(t["pos"].startswith("VRB") for t in tokens) or any(t["head"] == first["id"] and t["rel"] == "PRD" for t in tokens):
        return
    khabar = bases[at]
    if not noun_tagged(khabar) or listed(khabar, "nasab"):
        return
    first["head"], first["rel"] = 0, "---"
    khabar["head"], khabar["rel"] = first["id"], "PRD"


def _name_goes_on(word: dict, bases: list[dict], tokens: list[dict]) -> dict:
    """عبدِ اللهِ، عبدِ المطلبِ: the father's name is itself a مضاف (CAMeL's construct state)
    and the noun after it its مضاف إليه, wherever the parser hung that noun (as a khabar).
    Returns the name's last word."""
    at = bases.index(word)
    while at + 1 < len(bases):
        nxt = bases[at + 1]
        if not noun_tagged(nxt) or listed(nxt, "nasab") or _under(word, nxt, tokens):
            return word
        # the reading may miss the construct state: a bare noun (no ال, no tanween) before a
        # name, a noun with ال, or a noun typed with kasra (أبي طالبٍ) is its مضاف all the same
        if word.get("stt") != "c" and not (_bare(word) and (is_name(nxt) or nxt.get("stt") == "d" or _typed_kasra(nxt))):
            return word
        nxt["head"], nxt["rel"] = word["id"], "IDF"
        word["mudaf"] = True
        word, at = nxt, at + 1
    return word


def _typed_kasra(word: dict) -> bool:
    """Typed with kasra: a mubtada's khabar never is, so the noun is the name's مضاف إليه."""
    return typed_case(word.get("typed") or "") == "i"
