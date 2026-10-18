"""Words of one kind side by side, counted and tied to the word they follow."""
from __future__ import annotations

from backend.services.nahw_book import teacher_rules
from backend.services.syntax.naming import NAMED


def counted(cards: list[dict], roles: list[dict]) -> None:
    """Objects or khabars side by side, with no و between: the books count them
    (ظننتُ الامتحانَ سهلًا: مفعول به أول، مفعول به ثانٍ؛ إن الله غفور رحيم: خبر ثانٍ؛ a third is ثالث)."""
    ordinals = teacher_rules()["case_said"]["ordinals"]
    run = 0  # how many of this role came straight before
    for before, card in zip(cards, cards[1:]):
        role = card.get("role")
        if not role or role != before.get("role") or not (role == "مفعول به" or role.startswith("خبر")):
            run = 0
            continue
        run += 1
        said = f"لأنه {role}"

        def count(nth: str) -> str:  # خبر إن → خبر ثانٍ لإن، مفعول به → مفعول به ثانٍ
            return f"لأنه خبر {nth} ل{role[4:]}" if role.startswith("خبر ") else f"{said} {nth}"
        def bare(reason: str) -> bool:  # said, and not already counted (ظنّ names its own أول and ثانٍ)
            return said in reason and not any(f"{said} {nth}" in reason for nth in ordinals)
        if run == 1 and bare(before.get("reason", "")):
            before["reason"] = before["reason"].replace(said, count(ordinals[0]), 1)
        if bare(card.get("reason", "")):
            card["reason"] = card["reason"].replace(said, count(ordinals[min(run, len(ordinals) - 1)]), 1)


def followed(cards: list[dict], roles: list[dict]) -> None:
    """A follower names the word it follows (تابع لـ«زيدٌ»). Every معطوف of a chain is joined on
    its first word, the معطوف عليه, which says it is one; several on one word are counted
    (جاء زيدٌ وعمرٌو وبكرٌ: وعمرٌو معطوف أول على زيد، وبكرٌ معطوف ثانٍ)."""
    said = teacher_rules()["case_said"]
    atf = NAMED.matoof

    def root(i: int) -> int:
        seen = {i}
        while cards[i].get("role") == atf and isinstance(at := cards[i].get("follows"), int) \
                and 0 <= at < len(cards) and at not in seen:
            seen.add(i := at)
        return i

    joined: dict[int, list[int]] = {}
    for i, card in enumerate(cards):
        if card.get("role") == atf and isinstance(card.get("follows"), int):
            joined.setdefault(root(i), []).append(i)
    for i, card in enumerate(cards):
        at = card.get("follows")
        if not isinstance(at, int) or not 0 <= at < len(cards) or not card.get("reason"):
            continue
        on = root(i) if card.get("role") == atf else at
        card["reason"] = card["reason"].replace(said["before"], said["followed"].format(word=cards[on]["word"]), 1)
        if card.get("role") == atf and len(joined.get(on, [])) > 1:
            nth = said["ordinals"][min(joined[on].index(i), len(said["ordinals"]) - 1)]
            card["reason"] = card["reason"].replace(f"لأنه {atf}", f"لأنه {atf} {nth}", 1)
    for on in joined:
        if cards[on].get("reason") and said["joined_on"] not in cards[on]["reason"]:
            first, dot, rule = cards[on]["reason"].partition(". ")
            cards[on]["reason"] = f"{first}، {said['joined_on']}{dot}{rule}"
