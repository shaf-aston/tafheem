"""The bracket picture (tarkeeb) for a typed sentence, from the same links.

The cards say what each word is; this says which words join into a unit and what
that unit does. Both come from one reading, so the page can never show a word as
a فاعل in the cards and as something else in the picture.

Shape and wording follow the book examples in `data/tarkeeb/examples`, so a typed
sentence and a book example draw the same way: a unit carries what it **is**
(`label`) and what it **does** (`role`), a leaf carries its role and the index of
its word, and a word no rule could name is left as a gap rather than guessed.

`build` runs the phases in `picture/` in order over one shared `Picture`.
"""
from __future__ import annotations

from backend.services.nahw.syntax.naming import base_tokens
from backend.services.nahw.syntax.picture.condition import draw_conditions
from backend.services.nahw.syntax.picture.jobs import give_jobs, give_names
from backend.services.nahw.syntax.picture.layout import lay_out
from backend.services.nahw.syntax.picture.places import place_clauses
from backend.services.nahw.syntax.picture.rehang import rehang
from backend.services.nahw.syntax.picture.render import draw, find_doers
from backend.services.nahw.syntax.picture.state import Picture
from backend.services.nahw.syntax.picture.units import group_into_units
from backend.services.nahw.syntax.picture.unwritten import add_unwritten_khabars, add_unwritten_verbs


def build(words: list[str], tokens: list[dict], named: list[dict]) -> dict:
    """The tree for one typed sentence, ready for the diagram.

    `named` is what `naming.roles` returned, one entry per typed word.
    """
    bases = base_tokens(words, tokens)
    if not words or len(bases) != len(words) or len(named) != len(words):
        return {"words": words, "tree": {"gap": True}, "coverage": 0.0}
    picture = Picture(words, tokens, named, bases)
    for phase in (lay_out, rehang, add_unwritten_khabars, add_unwritten_verbs, give_jobs, give_names, place_clauses,
                  group_into_units, draw_conditions, find_doers):
        phase(picture)
    return draw(picture)


def is_drawable(tree: dict) -> bool:
    """False when nothing could be joined, so the page shows the cards alone."""
    return bool(tree.get("tree", {}).get("children")) and tree.get("coverage", 0) > 0
