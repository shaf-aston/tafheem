"""The one step that words each card after its sign is settled (iraab.cards).
Each pass reads naming's found entry for the word and rewrites only the card's role, name or
reason; they run in the order below, because a later one rewrites text an earlier one wrote:

    governor's pair name → passive name → sister's name → excepting noun → also → attached pieces
    → the doer and the pronouns written on → زائدة باء → كافة ما → counted → followed → condition

While they run, a card's reason is held as its parts (card["said"], a reason.Reason) and
written back once at the end, so no pass searches text another pass wrote.

A new grammar feature that changes a card's words is a pass here: naming finds it and leaves a
key on the found entry; the pass words it. Each pass takes (cards, roles), so it is tested
without the parser."""
from __future__ import annotations

from backend.services.card_wording import condition, counting, names, pieces
from backend.services.card_wording.reason import Reason

PASSES = (names.pair, names.printed, names.sister, names.tool, names.also,
          pieces.pieces, pieces.doer, pieces.extra_ba, pieces.kaffa, counting.counted, counting.followed,
          condition.condition)


def word(cards: list[dict], roles: list[dict]) -> None:
    run(PASSES, cards, roles)


def run(steps, cards: list[dict], roles: list[dict]) -> None:
    """These passes, in order, on the cards' reasons held as parts (a test runs one alone)."""
    for card in cards:
        if isinstance(card.get("reason"), str):
            card["said"] = Reason.read(card["reason"])
    for step in steps:
        step(cards, roles)
    for card in cards:
        if said := card.pop("said", None):
            card["reason"] = said.text()
