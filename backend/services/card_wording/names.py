"""Names the picture or the governor gives a word, written onto its card after the sign is settled."""
from __future__ import annotations

from backend.services.nahw_book import reason
from backend.services.syntax import teacher
from backend.services.syntax.naming import NAMED


def pair(cards: list[dict], roles: list[dict]) -> None:
    """لا رجلَ: its governor names the pair (اسم لا، خبر لا)."""
    for card, found in zip(cards, roles):
        if card.get("role") in found.get("pair", {}):
            card["role"] = found["pair"][card["role"]]
            card["reason"] = reason(card["role"])


def printed(cards: list[dict], roles: list[dict]) -> None:
    """أُمِرْتُ: فعل مجهول; its reason already says مبني للمجهول."""
    for card, found in zip(cards, roles):
        if found.get("printed") and card.get("role") == NAMED.fil:
            card["role"] = found["printed"]


def sister(cards: list[dict], roles: list[dict]) -> None:
    """اسم ليس: the reason names the sister the picture names, not the family's mother (لأنه اسم كان)."""
    for card, found in zip(cards, roles):
        if (name := found.get("name")) and card.get("role") and name.split()[0] == card["role"].split()[0]:
            card["reason"] = (card.get("reason") or "").replace(f"لأنه {card['role']}", f"لأنه {name}", 1)


def tool(cards: list[dict], roles: list[dict]) -> None:
    """غير، سوى: the excepted noun is the tool itself, and says so, not إلا's rule."""
    for card in cards:
        if said := teacher.tool_reason(card):
            card["reason"] = said


def also(cards: list[dict], roles: list[dict]) -> None:
    """A second thing the book says of the word, after its reason."""
    for card, found in zip(cards, roles):
        if found.get("also") and card.get("reason"):
            card["reason"] = f"{card['reason']}، {found['also']}"
