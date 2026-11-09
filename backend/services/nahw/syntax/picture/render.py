"""Whose pronoun a verb's hidden doer is."""
from __future__ import annotations

from backend.services.nahw.book import is_one, tarkeeb_rules
from backend.services.nahw.syntax.doer import DOER, doer as _doer, person_key as _person, persons as _persons
from backend.services.nahw.syntax.facts import completes_kaada, is_particle, is_preposition, is_verb
from backend.services.nahw.syntax.naming import NAMED, tone
from backend.services.nahw.syntax.picture.hang import is_inside, quieted, unbracket
from backend.services.nahw.syntax.picture.names import (
    CONDITION,
    FOLLOWED,
    FRAMES,
    JAR_MAJROOR,
    NOMINAL,
    UNIT_CHILDREN,
    VERBAL,
    finer_name,
    names_a_sentence,
    sentence_label,
    unit_label,
    unit_role,
    word_leaf,
)
from backend.services.nahw.syntax.picture.state import Picture


def find_doers(c: Picture) -> None:
    """Whose pronoun a verb's hidden doer is."""
    by_id, children_of, depth, described, drawn = c.by_id, c.children_of, c.depth, c.described, c.drawn
    named, replies, role_of, typed_at = c.named, c.replies, c.role_of, c.typed_at
    seen: set[int] = set()
    chained: set[int] = set()  # a معطوف عليه already drawn apart from the list it heads
    # every verb no typed word is the doer of, outermost first, so a khabar's pronoun can
    # go back to its subject: the اسم كان inside كنتَ, or the مبتدأ above يكتبُ; a صفة's or حال's
    # to the noun it describes (Ibn Aqil V3 p197: لا بد للجملة الواقعة صفة من ضمير يربطها
    # بالموصوف): حِجَارَةٌ لَا تَنْطِقُ is هي
    persons_of: dict[int, list[str]] = {}
    subjects = {NAMED.mubtada, NAMED.ism_inna, *DOER["explicit"]}
    for token in sorted(drawn, key=lambda t: depth(t)):
        # قُومِي: the doer may be a pronoun written onto the verb, kept inside its leaf
        on_it = named[typed_at[token["id"]]].get("attached", []) if token["id"] in typed_at else []
        if role_of[token["id"]] != NAMED.fil or any(
                role_of[kid["id"]] in DOER["explicit"] for kid in drawn if kid["head"] == token["id"]) \
                or any(piece["role"] in DOER["explicit"] for piece in on_it):
            continue
        up = by_id.get(token["head"])
        nouns = [t for t in drawn if role_of[t["id"]] in subjects and t["id"] != token["id"] and (
            t["id"] == token["head"] or (token["rel"] == "PRD" and t["head"] == token["head"]))] or (
            [described[token["id"]]] if token["id"] in described else [])
        owner = [_person({"per": "3", **{k: v for k, v in nouns[0].items() if v not in (None, "na")}})] if nouns else (
            persons_of.get(up["id"]) if up and token["rel"] == "PRD" else None)
        if owner is None and any(is_inside(token, by_id[reply], children_of) for reply in replies):
            owner = [DOER["reply_to"]]  # the answer is said to the one who asked
        persons_of[token["id"]] = _persons(token, owner)
    doer_of: dict[int, dict] = {}  # the doer drawn inside each typed verb, said on its card too
    c.chained, c.doer_of, c.persons_of, c.seen = chained, doer_of, persons_of, seen


