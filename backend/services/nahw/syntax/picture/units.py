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
    # إِنَّمَا زَيْدٌ قَائِمٌ: ما الكافة leaves إنّ working on nothing, so the pair is the إنّ's own sentence: the مبتدأ
    # right after the ما stands beside its khabar under the إنّ (as اسم إنّ does), not inside a sentence of its own
    for particle in [t for t in drawn if t["id"] in c.typed_at and c.named[c.typed_at[t["id"]]].get("kaffa")]:
        for khabar in list(children_of[particle["id"]]):
            subjects = [kid for kid in children_of[khabar["id"]] if role_of[kid["id"]] == NAMED.mubtada and min(
                t["id"] for t in drawn if t is kid or is_inside(t, kid, children_of)) == particle["id"] + 2]
            children_of[khabar["id"]] = [kid for kid in children_of[khabar["id"]] if kid not in subjects]
            children_of[particle["id"]] += subjects
    # زَيْدٌ قَائِمٌ وَعَمْرٌو قَاعِدٌ، زَيْدٌ فِي الدَّارِ وَهُوَ نَائِمٌ، إِنَّمَا زَيْدٌ قَائِمٌ وَعَمْرٌو قَاعِدٌ: a nominal sentence
    # (a مبتدأ with its khabar, or إنّ and its pair) the و brings after a unit of the first sentence is joined to that
    # whole sentence, not to the unit the parser hung it on: so it and its و stand beside that unit. Inside a clause
    # (a صلة) the clause is the sentence it joins.
    def nominal(token: dict) -> bool:
        kids = children_of[token["id"]]
        return c.family_of[token["id"]] == "inna" or any(role_of[t["id"]] == NAMED.mubtada for t in kids) \
            or token["pos"] == "PRT" and any(nominal(t) for t in kids)
    def is_waw(token: dict) -> bool:
        return token["pos"] == "PRT" and token["lemma"].strip("+") == "و"
    def home_of(token: dict) -> dict | None:
        return next((t for t in drawn if token in children_of[t["id"]]), None)
    # the khabar a word, not a sentence (فَأُعَذِّبُهُمْ... وَمَا لَهُمْ مِنْ نَاصِرِينَ: a sentence joins the sentence before it;
    # a verb is named فعل), or a jar hung on the khabar no one writes (زَيْدٌ فِي الدَّارِ)
    def word_khabar(token: dict) -> bool:
        return (role_of[token["id"]] in c.khabars or token["id"] in c.hung) and (token in roots or home_of(token) in roots)
    for unit in [t for t in drawn if word_khabar(t)]:
        for head in [kid for kid in children_of[unit["id"]] if nominal(kid)]:
            first = min(t["id"] for t in drawn if t is head or is_inside(t, head, children_of))
            waw = head if is_waw(head) else next((kid for kid in children_of[unit["id"]] if kid["id"] == first - 1 and is_waw(kid)), None)
            if waw is None:  # وَلَوْ أَنَّ لِلَّذِينَ ظَلَمُوا...: what لو opens stays under it
                continue
            home = home_of(unit)
            for moved in [head] if waw is head else [waw, head]:
                children_of[unit["id"]].remove(moved)
                (children_of[home["id"]] if home else roots).append(moved)
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
