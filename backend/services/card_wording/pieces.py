"""What a piece written onto the word does to its card: a family line, a زائدة باء, a كافة ما."""
from __future__ import annotations

from backend.services.nahw_book import book_map, family_cards


def pieces(cards: list[dict], roles: list[dict]) -> None:
    """A piece written onto the word that its family card says on the word's own card first
    (وَاللهُ: الواو حرف عطف، ويجوز أن تكون استئنافية), where the picture names it short."""
    said = dict(family_cards())
    for card, found in zip(cards, roles):
        for piece in found.get("attached", []):
            line = said.get((piece.get("reading") or {}).get("family"), {}).get("said")
            if line:
                card["reason"] = f"{line}، {card['reason']}"


def extra_ba(cards: list[dict], roles: list[dict]) -> None:
    """كفى بالله شهيدًا: the card says the باء is زائدة, and the word is مجرور in its letters and
    in its place's case (data: closed_words extra_ba), before the rule its place follows."""
    for card, found in zip(cards, roles):
        if not (place := found.get("extra_ba")):
            continue
        said = book_map("extra_ba", "said").format(place=book_map("extra_ba", "place_said")[place])
        rule = card.get("reason", "").partition(". ")[2]
        card.update(case="jarr", reason=f"الباء {book_map('extra_ba', 'named')}، {said} لأنه {card.get('name') or card['role']}"
                    + (f". {rule}" if rule else ""))


def kaffa(cards: list[dict], roles: list[dict]) -> None:
    """إنما الأعمال بالنيات: an إن-family word with ما written onto it works on nothing, and the
    card names the pair (data: closed_words inna `kaffa`; found by naming)."""
    rule = book_map("inna", "kaffa")
    for card, found in zip(cards, roles):
        if sister := found.get("kaffa"):
            card["name"] = rule["named"]
            card["reason"] = rule["said"].format(word=card["word"], bare=sister)
