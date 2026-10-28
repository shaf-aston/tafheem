"""Where clips come from: the marked recordings (judged on, never taught), professionals held out (tested), and
what is taught: professionals (everyayah) and learners (Tarteel v1), neither from a held voice or a held ayah."""
import json
import random
from collections import Counter
from pathlib import Path

import numpy as np
import requests
import soundfile
from ear import parquet
from ear.sound import sound_of
from ear.text import IMLAEI, SPELT, canon, letters
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from . import settings as S


def attached(marker):
    """The one file called `marker` under Kaggle's attached data; a missing or doubled one stops the run."""
    found = list(Path('/kaggle/input').rglob(marker))
    if len(found) != 1:
        raise SystemExit(f'expected one {marker} under /kaggle/input, found {len(found)}: attach the dataset in kernel-metadata.json')
    return found[0]


def checks():
    """The reviewer-marked recordings, each: id, ayah, kinds (per word), ref (per word phonemes), sound."""
    listing = attached(S.CHECKS_MARKER)
    clips = [json.loads(line) for line in listing.read_text(encoding='utf-8').splitlines()]
    audio = np.load(listing.parent / S.CHECKS_AUDIO, mmap_mode='r')
    for c in clips:  # 16-bit numbers kept exactly: the same ones the CPU run heard
        c['sound'] = audio[c['start']:c['stop']].astype(np.float32) / 32768
    return clips


def professional_test():
    """Held-out professional clips: mid-surah ayahs (a first ayah's recording carries the basmala) from the test
    reciters in turn. Each: sound, ayah, who."""
    pool = sorted(k for k, t in IMLAEI.items() if not k.endswith(':1') and S.PRO_WORDS[0] <= len(t.split()) <= S.PRO_WORDS[1])
    reciters = list(S.PRO_TEST)
    web = requests.Session()
    web.mount('https://', HTTPAdapter(max_retries=Retry(total=4, backoff_factor=2, status_forcelist=(429, 500, 502, 503))))
    clips = []
    for at, key in enumerate(random.Random(S.TEST_SEED).sample(pool, S.PRO_AYAHS)):
        who, (surah, ayah) = reciters[at % len(reciters)], map(int, key.split(':'))
        # everyayah refuses requests without a browser's name.
        mp3 = web.get(S.EVERYAYAH_URL.format(who=who, surah=surah, ayah=ayah), headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
        mp3.raise_for_status()
        clips.append({'sound': sound_of(mp3.content), 'ayah': key, 'who': who})
    return clips


def taught(held):
    """Training items (path, ayah, who, src) without a held voice or a held ayah. `held` is the test clips."""
    skip = {canon(c['ayah']) for c in held}
    tested = {name for names in S.PRO_TEST.values() for name in names}

    def read(r):
        key = SPELT.get(letters(r['text'] or ''))
        if key is None or key.endswith(':1') or r['duration'] > S.TRAIN_LONGEST_S or r['reciter'] in tested or key in skip:
            return None
        return r['reciter'], key

    found = parquet.index(S.EVERYAYAH, S.EVERYAYAH_SHARDS, ['reciter', 'duration', 'text'], read)
    plan = parquet.nonempty(parquet.balanced(found, S.PRO_CLIPS, random.Random(S.PLAN_SEED)), 'professional clips')
    items = [{'path': path, 'ayah': key, 'who': who, 'src': 'everyayah'} for (_, _, who, key), path in parquet.fetch(S.EVERYAYAH, plan)]
    listing = attached(S.TARTEEL_LISTING)
    files = [line.split(',')[0].replace('\\', '/') for line in listing.read_text(encoding='utf-8').splitlines()[1:]]
    random.Random(S.PLAN_SEED).shuffle(files)
    seen = Counter()
    for f in files:
        surah, ayah = Path(f).name.split('_')[:2]
        key = f'{surah}:{ayah}'
        if key not in IMLAEI or canon(key) in skip or seen[key] >= S.LEARNER_PER_AYAH:
            continue
        try:
            fits = 0 < soundfile.info(listing.parent / f).duration <= S.TRAIN_LONGEST_S
        except RuntimeError:
            fits = False  # a damaged file is skipped, not fatal
        if fits:
            seen[key] += 1
            items.append({'path': str(listing.parent / f), 'ayah': key, 'who': None, 'src': S.TARTEEL_V1})
        if sum(seen.values()) == S.LEARNER_CLIPS:
            break
    return items
