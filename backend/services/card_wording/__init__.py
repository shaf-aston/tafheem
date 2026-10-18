"""The one step that words each card after its sign is settled (iraab.cards).
Each pass reads naming's found entry for the word and rewrites only the card's role, name or
reason; they run in the order below, because a later one rewrites text an earlier one wrote:

    governor's pair name → passive name → sister's name → excepting noun → also → attached pieces
    → زائدة باء → كافة ما → counted → followed

A new grammar feature that changes a card's words is a pass here: naming finds it and leaves a
key on the found entry; the pass words it. Each pass takes (cards, roles), so it is tested
without the parser."""
from __future__ import annotations

from backend.services.card_wording import counting, names, pieces

PASSES = (names.pair, names.printed, names.sister, names.tool, names.also,
          pieces.pieces, pieces.extra_ba, pieces.kaffa, counting.counted, counting.followed)


def word(cards: list[dict], roles: list[dict]) -> None:
    for step in PASSES:
        step(cards, roles)
