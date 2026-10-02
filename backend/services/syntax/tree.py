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

from backend.services.syntax.naming import base_tokens, completes_kaada, opens_with_verb, tone
from backend.services.tarkeeb import term_ar

# What a unit is called, by the join that makes it. Spelled once, in
# data/nahw_rules/tarkeeb.json, so a typed sentence, a book example and an ayah
# name the same unit the same way.
IDAFA = term_ar("murakkab_idafi")
WASF = term_ar("murakkab_tawsifi")
JARR = term_ar("jar_majroor")
VERBAL = term_ar("jumlah_filiyyah")
NOMINAL = term_ar("jumlah_ismiyyah")
QUESTION = term_ar("jumlah_istifhamiyyah")
NIDA = term_ar("jumlah_nidaiyyah")
MAWSOOL = term_ar("mawsool_silah")


def _leaf(index: int, role: str | None, why: dict | None = None) -> dict:
    """One word on its own. No role means the rules could not name it; `why` is the
    teacher's reason when a rule took the name away, shown on hover."""
    leaf = {"word": index, "role": role, "tone": tone(role), "gap": role is None}
    if role is None and why:
        leaf["detail"] = f"{why['ar']} · {why['en']}"
    return leaf


def _label(head: dict, child_roles: list[str]) -> str:
    """What the unit this word heads is called."""
    if head["pos"] == "PRT" and "مجرور" in child_roles:
        return JARR
    if head["pos"] == "PRT" and "منادى" in child_roles:
        return NIDA
    if "صلة" in child_roles:
        return MAWSOOL
    if "مضاف إليه" in child_roles:
        return IDAFA
    if "صفة" in child_roles:
        return WASF
    return ""


def _unit_role(role: str | None, child_roles: list[str]) -> str | None:
    """What the head word is called inside its own unit.

    On its own it is a مبتدأ; inside كِتَابُ الطَّالِبِ it is the مضاف and the
    unit as a whole is the مبتدأ, which is how the books draw it.
    """
    if "صلة" in child_roles:
        return "اسم موصول"
    if "مضاف إليه" in child_roles:
        return "مضاف"
    if "صفة" in child_roles:
        return "موصوف"
    return role


def _sentence_label(roles: dict[int, str | None], tokens: list[dict]) -> str:
    if any("interrog" in t.get("pos_camel", "") for t in tokens):
        return QUESTION
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
    job_of = {token["id"]: "مبتدأ" if role_of[token["id"]] == "صفة" and any(
        t["head"] == token["id"] and t["id"] < token["id"] and role_of.get(t["id"]) == "مبتدأ" for t in bases)
        else role_of[token["id"]] for token in bases}
    # جاء الذي نجح: the verb after a relative opens its صلة, a clause with no place of its own
    for token in bases:
        up = next((t for t in bases if t["id"] == token["head"]), None)
        if up and "rel" in up.get("pos_camel", "") and up["id"] < token["id"] and role_of[token["id"]] == "فعل":
            job_of[token["id"]] = "صلة"
    children_of: dict[int, list[dict]] = {token["id"]: [] for token in bases}
    by_id = {t["id"]: t for t in tokens}

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
    subjects = [kid for kid in children_of[top["id"]] if role_of[kid["id"]] == "مبتدأ"]
    if len(roots) == 1 and role_of[top["id"]] == "خبر" and 0 < len(subjects) < len(children_of[top["id"]]):
        children_of[top["id"]] = [kid for kid in children_of[top["id"]] if kid not in subjects]
        roots = subjects + roots
    root = roots[0]

    seen: set[int] = set()

    def node(token: dict) -> dict:
        # the parser can hand back two words pointing at each other; a word already
        # drawn is left as a leaf rather than followed round the circle again
        seen.add(token["id"])
        kids = [kid for kid in children_of[token["id"]] if kid["id"] not in seen]
        index = at[token["id"]]
        if not kids:
            leaf = _leaf(index, role_of[token["id"]], why_of[token["id"]])
            # a صلة of one verb is still a clause, its doer the pronoun hidden in it
            return {"role": "صلة", "label": VERBAL, "tone": tone("صلة"), "children": [leaf]}                 if job_of[token["id"]] == "صلة" else leaf
        kid_roles = [job_of[kid["id"]] for kid in kids if job_of[kid["id"]]]
        seen.update(kid["id"] for kid in kids)
        inside = [(at[kid["id"]], node(kid)) for kid in kids]
        role = role_of[token["id"]]
        why = why_of[token["id"]]
        # a word the teacher dashed stays a dash at the head of its unit: مضاف would name it
        inside.append((index, _leaf(index, role if why else _unit_role(role, kid_roles), why)))
        label = _label(token, kid_roles) or (_sentence_label(role_of, bases) if token is root
                                             else VERBAL if job_of[token["id"]] == "صلة" else "")
        # A particle's name is what it is, not a job for the unit it heads: the
        # parser gives no job for a jar-majroor or a clause under إِذَا, so none
        # is written rather than calling the whole unit a حرف. The clause a كاد-type
        # verb is finished by is that verb's khabar as a whole.
        job = "خبر كاد" if completes_kaada(token, tokens) else (
            None if token is root or token["pos"] == "PRT" else job_of[token["id"]])
        return {"role": job,
                "label": label,
                "tone": tone(job or role),
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
