"""The bracket picture (tarkeeb) for a typed sentence, from the same links.

The cards say what each word is; this says which words join into a unit and what
that unit does. Both come from one reading, so the page can never show a word as
a فاعل in the cards and as something else in the picture.

Shape and wording follow the book examples in `data/tarkeeb/examples`, so a typed
sentence and a book example draw the same way: a unit carries what it **is**
(`label`) and what it **does** (`role`), a leaf carries its role and the index of
its word, and a word no rule could name is left as a gap rather than guessed.
"""
from __future__ import annotations

from backend.services.nahw_book import clause_of, family_cards, frames, named_roles, role_units, teacher_rules
from backend.services.syntax.facts import Sentence, completes_kaada, is_passive
from backend.services.syntax.naming import base_tokens, opens_with_verb, tone
from backend.services.arabic_text import strip_diacritics
from backend.services.nahw_book import book_words, term_ar

# What a unit is called, by the join that makes it. Spelled once, in
# data/nahw_rules/tarkeeb.json, so a typed sentence, a book example and an ayah
# name the same unit the same way; which role heads which unit is in roles.json.
VERBAL = term_ar("jumlah_filiyyah")
NOMINAL = term_ar("jumlah_ismiyyah")
QUESTION = term_ar("jumlah_istifhamiyyah")
CONDITION = term_ar("jumlah_shartiyyah")
NAMED = named_roles()
FRAMES = frames()
CARDS = dict(family_cards())
JAR_MAJROOR = term_ar("jar_majroor")
SHADDA = "ّ"


def _leaf(index: int, role: str | None, why: dict | None = None, name: str | None = None) -> dict:
    """One word on its own. No role means the rules could not name it; `why` is the
    teacher's reason when a rule took the name away, shown on hover. `name` is the
    finer name the picture prints (حرف نصب for a حرف), coloured as its role."""
    leaf = {"word": index, "role": name or role, "tone": tone(role), "gap": role is None}
    if role is None and why:
        leaf["detail"] = f"{why['ar']} · {why['en']}"
    return leaf


def _label(head: dict, child_roles: list[str]) -> str:
    """What the unit this word heads is called."""
    for unit in role_units():
        if unit["child"] in child_roles and (head["pos"] == "PRT" or not unit.get("on_particle")):
            return term_ar(unit["label"])
    return ""


def _unit_role(role: str | None, child_roles: list[str]) -> str | None:
    """What the head word is called inside its own unit.

    On its own it is a مبتدأ; inside كِتَابُ الطَّالِبِ it is the مضاف and the
    unit as a whole is the مبتدأ, which is how the books draw it.
    """
    for unit in role_units():
        if unit["child"] in child_roles and "head_as" in unit:
            return unit["head_as"]
    return role


DOER = FRAMES["doer"]


def _person(token: dict) -> str:
    """CAMeL's person, gender and number as one key of DOER["pronoun"] (2ms, 1s)."""
    per = token.get("per", "na")
    return per + ("" if per == "1" else token.get("gen", "na")) + token.get("num", "na")


def _persons(token: dict, owner: list[str] | None) -> list[str]:
    """Who a verb's doer may be: one person, or the two its letters allow (تكتبُ is you
    or she) narrowed by the subject its pronoun goes back to (`owner`)."""
    if token.get("asp") == "c" and token.get("per") != "2":
        return [DOER["command"]]  # a command speaks to the listener, whatever the reading said
    letter = strip_diacritics(token["base"])[:1]
    if token.get("asp") == "i" and letter in DOER["prefix_says"]:
        return [DOER["prefix_says"][letter]]
    if token.get("asp") == "i" and token.get("per", "na") not in DOER["prefix_person"].get(letter, token.get("per", "na")):
        return []  # the reading's person is not one its letter allows
    if token.get("asp") == "i" and token.get("num") == "s" and letter == "ت":
        both = DOER["ta_prefix"]
        # the subject's person settles it: a ت said of a third person is هي (هِنْدٌ تَكْتُبُ)
        return [key for key in both if key[0] in {o[0] for o in owner or []}] or both
    return [_person(token)]


def _doer(token: dict, family: str | None, persons: list[str]) -> dict | None:
    """The doer inside a verb no typed word stands as (اقبلْ: أنت, كنتَ: the تاء);
    None when the person is not known."""
    pronouns = [DOER["pronoun"].get(key) for key in persons]
    if token.get("asp") not in DOER["hidden"] or not pronouns or not all(pronouns):
        return None
    name = DOER["by_family"].get(family) or DOER["passive" if is_passive(token) else "active"]
    said = DOER["hidden_said" if persons[0] in DOER["hidden"][token["asp"]] else "attached_said"]
    pronoun = pronouns[0] if len(pronouns) == 1 else DOER["either"].format(one=pronouns[0], other=pronouns[1])
    return {"role": name, "tone": tone(name), "detail": said.format(pronoun=pronoun)}


