"""A reading the typed harakat did not settle, said on its card: the verb says it was read active
(or passive) because no harakat were typed and what the other reading would make of the noun
after it; that noun says its job rests on it. morphology.pick sets `assumed` on the verb's
reading; the words are teacher.json case_said.assumed."""
from __future__ import annotations

from backend.services.nahw.book import teacher_rules


def assumed(cards: list[dict], roles: list[dict]) -> None:
    said = teacher_rules()["case_said"]["assumed"]
    for card, found in zip(cards, roles):
        governor = found.get("governor")
        if not card.get("assumed") and governor is not None and card.get("role") in said["via_roles"] \
                and (cards[governor].get("assumed") or {}).get("vox"):
            card["assumed"] = {"via": governor}
    for card in cards:
        if not (guess := card.get("assumed")):
            continue
        line = said["via"] if "via" in guess else said["vox"][guess["vox"]]
        if "via" in guess:
            line = {key: text.format(word=cards[guess["via"]]["word"]) for key, text in line.items()}
        if reason := card.get("said"):
            reason.extras.append(line["ar"])
        card["notes"] = f"{card['notes']}. {line['en']}" if card.get("notes") else line["en"]
