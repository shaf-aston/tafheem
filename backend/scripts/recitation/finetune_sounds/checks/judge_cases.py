"""Does the sounds judge decide right, and would a bug in it be caught? CPU only, numpy only, seconds.

    python backend/scripts/recitation/finetune_sounds/checks/judge_cases.py

Planted cases with known answers run against sounds/judge.py and services/recitation/sound_compare.py: a word's phonemes against its
reference, then whole models against each other. Then each mutant (one small bug planted in judge.py) must change at
least one answer. A surviving mutant means the cases cannot see that rule."""
import sys
import types
from pathlib import Path

import numpy as np

LOOPS = Path(__file__).parents[2]
sys.path[:0] = [str(LOOPS / 'finetune_ear'), str(LOOPS / 'finetune_sounds')]
sys.path.append(str(LOOPS.parents[1] / 'services' / 'recitation'))  # sound_compare.py, as cloud.py ships it
from sounds import judge as real  # noqa: E402

REF = [['b', 'i', 's', 'm', 'i'], ['ll', 'a:', 'h', 'i'], ['rˤrˤ', 'a', 'ħ', 'm', 'a:', 'n', 'i']]
KINDS = [None, 'vowel', 'letter or word']  # a correct word, a vowel slip, a letter slip


def said(**edits):
    """REF as the model might write it: {'w1': ('a:', 'a')} turns word 1's a: into a, ('m', None) drops a symbol."""
    words = [[edits.get(f'w{n}', {}).get(p, p) for p in w] for n, w in enumerate(REF)]
    return [p for w in words for p in w if p is not None]


WORD_CASES = [  # (what, symbols heard, kinds, [right, letter, vowel] as [flagged, words])
    ('every symbol right', said(), KINDS, [[0, 1], [0, 1], [0, 1]]),
    ('long vowel heard short, in the vowel-slip word', said(w1={'a:': 'a'}), KINDS, [[0, 1], [0, 1], [1, 1]]),
    ('pharyngeal ħ heard as h, in the letter-slip word', said(w2={'ħ': 'h'}), KINDS, [[0, 1], [1, 1], [0, 1]]),
    ('a consonant dropped from the correct word', said(w0={'s': None}), KINDS, [[1, 1], [0, 1], [0, 1]]),
    ('a tajweed-only mark leaves the word out', said(w0={'s': None}), ['tajweed', 'vowel', 'letter or word'], [[0, 0], [0, 1], [0, 1]]),
    ('a vowel slip heard right is a miss, not a flag', said(), [None, 'vowel', None], [[0, 2], [0, 0], [0, 1]]),
]
RECORDED = np.array([[[229, 1000], [55, 100], [179, 200]]])  # the untuned model's baseline: right flagged 22.9%, letter 55%, vowel 89.5% caught
NASAL = [['ŋ', 'a', 'b']]  # a nasalised tajweed symbol the model leaves out: not a mistake


def planted(seed, size=300):
    """A model by its words flagged: [recording][group][flagged, words]; correct words 8 a recording, slips fewer."""
    r = np.random.default_rng(seed)
    words = np.stack([np.full(size, 8), (r.random(size) < 0.1) * 1, (r.random(size) < 0.4) * 1], 1)
    flagged = np.stack([r.binomial(words[:, 0], 0.23), r.binomial(words[:, 1], 0.55), r.binomial(words[:, 2], 0.9)], 1)
    return np.stack([flagged, words], 2)


def moved(base, group, points, only=None):
    """`base` with `points` percent of the group's words flagged differently: fewer if negative, more if positive,
    one word at a time from the recordings in `only` (all by default)."""
    out, g = base.copy(), ('right', 'letter', 'vowel').index(group)
    todo = int(round(abs(points) / 100 * base[:, g, 1].sum()))
    step, at = (1 if points > 0 else -1), 0
    pool = list(range(len(base))) if only is None else list(only)
    while todo:
        i = pool[at % len(pool)]
        at += 1
        if (step > 0 and out[i, g, 0] < out[i, g, 1]) or (step < 0 and out[i, g, 0] > 0):
            out[i, g, 0] += step
            todo -= 1
        elif at > 50 * len(pool):
            raise AssertionError('no room to move that many words')
    return out


