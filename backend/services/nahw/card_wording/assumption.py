"""A reading the typed harakat did not settle, said on its card: the verb says it was read active
(or passive) because no harakat were typed; a word whose job is another in the second reading
(iraab._rivalled sets `assumed` on its tag) says what it would be, and which word's other reading
makes it so. The words are teacher.json case_said.assumed."""
from __future__ import annotations

from backend.services.nahw.book import teacher_rules


def assumed(cards: list[dict], roles: list[dict]) -> None:
    said = teacher_rules()["case_said"]["assumed"]
    for card in cards:
        if not (guess := card.get("assumed")):
            continue
        line = said["vox"][guess["vox"]] if "vox" in guess else {
            key: text.format(other=guess["other"], word=cards[guess["if"]]["word"]) for key, text in said["other"].items()}
        if reason := card.get("said"):
            reason.extras.append(line["ar"])
        card["notes"] = f"{card['notes']}. {line['en']}" if card.get("notes") else line["en"]
