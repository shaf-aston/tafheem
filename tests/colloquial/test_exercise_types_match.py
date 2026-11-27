"""The server and the page name the same exercise types.

A type the server sends with no renderer on the page shows a plain note instead
of the exercise; a renderer the server never sends is dead code. Both registries
say they must match, and this is the check that holds them to it.
"""
import re
from pathlib import Path

from backend.services.colloquial.exercises.registry import TYPES

PAGE_REGISTRY = Path(__file__).parents[2] / "frontend/src/components/colloquial/exercises/registry.js"


def test_page_and_server_name_the_same_exercise_types():
    table = re.search(r"const EXERCISES = \{(.*?)\n\}", PAGE_REGISTRY.read_text(encoding="utf-8"), re.S).group(1)
    page = set(re.findall(r"^\s+(\w+):", table, re.M))
    assert page == set(TYPES)
