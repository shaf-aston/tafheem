"""مَنْ فِي البيتِ: an opening مَنْ with no verb to be the صلة of asks a question.

The analyser often reads it as the relative; a relative needs its صلة, and with no verb
in the sentence a jar-majroor or ظرف after it is told of it, so it is the question word,
the مبتدأ (Tasheel, أسماء الاستفهام)."""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics
from backend.services.syntax.facts import is_verb


def asked_man(bases: list[dict], tokens: list[dict]) -> None:
    if not bases or any(is_verb(t) for t in tokens):
        return
    first = bases[0]
    if first.get("pos_camel") == "pron_rel" and strip_diacritics(first["form"]) == "من" and first["head"] == 0:
        first["pos_camel"] = "pron_interrog"
