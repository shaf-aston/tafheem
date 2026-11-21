"""A condition has the front of its sentence: opener, clause and answer side by side in one unit."""
from __future__ import annotations

from backend.services.nahw.book import condition_of
from backend.services.nahw.syntax.condition import subject_id
from backend.services.nahw.syntax.facts import reading, spelled
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
    # فَإِمَّا يَأْتِيَنَّكُمْ ... فَمَنْ تَبِعَ ... فَلَا خَوْفٌ: a condition answering the one before it is drawn first, whole, and
    # stands as that one's answer (syntax.condition): inner answer id -> (outer opener, verb, ties, the answer's job)
    wraps: dict[int, tuple] = {}
    answer_of: dict[int, int] = {}  # opener id -> its answer id, for the condition around it
    for i, found in reversed(list(enumerate(named))):
        if found.get("condition", {}).get("part") != "opener" or found["condition"]["answer"] is None:
            continue
        condition = condition_of(spelled(bases[i]))
        opener, verb, answer = bases[i], by_id[subject_id(i, found, bases)], bases[found["condition"]["answer"]]
        inner = answer_of.get(answer["id"])
        answer = by_id[inner] if inner is not None else answer
        # فَهُوَ نَاجِحٌ، فَلَهُ أَجْرٌ: the answer is the sentence its first word is in, so a مبتدأ (or a jar) the tying
        # letter is written on answers through the khabar heading that sentence (picture.unwritten)
        while (up := by_id.get(by_id[answer["id"]]["head"])) and up["id"] in c.nominal and up["id"] not in (opener["id"], verb["id"]):
            answer = up
        # the مبتدأ the top khabar was drawn beside (picture.units) is inside the answer, which is one sentence
        for kid in [k for k in roots if k["id"] != answer["id"] and by_id[k["id"]]["head"] == answer["id"]]:
            move_to(holder, kid, children_of[answer["id"]])
        if not condition["noun"]:
            # إن: حرف شرط جازم; a noun keeps its place; إِلَّا تَنْصُرُوهُ, إنْ merged into لا, is named as its reading says
            name_of[opener["id"]] = reading(opener, "named") if reading(opener, "spells") else condition["opener"]
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
        units = ((verb, verb_job, verb_case), (answer, condition.get("answer_named") or condition["answer"], answer_case))
        # لَوْلَا أَنَّكَ صَدِيقِي: a masdar keeps the مبتدأ's job and place it was given (picture.jobs)
        for unit, job, case in units[found["condition"]["masdar"]:len(units) - (inner is not None)]:
            job_of[unit["id"]] = job
            place_of[unit["id"]] = in_place(case) if case else said["no_place"]
            clauses.add(unit["id"])
            framed.add(unit["id"])
        # أينما تكونوا يدرككم: an answer hung nowhere, or under the opener or its verb (which
        # leave their places just below), stands beside them at the top
        if answer["id"] not in holder or any(is_inside(answer, unit, children_of) for unit in (opener, verb)):
            holder.setdefault(answer["id"], [answer])
            move_to(holder, answer, roots)
        # لَوْلَا أَنَّكَ صَدِيقِي: the khabar no one writes (picture.unwritten), hung beside the masdar, follows it
        beside = [take_from(holder, kid) for kid in list(children_of[opener["id"]])
                  if found["condition"]["masdar"] and kid["id"] in c.understood]
        for unit in (opener, verb):
            take_from(holder, unit)
            del holder[unit["id"]]
        answer_of[opener["id"]] = answer["id"]
        if inner is not None:
            wraps[inner] = ((opener, verb, *beside, *ties), units[1][1])
            continue
        opened[answer["id"]] = (opener, verb, *beside, *ties)
    # مَنْ شاء فليصمه ومَن شاء أفطر: a condition has the front of its sentence, so the وَ
    # bringing a second one joins it beside the first, not inside the first one's answer
    for answer_id in opened:
        up = next((t for t in drawn if any(kid["id"] == answer_id for kid in children_of[t["id"]])
                   and t["pos"] == "PRT"), None)
        outer = next((a for a in opened if up and is_inside(up, by_id[a], children_of)), None)
        if up and outer is not None and up["id"] in holder:
            move_to(holder, up, holder[outer])
    # وَمَنْ يُشْرِكْ: a particle typed before the opener, which the parser hung on the answer (or on the opener: فَمَنْ),
    # comes before the whole condition, so it stands at the front of the condition's unit, not in the answer
    for answer_id, (opener, *_) in opened.items():
        for kid in [k for k in children_of[answer_id] + children_of[opener["id"]] if k["pos"] == "PRT" and at[k["id"]] < at[opener["id"]]]:
            opened[answer_id] += (take_from(holder, kid),)
    # فَإِمَّا يَأْتِيَنَّكُمْ ... فَمَنْ ...: so too for a condition standing around another, which the parser may hang on its verb
    for inner, ((opener, verb, *rest), job) in list(wraps.items()):
        front = [k for k in children_of[opener["id"]] + children_of[verb["id"]] if k["pos"] == "PRT" and at[k["id"]] < at[opener["id"]]]
        wraps[inner] = ((opener, verb, *rest, *(take_from(holder, kid) for kid in front)), job)
    # a مبتدأ drawn beside its khabar unit heads no sentence, nor does that khabar: each keeps its
    # job under the sentence, a مبتدأ with words of its own too (كِتَابُ الطَّالِبِ جَدِيدٌ، لَزَيْدٌ أَفْضَلُ); so is
    # any half of a sentence drawn in several halves side by side (رَجُلٌ كَرِيمٌ فِي الدَّارِ: the مبتدأ unit beside
    # its unwritten خبر ثابت): the sentence is all of them, none is it alone
    root = None if len(roots) > 1 or pulled else roots[0]
    c.opened, c.root, c.wraps = opened, root, wraps
