"""Names the picture or the governor gives a word, written onto its card after the sign is settled."""
from __future__ import annotations

from backend.services.nahw.card_wording.reason import Reason
from backend.services.nahw.book import family_cards, reason
from backend.services.nahw.syntax import teacher
from backend.services.nahw.syntax.naming import NAMED


def pair(cards: list[dict], roles: list[dict]) -> None:
    """لا رجلَ: its governor names the pair (اسم لا، خبر لا); a noun built in the place
    of its case (signs.settle) says so, one with a مضاف إليه (لا طالبَ علمٍ) is منصوب."""
    for card, found in zip(cards, roles):
        if card.get("role") in found.get("pair", {}):
            card["role"] = found["pair"][card["role"]]
            card["said"] = Reason.read(reason(card["role"], mabni=bool(card.get("in_place"))))


def printed(cards: list[dict], roles: list[dict]) -> None:
    """أُمِرْتُ: فعل مجهول; its reason already says مبني للمجهول."""
    for card, found in zip(cards, roles):
        if found.get("printed") and card.get("role") == NAMED.fil:
            card["role"] = found["printed"]


def sister(cards: list[dict], roles: list[dict]) -> None:
    """اسم ليس: the reason names the sister the picture names, not the family's mother (لأنه اسم كان); a
    particle working as the family does tells its own rule (اسم ما: ما الحجازية تعمل عمل ليس)."""
    rule_as = {word: rule for _, family in family_cards() for word, rule in family.get("rule_as", {}).items()}
    for card, found in zip(cards, roles):
        if (name := found.get("name")) and (said := card.get("said")) and card.get("role") \
                and name.split()[0] == card["role"].split()[0]:
            said.rename(card["role"], name)
            if said.says(name) and said.rule and (rule := rule_as.get(name.split()[-1])):
                said.rule = rule


def tool(cards: list[dict], roles: list[dict]) -> None:
    """غير، سوى: the excepted noun is the tool itself, and says so, not إلا's rule."""
    for card in cards:
        if said := teacher.tool_reason(card):
            card["said"] = Reason.read(said)


def also(cards: list[dict], roles: list[dict]) -> None:
    """A second thing the book says of the word, after its reason."""
    for card, found in zip(cards, roles):
        if found.get("also") and (said := card.get("said")):
            said.tail.append(found["also"])
