"""A condition's parts on their cards: فعل الشرط and جواب الشرط, each in jazm or in the place its
opener gives it when built (كُنْتَ), with the letter that ties the answer to it (فاقبلها، لأمرتُ);
a conditional noun named for its place (مبتدأ) says what it is first; لولا's noun says its
khabar is left out. Found by syntax.condition (the entry's `condition`); worded here, on the
reason's parts, after the sign is settled (data: teacher.json case_said.condition)."""
from __future__ import annotations

from backend.services.nahw_book import frames, teacher_rules


def condition(cards: list[dict], roles: list[dict]) -> None:
    said = teacher_rules()["case_said"]["condition"]
    for card, found in zip(cards, roles):
        part = found.get("condition") or {}
        reason = card.get("said")
        if not part or not reason:
            continue
        if part.get("kind") and card.get("role") != part["kind"]:
            reason.front.insert(0, part["kind"])  # مَنْ: اسم شرط جازم، مبني في محل رفع لأنه مبتدأ
        if part.get("part") == "subject" and (left := said["by_family"][part["family"]].get("subject")):
            reason.extras.append(left)  # لولا زيدٌ: وخبره محذوف وجوبًا
            continue
        if part.get("part") not in ("verb", "answer") or card.get("type") != "fi'l":
            continue
        own = said["by_family"][part["family"]]
        # إذا: the condition's clause is its مضاف إليه, the answer's has no place
        place = own["place"][part["part"]] if isinstance(own["place"], dict) else own["place"]
        # فَلْيَصُمْهُ: tied by its letter, the answer is a sentence standing in the place of jazm
        where = said["jazm"] if card.get("case") == "jazm" and not part["tie"] else place
        name = part.get("named") or frames()["condition"][part["part"]]  # جواب لولا, else فعل الشرط / جواب الشرط
        if part["tie"]:
            reason.extras.append(own["ties"][part["tie"]])
        reason.extras.append(where.format(part=said["is"].format(name=name)))
        card.setdefault("name", None)
        card["name"] = card["name"] or name  # the card prints the part, as the picture does (فعل مجهول keeps its own)
