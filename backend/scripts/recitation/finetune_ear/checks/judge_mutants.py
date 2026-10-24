"""Does the judge decide right, and would a bug in it be caught? CPU only, numpy only, seconds.

    python backend/scripts/recitation/finetune_ear/checks/judge_mutants.py

Scenarios with known answers run against ear/judge.py; then each mutant (one small bug planted in the
source) must change at least one answer. A surviving mutant means the scenarios cannot see that rule."""
import json
import sys
import types
from pathlib import Path

import numpy as np

EAR = Path(__file__).parents[1] / 'ear'
sys.path.insert(0, str(EAR.parent))
import ear  # noqa: E402,F401  (judge.py imports ear.settings relative to this package)

WORDS = np.random.default_rng(1).integers(5, 20, size=400)


def fake_ear(new, pro, seed):
    """An ear by its per-word error rate on each group; each clip's errors drawn over the same words."""
    r = np.random.default_rng(seed)
    return {g: {'counts': np.stack([r.binomial(WORDS, p), WORDS], 1)} for g, p in (('new ayahs', new), ('professional', pro))}


def shifted(base, group, points):
    """`base` with `points` more (or, negative, fewer) words wrong on `group`, one word per clip in turn."""
    out = {g: {'counts': v['counts'].copy()} for g, v in base.items()}
    c = out[group]['counts']
    step, j = (1 if points > 0 else -1), 0
    for _ in range(int(round(abs(points) / 100 * c[:, 1].sum()))):
        while step < 0 and c[j % len(c), 0] == 0:
            j += 1
        c[j % len(c), 0] += step
        j += 1
    return out


untuned, served, inband = fake_ear(0.21, 0.007, 1), fake_ear(0.145, 0.021, 2), fake_ear(0.145, 0.013, 3)
lumpy = shifted(served, 'new ayahs', 0)
lumpy['new ayahs']['counts'][:2, 0] += 60  # 2.5 points worse, all on two clips
both = lambda e, new, pro: shifted(shifted(e, 'new ayahs', new), 'professional', pro)  # noqa: E731
pro_noise = shifted(served, 'new ayahs', -3)
pro_noise['professional']['counts'][:3, 0] += 5  # 0.3 points, on three clips: not surely worse
CASES = [  # (what, held, candidate, keep?)
    ('same ear', served, served, False),
    ('untuned against served', served, untuned, False),
    ('learns 3 points', served, both(served, -3, 0), True),
    ('learns 1 point: under the margin', served, both(served, -1, 0), False),
    ('learns 2.5 points, all from two clips: unsure', lumpy, served, False),
    ('learns 3, pros 0.3 worse by noise, already past the band', served, pro_noise, True),
    ('learns 3, pros 0.8 surely worse, already past the band', served, both(served, -3, 0.8), False),
    ('learns 3, pros 1.5 worse: over the margin', inband, both(inband, -3, 1.5), False),
    ('learns 3, pros 0.6 worse, still in the band', inband, both(inband, -3, 0.6), True),
    ('learns 3, pros 0.9 worse, leaves the band', inband, both(inband, -3, 0.9), False),
    ('repairs pros 1.3, new ayahs 0.5 worse', served, both(served, 0.5, -1.3), True),
    ('repairs pros 1.3, new ayahs 2 worse', served, both(served, 2, -1.3), False),
]
MUTANTS = [  # (in judge.py, planted instead)
    ("gains[g]['points'] >= m", "gains[g]['points'] >= 0"),
    ("and gains[g]['low'] > 0", ''),
    ("-gains[g]['points'] > m", "-gains[g]['points'] > 99"),
    ("wrong(untuned['professional']['counts']) + S.FORGET", "wrong(held['professional']['counts']) + S.FORGET"),
    ("and gains['professional']['high'] < 0)", ')'),
    ('not worse and not forgot', 'not worse'),
    ('bool(better) and', 'True and'),
    ('wrong(held) - wrong(cand)', 'wrong(cand) - wrong(held)'),
    ('counts[:, 0].sum() / counts[:, 1].sum()', 'counts[:, 0].mean()'),
]


def judge_from(code):
    m = types.ModuleType('ear.judge')
    m.__package__ = 'ear'
    exec(compile(code, 'judge.py', 'exec'), m.__dict__)
    return m


def answers(judge):
    return [judge.verdict(held, cand, untuned)['keep'] for _, held, cand, _ in CASES]


code = (EAR / 'judge.py').read_text(encoding='utf-8')
right = answers(judge_from(code))
for (what, *_, want), got in zip(CASES, right):
    print('ok  ' if got == want else 'WRONG', what)
alive = []
for old, new in MUTANTS:
    assert old in code, f'mutant no longer matches judge.py: {old}'
    try:
        caught = answers(judge_from(code.replace(old, new, 1))) != right
    except Exception:
        caught = True
    if not caught:
        alive.append(old)
wrong_cases = sum(got != want for (*_, want), got in zip(CASES, right))
json.dumps([judge_from(code).verdict(h, c, untuned) for _, h, c, _ in CASES])  # verdict.json must be able to hold it
print(f'{len(CASES) - wrong_cases}/{len(CASES)} decisions right; {len(MUTANTS) - len(alive)}/{len(MUTANTS)} planted bugs caught',
      *(f'\n  survived: {a}' for a in alive))
sys.exit(1 if wrong_cases or alive else 0)