untuned, small = planted(1), planted(2, size=25)
small[:2, 0, 0] = 8  # two recordings with every correct word flagged ...
lumpy = small.copy()
lumpy[:2, 0, 0] = 0  # ... and none after: an 8 point drop that rests on two recordings, so not sure
CASES = [  # (what, untuned, trained, keep?)
    ('same model', untuned, untuned, False),
    ('correct words flagged 5 points fewer', untuned, moved(untuned, 'right', -5), True),
    ('correct words flagged 2.5 points fewer: under the bar', untuned, moved(untuned, 'right', -2.5), False),
    ('6 points fewer, all from two recordings: not sure', small, lumpy, False),
    ('correct words flagged 3 points more', untuned, moved(untuned, 'right', 3), False),
    ('5 fewer, vowel slips caught 5 points less', untuned, moved(moved(untuned, 'right', -5), 'vowel', -5), False),
    ('5 fewer, vowel slips caught 2 points less', untuned, moved(moved(untuned, 'right', -5), 'vowel', -2), True),
    ('5 fewer, vowel slips caught 5 points more', untuned, moved(moved(untuned, 'right', -5), 'vowel', 5), True),
    ('5 fewer, letter slips caught 20 points less: reported, not gated', untuned, moved(moved(untuned, 'right', -5), 'letter', -20), True),
]
MUTANTS = [  # (in judge.py, planted instead)
    ("drop['points'] >= S.DROP_MIN", "drop['points'] >= 0"),
    ("and drop['low'] > 0", ''),
    ("vowel['points'] >= -S.VOWEL_FALL_MAX", 'True'),
    ("vowel['points'] >= -S.VOWEL_FALL_MAX", "vowel['points'] >= 0"),
    ('return {**out, \'keep\': all(why.values()), \'why\': why}', "return {**out, 'keep': any(why.values()), 'why': why}"),
    ("return c if group == 'right' else", 'return c if True else'),
    ("c[:, 1] - c[:, 0], c[:, 1]]", "c[:, 0], c[:, 1]]"),
    ("'letter or word': 'letter', 'vowel': 'vowel'", "'letter or word': 'vowel', 'vowel': 'letter'"),
    ("None: 'right', ", "None: 'right', 'tajweed': 'right', "),
    ("and word is not None:", ":"),
    ("r is not None and r >= S.MATCH_FLOOR", 'True'),
    ("(own if rates is None else rates)", 'own'),
    ('prev + (x != y)', 'prev'),
    ('min(row[j] + 1, row[j - 1] + 1,', 'min(row[j] + 1,'),
    ("if same['keep']:", 'if False:'),
]


def judge_from(code):
    m = types.ModuleType('sounds.judge')
    m.__package__ = 'sounds'
    exec(compile(code, 'judge.py', 'exec'), m.__dict__)
    return m


def answers(judge):
    """Everything the judge decides, as plain data, so two judges can be compared."""
    two = [{'ref': REF, 'kinds': KINDS}] * 2
    heard = [said(), said(w0={'s': None})]
    def self_check(rows):
        try:
            judge.self_check(rows)
            return 'passed'
        except SystemExit:
            return 'refused'

    held = judge.verdict
    judge.verdict = lambda u, t: {**held(u, t), 'keep': True}  # a verdict that lets a model beat itself
    beats_itself = self_check(RECORDED)
    judge.verdict = held
    return {
        'words': [judge.counts({'ref': REF, 'kinds': k}, h)[1].tolist() for _, h, k, _ in WORD_CASES],
        'nasal': judge.counts({'ref': NASAL, 'kinds': [None]}, ['a', 'b'])[1].tolist(),
        'floor': judge.tally(two, heard, [0.9, 0.5])[0].tolist(),  # the second recording is partial in the untuned rate
        'own': judge.tally(two, heard)[0].tolist(),
        'edit': [judge.edit_distance(a, b) for a, b in ((list('abc'), list('ac')), (list('abc'), list('axc')), ([], list('ab')), (list('ab'), []), (list('a'), list('ab')))],
        'keeps': [judge.verdict(u, t)['keep'] for _, u, t, _ in CASES],
        'recorded': self_check(RECORDED),
        'planted': self_check(untuned),
        'beats_itself': beats_itself,
        'bare': judge.counts({'ref': [['ŋ']], 'kinds': [None]}, [])[1].tolist(),
    }


code = Path(real.__file__).read_text(encoding='utf-8')
now = answers(judge_from(code))
EXPECT = [(what, now['words'][i], want) for i, (what, _, _, want) in enumerate(WORD_CASES)]
EXPECT += [('a nasalised tajweed symbol left out is not flagged', now['nasal'], [[0, 1], [0, 0], [0, 0]]),
           ('a partial recording is zeroed by the untuned rate', now['floor'][1], [[0, 0]] * 3),
           ('the same recording by its own rate is counted', now['own'][1], [[1, 1], [0, 1], [0, 1]]),
           ('a word with only tajweed symbols has nothing to flag', now['bare'], [[0, 0]] * 3),
           ('edit distance: drop, swap, insert, delete, append', now['edit'], [1, 1, 2, 2, 1]),
           ('the recorded baseline is accepted', now['recorded'], 'passed'),
           ('a model off the recorded baseline is refused', now['planted'], 'refused'),
           ('a verdict that lets a model beat itself is refused', now['beats_itself'], 'refused')]
EXPECT += [(what, got, want) for (what, *_, want), got in zip(CASES, now['keeps'])]
for what, got, want in EXPECT:
    print('ok  ' if got == want else 'WRONG', what, '' if got == want else f'(got {got})')
wrong_cases = sum(got != want for _, got, want in EXPECT)
alive = []
for old, new in MUTANTS:
    assert old in code, f'mutant no longer matches judge.py: {old}'
    try:
        caught = answers(judge_from(code.replace(old, new, 1))) != now
    except Exception:
        caught = True
    if not caught:
        alive.append(old)
print(f'{len(EXPECT) - wrong_cases}/{len(EXPECT)} decisions right; {len(MUTANTS) - len(alive)}/{len(MUTANTS)} planted bugs caught',
      *(f'\n  survived: {a}' for a in alive))
sys.exit(1 if wrong_cases or alive else 0)
