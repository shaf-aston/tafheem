"""Grow's paths: what to learn to say, in order, and a scholar's words on each.

Read from hand-written files and served as they are: data/grow/sources.json
names every book quoted, and data/grow/worlds/<world>/ holds a world's paths,
one file each. Nothing here judges a recitation (that is /api/listen/check
and /check-text) and nothing here makes a ruling: every ruling in the files
is a scholar's own sentence, quoted.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

from backend.config import data_path
from backend.models.grow import GrowPath

router = APIRouter(prefix="/api/grow", tags=["grow"])


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def sources() -> dict[str, dict]:
    """Every book quoted, by id: who wrote it and where its text is."""
    return _read(data_path("grow_dir") / "sources.json")["sources"]


def _with_author(step: dict, books: dict[str, dict]) -> dict:
    """A step's ruling with its book's name and author filled in from sources.json."""
    ruling = step.get("ruling")
    if not ruling:
        return step
    book = books[ruling["source"]]
    named = {key: book[key] for key in ("book", "author", "known_as")}
    return {**step, "ruling": {**named, **ruling}}


@lru_cache(maxsize=None)
def world_paths(world: str) -> list[GrowPath]:
    """A world's paths, in the order its world.json names them. Read once."""
    folder = data_path("grow_dir") / "worlds" / world
    books = sources()
    paths = []
    for name in _read(folder / "world.json")["paths"]:
        raw = _read(folder / "paths" / f"{name}.json")
        paths.append(GrowPath(**{**raw, "steps": [_with_author(step, books) for step in raw["steps"]]}))
    return paths


def paths() -> list[GrowPath]:
    """The Prayer world's paths, the one path world so far."""
    return world_paths("prayer")


@router.get("/paths", response_model=list[GrowPath])
async def all_paths() -> list[GrowPath]:
    return paths()
