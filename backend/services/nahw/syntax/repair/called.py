"""Repair 4: a verb hung on يا, or a command on the noun called, is the call's answer, not a called noun or its صفة."""
from __future__ import annotations

from backend.services.nahw.book import is_one
from backend.services.nahw.syntax.facts import Sentence, calling_head, is_verb


def called(tokens: list[dict]) -> None:
    """يَا فَاطِمَةُ اجْلِسِي: the parser may hang the command on يا beside the called noun;
    only a noun is called (Tasheel 3.6), so the verb stands as a sentence of its own.
    رَبِّ اغْفِرْ لِي: hung on the called noun itself it reads as its صفة, but a command is
    never one (Ibn Aqil V3 p198: لا تقع الجملة الطلبية صفة), so it stands alone too."""
    s = Sentence(tokens)
    for token in tokens:
        head = s.head(token)
        if not (head and is_verb(token)):
            continue
        on_ya = head["pos"] == "PRT" and is_one(head["lemma"], "nida") and "interrog" not in head.get("pos_camel", "")
        on_called = token.get("asp") == "c" and head["pos"] != "PRT" and calling_head(head, s) == "nida"
        if on_ya or on_called:
            token["head"], token["rel"] = 0, "---"
