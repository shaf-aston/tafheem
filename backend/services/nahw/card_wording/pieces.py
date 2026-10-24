"""What a piece written onto the word does to its card: a family line, a زائدة باء, a كافة ما."""
from __future__ import annotations

from backend.services.nahw.card_wording.reason import Reason
from backend.services.nahw.syntax.facts import reading
from backend.services.nahw.book import case_of, extra_ba_named, extra_ba_said, family_cards, kaffa_card, teacher_rules


def pieces(cards: list[dict], roles: list[dict]) -> None:
    """A piece written onto the word that its family card says on the word's own card first
    (وَاللهُ: الواو حرف عطف، ويجوز أن تكون استئنافية), where the picture names it short."""
    said = dict(family_cards())
    for card, found in zip(cards, roles):
        for piece in found.get("attached", []):
            line = said.get(reading(piece), {}).get("said")
            if line and (reason := card.get("said")):
                reason.front.insert(0, line)  # the last piece written is said first


def doer(cards: list[dict], roles: list[dict]) -> None:
    """كَتَبَ، كَتَبْتُ، زَارَنَا: a verb's card says the doer the picture draws inside it (hidden, or a
    pronoun written onto it), and any pronoun written onto the word with a job of its own
    (the نا that is زارنا's object), each with its place (data: teacher.json doer_said, piece_said)."""
    said = teacher_rules()["case_said"]
    for card, found in zip(cards, roles):
        if not (reason := card.get("said")):
            continue
        if (drawn := found.get("doer")) and (line := said["doer_said"].get(drawn["role"])):
            reason.extras.append(line.format(detail=drawn["detail"]))
        for piece in found.get("attached", []):
            if not piece["before"] and piece.get("role") and (place := case_of(piece["role"])):
                reason.extras.append(said["piece_said"].format(form=piece["form"], place=said["place"][place], role=piece["role"]))


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
