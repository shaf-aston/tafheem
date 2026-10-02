"""Walks the book's classification tree to a word's role.

The tree (data/nahw_rules/naming_tree.json) holds the divisions of the nahw book;
this module only reads it. A branch splits on one axis (facts.py) and each child
takes one answer, so a word can reach at most one leaf by construction. The leaf
it ends on is its role, with the path of branch names as the book section that
decided it.

Pure and offline; a malformed tree fails loud on first use.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import NamedTuple

from backend.services.nahw_book import RULES, role_table
from backend.services.syntax.facts import AXES

TREE_FILE = RULES / "naming_tree.json"
# a book reference is the Tasheel section and its page: "3.1 p60"
BOOK_REF = re.compile(r"\d+(\.\d+)* p\d+")


class Walked(NamedTuple):
    """The leaf a word reached: its role, the branch names from the root down, the leaf's book section."""
    role: str
    path: list[str]
    book: str


def _answers(child: dict) -> list[str]:
    """The answers a child takes: `is` is one answer or a list of them."""
    answer = child["is"]
    return [answer] if isinstance(answer, str) else list(answer)


def validate(node: dict, axes: dict = AXES, roles: dict | None = None, left: dict | None = None) -> None:
    """Raise ValueError naming the branch if the node or any below it is malformed.

    `left` maps an axis to the answers that can still reach this node: a split on an axis
    already split above may use only the answers its parent child took (the rest, for an
    `else`), so a nested branch can never name an answer it cannot be given."""
    roles = role_table() if roles is None else roles
    left = left or {}
    branch = node.get("branch")
    if not branch or not BOOK_REF.fullmatch(node.get("book") or ""):
        raise ValueError(f"naming tree: a node needs `branch` and a `book` like '3.1 p60': {node!r}")
    if ("children" in node) == ("role" in node):
        raise ValueError(f"naming tree: {branch} needs exactly one of `children` or `role`")
    if "role" in node:
        if node["role"] not in roles:
            raise ValueError(f"naming tree: {branch} names unknown role {node['role']!r}")
        return
    children = node["children"]
    if not children:
        raise ValueError(f"naming tree: {branch} has empty `children`: fill every branch or delete it")
    axis = node.get("split")
    if axis not in axes:
        raise ValueError(f"naming tree: {branch} splits on unknown axis {axis!r}")
    allowed = left.get(axis, axes[axis][0])
    taken, elses = [], 0
    for child in children:
        if ("is" in child) == ("else" in child):
            raise ValueError(f"naming tree: {child.get('branch')} needs exactly one of `is` or `else`")
        if "else" in child:
            if child["else"] is not True:
                raise ValueError(f"naming tree: {child.get('branch')} `else` must be true")
            elses += 1
        else:
            for answer in _answers(child):
                if answer not in allowed:
                    raise ValueError(f"naming tree: {child.get('branch')} is {answer!r}, not one of {allowed}")
                taken.append(answer)
    if elses > 1:
        raise ValueError(f"naming tree: {branch} has more than one `else`")
    if len(taken) != len(set(taken)):
        raise ValueError(f"naming tree: {branch} has two children for the same answer")
    rest = tuple(answer for answer in allowed if answer not in taken)
    if elses and not rest:
        raise ValueError(f"naming tree: {branch} has an `else` but its other children take every answer")
    for child in children:
        validate(child, axes, roles, {**left, axis: tuple(_answers(child)) if "is" in child else rest})


@lru_cache(maxsize=1)
def load() -> dict:
    tree = json.loads(TREE_FILE.read_text(encoding="utf-8"))["tree"]
    validate(tree)
    return tree


def walk(values: dict[str, str], tree: dict | None = None) -> Walked | None:
    """The leaf the word reaches, or None where the tree has no child for it."""
    node = tree or load()
    path = [node["branch"]]
    while "children" in node:
        value = values[node["split"]]
        node = (next((c for c in node["children"] if "is" in c and value in _answers(c)), None)
                or next((c for c in node["children"] if "else" in c), None))
        if node is None:
            return None
        path.append(node["branch"])
    return Walked(node["role"], path, node["book"])
