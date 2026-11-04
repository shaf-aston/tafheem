"""Grow's paths: what to learn to say, in order, and a scholar's words on each.

Read from hand-written files and served as they are: data/grow/sources.json
names every book quoted, and data/grow/worlds/<world>/ holds a world's paths
and units, one file each. Nothing here judges a recitation (that is /api/listen/check) and nothing here makes a ruling: every ruling in the files
is a scholar's own sentence, quoted.

The Grow tab's Prayer world reads /worlds/prayer (frontend lib/grow/usePrayerWorld.js):
its phrases to say, from wudu to the adhkar, become lessons there. /paths is
the same paths alone, kept for any caller that wants only them.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.config import data_path
from backend.models.grow import GrowPath, GrowUnit, GrowWorld

router = APIRouter(prefix="/api/grow", tags=["grow"])
WORLD_ID = re.compile(r"[a-z-]+")  # a folder's name, never a path


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def sources() -> dict[str, dict]:
    """Every book quoted, by id: who wrote it and where its text is."""
    return _read(data_path("grow_dir") / "sources.json")["sources"]


def _with_author(card: dict, books: dict[str, dict]) -> dict:
    """A step or card with each quote's book name and author filled in from
    sources.json: a step's `ruling`, a ruling card's `quote` and `why`, and
    every position's `quote` on a difference card."""
    filled = dict(card)
    for key in ("ruling", "quote", "why"):
        if card.get(key):
            book = books[card[key]["source"]]
            named = {name: book[name] for name in ("book", "author", "known_as")}
            filled[key] = {**named, **card[key]}
    if "positions" in card:
        filled["positions"] = [_with_author(position, books) for position in card["positions"]]
    return filled


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


@lru_cache(maxsize=None)
def world(name: str) -> GrowWorld:
    """A world whole: its levels, its paths and its units, in world.json's order. Read once."""
    folder = data_path("grow_dir") / "worlds" / name
    raw = _read(folder / "world.json")
    books = sources()
    units = []
    for file in raw["units"]:
        unit = _read(folder / file)
        units.append(GrowUnit(**{**unit, "cards": [_with_author(card, books) for card in unit["cards"]]}))
    return GrowWorld(id=name, levels=raw["levels"], paths=world_paths(name), units=units)


@router.get("/paths", response_model=list[GrowPath])
async def all_paths() -> list[GrowPath]:
    return paths()


@router.get("/worlds/{world_id}", response_model=GrowWorld)
async def one_world(world_id: str) -> GrowWorld:
    if not WORLD_ID.fullmatch(world_id) or not (data_path("grow_dir") / "worlds" / world_id / "world.json").is_file():
        raise HTTPException(status_code=404, detail=f"no world {world_id!r}")
    return world(world_id)
