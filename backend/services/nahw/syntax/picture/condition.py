"""A condition has the front of its sentence: opener, clause and answer side by side in one unit."""
from __future__ import annotations

from backend.services.nahw.book import condition_of
from backend.services.nahw.syntax.picture.hang import is_inside, move_to, take_from
from backend.services.nahw.syntax.picture.state import Picture


def draw_conditions(c: Picture) -> None:
    """A condition has the front of its sentence: opener, clause and answer side by side in one unit."""
    at, bases, by_id, children_of, clauses, drawn = c.at, c.bases, c.by_id, c.children_of, c.clauses, c.drawn
    framed, in_place, job_of, name_of, named = c.framed, c.in_place, c.job_of, c.name_of, c.named
    place_of, pulled, roots, said, split = c.place_of, c.pulled, c.roots, c.said, c.split
    # مَنْ شاء فليصمه: the opener, the condition's clause and the answer's side by side in
    # one unit, as the books draw it, wherever the parser hung them (syntax.condition)
    holder = {kid["id"]: kids for kids in (roots, *children_of.values()) for kid in kids}
    opened: dict[int, tuple[dict, ...]] = {}  # answer id -> (opener, condition verb, tie letters)
    for i, found in enumerate(named):
        if found.get("condition", {}).get("part") != "opener" or found["condition"]["answer"] is None:
            continue
        condition = condition_of(bases[i]["form"])
        opener, verb, answer = (bases[i], bases[found["condition"]["verb"]], bases[found["condition"]["answer"]])
        if not condition["noun"]:
            name_of[opener["id"]] = condition["opener"]  # إن: حرف شرط جازم; a noun keeps its place
        # فَلْيَصُمْهُ، لأمرتُ: the letter written onto the answer ties it to the condition, so it
        # stands beside the answer's sentence in the condition's unit, not inside that sentence
        ties = []
        for piece in named[found["condition"]["tie_at"]].get("attached", []):
            if piece["id"] in split and piece["before"] and piece["form"] in condition["ties"]:
                name_of[piece["id"]] = condition["ties"][piece["form"]]
                tied = by_id[piece["id"]]
                for under in list(children_of[tied["id"]]):  # a فَ the parser made the head of its clause: the clause takes its place
                    move_to(holder, under, holder[tied["id"]])
                ties.append(take_from(holder, tied))
        verb_case, answer_case = condition.get("verb_case"), condition["case"] if ties else None
        # لولا زيدٌ: the noun is a مبتدأ, no فعل الشرط; the answer is جواب لولا
        verb_job = None if condition.get("subject") else condition.get("verb_named") or condition["verb"]
        for unit, job, case in ((verb, verb_job, verb_case), (answer, condition.get("answer_named") or condition["answer"], answer_case)):
            job_of[unit["id"]] = job
            place_of[unit["id"]] = in_place(case) if case else said["no_place"]
            clauses.add(unit["id"])
            framed.add(unit["id"])
        # أينما تكونوا يدرككم: an answer hung nowhere, or under the opener or its verb (which
        # leave their places just below), stands beside them at the top
        if answer["id"] not in holder or any(is_inside(answer, unit, children_of) for unit in (opener, verb)):
            holder.setdefault(answer["id"], [answer])
            move_to(holder, answer, roots)
        for unit in (opener, verb):
            take_from(holder, unit)
            del holder[unit["id"]]
        opened[answer["id"]] = (opener, verb, *ties)
    # مَنْ شاء فليصمه ومَن شاء أفطر: a condition has the front of its sentence, so the وَ
    # bringing a second one joins it beside the first, not inside the first one's answer
    for answer_id in opened:
        up = next((t for t in drawn if any(kid["id"] == answer_id for kid in children_of[t["id"]])
                   and t["pos"] == "PRT"), None)
        outer = next((a for a in opened if up and is_inside(up, by_id[a], children_of)), None)
        if up and outer is not None and up["id"] in holder:
            move_to(holder, up, holder[outer])
    # وَمَنْ يُشْرِكْ: a particle typed before the opener, which the parser hung on the answer, comes
    # before the whole condition, so it stands at the front of the condition's unit, not in the answer
    for answer_id, (opener, *_) in opened.items():
        for kid in [k for k in children_of[answer_id] if k["pos"] == "PRT" and at[k["id"]] < at[opener["id"]]]:
            opened[answer_id] += (take_from(holder, kid),)
    # a مبتدأ drawn beside its khabar unit heads no sentence, nor does that khabar: each keeps its
    # job under the sentence, a مبتدأ with words of its own too (كِتَابُ الطَّالِبِ جَدِيدٌ، لَزَيْدٌ أَفْضَلُ); so is
    # any half of a sentence drawn in several halves side by side (رَجُلٌ كَرِيمٌ فِي الدَّارِ: the مبتدأ unit beside
    # its unwritten خبر ثابت): the sentence is all of them, none is it alone
    root = None if pulled or len(roots) > 1 else roots[0]
    c.opened, c.root = opened, root
