"""Verbally similar verses (mutashabihat): the catalogue, and a finder for what it misses.

The catalogue (data/quran/mutashabihat.json) is what scholars recorded, built by
scripts/build_mutashabihat.py. The finder is a 2-word shingle index over the
whole Qur'an, built lazily on first call. It only ever proposes; a proposal is
never added to the catalogue without a person reading it.

Word spans are [start, end) indexes into the imlaei text split on whitespace, so
the page can highlight them. Comparison is on folded words, never on the display.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from functools import lru_cache

from backend.config import data_path, get_settings
from backend.services.arabic_text import bare_letters


def fold(text: str) -> str:
    """Letters only: marks stripped, alef and ya unified (bare_letters), ta marbuta as ha."""
    return bare_letters(text).replace("ة", "ه")


def _folded(words: list[str]) -> tuple[list[str], list[int]]:
    """Folded words with their original positions; pause marks fold to nothing and drop out."""
    kept = [(i, fold(word)) for i, word in enumerate(words)]
    kept = [(i, word) for i, word in kept if word]
    return [word for _, word in kept], [i for i, _ in kept]


def _span(at: list[int], start: int, end: int) -> list[int]:
    """Folded-list range back to a [start, end) range of original word positions."""
    return [at[start], at[end - 1] + 1]


def diff(words_a: list[str], words_b: list[str]) -> tuple[list[list[int]], list[list[int]]]:
    """Where two verses differ: spans in a, spans in b.

    A replacement marks both sides, an addition only the side that has the extra
    words. Spans are over the words as given. Same words in another order show as
    a move: the aligner keeps the longest common run and marks the rest.
    """
    folded_a, at_a = _folded(words_a)
    folded_b, at_b = _folded(words_b)
    spans_a: list[list[int]] = []
    spans_b: list[list[int]] = []
    for tag, a0, a1, b0, b1 in SequenceMatcher(None, folded_a, folded_b, autojunk=False).get_opcodes():
        if tag == "equal":
            continue
        if a1 > a0:
            spans_a.append(_span(at_a, a0, a1))
        if b1 > b0:
            spans_b.append(_span(at_b, b0, b1))
    return spans_a, spans_b


def pair_key(a: str, b: str) -> tuple[str, str]:
    """One order for a pair, so (a, b) and (b, a) are the same pair."""
    return tuple(sorted((a, b), key=lambda k: tuple(map(int, k.split(":")))))  # type: ignore[return-value]


@lru_cache(maxsize=1)
def texts() -> dict[str, str]:
    """Every ayah in vowelled spelling, "s:a" -> text."""
    return json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _catalogue() -> dict:
    path = data_path("mutashabihat_path")
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"groups": []}


@lru_cache(maxsize=1)
def _by_key() -> dict[str, list[tuple[dict, dict]]]:
    """key -> [(pair, group)] for every pair the verse is in."""
    index: dict[str, list[tuple[dict, dict]]] = defaultdict(list)
    for group in _catalogue()["groups"]:
        for pair in group["pairs"]:
            index[pair["a"]].append((pair, group))
            index[pair["b"]].append((pair, group))
    return index


def catalogued_pairs() -> set[tuple[str, str]]:
    return {pair_key(p["a"], p["b"]) for g in _catalogue()["groups"] for p in g["pairs"]}


def partners(key: str) -> list[dict]:
    """Catalogued partners of a verse, each with its text, both diffs, type and sources."""
    out = []
    for pair, _ in _by_key().get(key, []):
        mine = pair["a"] == key
        other = pair["b"] if mine else pair["a"]
        out.append({
            "key": other,
            "text": texts()[other],
            "diff_self": pair["diff_a"] if mine else pair["diff_b"],
            "diff_other": pair["diff_b"] if mine else pair["diff_a"],
            "change_type": pair["change_type"],
            "sources": pair["sources"],
        })
    return sorted(out, key=lambda p: tuple(map(int, p["key"].split(":"))))


def surah_groups(surah: int) -> list[dict]:
    """Every group with a verse in this surah, once each, in id order."""
    prefix = f"{surah}:"
    seen = {id(g): g for k, rows in _by_key().items() if k.startswith(prefix) for _, g in rows}
    return sorted(seen.values(), key=lambda g: g["id"])


# The finder ----------------------------------------------------------------

@lru_cache(maxsize=1)
def _index() -> tuple[dict[str, set[tuple[str, ...]]], dict[tuple[str, ...], list[str]]]:
    """(shingles of each verse, verses holding each shingle), stock phrases left out."""
    cfg = get_settings()
    size = cfg.mutashabihat_shingle_size
    per_verse: dict[str, set[tuple[str, ...]]] = {}
    holders: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for key, text in texts().items():
        words, _ = _folded(text.split())
        grams = {tuple(words[i:i + size]) for i in range(len(words) - size + 1)}
        per_verse[key] = grams
        for gram in grams:
            holders[gram].append(key)
    common = [g for g, keys in holders.items() if len(keys) > cfg.mutashabihat_shingle_cap]
    for gram in common:
        del holders[gram]
    return per_verse, holders


def _scores(key: str) -> dict[str, float]:
    per_verse, holders = _index()
    mine = per_verse.get(key, set())
    shared: Counter[str] = Counter()
    for gram in mine:
        for other in holders.get(gram, ()):
            if other != key:
                shared[other] += 1
    return {other: n / min(len(mine), len(per_verse[other])) for other, n in shared.items()}


def candidates(key: str, limit: int | None = None) -> list[str]:
    """Verses most like this one, best first: shared shingles over the shorter verse's."""
    limit = limit or get_settings().mutashabihat_candidate_limit
    ranked = sorted(_scores(key).items(), key=lambda kv: (-kv[1], tuple(map(int, kv[0].split(":")))))
    return [other for other, _ in ranked[:limit]]


def propose(limit: int | None = None) -> list[dict]:
    """High-scoring pairs the catalogue lacks, for a person to review. Never auto-added."""
    cfg = get_settings()
    limit = limit or cfg.mutashabihat_propose_limit
    known = catalogued_pairs()
    found: dict[tuple[str, str], float] = {}
    for key in texts():
        for other, score in _scores(key).items():
            pair = pair_key(key, other)
            if score >= cfg.mutashabihat_propose_min_score and pair not in known:
                found[pair] = score
    top = sorted(found.items(), key=lambda kv: (-kv[1], kv[0][0], kv[0][1]))[:limit]
    return [{"a": a, "b": b, "score": round(score, 3), "diff_a": d[0], "diff_b": d[1]}
            for (a, b), score in top
            for d in [diff(texts()[a].split(), texts()[b].split())]]
