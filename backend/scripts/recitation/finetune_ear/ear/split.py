"""Which clips are held for the judge and which are taught. A held voice is never trained on, nor a held
ayah by anyone. This split made the served ear (v13); a hash split tried 2026-10-17 put 4 in 5 of its
training clips in the tests, so it stays seeded exactly as it was."""
import random
import shutil
from collections import Counter

import numpy as np
from datasets import Dataset, concatenate_datasets

from . import parquet, sources
from . import settings as S
from .sound import rough
from .text import canon

KEPT = ['sound', 'said', 'src', 'secs']
# What filters read. Given whole rows they unpacked every clip's sound: 25 clips a second, ~45 min a run.
NAMES = ['who', 'ayah']


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
        'new voices': whole.filter(lambda who, ayah: who in new_voices and ayah not in new_ayahs, input_columns=NAMES),
        'new ayahs': whole.filter(lambda who, ayah: ayah in new_ayahs, input_columns=NAMES),
        # Unseen by training is what matters; learners now cover nearly every ayah, so skipping all of them left too few.
        'professional': Dataset.from_generator(sources.professional_clips, gen_kwargs={'skip': taught_ayahs}),
    }
    tests = {k: v.shuffle(seed=7).select(range(min(S.TESTED, len(v)))) for k, v in tests.items()}
    # The same professional clips through a rough channel, each clip's fixed by its place, so every ear hears the same.
    tests['rough professional'] = tests['professional'].map(
        lambda r, at: {'sound': rough(r['sound'], np.random.default_rng(at))}, with_indices=True)
    learners = whole.filter(lambda who, ayah: who not in new_voices and ayah not in new_ayahs, input_columns=NAMES)
    # Every parquet clip taught avoids the held ayahs and the professional test's.
    skip = {canon(k) for k in new_ayahs | set(tests['professional']['ayah'])}
    # Shares are of the final training set: learners are the rest, so each target is learners * share / learner share.
    rest = 1 - S.TADABUR_SHARE - S.REPLAY_SHARE - S.TLOG_SHARE

    def fetched(src, share, rows):  # rows: sources.tadabur, replay or tlog
        return Dataset.from_generator(sources.parquet_clips, gen_kwargs={
            'rows': rows(skip, round(len(learners) * share / rest)), 'src': src})

    def phrases(src, share, rows):  # Iqra's: shares of what the sources above make, so they never shrink those
        return Dataset.from_generator(sources.phrase_clips, gen_kwargs={
            'rows': rows(skip, round(len(learners) / rest * share)), 'src': src})

    spoken = phrases('iqra slips', S.IQRA_SLIPS_SHARE, sources.slips)
    real = phrases('iqra real', S.IQRA_REAL_SHARE, sources.real_phrases)
    big = fetched('tadabur', S.TADABUR_SHARE, sources.tadabur)
    replay = fetched('replay', S.REPLAY_SHARE, sources.replay)
    tlog = fetched('tlog', S.TLOG_SHARE, sources.tlog)
    # Downloads out of the folder Kaggle hands back: cloud.py fetches it whole, and wants only the result.
    shutil.rmtree(parquet.CLIPS)
    shutil.rmtree(parquet.FILES, ignore_errors=True)
    tests['tadabur new voices'] = big.filter(lambda part: part == 'test', input_columns='part')
    tests['spoken slips'] = spoken.filter(lambda part: part == 'test', input_columns='part')
    empty = [g for g, v in tests.items() if not len(v)]
    if empty:
        raise SystemExit(f'test groups with no clips: {empty}')
    taught = concatenate_datasets([learners.select_columns(KEPT), big.filter(lambda part: part == 'train', input_columns='part').select_columns(KEPT),
                                   replay.select_columns(KEPT), tlog.select_columns(KEPT),
                                   spoken.filter(lambda part: part == 'train', input_columns='part').select_columns(KEPT),
                                   real.select_columns(KEPT)]).shuffle(seed=7)
    hours = Counter()
    for src, secs in zip(taught['src'], taught['secs']):
        hours[src] += secs / 3600
    hours = {k: round(v, 2) for k, v in hours.items()}
    print(len(whole), 'learner clips of', len(ayahs), 'ayahs;', len(taught), 'to learn from; tests:',
          {k: len(v) for k, v in tests.items()}, flush=True)
    print('hours to learn from, per source:', hours, flush=True)
    return tests, taught, hours
