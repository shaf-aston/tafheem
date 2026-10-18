"""Repair: صَاعًا شَعِيرًا، أَثْقَلُ وَزْنًا: an indefinite noun in nasb straight after what it measures
or compares tells what was meant, the تمييز (Tasheel, التمييز)."""
from __future__ import annotations

from backend.services.syntax.facts import indefinite_nasb


def measured(tokens: list[dict]) -> None:
    """A صفة describes, so it is an adjective; a indefinite noun the parser hung on another
    indefinite noun in nasb as its صفة names the thing measured. Written over before the words are read."""
    by_id = {t["id"]: t for t in tokens}
    for token in tokens:
        head = by_id.get(token["head"])
        if (head and token["rel"] == "MOD" and head["id"] == token["id"] - 1 and token.get("pos_camel") == "noun"
                and head.get("pos_camel") == "noun" and indefinite_nasb(token) and indefinite_nasb(head)):
            token["rel"] = "TMZ"
