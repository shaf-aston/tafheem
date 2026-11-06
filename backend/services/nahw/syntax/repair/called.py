"""Repair 4: a verb hung on يا, or a command on the noun called, is the call's answer, not a called noun or its صفة."""
from __future__ import annotations

from backend.services.nahw.book import is_one
from backend.services.nahw.syntax.facts import Sentence, calling_head, is_describing, is_verb, noun_tagged, typed_case_of, typed_tanween


def called(s: Sentence) -> None:
    """يَا فَاطِمَةُ اجْلِسِي: the parser may hang the command on يا beside the called noun;
    only a noun is called (Tasheel 3.6), so the verb stands as a sentence of its own.
    رَبِّ اغْفِرْ لِي: hung on the called noun itself it reads as its صفة, but a command is
    never one (Ibn Aqil V3 p198: لا تقع الجملة الطلبية صفة), so it stands alone too."""
    tokens = s.tokens
    for token in tokens:
        head = s.head(token)
        if not (head and is_verb(token)):
            continue
        on_ya = head["pos"] == "PRT" and is_one(head["lemma"], "nida") and "interrog" not in head.get("pos_camel", "")
        on_called = token.get("asp") == "c" and head["pos"] != "PRT" and calling_head(head, s) == "nida"
        if on_ya or on_called:
            s.relink(token, 0, "---")


def called_annexes(s: Sentence) -> None:
    """يَا عَبْدَ اللَّهِ اجْتَهِدْ typed bare: a noun the parser left without a link straight after the called
    noun is its مضاف إليه when the called noun shows no damma or tanween, which a called noun built on its
    own sound would (Tasheel 3.6: the called noun is built on damma, or is a مضاف and in nasb); a describing
    word after it is a صفة instead."""
    tokens = s.tokens
    for token in tokens:
        head = s.head(token)
        if (token["rel"] == "---" and head and head["id"] == token["id"] - 1 and noun_tagged(token)
                and not is_describing(token) and calling_head(head, s) == "nida"
                and typed_case_of(head) is None and not typed_tanween(head)):
            token["rel"] = "IDF"
