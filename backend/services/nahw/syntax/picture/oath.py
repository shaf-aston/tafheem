"""An oath is two sentences: the one that swears, its verb left unsaid after و or ت, and the one it swears, its answer."""
from __future__ import annotations

from backend.services.nahw.book import condition_of, is_one
from backend.services.nahw.syntax.facts import is_preposition, is_verb, opens_answer_inside, spelled, sworn_by
from backend.services.nahw.syntax.picture.hang import move_to, take_from
from backend.services.nahw.syntax.picture.names import FRAMES, NAMED
from backend.services.nahw.syntax.picture.state import Picture
from backend.services.text.arabic_text import strip_diacritics


def draw_oaths(c: Picture) -> None:
    """وَاللَّهِ لَأَفْعَلَنَّ: the و or ت swears and works jarr, and its jar hangs on the verb of swearing, which is left
    unsaid (أُقْسِمُ), so it stands beside the sentence it swears, not inside it; that sentence is the oath's answer, with no
    place (Ibn Aqil, bab al-qasam, vol 4 p42). أُقْسِمُ بِاللَّهِ لَأَفْعَلَنَّ says the verb, and its answer is the same.
    The answer opens on what only an answer opens on (closed_words jarr `oath_answer`), its لام the one in an oath's answer.
    لَئِنْ شَكَرْتُمْ لَأَزِيدَنَّكُمْ: a لام on a condition's إنْ announces the oath, and the answer is the oath's (syntax.condition)."""
    oath, by_id, children_of, roots = FRAMES["oath"], c.by_id, c.children_of, c.roots
    c.sworn = set()
    holder = {kid["id"]: kids for kids in (roots, *children_of.values()) for kid in kids}

    def answers(token: dict, after: int = -1) -> bool:
        """The sentence opens as an oath's answer does: on the particle itself or on the first one before its head
        (وَاللَّهِ إِنْ قَامَ زَيْدٌ لَأَقُومَنَّ opens on a condition's إنْ, which no answer of an oath opens on)."""
        first = next((kid for kid in sorted(children_of[token["id"]], key=lambda k: k["id"])
                      if kid["pos"] == "PRT" and after < kid["id"] < token["id"]), None)
        return token["pos"] == "PRT" and is_one(token["lemma"], "jarr", "oath_answer") or bool(
            first and is_one(first["lemma"], "jarr", "oath_answer")) or opens_answer_inside(token, c.sentence, after)

    def to_top(token: dict) -> None:
        if token not in roots:
            move_to(holder, token, roots)

    def answered(answer: dict, after: int) -> None:
        """The oath's answer: no place; the لام it opens on, before its head, the oath's (إِنَّ زَيْدًا لَقَائِمٌ: that one is إنّ's)."""
        c.job_of[answer["id"]], c.place_of[answer["id"]] = oath["answer"], c.said["no_place"]
        c.clauses.add(answer["id"])
        c.framed.add(answer["id"])
        # وَاللَّهِ لَزَيْدٌ قَائِمٌ: a nominal answer, its khabar at the top beside its مبتدأ, holds that مبتدأ as one sentence
        lam_on = (by_id.get(after + 1) or {}).get("head")
        if not is_verb(answer) and (subject := next((t for t in roots if t["id"] == lam_on and t["id"] < answer["id"]
                                                     and c.role_of.get(t["id"]) == NAMED.mubtada), None)):
            move_to(holder, subject, children_of[answer["id"]])
            children_of[answer["id"]].sort(key=lambda kid: kid["id"])
        # past any particle before it: وَاللَّهِ إِنْ قَامَ زَيْدٌ لَأَقُومَنَّ has a condition's إنْ first
        if lam := next((t for t in c.drawn if after < t["id"] < answer["id"] and t["pos"] == "PRT"
                        and strip_diacritics(t["lemma"]).strip("+") == oath["lam"]["letter"]), None):
            c.name_of[lam["id"]] = oath["lam"]["name"]

    noun = sworn_by(c.sentence)
    letter = noun and by_id.get(noun["id"] - 1)
    if letter and (up := by_id.get(letter["head"])) and up in roots and up["id"] > noun["id"] and answers(up, noun["id"]):
        # و، ت: the oath's jar beside its answer, both at the top; a particle typed before the oath (فَوَاللَّهِ) before both
        c.name_of[letter["id"]] = oath["letter"]
        c.sworn.add(letter["id"])
        for token in [letter, *(k for k in children_of[up["id"]] if k["pos"] == "PRT" and k["id"] < letter["id"])]:
            to_top(token)
        answered(up, noun["id"])
    elif len(roots) == 1 and roots[0]["id"] not in c.understood and strip_diacritics(roots[0]["lemma"]) in oath["verbs"]:
        # أُقْسِمُ بِاللَّهِ لَأَفْعَلَنَّ، أُقْسِمُ لَأَفْعَلَنَّ: the sentence it hangs after its jar, or after it where it has none;
        # a verb the picture adds itself (شكرًا's) is no written oath
        kids = children_of[roots[0]["id"]]
        after = next((kid for kid in kids if kid["id"] > roots[0]["id"] and is_preposition(kid)), roots[0])["id"]
        if answer := next((kid for kid in kids if kid["id"] > after and answers(kid, after)), None):
            answered(answer, after)
    for i, found in enumerate(c.named):
        opens = found.get("condition", {})
        if opens.get("part") != "opener" or opens.get("sworn") is None:
            continue
        # لَئِنْ: the condition, its answer left out, beside the oath's answer, which tells it
        condition = condition_of(spelled(c.bases[i]))
        opener, verb, answer = (by_id[c.bases[k]["id"]] for k in (i, opens["verb"], opens["sworn"]))
        c.name_of[opener["id"]] = condition["opener"]
        # إنْ is the only word the لام comes onto (`oath_lam`), and its clause has no place (picture.condition: no `verb_case`)
        c.job_of[verb["id"]], c.place_of[verb["id"]] = condition["verb"], c.said["no_place"]
        c.clauses.add(verb["id"])
        c.framed.add(verb["id"])
        to_top(answer)
        answered(answer, verb["id"])
        c.place_of[answer["id"]] += "، " + oath["condition_answer"]
        to_top(verb)
        beside = [k for k in children_of[opener["id"]] + children_of[verb["id"]] if k["pos"] == "PRT" and k["id"] < opener["id"]]
        for primer in beside:
            if strip_diacritics(primer["lemma"]).strip("+") == oath["lam"]["letter"]:
                c.name_of[primer["id"]] = oath["primer"]
        c.opened[verb["id"]] = tuple(take_from(holder, token) for token in (opener, *beside))
    c.root = None if len(roots) > 1 else c.root
