"""Heard sounds against expected ones, word by word. Pure: symbols in, verdicts out; the standard
library only, so the server (sounds.py), the research yardstick (score_phoneme_checker.py) and
the Kaggle training judge (finetune_sounds, which ships this file as it is) all mean the same by
"wrong"."""
from __future__ import annotations

import difflib
import itertools

# <pad> is the CTC blank and <unk> says nothing; neither is a sound.
SILENT = (0, 1)
# Ikhfaa, idgham, iqlab, ghunnah and qalqalah symbols: out of scope, dropped from
# the expected sounds and from what was heard, so neither side is judged on them.
TAJWEED_EXCLUDE = frozenset({"m̃", "ñ", "j̃", "w̃", "ŋ", "Q"})
VOWELS = frozenset({"a", "a:", "i", "i:", "u", "u:", "aˤ", "aˤ:"})


def collapse(ids, id2sym: dict[int, str]) -> tuple[list[str], list[int]]:
    """Greedy CTC decode: the symbols, repeats merged, silent moments and tajweed
    symbols dropped, and how many moments (frames) each one was held for, in the
    same order."""
    symbols, runs = [], []
    for sym_id, group in itertools.groupby(ids):
        if sym_id in SILENT or id2sym[sym_id] in TAJWEED_EXCLUDE:
            continue
        symbols.append(id2sym[sym_id])
        runs.append(sum(1 for _ in group))
    return symbols, runs


def flatten(ph_by_word) -> tuple[list[str], list[int]]:
    """Expected sounds, tajweed symbols dropped, with each one's word index."""
    flat, idx = [], []
    for w, word in enumerate(ph_by_word):
        for p in word:
            if p in TAJWEED_EXCLUDE:
                continue
            flat.append(p)
            idx.append(w)
    return flat, idx


def word_verdicts(opcodes, ref_flat: list[str], ref_word_idx: list[int], n_words: int):
    """Per expected word: True (every sound of that kind matched), False (one
    was substituted or dropped), or None (the word has none of that kind)."""
    bad = [False] * len(ref_flat)
    for tag, a1, a2, _b1, _b2 in opcodes:
        if tag in ("replace", "delete"):
            for i in range(a1, a2):
                bad[i] = True
    artic: list[bool | None] = [None] * n_words
    length: list[bool | None] = [None] * n_words
    for i, w in enumerate(ref_word_idx):
        ok = not bad[i]
        if ref_flat[i] in VOWELS:
            length[w] = ok if length[w] is None else (length[w] and ok)
        else:
            artic[w] = ok if artic[w] is None else (artic[w] and ok)
    return artic, length


def heard_by_word(opcodes, ref_word_idx: list[int], heard: list[str], n_words: int) -> list[list[str]]:
    """The heard sounds filed under the word they line up with. A swapped sound
    goes to the word it replaced; an extra one between two expected sounds to the
    word before it; extras before the first or after the last are outside the
    words asked about and are left out."""
    out: list[list[str]] = [[] for _ in range(n_words)]
    for tag, a1, a2, b1, b2 in opcodes:
        if tag == "equal":
            for k in range(b2 - b1):
                out[ref_word_idx[a1 + k]].append(heard[b1 + k])
        elif tag == "replace":
            for k in range(b2 - b1):
                out[ref_word_idx[a1 + min(k, a2 - a1 - 1)]].append(heard[b1 + k])
        elif tag == "insert" and 0 < a1 < len(ref_word_idx):
            out[ref_word_idx[a1 - 1]] += heard[b1:b2]
    return out


def compare(expected_per_word, heard: list[str]) -> list[dict | None]:
    """Per expected word {heard, expected, letter_ok, vowel_ok}, or None for a
    word with no expected sounds. `heard` is the decode, tajweed symbols dropped.

    letter_ok: no consonant substituted or dropped. vowel_ok: no vowel
    substituted, dropped or held the wrong length (a long one decoded short or the
    other way is a different symbol). A word with none of a kind passes it.
    """
    n = len(expected_per_word)
    ref, owner = flatten(expected_per_word)
    opcodes = difflib.SequenceMatcher(a=ref, b=heard, autojunk=False).get_opcodes()
    letter, vowel = word_verdicts(opcodes, ref, owner, n)
    said = heard_by_word(opcodes, owner, heard, n)
    expected = [[] for _ in range(n)]
    for p, w in zip(ref, owner):
        expected[w].append(p)
    return [
        {"heard": said[w], "expected": expected[w], "letter_ok": letter[w] is not False,
         "vowel_ok": vowel[w] is not False} if expected[w] else None
        for w in range(n)
    ]
