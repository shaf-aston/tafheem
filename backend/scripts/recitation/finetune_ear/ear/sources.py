"""Where clips come from: learners (taught and tested), professionals (tested), and the two big parquet sets,
Tadabur (taught and tested) and everyayah (replayed). Each clip is a dict: sound, said, ayah, who, src, secs."""
import random
import re
import subprocess
import zlib
from collections import Counter
from pathlib import Path

import requests
from datasets import Audio, Dataset, load_dataset

from . import settings as S
from .parquet import balanced, index, nonempty
from .sound import sound_of
from .text import IMLAEI, SAYABLE, SPELT, canon, letters


def clip(sound, key, who, src, **more):
    return {'sound': sound, 'said': IMLAEI[key], 'ayah': key, 'who': who, 'src': src, 'secs': len(sound) / S.RATE, **more}


def fits(sound):
    return 0 < len(sound) <= S.LONGEST


# Each learner source: which clips to keep, which ayah, and who recited (None: unknown, split by clip).
# Only clips a reviewer marked nothing on: where someone really recited wrong, the printed
# ayah is not what was said, and the model would learn to hear the mistake as right.
# sobolev210/quran-recitation-errors is left out: its clips are cut in the wrong places,
# running into the ayahs before and after or stopping after one word, so its labels lie.
LEARNERS = {
    'MuazAhmad7/Surah_Ikhlas-Labeled_Dataset': (  # CC BY 4.0; files are ID<person>V<verse>
        lambda r: r['label'] == 1, lambda r: f"112:{r['verse_number']}",
        lambda r: (re.search(r'ID(\d+)V', r['audio']['path'] or '') or [None, None])[1]),
    # Learners from 81 countries, crowd-marked per clip. No licence stated: experiment only.
    # Its Aya field is the ayah's printed text, not a number, so it is matched by letters.
    'RetaSy/quranic_audio_dataset': (
        lambda r: r['final_label'] == 'correct', lambda r: SPELT.get(letters(r['Aya'] or '')),
        lambda r: None if r['reciter_id'] in (None, 'Unknown') else r['reciter_id']),
    # Tarteel v1 (2019): 18,400 phone recordings by app users, 5,846 ayahs. Already filtered by
    # its uploader; files are <surah>_<ayah>_<id>.wav, and who recited is not recorded. No licence stated.
    S.TARTEEL_V1: (lambda r: True, lambda r: '{}:{}'.format(*Path(r['audio']['path']).name.split('_')[:2]), lambda r: None),
}


def _rows_of(name):
    """A source's clips, sound undecoded. Tarteel v1 is files plus a list, not a Hugging Face set."""
    if name != S.TARTEEL_V1:
        return load_dataset(name, split='train')
    listing = next(Path('/kaggle/input').rglob('tusers_filtered.csv'))
    files = [line.split(',')[0].replace('\\', '/') for line in listing.read_text(encoding='utf-8').splitlines()[1:]]
    return Dataset.from_dict({'audio': [{'bytes': None, 'path': str(listing.parent / f)} for f in files]})


def learner_clips():
    seen = Counter()
    share = random.Random(5)
    for name, (clean, ayah, who) in LEARNERS.items():
        # Judged with the sound still undecoded, so rejected clips cost nothing.
        rows = (_rows_of(name).cast_column('audio', Audio(decode=False))
                .filter(lambda r: clean(r) and ayah(r) in SAYABLE)
                .map(lambda r, at: {'who': f'{name}:{who(r) or at}'}, with_indices=True))
        damaged = 0
        for row in rows:
            key = ayah(row)
            if seen[key] >= S.PER_AYAH or share.random() > S.LEARNER_SHARE:
                continue
            # Decoded one at a time: a damaged file is counted and skipped, not fatal to the run.
            try:
                sound = sound_of(row['audio']['bytes'] or Path(row['audio']['path']).read_bytes())
            except subprocess.CalledProcessError:
                damaged += 1
                continue
            if fits(sound):
                seen[key] += 1
                yield clip(sound, key, row['who'], name)
        print(name, len(rows), 'clean clips,', damaged, 'damaged and skipped', flush=True)


def professional_clips(skip):
    """Mid-surah ayahs (a first ayah's recording carries the basmala) no learner was taught, PRO_TEST's reciters in turn.
    `skip` holds canon() names."""
    pool = sorted(k for k, t in IMLAEI.items() if not k.endswith(':1') and canon(k) not in skip and 5 <= len(t.split()) <= 20)
    reciters = list(S.PRO_TEST)
    for at, key in enumerate(random.Random(11).sample(pool, S.PROS)):
        surah, ayah = map(int, key.split(':'))
        who = reciters[at % len(reciters)]
        # everyayah refuses requests without a browser's name.
        mp3 = requests.get(S.EVERYAYAH_URL.format(who=who, surah=surah, ayah=ayah), headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
        mp3.raise_for_status()
        yield clip(sound_of(mp3.content), key, who, 'everyayah')


def tadabur_plan(skip, target):
    """Tadabur rows as (shard, row, who, ayah, part). Held reciters are tested whole; the rest are taught."""
    off = Counter()

    def read(r):
        key = f"{r['surah_id'] + S.TADABUR_SURAH_BASE}:{r['ayah_id']}"
        if r['ayah_duration_s'] > S.LONGEST / S.RATE or key not in SAYABLE:
            return None
        # The printed text must be the ayah the id names: a wrong id would teach a wrong label.
        if letters(r['text_ar_simple']) != letters(IMLAEI[key]):
            off['text'] += 1
            return None
        return r['reciter_id'], canon(key)

    found = index(S.TADABUR, S.TADABUR_SHARDS, ['reciter_id', 'surah_id', 'ayah_id', 'text_ar_simple', 'ayah_duration_s'], read)
    print('tadabur:', off['text'], 'dropped, text not the named ayah', flush=True)
    pick = random.Random(13)
    test = [f for f in found if held(f[2])]
    test = [f + ('test',) for f in pick.sample(test, min(S.TADABUR_TEST, len(test)))]
    train = [f + ('train',) for f in balanced([f for f in found if not held(f[2]) and f[3] not in skip], target, pick)]
    print(f'tadabur: {len(test)} test clips from held reciters, {len(train)} train clips (wanted {target})', flush=True)
    return nonempty(train, 'tadabur train clips') + nonempty(test, 'tadabur test clips')


def replay_plan(skip, target):
    """everyayah rows as (shard, row, who, ayah, 'train'), from reciters the professional test never hears."""
    tested = {name for names in S.PRO_TEST.values() for name in names}

    def read(r):
        key = SPELT.get(letters(r['text'] or ''))
        if r['duration'] > S.LONGEST / S.RATE or key not in SAYABLE or key in skip or r['reciter'] in tested:
            return None
        return r['reciter'], key

    found = index(S.REPLAY, S.REPLAY_SHARDS, ['reciter', 'duration', 'text'], read)
    train = [f + ('train',) for f in balanced(found, target, random.Random(17))]
    print(f'replay: {len(train)} train clips; reciters:', dict(Counter(f[2] for f in train)), f'(wanted {target})', flush=True)
    return nonempty(train, 'replay train clips')


def held(name):
    """One Tadabur reciter in HELD, by a fixed hash, never trained on."""
    return zlib.crc32(str(name).encode()) % S.HELD == 0


def parquet_clips(rows, src):
    for (_, _, who, key, part), path in rows:
        try:
            sound = sound_of(Path(path).read_bytes())
        except subprocess.CalledProcessError:
            continue
        if fits(sound):
            yield clip(sound, key, f'{src}:{who}', src, part=part)
