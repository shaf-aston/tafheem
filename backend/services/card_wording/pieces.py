"""What a piece written onto the word does to its card: a family line, a زائدة باء, a كافة ما."""
from __future__ import annotations

from backend.services.card_wording.reason import Reason
from backend.services.nahw_book import extra_ba_named, extra_ba_said, family_cards, kaffa_card


def pieces(cards: list[dict], roles: list[dict]) -> None:
    """A piece written onto the word that its family card says on the word's own card first
    (وَاللهُ: الواو حرف عطف، ويجوز أن تكون استئنافية), where the picture names it short."""
    said = dict(family_cards())
    for card, found in zip(cards, roles):
        for piece in found.get("attached", []):
            line = said.get((piece.get("reading") or {}).get("family"), {}).get("said")
            if line and (reason := card.get("said")):
                reason.front.insert(0, line)  # the last piece written is said first


def extra_ba(cards: list[dict], roles: list[dict]) -> None:
    """كفى بالله شهيدًا: the card says the باء is زائدة, and the word is مجرور in its letters and
    in its place's case (data: closed_words extra_ba), before the rule its place follows."""
    for card, found in zip(cards, roles):
        if not (place := found.get("extra_ba")):
            continue
        if not (reason := card.get("said")):
            continue
        # the باء's own line takes the lead; the rule the place follows and anything after it stay
        reason.lead, reason.because, reason.front, reason.extras = \
            f"الباء {extra_ba_named()}، {extra_ba_said(place)} ", card.get("name") or card["role"], [], []
        card["case"] = "jarr"


def kaffa(cards: list[dict], roles: list[dict]) -> None:
    """إنما الأعمال بالنيات: an إن-family word with ما written onto it works on nothing, and the
    card names the pair (data: closed_words inna `kaffa`; found by naming)."""
    for card, found in zip(cards, roles):
        if sister := found.get("kaffa"):
            card["name"], said = kaffa_card(card["word"], sister)
            card["said"] = Reason.read(said)
