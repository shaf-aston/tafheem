"""Repair 5: khabars the parser hung elsewhere: a second adjective khabar, and a لا clause after its mubtada."""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics
from backend.services.syntax.facts import is_participle, is_verb, typed_or_parsed_case, subject_link


def second_khabar(tokens: list[dict]) -> None:
    """إِنَّ اللَّهَ كَانَ عَلِيمًا حَكِيمًا، زيدٌ ذكيٌّ مجتهدٌ: a describing word describes a noun, not
    another describing word, so the second, in the first's case, is a khabar of its own
    (تعدد الخبر). A noun khabar keeps its صفة (زيدٌ طالبٌ مجتهدٌ).
    Written over before the words are read."""
    by_id = {t["id"]: t for t in tokens}
    for token in tokens:
        head = by_id.get(token["head"])
        if (head and token["rel"] == "MOD" and head["rel"] == "PRD" and head["id"] == token["id"] - 1
                and is_participle(head) and is_participle(token) and token.get("stt") == head.get("stt") == "i"
                and typed_or_parsed_case(token) == typed_or_parsed_case(head)):
            token["head"], token["rel"] = head["head"], "PRD"


def before_la(tokens: list[dict]) -> None:
    """ذَلِكَ الْكِتَابُ لَا رَيْبَ فِيهِ: the noun of لا النافية للجنس stands after it, so a noun
    the parser hung on لا from before it is the mubtada, and the لا clause its khabar.
    Written over before the words are read."""
    by_id = {t["id"]: t for t in tokens}
    for token in tokens:
        la = by_id.get(token["head"])
        if (la and la["pos"] == "PRT" and strip_diacritics(la["form"]) == "لا" and token["id"] < la["id"]
                and subject_link(token) and la["head"] == 0):
            token["head"], token["rel"] = 0, "---"
            la["head"], la["rel"] = token["id"], "PRD"


def after_pointer(tokens: list[dict]) -> None:
    """هَاتَانِ قِلَادَتَانِ، زَيْدٌ ضَارِبٌ: a نعت matches its noun in being definite (هذا الكتابُ،
    زيدٌ الكريمُ), so an indefinite noun or adjective the parser hung as the صفة of a definite
    word that opens the sentence (a pointer, a name, a word with ال) is the khabar, that word its mubtada.
    Written over before the words are read."""
    by_id = {t["id"]: t for t in tokens}
    for token in tokens:
        head = by_id.get(token["head"])
        if (head and head["head"] == 0 and head["pos"] in ("NOM", "PROP") and not is_verb(head) and token["rel"] == "MOD"
                and (head.get("pos_camel") in ("pron_dem", "noun_prop") or head.get("stt") == "d")
                and token["id"] > head["id"] and token.get("pos_camel") in ("noun", "adj")
                and _indefinite(token, tokens)
                and not any(t["head"] == head["id"] and t["rel"] in ("PRD", "SBJ") for t in tokens)):
            token["head"], token["rel"] = 0, "---"
            head["head"], head["rel"] = token["id"], "SBJ"


def _indefinite(token: dict, tokens: list[dict]) -> bool:
    """Without ال: read so, or read as a مضاف with nothing added to it (الملاحون أقوياء), which it then is not."""
    return token.get("stt") == "i" or (token.get("stt") == "c" and not any(
        t["head"] == token["id"] and t["rel"] == "IDF" for t in tokens))
