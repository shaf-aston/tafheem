"""Repair 4: a verb hung on يا is the call's answer, not a second called noun."""
from __future__ import annotations

from backend.services.nahw_book import is_one
from backend.services.syntax.facts import is_verb


def called(tokens: list[dict]) -> None:
    """يَا فَاطِمَةُ اجْلِسِي: the parser may hang the command on يا beside the called noun;
    only a noun is called (Tasheel 3.6), so the verb stands as a sentence of its own.
    Written over before the words are read."""
    by_id = {t["id"]: t for t in tokens}
    for token in tokens:
        head = by_id.get(token["head"])
        if (head and head["pos"] == "PRT" and is_one(head["lemma"], "nida")
                and "interrog" not in head.get("pos_camel", "") and is_verb(token)):
            token["head"], token["rel"] = 0, "---"
