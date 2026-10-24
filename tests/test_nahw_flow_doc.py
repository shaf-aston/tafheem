"""docs/glossary/nahw-flow.md is the map of the nahw engine: it must name files that exist and
list each stage's rules exactly as the code registers them, in the code's order."""
import ast
import inspect
import json
import re
from pathlib import Path

from backend.services.nahw.syntax import mask, teacher
from backend.services.nahw.syntax.facts import AXES
from backend.services.nahw.syntax.repair import correct

ROOT = Path(__file__).resolve().parents[1]
DOC = (ROOT / "docs/glossary/nahw-flow.md").read_text(encoding="utf-8")


def _listed(name: str) -> list[str]:
    body = re.search(rf"<!-- list:{name} -->\n(.*?)<!-- /list -->", DOC, re.S).group(1)
    return [line[2:].split(":")[0].strip() for line in body.splitlines() if line.startswith("- ")]


def _leaves(node: dict) -> list[str]:
    return [node["role"]] if "role" in node else [r for kid in node["children"] for r in _leaves(kid)]


def test_every_path_named_exists():
    paths = set(re.findall(r"`((?:backend|tests|docs)/[^`\s]+)`", DOC))
    assert paths and not [p for p in paths if not (ROOT / p).exists()]


def test_the_repair_order_is_the_codes():
    calls = [n.func for n in ast.walk(ast.parse(inspect.getsource(correct))) if isinstance(n, ast.Call)]
    names = [f.attr if isinstance(f, ast.Attribute) else f.id for f in calls]
    assert _listed("repair") == [n for n in names if n not in ("len", "base_tokens")]


def test_the_rule_registries_match():
    assert _listed("vetoes") == list(mask._VETOES)
    assert _listed("links") == list(mask._LINKS)
    assert _listed("checks") == list(teacher.CHECKS)
    assert _listed("axes") == list(AXES)


def test_the_roles_are_the_trees_leaves():
    tree = json.loads((ROOT / "backend/data/nahw_rules/naming_tree.json").read_text(encoding="utf-8"))
    assert _listed("roles") == sorted(set(_leaves(tree.get("tree", tree))))
