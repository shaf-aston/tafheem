"""Repair 5: khabars the parser hung elsewhere: a second adjective khabar, and a لا clause after its mubtada."""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics
from backend.services.syntax.facts import is_participle, typed_or_parsed_case, subject_link


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
    """هَاتَانِ قِلَادَتَانِ: what describes or stands for a pointing word carries ال (هذا الكتابُ),
    so an indefinite noun the parser hung on one as its صفة is the khabar, the pointer its mubtada.
    Written over before the words are read."""
    by_id = {t["id"]: t for t in tokens}
    for token in tokens:
        pointer = by_id.get(token["head"])
        if (pointer and pointer.get("pos_camel") == "pron_dem" and pointer["head"] == 0 and token["rel"] == "MOD"
                and token["id"] > pointer["id"] and token["pos"] == "NOM" and token.get("stt") == "i"):
            token["head"], token["rel"] = 0, "---"
            pointer["head"], pointer["rel"] = token["id"], "SBJ"
