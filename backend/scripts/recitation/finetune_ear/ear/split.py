"""Which clips are held for the judge and which are taught. A held voice is never trained on, nor a held
ayah by anyone. This split made the served ear (v13); a hash split tried 2026-10-17 put 4 in 5 of its
training clips in the tests, so it stays seeded exactly as it was."""
import random
import shutil
from collections import Counter

from datasets import Dataset, concatenate_datasets

from . import settings as S
from . import sources
from .text import canon

KEPT = ['sound', 'said', 'src', 'secs']


def build():
    """(tests, taught, hours): tests maps group -> clips, taught is the shuffled training set, hours per source."""
    # Written to disk 1,000 clips at a time: held as one list, 19k decoded clips pass
    # Arrow's 2 GB limit for a single column block and the run dies before training.
    whole = Dataset.from_generator(sources.learner_clips)
    pick = random.Random(7)
    voices, ayahs = sorted(set(whole['who'])), sorted(set(whole['ayah']))
    pick.shuffle(voices)
    pick.shuffle(ayahs)
    new_voices, new_ayahs = set(voices[::S.HELD]), set(ayahs[::S.HELD])
    taught_ayahs = {canon(k) for k in set(ayahs) - new_ayahs}
    tests = {
        'new voices': whole.filter(lambda r: r['who'] in new_voices and r['ayah'] not in new_ayahs),
        'new ayahs': whole.filter(lambda r: r['ayah'] in new_ayahs),
        # Unseen by training is what matters; learners now cover nearly every ayah, so skipping all of them left too few.
        'professional': Dataset.from_generator(sources.professional_clips, gen_kwargs={'skip': taught_ayahs}),
    }
    tests = {k: v.shuffle(seed=7).select(range(min(S.TESTED, len(v)))) for k, v in tests.items()}
    learners = whole.filter(lambda r: r['who'] not in new_voices and r['ayah'] not in new_ayahs)
    # Every parquet clip taught avoids the held ayahs and the professional test's.
    skip = {canon(k) for k in new_ayahs | set(tests['professional']['ayah'])}
    # Shares are of the final training set: learners are the rest, so each target is learners * share / learner share.
    rest = 1 - S.TADABUR_SHARE - S.REPLAY_SHARE
    big = Dataset.from_generator(sources.parquet_clips, gen_kwargs={
        'rows': sources.fetch(S.TADABUR, sources.tadabur_plan(skip, round(len(learners) * S.TADABUR_SHARE / rest))),
        'src': 'tadabur'})
    replay = Dataset.from_generator(sources.parquet_clips, gen_kwargs={
        'rows': sources.fetch(S.REPLAY, sources.replay_plan(skip, round(len(learners) * S.REPLAY_SHARE / rest))),
        'src': 'replay'})
    # Downloads out of the folder Kaggle hands back: cloud.py fetches it whole, and wants only the result.
    shutil.rmtree(S.OUT / 'parquet-clips')
    shutil.rmtree(S.OUT / 'parquet-files', ignore_errors=True)
    tests['tadabur new voices'] = big.filter(lambda r: r['part'] == 'test')
    empty = [g for g, v in tests.items() if not len(v)]
    if empty:
        raise SystemExit(f'test groups with no clips: {empty}')
    taught = concatenate_datasets([learners.select_columns(KEPT), big.filter(lambda r: r['part'] == 'train').select_columns(KEPT),
                                   replay.select_columns(KEPT)]).shuffle(seed=7)
    hours = Counter()
    for src, secs in zip(taught['src'], taught['secs']):
        hours[src] += secs / 3600
    print(len(whole), 'learner clips of', len(ayahs), 'ayahs;', len(taught), 'to learn from; tests:',
          {k: len(v) for k, v in tests.items()}, flush=True)
    print('hours to learn from, per source:', {k: round(v, 2) for k, v in hours.items()}, flush=True)
    return tests, taught, {k: round(v, 2) for k, v in hours.items()}
