"""Repair 3: ابن between two names is the first name's صفة and مضاف to the second."""
from __future__ import annotations

from backend.services.harakat import has_tanween
from backend.services.syntax.facts import listed


def _is_name(token: dict) -> bool:
    return token["pos"] == "PROP" or token.get("pos_camel") == "noun_prop"


def _under(token: dict, ancestor: dict, by_id: dict) -> bool:
    """`ancestor` is one of the words `token` hangs under."""
    while (token := by_id.get(token["head"])):
        if token is ancestor:
            return True
    return False


def nasab(bases: list[dict], tokens: list[dict]) -> None:
    """محمدُ بنُ عبدِ اللهِ: ابن or بنت between a name and the noun after it is the name's صفة,
    in its case, and مضاف to that noun (Tasheel 3.10.1): the three are one name, never a
    mubtada and its khabar, typed vowels or none. A name typed with tanween is complete,
    so ابن after it opens what is told of it (زيدٌ ابنُ عمرٍو) and is left to the parser.
    The name keeps its own place in the sentence, or the one the ابن held when the parser
    hung the name under it. Written over before the words are read."""
    by_id = {t["id"]: t for t in tokens}
    for name, son, after in zip(bases, bases[1:], bases[2:]):
        if not (_is_name(name) and listed(son, "nasab") and after["pos"] in ("NOM", "PROP")
                and not has_tanween(name.get("typed") or "")):
            continue
        # محمدُ بنُ عبدِ اللهِ بنِ عبدِ المطلبِ: the second ابن describes the whole name عبد الله,
        # so it hangs on that name's first word, the مضاف
        while name["rel"] == "IDF" and (head := by_id.get(name["head"])) and head["id"] < name["id"] \
                and not listed(head, "nasab"):
            name = head
        # climb the name out from under the ابن and its noun into the place they held
        while (over := next((w for w in (son, after) if _under(name, w, by_id)), None)):
            name["head"], name["rel"] = over["head"], over["rel"]
        son["head"], son["rel"] = name["id"], "MOD"
        after["head"], after["rel"] = son["id"], "IDF"
        son["mudaf"] = True
        _name_goes_on(after, bases, by_id)


def _name_goes_on(word: dict, bases: list[dict], by_id: dict) -> None:
    """عبدِ اللهِ، عبدِ المطلبِ: the father's name is itself a مضاف (CAMeL's construct state)
    and the noun after it its مضاف إليه, wherever the parser hung that noun (as a khabar)."""
    at = bases.index(word)
    while at + 1 < len(bases):
        nxt = bases[at + 1]
        if nxt["pos"] not in ("NOM", "PROP") or listed(nxt, "nasab") or _under(word, nxt, by_id):
            return
        # untyped, the reading may miss the construct state: a bare noun (no ال, no tanween)
        # before a name or a noun with ال is that noun's مضاف all the same
        bare = not word["form"].startswith("ال") and not has_tanween(word.get("typed") or "")
        if word.get("stt") != "c" and not (bare and (_is_name(nxt) or nxt.get("stt") == "d")):
            return
        nxt["head"], nxt["rel"] = word["id"], "IDF"
        word["mudaf"] = True
        word, at = nxt, at + 1
