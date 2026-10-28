"""Phonemes judged word by word. Pure: symbols in, verdicts out, no model and no settings.
Shared by the research spike (score_phoneme_checker.py) and this loop's judge, so both mean the same by "wrong"."""
import difflib
import itertools

# Ikhfaa, idgham, iqlab, ghunnah, qalqalah symbols: out of scope by instruction, so they are
# stripped from the reference before anything is compared.
TAJWEED_EXCLUDE = frozenset({"m̃", "ñ", "j̃", "w̃", "ŋ", "Q"})
VOWELS = frozenset({"a", "a:", "i", "i:", "u", "u:", "aˤ", "aˤ:"})
BLANK, UNKNOWN = 0, 1  # this checkpoint's CTC convention (config.pad_token_id == 0)


def collapse(ids, id2sym):
    """Greedy CTC decode: collapsed symbols (blank and unknown dropped) and each one's run length in frames."""
    symbols, runs = [], []
    for sym_id, group in itertools.groupby(ids):
        n = sum(1 for _ in group)
        if sym_id in (BLANK, UNKNOWN):
            continue
        symbols.append(id2sym[sym_id])
        runs.append(n)
    return symbols, runs


def flatten(ph_by_word):
    """Reference phonemes, tajweed symbols dropped, with each one's word index."""
    flat, idx = [], []
    for w, word in enumerate(ph_by_word):
        for p in word:
            if p in TAJWEED_EXCLUDE:
                continue
            flat.append(p)
            idx.append(w)
    return flat, idx


def word_verdicts(opcodes, ref_flat, ref_word_idx, n_words):
    """Per expected word: True (every phoneme of that kind matched), False (one was substituted or
    dropped), or None (the word has none of that kind). Consonants are articulation, vowels are length."""
    bad = [False] * len(ref_flat)
    for tag, a1, a2, _b1, _b2 in opcodes:
        if tag in ("replace", "delete"):
            for i in range(a1, a2):
                bad[i] = True
    artic = [None] * n_words
    length = [None] * n_words
    for i, w in enumerate(ref_word_idx):
        ok = not bad[i]
        if ref_flat[i] in VOWELS:
            length[w] = ok if length[w] is None else (length[w] and ok)
        else:
            artic[w] = ok if artic[w] is None else (artic[w] and ok)
    return artic, length


def compare(ph_by_word, pred_flat):
    """(artic, length, ref_flat, opcodes, match_rate) of a decode against the reference words' phonemes."""
    ref_flat, ref_word_idx = flatten(ph_by_word)
    opcodes = difflib.SequenceMatcher(a=ref_flat, b=pred_flat, autojunk=False).get_opcodes()
    artic, length = word_verdicts(opcodes, ref_flat, ref_word_idx, len(ph_by_word))
    matched = sum(a2 - a1 for tag, a1, a2, _b1, _b2 in opcodes if tag == "equal")
    return artic, length, ref_flat, opcodes, (round(matched / len(ref_flat), 3) if ref_flat else None)


def flagged(artic, length):
    """True when the word is wrong by either test, None when neither test applied to it."""
    if artic is None and length is None:
        return None
    return artic is False or length is False
