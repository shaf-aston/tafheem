"""Who hangs inside whom: children, the roots, the مبتدأ beside its khabar, units that cannot keep the typed order."""
from __future__ import annotations

from backend.services.nahw.syntax.facts import is_preposition, is_verb, noun_tagged, reading
from backend.services.nahw.syntax.naming import NAMED
from backend.services.nahw.syntax.picture.hang import is_inside
from backend.services.nahw.syntax.picture.names import FRAMES
from backend.services.nahw.syntax.picture.state import Picture


def group_into_units(c: Picture) -> None:
    """Who hangs inside whom: children, the roots, the مبتدأ beside its khabar, units that cannot keep the typed order."""
    after_noun, at, by_id, columns, detail_of = c.after_noun, c.at, c.by_id, c.columns, c.detail_of
    drawn, job_of, role_of, tokens = c.drawn, c.job_of, c.role_of, c.tokens
    children_of: dict[int, list[dict]] = {token["id"]: [] for token in drawn}
    def depth(token: dict) -> int:
        steps, head = 0, token["head"]
        while head in by_id and steps < len(tokens):
            steps, head = steps + 1, by_id[head]["head"]
        return steps
    def parent(token: dict) -> int:
        # an attached و or بِ is not a word the reader typed apart, so a word hung
        # on one hangs on whatever that particle hung on
        head = token["head"]
        for _ in tokens:
            if head in children_of or head not in by_id:
                break
            head = by_id[head]["head"]
        return head
    unit_less = {t["id"] for t in drawn if reading(t) in FRAMES["unit_less"]}
    roots = []
    for token in drawn:
        up = parent(token)
        while up in unit_less:  # واللهُ أكبرُ: the و stands beside its sentence, heading nothing
            up = parent(by_id[up])
        # رِزْقُ اللَّهِ عَزَّ وَجَلَّ: a حال tells the state of its صاحب, it is no part of that noun, so it
        # stands beside it in the unit the noun stands in, not inside the noun's own box; nor inside
        # the jar-majroor of a مجرور صاحب (مَرَرْتُ بِزَيْدٍ رَاكِبًا: beside it, on the verb)
        if job_of[token["id"]] == NAMED.haal and up in by_id and noun_tagged(by_id[up]) and not is_verb(by_id[up]):
            detail_of[token["id"]] = after_noun["owner"].format(word=columns[at[up]])
            up = parent(by_id[up])
            while up in by_id and is_preposition(by_id[up]):
                up = parent(by_id[up])
        # a word drawn under a word already under it would close a loop (the moves above re-hang links)
        if up in children_of and up != token["id"] and not is_inside(by_id[up], token, children_of):
            children_of[up].append(token)
        else:
            roots.append(token)
    roots = roots or [drawn[0]]
    # هذا بيتٌ كبيرٌ: the مبتدأ is said of the whole khabar unit, not of its head word,
    # so it is drawn beside that unit under the sentence rather than inside it; so it is
    # beside the khabar a حال of it stands beside (هذا زيدٌ قائمًا: مبتدأ، خبر، حال)
    top = roots[0]
    subjects = [kid for kid in children_of[top["id"]] if role_of[kid["id"]] == NAMED.mubtada]
    beside_hal = len(roots) > 1 and all(job_of[t["id"]] == NAMED.haal for t in roots[1:])
    pulled = (len(roots) == 1 or beside_hal) and role_of[top["id"]] == NAMED.khabar and 0 < len(subjects) < len(children_of[top["id"]]) + beside_hal
    if pulled:
        children_of[top["id"]] = [kid for kid in children_of[top["id"]] if kid not in subjects]
        roots = subjects + roots
    # هل أنتَ تكتبُ، ما أنتَ إلا بشر، مَنْ أنتَ في المدينة: a unit typed wholly before or after the unit it
    # hangs in, with a word of another unit between them, cannot sit inside that unit and keep the
    # order typed, so it goes up to the unit above until no such word stands between
    for unit_head in drawn:
        span = [at[t["id"]] for t in drawn if t is unit_head or is_inside(t, unit_head, children_of)]
        while home := next((t for t in drawn if unit_head in children_of[t["id"]]), None):
            near = at[home["id"]]
            low, high = (max(span), near) if near > max(span) else (near, min(span))
            if low >= high or not any(low < at[other["id"]] < high and not is_inside(other, home, children_of)
                                      for other in drawn):
                break
            children_of[home["id"]].remove(unit_head)
            above = next((t for t in drawn if home in children_of[t["id"]]), None)
            (children_of[above["id"]] if above else roots).append(unit_head)
    c.children_of, c.depth, c.parent, c.pulled, c.roots = children_of, depth, parent, pulled, roots
