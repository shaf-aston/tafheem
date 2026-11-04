"""The judge: does the trained model flag fewer correct words than the untuned one, without going deaf to slips?
Plain numbers in, plain numbers out, so checks/judge_cases.py can prove it anywhere. Hearing the clips is hear.py."""
import difflib

import numpy as np
from ear.judge import gain, wrong
from sound_compare import compare, flatten

from . import settings as S

GROUPS = ('right', 'letter', 'vowel')
# The reviewer's kind of mark to the group its word is tallied in. No mark is a correct word; tajweed is absent: left out.
GROUP_OF = {None: 'right', 'letter or word': 'letter', 'vowel': 'vowel'}


def counts(clip, heard):
    """(match rate, array [group][flagged, words]) for one recording: its reference words against the symbols heard."""
    ref, _ = flatten(clip['ref'])
    matched = sum(b.size for b in difflib.SequenceMatcher(a=ref, b=heard, autojunk=False).get_matching_blocks())
    out = np.zeros((len(GROUPS), 2), dtype=np.int64)
    for kind, word in zip(clip['kinds'], compare(clip['ref'], heard)):
        if (group := GROUP_OF.get(kind)) is not None and word is not None:
            out[GROUPS.index(group)] += (not (word['letter_ok'] and word['vowel_ok']), 1)
    return (round(matched / len(ref), 3) if ref else None), out


def tally(clips, heard, rates=None):
    """(array [recording][group][flagged, words], each recording's match rate). `rates` are the untuned model's:
    a recording under the floor holds only part of its ayah, so it is zeroed for every model alike."""
    pairs = [counts(c, h) for c, h in zip(clips, heard)]
    own = [rate for rate, _ in pairs]
    keep = np.array([r is not None and r >= S.MATCH_FLOOR for r in (own if rates is None else rates)])
    return np.array([row for _, row in pairs]) * keep[:, None, None], own


def errors(rows, group):
    """[wrong, words] per recording that has words in `group`. For correct words wrong = flagged; for slips
    wrong = missed, so a fall in either is a gain in the same sense: fewer wrong."""
    c = rows[:, GROUPS.index(group)]
    c = c[c[:, 1] > 0]
    return c if group == 'right' else np.stack([c[:, 1] - c[:, 0], c[:, 1]], 1)


def verdict(untuned, trained):
    """Keep `trained`? Each argument is tally()'s array for one model over the same recordings."""
    out = {}
    for g in GROUPS:
        before, after = errors(untuned, g), errors(trained, g)
        assert len(before) == len(after) and (before[:, 1] == after[:, 1]).all(), 'models were tallied on different words'
        share = (lambda c: wrong(c)) if g == 'right' else (lambda c: round(100 - wrong(c), 2))  # flagged, or caught, %
        # better: points fewer correct words flagged, or more slips caught. Positive is better in both.
        out[g] = {'untuned': share(before), 'trained': share(after), 'words': int(before[:, 1].sum()),
                  'better': gain(before, after)}
    drop, vowel = out['right']['better'], out['vowel']['better']
    why = {'drops': bool(drop['points'] >= S.DROP_MIN and drop['low'] > 0),
           'vowel_holds': bool(vowel['points'] >= -S.VOWEL_FALL_MAX)}
    return {**out, 'keep': all(why.values()), 'why': why}


def edit_distance(a, b):
    """Symbols to change to turn list `a` into `b`: substitutions, deletions and insertions at one each."""
    row = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        prev, row[0] = row[0], i
        for j, y in enumerate(b, 1):
            prev, row[j] = row[j], min(row[j] + 1, row[j - 1] + 1, prev + (x != y))
    return row[-1]


def phoneme_errors(refs, heard):
    """[errors, reference symbols] per clip, every symbol counted, tajweed ones too: the model's own PER."""
    return np.array([(edit_distance(list(r), h), len(r)) for r, h in zip(refs, heard)], dtype=np.int64)


def self_check(rows):
    """The untuned model's own numbers must land where score_phoneme_checker.py put them, and it must not beat itself."""
    same = verdict(rows, rows)
    off = {g: (same[g]['untuned'], S.BASELINE[g]) for g in GROUPS if abs(same[g]['untuned'] - S.BASELINE[g]) > S.BASELINE_TOL[g]}
    if off:
        raise SystemExit(f'judge is broken: untuned model off its recorded baseline (now, recorded): {off}')
    if same['keep']:
        raise SystemExit('judge is broken: a model beat itself')
    return {g: same[g]['untuned'] for g in GROUPS}
