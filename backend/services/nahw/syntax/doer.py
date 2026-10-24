"""The doer every verb has when no typed word is it (Tasheel: الضمير المستتر والمتصل): the
pronoun hidden in the verb (اقبلْ: أنت) or written onto it (كنتَ: the تاء), by CAMeL's person,
gender and number. Read in data/nahw_rules/roles.json `frames.doer`.

Pure, token-level: naming records it on the word's entry (`doer`) and the picture draws the same
record, so the card and the bracket never name the doer apart."""
from __future__ import annotations

from backend.services.text.arabic_text import strip_diacritics
from backend.services.text.harakat import five_verb_nun
from backend.services.nahw.book import frames, verb_aspect
from backend.services.nahw.syntax.facts import is_passive
from backend.services.nahw.syntax.naming import tone

DOER = frames()["doer"]


def person_key(token: dict) -> str:
    """CAMeL's person, gender and number as one key of DOER["pronoun"] (2ms, 1s)."""
    per = token.get("per", "na")
    return per + ("" if per == "1" else token.get("gen", "na")) + token.get("num", "na")


def persons(token: dict, owner: list[str] | None) -> list[str]:
    """Who a verb's doer may be: one person, or the two its letters allow (تكتبُ is you
    or she) narrowed by the subject its pronoun goes back to (`owner`)."""
    # اضربْ typed with a bare alif: the card's own test names it a command, so the doer says so too
    if verb_aspect(token.get("asp", ""), strip_diacritics(token.get("base", ""))) == "c" and token.get("per") != "2":
        return [DOER["command"]]  # a command speaks to the listener, whatever the reading said
    letter = strip_diacritics(token["base"])[:1]
    if token.get("asp") == "i" and letter in DOER["prefix_says"]:
        return [DOER["prefix_says"][letter]]
    if token.get("asp") == "i" and token.get("per", "na") not in DOER["prefix_person"].get(letter, token.get("per", "na")):
        return []  # the reading's person is not one its letter allows
    # تَكْتُبِينَ: the ياء is the doer (أنتِ), so the reading's own person stands, not the bare ت that is أنتَ or هي
    if token.get("asp") == "i" and token.get("num") == "s" and letter == "ت" and not five_verb_nun(token.get("typed") or "", token.get("stuck_on", 0), token.get("weak_last")):
        both = DOER["ta_prefix"]
        # the subject's person settles it: a ت said of a third person is هي (هِنْدٌ تَكْتُبُ)
        return [key for key in both if key[0] in {o[0] for o in owner or []}] or both
    return [person_key(token)]


def doer(token: dict, family: str | None, persons: list[str]) -> dict | None:
    """The doer inside a verb no typed word stands as (اقبلْ: أنت, كنتَ: the تاء);
    None when the person is not known. `hidden` says whether it is unseen in the verb
    (مستتر) or written onto it (متصل); `pronoun` the pronoun it is."""
    pronouns = [DOER["pronoun"].get(key) for key in persons]
    if token.get("asp") not in DOER["hidden"] or not pronouns or not all(pronouns):
        return None
    name = DOER["by_family"].get(family) or DOER["passive" if is_passive(token) else "active"]
    hidden = persons[0] in DOER["hidden"][token["asp"]]
    said = DOER["hidden_said_by_family"].get(family, DOER["hidden_said"]) if hidden else DOER["attached_said"]
    pronoun = pronouns[0] if len(pronouns) == 1 else DOER["either"].format(one=pronouns[0], other=pronouns[1])
    return {"role": name, "tone": tone(name), "detail": said.format(pronoun=pronoun), "pronoun": pronoun, "hidden": hidden}
