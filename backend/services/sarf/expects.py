"""The word class a governor wants after it: a verb after لم، لن، هل، سوف، a relative ...
(data/nahw_rules/expects.json, each rule with its source). morphology.pick asks, and takes a
verb reading for the word after only where the typed vowels fit it as well as the reading kept."""
from __future__ import annotations

from functools import lru_cache

from backend.services.nahw.book import book_file, book_spelling, book_words


@lru_cache(maxsize=None)
def _rules() -> list[dict]:
    rules = book_file("expects.json")["rules"]
    if bad := [rule["name"] for rule in rules if rule["next"] != "verb"]:
        raise ValueError(f"expects.json: only `verb` can be expected next, not in {bad}")
    return rules


# The letters a reading's proclitics write before the governor (CAMeL prc3, prc2): the question hamza and the
# joining و/ف. They change nothing the governor asks for, so فَلَمْ، وَلَنْ، أَلَمْ، فَسَوْفَ are looked up as لم، لن، سوف
_JOINED = (("prc3", "_ques", "أ"), ("prc2", "_conj", "وف"))


def _governor(token: str, reading: dict) -> str:
    """The word before as the book lists it: its typed letters less the question hamza and the joining و/ف its reading has."""
    spelled = book_spelling(token)
    for field, kind, letters in _JOINED:
        if str(reading.get(field, "")).endswith(kind) and len(spelled) > 1 and spelled[0] in letters:
            spelled = spelled[1:]
    return spelled


def _follows(after: dict, token: str, reading: dict) -> bool:
    """The word before is one the rule names: on its list or among its words (typed letters), or read as it says."""
    spelled = _governor(token, reading)
    return ("family" in after and spelled in book_words(after["family"], after["part"]) and spelled not in after.get("except", ())
            or spelled in after.get("words", ())
            or "pos" in after and reading.get("pos") == after["pos"]
            or "enc0_ends" in after and str(reading.get("enc0", "")).endswith(after["enc0_ends"]))


def verb_after(tokens: list[str], readings: list[dict], i: int) -> str | None:
    """The name of the rule that wants a verb at word i, from the word before it; None when none does."""
    return next((rule["name"] for rule in _rules()
                 if _follows(rule["after"], tokens[i - 1], readings[i - 1]) and not (rule.get("not_first") and i < 2)), None)


def only_verb(tokens: list[str], readings: list[dict], i: int) -> bool:
    """Word i follows a governor no noun can follow (لم، لن، سوف: «لأن الاسم لا يقع بعدها»), so it is a verb whatever else fits."""
    name = verb_after(tokens, readings, i)
    return any(rule["name"] == name and rule.get("only") for rule in _rules())
