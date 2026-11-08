"""Where clips come from: learners (taught and tested), professionals (tested), and the big parquet sets,
Tadabur (taught and tested), everyayah (replayed) and tlog (real app users, taught). Each clip is a dict: sound, said, ayah, who, src, secs."""
import random
import re
import sys
import zlib
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq
import requests
from datasets import Audio, Dataset, load_dataset

from . import settings as S
from .judge import listen
from .parquet import CLIPS, balanced, fetch, index, nonempty, saved
from .sound import decoded, opened, sound_of
from .text import IMLAEI, SAID, SAYABLE, SPELT, canon, letters


def clip(sound, key, who, src, **more):
    return {'sound': sound, 'said': SAID[key], 'ayah': key, 'who': who, 'src': src, 'secs': len(sound) / S.RATE, **more}


def fits(sound):  # decoded, and short enough to be heard whole
    return sound is not None and 0 < len(sound) <= S.LONGEST


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
    for name, (clean, ayah, who) in LEARNERS.items():
        # Judged with the sound still undecoded, so rejected clips cost nothing.
        rows = (_rows_of(name).cast_column('audio', Audio(decode=False))
                .filter(lambda r: clean(r) and ayah(r) in SAYABLE)
                .map(lambda r, at: {'who': f'{name}:{who(r) or at}'}, with_indices=True))
        damaged = 0
        sounds = decoded(r['audio']['bytes'] or Path(r['audio']['path']).read_bytes() for r in rows)
        for row, sound in zip(rows, sounds):  # every clip decoded, so the cap below picks exactly as one at a time did
            key = ayah(row)
            if seen[key] >= S.PER_AYAH:
                continue
            damaged += sound is None
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


# --- the parquet sets. tadabur(), replay() and tlog() each take (skip, target) and return saved clips as
# ((shard, row, who, ayah, part), path): the small columns are indexed, rows chosen, then only their sound fetched.

def tadabur(skip, target):
    """Held reciters are tested whole; the rest are taught."""
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
    return fetch(S.TADABUR, nonempty(train, 'tadabur train clips') + nonempty(test, 'tadabur test clips'))


def replay(skip, target):
    """everyayah, taught, from reciters the professional test never hears."""
    tested = {name for names in S.PRO_TEST.values() for name in names}

    def read(r):
        key = SPELT.get(letters(r['text'] or ''))
        if r['duration'] > S.LONGEST / S.RATE or key not in SAYABLE or key in skip or r['reciter'] in tested:
            return None
        return r['reciter'], key

    found = index(S.REPLAY, S.REPLAY_SHARDS, ['reciter', 'duration', 'text'], read)
    train = [f + ('train',) for f in balanced(found, target, random.Random(17))]
    print(f'replay: {len(train)} train clips; reciters:', dict(Counter(f[2] for f in train)), f'(wanted {target})', flush=True)
    return fetch(S.REPLAY, nonempty(train, 'replay train clips'))


def held(name):
    """One Tadabur reciter in HELD, by a fixed hash, never trained on."""
    return zlib.crc32(str(name).encode()) % S.HELD == 0


def tlog_files():
    """The clips cloud.py --tlog copied up: tlog is gated, and Kaggle gives a run sent from the command line
    no secrets, so the run reads a private copy instead of Hugging Face."""
    return sorted(Path('/kaggle/input').rglob('tlog-*.parquet')) or sys.exit(
        f'no tlog copy attached: run cloud.py --tlog, which uploads {S.TLOG_COPY}')


def tlog(skip, target):
    """Real app users, taught only where the checker hears exactly the ayah meant.
    The checker leaves the card before training."""
    from faster_whisper import WhisperModel
    checker = WhisperModel(S.TLOG_CHECKER, device='cuda', compute_type='float16')
    rows, heard = [], 0
    CLIPS.mkdir(exist_ok=True)
    for path in tlog_files():
        if len(rows) >= target:
            break
        shard = path.name
        clips = pq.read_table(path, columns=['audio']).column('audio').to_pylist()
        meant = [('{}:{}'.format(*a['path'].split('_')[:2]), a) for a in clips]
        meant = [(key, a) for key, a in meant if key in SAYABLE and canon(key) not in skip]
        # Decoded on the CPUs while the checker hears on the card, not one after the other.
        for (key, _), sound in zip(meant, decoded(a['bytes'] for _, a in meant)):
            if len(rows) >= target:
                break
            if not fits(sound):
                continue
            heard += 1
            if letters(listen(checker, sound)) == letters(IMLAEI[key]):
                saved(rows, (None, None, shard, key, 'train'), 'tlog', sound)
    del checker
    print(f'tlog: {len(rows)} of {heard} clips heard as the ayah meant, taught (wanted {target})', flush=True)
    return nonempty(rows, 'tlog train clips')


def parquet_clips(rows, src):
    for (_, _, who, key, part), path in rows:
        sound = opened(path)
        if fits(sound):
            yield clip(sound, key, f'{src}:{who}', src, part=part)
