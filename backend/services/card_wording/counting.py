"""Words of one kind side by side, counted and tied to the word they follow."""
from __future__ import annotations

from backend.services.nahw_book import counted_name, teacher_rules
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

        def bare(card: dict) -> bool:  # said, and not already counted (ظنّ names its own أول and ثانٍ)
            said = card.get("said")
            return bool(said) and said.says(role) and not any(said.says(f"{role} {nth}") for nth in ordinals)
        if run == 1 and bare(before):
            before["said"].rename(role, counted_name(role, 0))
        if bare(card):
            card["said"].rename(role, counted_name(role, run))

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
        if not isinstance(at, int) or not 0 <= at < len(cards) or not (reason := card.get("said")):
            continue
        on = root(i) if card.get("role") == atf else at
        reason.swap(said["before"], said["followed"].format(word=cards[on]["word"]))
        if card.get("role") == atf and len(joined.get(on, [])) > 1:
            reason.rename(atf, f"{atf} {said['ordinals'][min(joined[on].index(i), len(said['ordinals']) - 1)]}")
    for on in joined:
        if (reason := cards[on].get("said")) and said["joined_on"] not in reason.text():
            reason.extras.append(said["joined_on"])