def draw(c: Picture) -> dict:
    """The nested picture and the facts the cards read back from it."""
    at, bases, by_id, chained, children_of = c.at, c.bases, c.by_id, c.chained, c.children_of
    clauses, columns, detail_of, doer_of, drawn = c.clauses, c.columns, c.detail_of, c.doer_of, c.drawn
    family_of, framed, hung, job_of, joins, kept = c.family_of, c.framed, c.hung, c.job_of, c.joins, c.kept
    label_of, ma_card, mubdal_minhu, name_of, named = c.label_of, c.ma_card, c.mubdal_minhu, c.name_of, c.named
    named_by_unsaid, nominal, opened, parent = c.named_by_unsaid, c.nominal, c.opened, c.parent
    persons_of, place_of, role_of, root, roots = c.persons_of, c.place_of, c.role_of, c.root, c.roots
    seen, sentence, split, typed_at, understood = c.seen, c.sentence, c.split, c.typed_at, c.understood
    why_of, words, written = c.why_of, c.words, c.written
    def said_of(token: dict) -> str | None:
        """What the books say of a unit beyond its job: its place (في محل نصب), then whose it is (حال من «الله»)."""
        return " ".join(filter(None, (place_of.get(token["id"]), detail_of.get(token["id"])))) or None
    def pieces(token: dict, leaf: dict) -> dict:
        """The leaf with what is written after a verb (ـها) and its doer, in the order
        the books say them: the verb, its doer, then the pronoun on it."""
        found = named[typed_at[token["id"]]] if token["id"] in typed_at else {}
        leaf = {**leaf, "hidden": True} if token["id"] in understood else leaf
        attached = [{"role": finer_name(piece, piece["role"], piece["family"]), "tone": tone(piece["role"]),
                     "gap": piece["role"] is None}
                    for piece in found.get("attached", []) if piece["id"] not in split]
        doer = _doer(token, family_of[token["id"]], persons_of[token["id"]]) if token["id"] in persons_of else None
        if doer and token["id"] in typed_at:
            doer_of[token["id"]] = doer
        stands_for = mubdal_minhu.get(token["id"])
        inner = {**stands_for, "tone": tone(NAMED.badal), "hidden": True} if stands_for else None
        if not attached and not doer and not inner:
            return leaf
        own = {key: leaf[key] for key in ("role", "tone", "gap", "detail") if key in leaf}
        return {**leaf, "parts": [own] + ([doer] if doer else []) + ([inner] if inner else []) + attached}
    def kind_of(token: dict) -> str:
        """A unit with no name of its own is still a sentence when its head opens one,
        wherever it hangs (وَأَطِيعُوا، وَإِنَّ كَيْدَ الشَّيْطَانِ كَانَ ضَعِيفًا، وَإِنِ اسْتُعْمِلَ):
        a verb a verbal one, a particle of إنّ's family a nominal one, a condition's
        opener a condition."""
        found = named[typed_at[token["id"]]] if token["id"] in typed_at else {}
        if found.get("condition", {}).get("part") == "opener":
            return CONDITION
        if is_verb(token):
            return VERBAL
        if family_of[token["id"]] == "inna":
            return NOMINAL
        # وَأَطِيعُوا hung on its وَ: the joined sentence is what the وَ brings; a condition's answer is
        # drawn in the condition's own unit (وَمَنْ شَاءَ أَفْطَرَ), so the وَ beside it names nothing
        if token["pos"] == "PRT":
            return next((kind for kid in children_of[token["id"]] if kid["id"] not in opened and (kind := kind_of(kid))), "")
        return ""
    def node(token: dict) -> dict:
        # the parser can hand back two words pointing at each other; a word already
        # drawn is left as a leaf rather than followed round the circle again
        seen.add(token["id"])
        kids = [kid for kid in children_of[token["id"]] if kid["id"] not in seen]
        index = at[token["id"]]
        if not kids:
            leaf = pieces(token, word_leaf(index, role_of[token["id"]], why_of.get(token["id"]), name_of[token["id"]]))
            # a صلة of one verb is still a clause, its doer the pronoun hidden in it; a khabar
            # whose مبتدأ is drawn beside it is a word (هذا زيدٌ قائمًا)
            if token["id"] in clauses - nominal:
                return {"role": job_of[token["id"]], "label": VERBAL, "tone": tone(job_of[token["id"]]) or leaf["tone"],
                        "detail": said_of(token), "children": [leaf]}
            return {"detail": detail_of[token["id"]], **leaf} if token["id"] in detail_of else leaf
        kid_roles = [job_of[kid["id"]] for kid in kids if job_of[kid["id"]]]
        if token is root and role_of[token["id"]] and token["id"] not in opened and (own := unit_label(token, kid_roles, kids)) and not names_a_sentence(own):
            # كِتَابُ الطَّالِبِ جَدِيدٌ: the مضاف heads its unit, but the خبر hangs outside it;
            # the sentence holds both, the unit as a whole is the مبتدأ
            if beside := [kid for kid in kids if job_of[kid["id"]] not in UNIT_CHILDREN]:
                children_of[token["id"]] = [kid for kid in kids if kid not in beside]
                seen.discard(token["id"])
                whole = {**node(token), "role": role_of[token["id"]], "tone": tone(role_of[token["id"]])}
                seen.update(kid["id"] for kid in beside)
                inside = [(index, whole), *((at[kid["id"]], unit(kid)) for kid in beside)]
                return {"role": None, "label": top_label, "tone": None, "detail": None,
                        "children": [drawn for _, drawn in sorted(inside, key=lambda pair: pair[0])]}
        # جاء زيدٌ وعمرٌو، وَإِقَامِ الصَّلَاةِ وَإِيتَاءِ الزَّكَاةِ: the word the معطوفات are joined on, with what is its
        # own (its مضاف إليه, its صفة), is the معطوف عليه; the job belongs to the whole list, drawn above all of it
        joined = [kid for kid in kids if joins(kid) and any(job_of[k["id"]] == NAMED.matoof for k in children_of[kid["id"]])]
        if joined and token["id"] not in chained:
            start = min(at[kid["id"]] for kid in joined)
            rest = [kid for kid in kids if at[kid["id"]] >= start]
            children_of[token["id"]] = [kid for kid in kids if kid not in rest]
            seen.discard(token["id"])
            chained.add(token["id"])
            first = node(token)
            seen.add(token["id"])
            own = {"role": NAMED.matoof_alayh, "tone": tone(NAMED.matoof_alayh)}
            first = {**first, **own, **({"parts": [{**first["parts"][0], **own}, *first["parts"][1:]]} if first.get("parts") else {})}
            seen.update(kid["id"] for kid in rest)
            inside = [(index, first), *((at[kid["id"]], unit(kid)) for kid in rest)]
            job = None if token is root or is_particle(token) else job_of[token["id"]]
            label = top_label if token is root and token["id"] not in opened else ""
            return {"role": job, "label": label, "tone": tone(job), "detail": said_of(token),
                    "children": [drawn for _, drawn in sorted(inside, key=lambda pair: pair[0])]}
        seen.update(kid["id"] for kid in kids)
        inside = [(at[kid["id"]], unit(kid)) for kid in kids]
        role = role_of[token["id"]]
        why = why_of.get(token["id"])
        # a word the teacher dashed stays a dash at the head of its unit: مضاف would name it
        own = unit_label(token, kid_roles, kids)
        # a name with its ابن is the متبوع: موصوف or مبدل منه would pick one of the three readings
        head_name = FOLLOWED if own is None else unit_role(token, name_of[token["id"]], kid_roles)
        inside.append((index, pieces(token, word_leaf(index, role, why, None if why else head_name))))
        # الطالبُ مجتهدٌ في المدرسة: a خبر whose مبتدأ is drawn beside it is a word with its
        # jar-majroor, not a sentence
        lone_khabar = role == NAMED.khabar and token["id"] in nominal and not any(
            role_of[kid["id"]] == NAMED.mubtada for kid in kids)
        label = label_of.get(token["id"]) or ("" if own is None or lone_khabar else own or (
            top_label if token is root and token["id"] not in opened
            else NOMINAL if token["id"] in clauses & nominal
            else VERBAL if token["id"] in clauses or role == NAMED.fil else kind_of(token)))
        # A particle's name is what it is, not a job for the unit it heads: the
        # parser gives no job for a jar-majroor or a clause under إِذَا, so none
        # is written rather than calling the whole unit a حرف. The clause a كاد-type
        # verb is finished by is that verb's khabar as a whole.
        job = NAMED.khabar_kaada if completes_kaada(token, sentence) else (
            job_of[token["id"]] if token["id"] in framed
            else None if token is root or is_particle(token) or job_of[token["id"]] == NAMED.fil
            else job_of[token["id"]])
        # مِن نارٍ: a jar-majroor with a word to hang on is named by it, متعلق بـX
        if token["id"] in hung:
            label = FRAMES["attached"].format(word=kept["word"])
        elif label == JAR_MAJROOR and (up := parent(token)) in at:
            # فِي سَنَةٍ أَوْ فِي ثَلَاثِ سِنِينَ: hung on a حرف عطف, it is معطوف on the jar-majroor that
            # حرف follows, and hangs where that one hangs (the معطوف follows its معطوف عليه)
            # A حرف عطف at the root follows nothing: no word to look at, so no loop.
            while is_one(by_id[up]["form"], "atf") and (followed := by_id.get(parent(by_id[up]))) \
                    and is_preposition(followed) and parent(followed) in at:
                job, up = NAMED.matoof, parent(followed)
            label = FRAMES["attached"].format(word=columns[at[up]])
        return {"role": job,
                "label": label,
                "tone": tone(job) or tone(role),
                "detail": said_of(token),
                # right to left, so the picture reads in the order they were typed
                "children": [drawn for _, drawn in sorted(inside, key=lambda pair: pair[0])]}
    # the parser can leave a sentence as two loose halves; they are still one
    # sentence, so they are drawn side by side under it rather than one dropped
    def unit(token: dict) -> dict:
        """A word's node, or for a condition's answer the whole condition around it."""
        if token["id"] not in opened:
            return node(token)
        beside = opened[token["id"]]
        seen.update(t["id"] for t in beside)
        inside = [(at[t["id"]], node(t)) for t in (*beside, token)]
        return {"role": None, "label": CONDITION, "tone": None, "detail": None,
                "children": [drawn for _, drawn in sorted(inside, key=lambda pair: pair[0])]}
    top_label = sentence_label(role_of, drawn, named)
    drawn = sorted(((at[part["id"]], unit(part)) for part in roots), key=lambda pair: pair[0])
    tree = drawn[0][1] if len(drawn) == 1 else None
    # a phrase alone (محمد بن عبد الله): its head has no job, nothing makes it a sentence
    phrase = tree is not None and tree.get("word") is None and not role_of[roots[0]["id"]]
    if not phrase and (tree is None or tree.get("word") is not None or not tree.get("label")):
        tree = {"label": top_label,
                "children": [part for _, part in drawn] if tree is None else [tree]}
    tree = quieted(unbracket(tree))
    covered = sum(1 for found in named if found["role"])
    return {"words": columns, "written": written, "tree": tree, "coverage": round(covered / len(words), 2),
            "unsaid": [role_of[token["id"]] if token["id"] in named_by_unsaid else None for token in bases],  # the job on the card too
            # the picture's finer name (حرف ناسخ, فعل أمر, فعل مجهول) where it says more than the role
            "finer": [name_of.get(token["id"]) if name_of.get(token["id"]) != role_of[token["id"]] else None for token in bases],
            # the doer no typed word is (هو hidden in يكتبُ, the تاء of كتبتُ): the card says it as the picture draws it
            "doer": [doer_of.get(token["id"]) for token in bases],
            # ما read by its عائد (facts.ma_kind): the relative's job and case, or (None, None) for ما المصدرية
            "ma": [ma_card.get(token["id"]) for token in bases],
            **({"unwritten": {"mark": columns[written.index(-1)], "note": tarkeeb_rules()["treebank"]["unwritten_note"]}} if understood else {})}
