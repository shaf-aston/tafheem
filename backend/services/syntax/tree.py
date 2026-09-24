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

from backend.services.syntax.naming import tone

# What a unit is called, by the join that makes it
IDAFA = "مُرَكَّبٌ إِضَافِيٌّ"
WASF = "مُرَكَّبٌ تَوْصِيْفِيٌّ"
JARR = "جَارٌّ وَمَجْرُوْرٌ"
VERBAL = "جُمْلَةٌ فِعْلِيَّةٌ"
NOMINAL = "جُمْلَةٌ اِسْمِيَّةٌ"
QUESTION = "جُمْلَةٌ إِنْشَائِيَّةٌ اِسْتِفْهَامِيَّةٌ"


def _leaf(index: int, role: str | None) -> dict:
    """One word on its own. No role means the rules could not name it."""
    return {"word": index, "role": role, "tone": tone(role), "gap": role is None}


def _label(head: dict, child_roles: list[str]) -> str:
    """What the unit this word heads is called."""
    if head["pos"] == "PRT" and "مجرور" in child_roles:
        return JARR
    if "مضاف إليه" in child_roles:
        return IDAFA
    if "نعت" in child_roles:
        return WASF
    return ""


def _unit_role(role: str | None, child_roles: list[str]) -> str | None:
    """What the head word is called inside its own unit.

    On its own it is a مبتدأ; inside كِتَابُ الطَّالِبِ it is the مضاف and the
    unit as a whole is the مبتدأ, which is how the books draw it.
    """
    if "مضاف إليه" in child_roles:
        return "مضاف"
    if "نعت" in child_roles:
        return "موصوف"
    return role


def _sentence_label(root: dict, roles: dict[int, str | None], tokens: list[dict]) -> str:
    if any("interrog" in t.get("pos_camel", "") for t in tokens):
        return QUESTION
    return VERBAL if roles.get(root["id"]) == "فعل" else NOMINAL


def build(words: list[str], tokens: list[dict], named: list[dict]) -> dict:
    """The tree for one typed sentence, ready for the diagram.

    `named` is what `naming.roles` returned, one entry per typed word.
    """
    bases = [t for t in tokens if t.get("token_type") == "baseword"]
    if len(bases) != len(words):
        bases = [t for t in tokens if not t["form"].startswith("+")]
    if not words or len(bases) != len(words) or len(named) != len(words):
        return {"words": words, "tree": {"gap": True}, "coverage": 0.0}

    at = {token["id"]: index for index, token in enumerate(bases)}
    role_of = {token["id"]: found["role"] for token, found in zip(bases, named)}
    children_of: dict[int, list[dict]] = {token["id"]: [] for token in bases}
    roots = []
    for token in bases:
        if token["head"] in children_of and token["head"] != token["id"]:
            children_of[token["head"]].append(token)
        else:
            roots.append(token)
    roots = roots or [bases[0]]
    root = roots[0]

    seen: set[int] = set()

    def node(token: dict) -> dict:
        # the parser can hand back two words pointing at each other; a word already
        # drawn is left as a leaf rather than followed round the circle again
        seen.add(token["id"])
        kids = [kid for kid in children_of[token["id"]] if kid["id"] not in seen]
        index = at[token["id"]]
        if not kids:
            return _leaf(index, role_of[token["id"]])
        kid_roles = [role_of[kid["id"]] for kid in kids if role_of[kid["id"]]]
        seen.update(kid["id"] for kid in kids)
        inside = [(at[kid["id"]], node(kid)) for kid in kids]
        inside.append((index, _leaf(index, _unit_role(role_of[token["id"]], kid_roles))))
        role = role_of[token["id"]]
        label = _label(token, kid_roles) or (_sentence_label(token, role_of, bases)
                                             if token is root else "")
        return {"role": None if token is root else role,
                "label": label,
                "tone": tone(role),
                # right to left, so the picture reads in the order they were typed
                "children": [drawn for _, drawn in sorted(inside, key=lambda pair: pair[0])]}

    # the parser can leave a sentence as two loose halves; they are still one
    # sentence, so they are drawn side by side under it rather than one dropped
    drawn = sorted(((at[part["id"]], node(part)) for part in roots), key=lambda pair: pair[0])
    tree = drawn[0][1] if len(drawn) == 1 else None
    if tree is None or tree.get("word") is not None or not tree.get("label"):
        tree = {"label": _sentence_label(root, role_of, bases),
                "children": [part for _, part in drawn] if tree is None else [tree]}
    covered = sum(1 for found in named if found["role"])
    return {"words": words, "tree": tree, "coverage": round(covered / len(words), 2)}


def is_drawable(tree: dict) -> bool:
    """False when nothing could be joined, so the page shows the cards alone."""
    return bool(tree.get("tree", {}).get("children")) and tree.get("coverage", 0) > 0
