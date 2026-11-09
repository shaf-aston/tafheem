"""docs/glossary/nahw-flow.md is the map of the nahw engine: it must name files that exist and
list each stage's rules exactly as the code registers them, in the code's order."""
import json
import re
from pathlib import Path

from backend.services.nahw.syntax import mask, teacher
from backend.services.nahw.syntax.facts import AXES
from backend.services.nahw.syntax.repair import PASSES

ROOT = Path(__file__).resolve().parents[2]
DOC = (ROOT / "docs/glossary/nahw-flow.md").read_text(encoding="utf-8")
# One glossary list entry is a name, one plain line and its file; the detail is in the function's docstring.
# Just above the median entry when this cap was set (179 characters).
ENTRY_MAX = 200


def _entries(name: str = r"\w+") -> list[str]:
    bodies = re.findall(rf"<!-- list:{name} -->\n(.*?)<!-- /list -->", DOC, re.S)
    return [line for body in bodies for line in body.splitlines() if line.startswith("- ")]


def _listed(name: str) -> list[str]:
    return [line[2:].split(":")[0].strip() for line in _entries(name)]


def _leaves(node: dict) -> list[str]:
    return [node["role"]] if "role" in node else [r for kid in node["children"] for r in _leaves(kid)]


def test_every_path_named_exists():
    paths = set(re.findall(r"`((?:backend|tests|docs)/[^`\s]+)`", DOC))
    assert paths and not [p for p in paths if not (ROOT / p).exists()]


def test_the_repair_order_is_the_codes():
    # book_links runs first, PASSES between, and untangle after each of them (listed once, last)
    assert _listed("repair") == ["book_links", *(repair.__name__ for repair, _ in PASSES), "untangle"]


def test_a_list_entry_is_one_short_line():
    assert [e[:40] for e in _entries() if len(e) > ENTRY_MAX] == []


def test_the_rule_registries_match():
    assert _listed("vetoes") == list(mask._VETOES)
    assert _listed("links") == list(mask._LINKS)
    assert _listed("checks") == list(teacher.CHECKS)
    assert _listed("axes") == list(AXES)


def test_the_roles_are_the_trees_leaves():
    tree = json.loads((ROOT / "backend/data/nahw_rules/naming_tree.json").read_text(encoding="utf-8"))
    assert _listed("roles") == sorted(set(_leaves(tree.get("tree", tree))))