def _finer(token: dict, role: str | None, family: str | None) -> str | None:
    """A governor's name in the picture: كان is a فعل ناقص, أنْ a حرف نصب, as its card says."""
    if family in FRAMES["leaf_by_family"]:
        return FRAMES["leaf_by_family"][family]
    card = CARDS.get(family)
    named = card and card.get("named_as", {}).get(strip_diacritics(token["form"]), card["named"])
    # only a finer name for the same role (حرف نصب for حرف), so card and picture still agree
    return named if role in (NAMED.harf, NAMED.harf_jarr) and named and named.startswith(role) else role


def _sentence_label(roles: dict[int, str | None], tokens: list[dict]) -> str:
    if any("interrog" in t.get("pos_camel", "") for t in tokens):
        return QUESTION
    # إن كنتَ ... فاقبلها: a conditional particle and its verb, as rule_engine.opens_condition
    if len(tokens) > 1 and roles[tokens[1]["id"]] == NAMED.fil and strip_diacritics(
            tokens[0]["form"]) in book_words("jazm", "conditional_particles"):
        return CONDITION
    return VERBAL if opens_with_verb([roles[t["id"]] for t in tokens]) else NOMINAL


def build(words: list[str], tokens: list[dict], named: list[dict]) -> dict:
    """The tree for one typed sentence, ready for the diagram.

    `named` is what `naming.roles` returned, one entry per typed word.
    """
    bases = base_tokens(words, tokens)
    if not words or len(bases) != len(words) or len(named) != len(words):
        return {"words": words, "tree": {"gap": True}, "coverage": 0.0}

    at = {token["id"]: index for index, token in enumerate(bases)}
    role_of = {token["id"]: found["role"] for token, found in zip(bases, named)}
    why_of = {token["id"]: found.get("gap") for token, found in zip(bases, named)}
    # what each unit does for the word above it: هذا البيتُ is drawn with the noun over its
    # pointer, but the pair is the مبتدأ, not a صفة of the khabar
    job_of = {token["id"]: NAMED.mubtada if role_of[token["id"]] == NAMED.sifah and any(
        t["head"] == token["id"] and t["id"] < token["id"] and role_of.get(t["id"]) == NAMED.mubtada for t in bases)
        else role_of[token["id"]] for token in bases}
    # a clause inside the sentence is headed by its verb, or by a khabar with its own مبتدأ
    # before it under it (زيدٌ أبوه عالمٌ): verbal or nominal, it is drawn as a sentence
    # (hung on a word other than that مبتدأ: the parser can draw the two pointing at each other)
    nominal = {token["id"] for token in bases if role_of[token["id"]] == NAMED.khabar and any(
        t["head"] == token["id"] and t["id"] < token["id"] and role_of[t["id"]] == NAMED.mubtada
        and token["head"] != t["id"] for t in bases)}
    opens = {token["id"] for token in bases if role_of[token["id"]] == NAMED.fil} | nominal
    # جاء الذي نجح: the clause after a relative is its صلة, with no place of its own
    for token in bases:
        up = next((t for t in bases if t["id"] == token["head"]), None)
        if up and "rel" in up.get("pos_camel", "") and up["id"] < token["id"] and token["id"] in opens:
            job_of[token["id"]] = NAMED.silah
    # الولدُ يكتبُ: the clause hung on a مبتدأ (or اسم كان) is its khabar, standing in a case;
    # كان الولدُ يكتبُ: so is the one beside it, the khabar (PRD) under their governor
    said = teacher_rules()["case_said"]
    family_of = {token["id"]: found.get("family") for token, found in zip(bases, named)}
    name_of = {token["id"]: _finer(token, role_of[token["id"]], family_of[token["id"]]) for token in bases}
    place_of: dict[int, str] = {}
    label_of: dict[int, str] = {}
    framed: set[int] = set()  # units whose job a governor gave, drawn even under a particle

    def in_place(case: str) -> str:
        return said["in_place"].format(place=said["place"][case])

    for token in bases:
        owners = [t for t in bases if t["id"] == token["head"] or (
            token["rel"] == "PRD" and t["head"] == token["head"] and t["id"] != token["id"])]
        # كنتَ تحبُّ: the clause on كان's PRD is its khabar, with no اسم كان word to hang it on
        clause = next((found for t in owners if (found := clause_of(role_of.get(t["id"])) or (
            (by := FRAMES["clause_by_family"].get(family_of[t["id"]])) and token["rel"] == by["rel"] and by))), None)
        if clause and token["id"] in opens:
            job_of[token["id"]] = clause["job"]
            place_of[token["id"]] = in_place(clause["case"])
    # تحب أن تطوّق: أنْ and the verb hung on it are one masdar, doing the job أنْ hangs by
    # (the parser's أنّ takes a noun, so a verb on it is the nasb أنْ whatever the card guessed)
    masdar = FRAMES["masdar"]
    for token in bases:
        if (strip_diacritics(token["form"]) in masdar["words"] and SHADDA not in token["form"]
                and token["rel"] in masdar["job_by_rel"]
                and any(t["head"] == token["id"] and role_of[t["id"]] == NAMED.fil for t in bases)):
            name_of[token["id"]] = CARDS[masdar["family"]]["named"]
            label_of[token["id"]] = masdar["label"]
            job_of[token["id"]] = masdar["job_by_rel"][token["rel"]]
            place_of[token["id"]] = in_place(masdar["case_by_rel"][token["rel"]])
            framed.add(token["id"])
    clauses = {token["id"] for token in bases if job_of[token["id"]] == NAMED.silah} | set(place_of)
    children_of: dict[int, list[dict]] = {token["id"]: [] for token in bases}
    by_id = {t["id"]: t for t in tokens}

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

    roots = []
    for token in bases:
        up = parent(token)
        if up in children_of and up != token["id"]:
            children_of[up].append(token)
        else:
            roots.append(token)
    roots = roots or [bases[0]]
    # هذا بيتٌ كبيرٌ: the مبتدأ is said of the whole khabar unit, not of its head word,
    # so it is drawn beside that unit under the sentence rather than inside it
    top = roots[0]
    subjects = [kid for kid in children_of[top["id"]] if role_of[kid["id"]] == NAMED.mubtada]
    if len(roots) == 1 and role_of[top["id"]] == NAMED.khabar and 0 < len(subjects) < len(children_of[top["id"]]):
        children_of[top["id"]] = [kid for kid in children_of[top["id"]] if kid not in subjects]
        roots = subjects + roots
    # إن كنتَ ... فاقبلها: the particle, the condition's clause and the answer's side by side
    # under the sentence, as the books draw it, rather than the condition inside the answer
    condition = FRAMES["condition"]
    fa = condition["fa"]  # فاقبلها: the ف on the answer ties it to the condition
    particle = bases[0] if _sentence_label(role_of, bases) == CONDITION else None
    verb = next((kid for kid in children_of[particle["id"]] if role_of[kid["id"]] == NAMED.fil), None) if particle else None
    answer = next((t for t in roots if t["id"] == parent(particle) and role_of[t["id"]] == NAMED.fil), None) if verb else None
    if answer:
        name_of[particle["id"]] = condition["particle"]
        for unit, job in ((verb, condition["verb"]), (answer, condition["answer"])):
            job_of[unit["id"]] = job
            place_of[unit["id"]] = in_place(condition["case"])
            clauses.add(unit["id"])
            framed.add(unit["id"])
        children_of[answer["id"]].remove(particle)
        children_of[particle["id"]].remove(verb)
        roots = [particle, verb] + roots
    root = roots[0]

    seen: set[int] = set()
    sentence = Sentence(tokens)

    # every verb no typed word is the doer of, outermost first, so a khabar's pronoun can
    # go back to its subject: the اسم كان inside كنتَ, or the مبتدأ above يكتبُ
    persons_of: dict[int, list[str]] = {}
    subjects = {NAMED.mubtada, NAMED.ism_inna, *DOER["explicit"]}
    for token in sorted(bases, key=lambda t: depth(t)):
        if role_of[token["id"]] != NAMED.fil or any(
                role_of[kid["id"]] in DOER["explicit"] for kid in bases if kid["head"] == token["id"]):
            continue
        up = by_id.get(token["head"])
        nouns = [t for t in bases if role_of[t["id"]] in subjects and t["id"] != token["id"] and (
            t["id"] == token["head"] or (token["rel"] == "PRD" and t["head"] == token["head"]))]
        owner = [_person({"per": "3", **{k: v for k, v in nouns[0].items() if v not in (None, "na")}})] if nouns else (
            persons_of.get(up["id"]) if up and token["rel"] == "PRD" else None)
        persons_of[token["id"]] = _persons(token, owner)

    def pieces(token: dict, leaf: dict) -> dict:
        """The leaf with what is written onto its word (فـ، ـها) and the verb's doer, in
        the order the books say them: before it, the word, its doer, after it."""
        found = named[at[token["id"]]]
        # a piece is named finer the way a typed word is (وَ حرف عطف), the answer's ف aside
        attached = [{"role": fa if piece["before"] and token is answer and piece["role"] == NAMED.harf
                     else _finer(piece, piece["role"], piece["family"]), "tone": tone(piece["role"]),
                     "gap": piece["role"] is None, "before": piece["before"]}
                    for piece in found.get("attached", [])]
        doer = _doer(token, family_of[token["id"]], persons_of[token["id"]]) if token["id"] in persons_of else None
        if not attached and not doer:
            return leaf
        own = {key: leaf[key] for key in ("role", "tone", "gap", "detail") if key in leaf}
        parts = [p for p in attached if p["before"]] + [own] + ([doer] if doer else []) + [
            p for p in attached if not p["before"]]
        return {**leaf, "parts": [{k: v for k, v in p.items() if k != "before"} for p in parts]}

    def node(token: dict) -> dict:
        # the parser can hand back two words pointing at each other; a word already
        # drawn is left as a leaf rather than followed round the circle again
        seen.add(token["id"])
        kids = [kid for kid in children_of[token["id"]] if kid["id"] not in seen]
        index = at[token["id"]]
        if not kids:
            leaf = pieces(token, _leaf(index, role_of[token["id"]], why_of[token["id"]], name_of[token["id"]]))
            # a صلة of one verb is still a clause, its doer the pronoun hidden in it
            return {"role": job_of[token["id"]], "label": VERBAL, "tone": tone(job_of[token["id"]]) or leaf["tone"],
                    "detail": place_of.get(token["id"]), "children": [leaf]} if token["id"] in clauses else leaf
        kid_roles = [job_of[kid["id"]] for kid in kids if job_of[kid["id"]]]
        seen.update(kid["id"] for kid in kids)
        inside = [(at[kid["id"]], node(kid)) for kid in kids]
        role = role_of[token["id"]]
        why = why_of[token["id"]]
        # a word the teacher dashed stays a dash at the head of its unit: مضاف would name it
        inside.append((index, pieces(token, _leaf(index, role, why, None if why else _unit_role(name_of[token["id"]], kid_roles)))))
        label = label_of.get(token["id"]) or _label(token, kid_roles) or (_sentence_label(role_of, bases) if token is root
                                             else NOMINAL if token["id"] in clauses & nominal
                                             else VERBAL if token["id"] in clauses or role == NAMED.fil else "")
        # A particle's name is what it is, not a job for the unit it heads: the
        # parser gives no job for a jar-majroor or a clause under إِذَا, so none
        # is written rather than calling the whole unit a حرف. The clause a كاد-type
        # verb is finished by is that verb's khabar as a whole.
        job = NAMED.khabar_kaada if completes_kaada(token, sentence) else (
            job_of[token["id"]] if token["id"] in framed
            else None if token is root or token["pos"] == "PRT" or job_of[token["id"]] == NAMED.fil
            else job_of[token["id"]])
        # مِن نارٍ: a jar-majroor is said with the word it hangs on
        attached = FRAMES["attached"].format(word=words[at[up]]) if label == JAR_MAJROOR and (
            up := parent(token)) in at else None
        return {"role": job,
                "label": label,
                "tone": tone(job) or tone(role),
                "detail": place_of.get(token["id"]) or attached,
                # right to left, so the picture reads in the order they were typed
                "children": [drawn for _, drawn in sorted(inside, key=lambda pair: pair[0])]}

    # the parser can leave a sentence as two loose halves; they are still one
    # sentence, so they are drawn side by side under it rather than one dropped
    drawn = sorted(((at[part["id"]], node(part)) for part in roots), key=lambda pair: pair[0])
    tree = drawn[0][1] if len(drawn) == 1 else None
    if tree is None or tree.get("word") is not None or not tree.get("label"):
        tree = {"label": _sentence_label(role_of, bases),
                "children": [part for _, part in drawn] if tree is None else [tree]}
    covered = sum(1 for found in named if found["role"])
    return {"words": words, "tree": tree, "coverage": round(covered / len(words), 2)}


def is_drawable(tree: dict) -> bool:
    """False when nothing could be joined, so the page shows the cards alone."""
    return bool(tree.get("tree", {}).get("children")) and tree.get("coverage", 0) > 0
