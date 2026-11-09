"""Hanging words in and out of units, and the small predicates that read the hanging."""
from __future__ import annotations

from backend.services.nahw.syntax.picture.names import QUIET_UNDER_JOB

# the roles that stay inside the unit their head names (a صفة of the مضاف إليه, a عطف on it)
def quieted(node: dict) -> dict:
    """مفعول به, not مفعول به / مركب إضافي: a unit wearing a job leaves off the name of what it
    is made of (roles.json units `quiet_under_job`); one with no job keeps it."""
    label = "" if node.get("role") and node.get("label") in QUIET_UNDER_JOB else node.get("label")
    return {**node, **({"label": label} if "label" in node else {}),
            **({"children": [quieted(kid) for kid in node["children"]]} if node.get("children") else {})}


def unbracket(node: dict) -> dict:
    """A brace with no name and no job says nothing (وَ with its معطوف, the books name
    neither the pair nor the unit), so its words are drawn under the brace above it."""
    if node.get("word") is not None or "children" not in node:
        return node
    children = []
    for kid in map(unbracket, node["children"]):
        bare = kid.get("word") is None and "children" in kid and not kid.get("label") and not kid.get("role")
        children.extend(kid["children"] if bare else [kid])
    return {**node, "children": children}


def definite(token: dict) -> bool:
    """ال, a مضاف, a name or a pronoun stuck on it makes a noun known."""
    return token.get("stt") in ("d", "c") or token["pos"] == "PROP" or bool(token.get("stuck_on"))


def move_to(holder: dict[int, list[dict]], token: dict, to: list[dict]) -> None:
    """Hang a word in another unit: off the list that holds it, onto `to`."""
    to.append(take_from(holder, token))
    holder[token["id"]] = to


def take_from(holder: dict[int, list[dict]], token: dict) -> dict:
    """Off the list that holds it, by its id: the picture's own token, which may carry more
    than the one asked with (6:139's answer هم did, and a list.remove of it failed)."""
    kids = holder[token["id"]]
    return kids.pop(next(i for i, kid in enumerate(kids) if kid["id"] == token["id"]))


def hangs_under(token: dict, top: dict, by_id: dict[int, dict]) -> bool:
    """Whether a word is `top` or hangs under it, read up its heads: for the parser's links,
    before `children_of` is made (`is_inside` reads down it)."""
    while token is not None and token["id"] != top["id"]:
        token = by_id.get(token["head"])
    return token is not None


def is_inside(token: dict, top: dict, children_of: dict[int, list[dict]]) -> bool:
    """Whether a word hangs anywhere under `top`."""
    below = list(children_of[top["id"]])
    while below:
        kid = below.pop()
        if kid["id"] == token["id"]:
            return True
        below += children_of[kid["id"]]
    return False
