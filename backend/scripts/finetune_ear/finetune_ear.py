"""Teach the recitation ear on ordinary voices, on a free cloud graphics card.

Plays the app's own Qur'an model recordings of ordinary people reciting, then
checks whether it hears them better than before. Started from this computer by
cloud.py (next to this file); on Lightning.ai or Colab, run `python finetune_ear.py`
on a GPU machine. Everything it writes goes to the folder it was started in.

How it is judged, and what happens after: README.md next to this file.

Model: tarteel-ai/whisper-SIZE-ar-quran (Apache 2.0); base is the original of the
CTranslate2 export the app runs, tiny the faster one. Recordings: MuazAhmad7/Surah_Ikhlas-Labeled_Dataset
(CC BY 4.0), RetaSy/quranic_audio_dataset and Tarteel v1 (learners; no licence stated, so a
model taught on it is an experiment until its authors say otherwise).
"""
# ruff: noqa: E402  (the tools are installed before they are imported)
import io
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

# One card: two T4s would split each batch for no gain on a model this small.
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'peft', 'jiwer', 'faster-whisper'], check=True)
# Kaggle's image carries a torchao too old for the new peft, which then refuses to start.
subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', '-q', 'torchao'], check=True)

import jiwer
import numpy as np
import pyarrow.parquet as pq
import requests
import soundfile
import torch
import zipfile
import zlib
from datasets import Audio, Dataset, concatenate_datasets, load_dataset
from faster_whisper import WhisperModel
from huggingface_hub import HfFileSystem, hf_hub_download, list_repo_files
from scipy.signal import fftconvolve, resample_poly
from peft import LoraConfig, get_peft_model
from transformers import GenerationConfig, Seq2SeqTrainer, Seq2SeqTrainingArguments, WhisperConfig, WhisperForConditionalGeneration, WhisperProcessor, WhisperTokenizerFast

SIZE = 'base'  # 'tiny': two thirds the time at home, pros 1.2 points worse; tuned on 45 ayahs it slipped 3 more
NAME = f'tarteel-ai/whisper-{SIZE}-ar-quran'
RATE = 16000
LONGEST = 30 * RATE  # Whisper hears 30 seconds at most; a longer clip's text would be cut short
PER_AYAH = 40  # two thirds of the clips are al-Ikhlas; uncapped it teaches that one surah
HELD = 5  # one voice, one ayah and one Tadabur reciter in HELD are never trained on
BAR = 1.5  # points fewer words wrong on new ayahs the new model must win by
SLIP = 1.0  # points more wrong on professionals it may lose; more means it forgot
PROS = 40  # professional clips, 5 to 20 words each
TESTED = 600  # clips per test group at most: 3,000 held clips heard twice would cost an hour
EPOCHS = 2  # 18,000 clips: two passes is already ten times the steps four passes over 45 ayahs took
TARTEEL_V1 = 'tarteel-v1'
CHAMPION = 'shafTheG/quran-ear'  # the served ear, its newest upload; cloud.py --ship uploads a win here
# A pilot takes a quarter of the learner clips (0.25): a quarter-size run ended 6 points behind
# the served ear on new ayahs, 2026-10-17, so a run meant to ship takes them all.
LEARNER_SHARE = 1.0  # share of learner clips kept, picked before decoding
# Training clips are changed on the fly, test clips never (recipe: Muno459/zipformer_p-arabic-v2 card).
NOISE_SET = 'obadx/freesound-commercial-50k-noise-only'  # per-clip CC0 / CC-BY
NOISE_SHARDS = 1  # of 104 files, 265 clips and half a gigabyte each
NOISE_P = 0.5  # chance a clip gets background noise
NOISE_SNR_DB = (10, 20)  # noise this far under the voice, drawn evenly between
NOISE_MAX_S = 30  # seconds kept of each noise clip
RIR_ZIP = 'https://www.openslr.org/resources/28/rirs_noises.zip'  # OpenSLR 28, Apache 2.0
RIR_LIST = 'RIRS_NOISES/real_rirs_isotropic_noises/rir_list'  # the 325 real room recordings in the zip
REVERB_P = 0.3  # chance a clip gets a room
RIR_MAX_S = 1.0  # seconds of a room's tail kept
SPEEDS = (0.9, 1.0, 1.1)  # one drawn per clip
# Tadabur: 384k ayahs by 600+ reciters, 938 GB, CC BY-NC 4.0. Only a few files are read.
TADABUR = 'FaisaI/tadabur'
TADABUR_SHARDS = 8  # of ~390 files, 1,000 ayahs and 2.4 GB each, spread evenly; 3 gave 2,796 usable
TADABUR_SHARE = 0.25  # of the training clips
TADABUR_TEST = 300  # clips of those reciters, at most
TADABUR_SURAH_BASE = 1  # its surah_id counts from 0; checked against the printed ayah text
RECITERS = ['Alafasy_128kbps', 'Husary_128kbps', 'Abdul_Basit_Murattal_192kbps', 'Minshawy_Murattal_128kbps',
            'Saood_ash-Shuraym_128kbps', 'Abdurrahmaan_As-Sudais_192kbps', 'Hudhaify_128kbps']
OUT = Path.cwd()

if not torch.cuda.is_available():
    raise SystemExit('No graphics card: on Kaggle, Settings > Accelerator > GPU T4.')
print('graphics card:', torch.cuda.get_device_name(0), flush=True)

# Plain vowelled spelling, the spelling this model writes; Uthmani would score right words as wrong.
verses = requests.get('https://api.quran.com/api/v4/quran/verses/imlaei', timeout=60).json()['verses']
IMLAEI = {v['verse_key']: v['text_imlaei'] for v in verses}
UTHMANI = requests.get('https://api.quran.com/api/v4/quran/verses/uthmani', timeout=60).json()['verses']


def held(name):
    """One Tadabur reciter in HELD, by a fixed hash, never trained on."""
    return zlib.crc32(str(name).encode()) % HELD == 0


def letters(text):
    """Bare letters, one alef, one yeh: the key a printed ayah is matched by in either script."""
    text = re.sub('[ٱأإآ]', 'ا', text).replace('ی', 'ي').replace('ى', 'ي')
    return re.sub('[^ء-ي]|ـ', '', text)  # the stretch mark sits inside the letter range


# Letters to the one ayah they spell. A spelling shared by ayahs that read differently is
# ambiguous and left out; a repeated ayah (55:13 and its echoes) reads the same, so it stays.
SPELT = {}
for v in verses + UTHMANI:
    SPELT.setdefault(letters(v.get('text_imlaei') or v['text_uthmani']), set()).add(v['verse_key'])
SPELT = {k: min(keys) for k, keys in SPELT.items() if len({IMLAEI[x] for x in keys}) == 1}

# Each source: which clips to keep, which ayah, and who recited (None: unknown, split by clip).
# Only clips a reviewer marked nothing on: where someone really recited wrong, the printed
# ayah is not what was said, and the model would learn to hear the mistake as right.
# sobolev210/quran-recitation-errors is left out: its clips are cut in the wrong places,
# running into the ayahs before and after or stopping after one word, so its labels lie.
SOURCES = {
    'MuazAhmad7/Surah_Ikhlas-Labeled_Dataset': (  # CC BY 4.0; files are ID<person>V<verse>
        lambda r: r['label'] == 1, lambda r: f"112:{r['verse_number']}",
        lambda r: (re.search(r'ID(\d+)V', r['audio']['path'] or '') or [None, None])[1]),
    # Learners from 81 countries, crowd-marked per clip. No licence stated: experiment only.
    # Its Aya field is the ayah's printed text, not a number, so it is matched by letters.
    'RetaSy/quranic_audio_dataset': (
        lambda r: r['final_label'] == 'correct', lambda r: SPELT.get(letters(r['Aya'] or '')),
        lambda r: None if r['reciter_id'] in (None, 'Unknown') else r['reciter_id']),
    # Tarteel v1 (2019): 18,400 phone recordings by app users, 5,846 ayahs. Already filtered by
    # its uploader; files are <surah>_<ayah>_<id>.wav, and who recited is not recorded.
    # Attached on Kaggle as dhiauji/user-tarteel. No licence stated: experiment only.
    TARTEEL_V1: (lambda r: True, lambda r: '{}:{}'.format(*Path(r['audio']['path']).name.split('_')[:2]), lambda r: None),
}


processor = WhisperProcessor.from_pretrained(NAME, language='ar', task='transcribe')
# Whisper writes so many marks at most, start marks included. An ayah spelt in more can be
# neither taught (training stops on it) nor heard whole, so it is left out on both sides.
MOST_MARKS = WhisperConfig.from_pretrained(NAME).max_target_positions
SAYABLE = {k for k, t in IMLAEI.items() if len(processor.tokenizer(t).input_ids) <= MOST_MARKS}
print(len(IMLAEI) - len(SAYABLE), 'ayahs too long for the model to write, left out', flush=True)


def rows_of(name):
    """A source's clips, sound undecoded. Tarteel v1 is files plus a list, not a Hugging Face set."""
    if name != TARTEEL_V1:
        return load_dataset(name, split='train')
    listing = next(Path('/kaggle/input').rglob('tusers_filtered.csv'))
    files = [line.split(',')[0].replace('\\', '/') for line in listing.read_text(encoding='utf-8').splitlines()[1:]]
    return Dataset.from_dict({'audio': [{'bytes': None, 'path': str(listing.parent / f)} for f in files]})


def sound_of(recording):
    """Any recording's bytes as 16 kHz mono. ffmpeg, not the datasets decoder: RetaSy's WAV
    headers state the wrong length, which torchcodec refuses (328 of 357 clips) and ffmpeg reads."""
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'pipe:0', '-f', 'f32le', '-ac', '1', '-ar', str(RATE), 'pipe:1'],
                         input=recording, capture_output=True, check=True)
    return np.frombuffer(out.stdout, dtype=np.float32)


def learner_clips():
    seen = Counter()
    share = random.Random(5)
    for name, (clean, ayah, who) in SOURCES.items():
        # Judged with the sound still undecoded, so rejected clips cost nothing.
        rows = (rows_of(name).cast_column('audio', Audio(decode=False))
                .filter(lambda r: clean(r) and ayah(r) in SAYABLE)
                .map(lambda r, at: {'who': f'{name}:{who(r) or at}'}, with_indices=True))
        damaged = 0
        for row in rows:
            key = ayah(row)
            if seen[key] >= PER_AYAH or share.random() > LEARNER_SHARE:
                continue
            # Decoded one at a time: a damaged file is counted and skipped, not fatal to the run.
            try:
                sound = sound_of(row['audio']['bytes'] or Path(row['audio']['path']).read_bytes())
            except subprocess.CalledProcessError:
                damaged += 1
                continue
            if 0 < len(sound) <= LONGEST:
                seen[key] += 1
                yield {'sound': sound, 'said': IMLAEI[key], 'ayah': key, 'who': row['who'], 'src': name,
                       'secs': len(sound) / RATE}
        print(name, len(rows), 'clean clips,', damaged, 'damaged and skipped', flush=True)


def professional_clips(skip):
    """Mid-surah ayahs (a first ayah's recording carries the basmala) no learner recited."""
    pool = [k for k, t in IMLAEI.items() if not k.endswith(':1') and k not in skip and 5 <= len(t.split()) <= 20]
    for at, key in enumerate(random.Random(11).sample(pool, PROS)):
        surah, ayah = map(int, key.split(':'))
        who = RECITERS[at % len(RECITERS)]
        # everyayah refuses requests without a browser's name.
        mp3 = requests.get(f'https://everyayah.com/data/{who}/{surah:03d}{ayah:03d}.mp3',
                           headers={'User-Agent': 'Mozilla/5.0'}, timeout=60)
        mp3.raise_for_status()
        sound = sound_of(mp3.content)
        yield {'sound': sound, 'said': IMLAEI[key], 'ayah': key, 'who': who, 'src': 'everyayah', 'secs': len(sound) / RATE}


def tadabur_plan(skip, target):
    """Which Tadabur rows to take, as (file, row, reciter, ayah, part). Only the small columns are read here.
    Reciters are held out whole; the rest give at most `each` clips, the smallest each that reaches target."""
    fs = HfFileSystem()
    files = sorted(f for f in list_repo_files(TADABUR, repo_type='dataset') if f.startswith('data/train-'))
    step = len(files) // TADABUR_SHARDS
    found, off = [], 0
    for shard in files[step // 2::step][:TADABUR_SHARDS]:
        rows = pq.ParquetFile(fs.open(f'datasets/{TADABUR}/{shard}')).read(
            columns=['reciter_id', 'surah_id', 'ayah_id', 'text_ar_simple', 'ayah_duration_s']).to_pylist()
        for at, r in enumerate(rows):
            key = f"{r['surah_id'] + TADABUR_SURAH_BASE}:{r['ayah_id']}"
            if r['ayah_duration_s'] > LONGEST / RATE or key not in SAYABLE:
                continue
            # The printed text must be the ayah the id names: a wrong id would teach a wrong label.
            if letters(r['text_ar_simple']) != letters(IMLAEI[key]):
                off += 1
                continue
            found.append((shard, at, r['reciter_id'], key))
    print('tadabur:', len(found), 'usable ayahs under 30 s;', off, 'dropped, text not the named ayah', flush=True)
    by = {}
    for f in found:
        by.setdefault(f[2], []).append(f)
    reciters = sorted(by)
    pick = random.Random(13)
    strangers = [who for who in reciters if held(who)]
    rest = [who for who in reciters if not held(who)]
    test = [f for who in strangers for f in by[who]]
    test = [f + ('test',) for f in pick.sample(test, min(TADABUR_TEST, len(test)))]
    free = {who: [f for f in by[who] if f[3] not in skip] for who in rest}
    each = 1
    while sum(min(each, len(c)) for c in free.values()) < target and each < max(map(len, free.values())):
        each += 1
    train = [f for c in free.values() for f in pick.sample(c, min(each, len(c)))]
    train = [f + ('train',) for f in pick.sample(train, min(target, len(train)))]
    print(f'tadabur: {len(strangers)} held reciters give {len(test)} test clips; {len(rest)} other reciters,'
          f' at most {each} each, give {len(train)} train clips (wanted {target})', flush=True)
    return train + test


def tadabur_files(plan):
    """Each planned row's recording saved as its own file, as (row, path).
    A Tadabur file is one 2.4 GB block: streamed from the hub it was re-read per batch and the run was
    killed for memory. Downloaded, read once (~7 GB peak, 10 s), its wanted rows written out, then deleted.
    Done before the dataset is built: the builder fingerprints its generator's code, and walking
    hf_hub_download's wrappers overflows (RecursionError, datasets 5.1 / huggingface_hub 2.2)."""
    rows = []
    for shard in sorted({p[0] for p in plan}):
        want = {p[1]: p for p in plan if p[0] == shard}
        path = Path(hf_hub_download(TADABUR, shard, repo_type='dataset', local_dir=OUT / 'tadabur'))
        at = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=50, columns=['audio']):
            for clip in batch.column('audio').to_pylist():
                if at in want:
                    rows.append((want[at], str(OUT / 'tadabur' / f'{len(rows)}.audio')))
                    Path(rows[-1][1]).write_bytes(clip['bytes'])
                at += 1
        path.unlink()
    return rows


def tadabur_clips(rows):
    for (_, _, who, key, part), path in rows:
        try:
            sound = sound_of(Path(path).read_bytes())
        except subprocess.CalledProcessError:
            continue
        if 0 < len(sound) <= LONGEST:
            yield {'sound': sound, 'said': IMLAEI[key], 'ayah': key, 'who': f'tadabur:{who}',
                   'src': 'tadabur', 'secs': len(sound) / RATE, 'part': part}


def noise_bank():
    """Background sounds, 16 kHz mono, each cut to NOISE_MAX_S."""
    fs = HfFileSystem()
    files = sorted(f for f in list_repo_files(NOISE_SET, repo_type='dataset') if f.startswith('data/'))[:NOISE_SHARDS]
    bank = []
    for shard in files:
        for batch in pq.ParquetFile(fs.open(f'datasets/{NOISE_SET}/{shard}')).iter_batches(batch_size=20, columns=['audio']):
            for audio in batch.column('audio').to_pylist():
                try:
                    bank.append(sound_of(audio['bytes'])[:NOISE_MAX_S * RATE])
                except subprocess.CalledProcessError:
                    pass
    return [n for n in bank if len(n) > RATE]


def rir_archive():
    """The OpenSLR 28 zip, downloaded once next to the outputs."""
    path = OUT / 'rirs_noises.zip'
    if not path.exists():
        with requests.get(RIR_ZIP, stream=True, timeout=60) as r, open(path, 'wb') as f:
            r.raise_for_status()
            shutil.copyfileobj(r.raw, f)
    return path


def room_bank(archive):
    """Real room impulse responses from the OpenSLR 28 zip, 16 kHz, from the direct sound on, unit energy."""
    bank = []
    with zipfile.ZipFile(archive) as z:
        for line in z.read(RIR_LIST).decode().splitlines():
            wav, rate = soundfile.read(io.BytesIO(z.read(line.split()[-1])), always_2d=True)
            gcd = math.gcd(RATE, rate)
            wav = resample_poly(wav[:, 0], RATE // gcd, rate // gcd)
            wav = wav[np.argmax(np.abs(wav)):][:int(RIR_MAX_S * RATE)]
            bank.append((wav / np.linalg.norm(wav)).astype(np.float32))
    return bank


def rms(x):
    return float(np.sqrt(np.mean(np.square(x)))) + 1e-9


def augmented(sound, noises, rooms, rng):
    """One training clip made harder: speed, then room, then background noise. Never run on a test clip."""
    x = np.asarray(sound, dtype=np.float32)
    speed = float(rng.choice(SPEEDS))
    if speed != 1.0:
        slowed = resample_poly(x, 100, int(round(100 * speed)))  # 0.9 plays slower, so longer
        if len(slowed) <= LONGEST:  # a longer clip would lose its end but keep its text
            x = slowed.astype(np.float32)
    if rng.random() < REVERB_P:
        wet = fftconvolve(x, rooms[rng.integers(len(rooms))])[:len(x)]
        x = (wet * rms(x) / rms(wet)).astype(np.float32)
    if rng.random() < NOISE_P:
        noise = np.resize(noises[rng.integers(len(noises))], len(x))  # repeated if shorter
        snr = rng.uniform(*NOISE_SNR_DB)
        x = (x + noise * rms(x) / rms(noise) / 10 ** (snr / 20)).astype(np.float32)
    return x


# Written to disk 1,000 clips at a time: held as one list, 19k decoded clips pass
# Arrow's 2 GB limit for a single column block and the run dies before training.
whole = Dataset.from_generator(learner_clips)
# A held voice is never trained on, nor a held ayah by anyone. This split made the served ear
# (v13); a hash split tried 2026-10-17 put 4 in 5 of its training clips in the tests.
pick = random.Random(7)
voices, ayahs = sorted(set(whole['who'])), sorted(set(whole['ayah']))
pick.shuffle(voices)
pick.shuffle(ayahs)
new_voices, new_ayahs = set(voices[::HELD]), set(ayahs[::HELD])
taught_ayahs = set(ayahs) - new_ayahs
TESTS = {
    'new voices': whole.filter(lambda r: r['who'] in new_voices and r['ayah'] not in new_ayahs),
    'new ayahs': whole.filter(lambda r: r['ayah'] in new_ayahs),
    # Unseen by training is what matters; learners now cover nearly every ayah, so skipping all of them left too few.
    'professional': Dataset.from_generator(professional_clips, gen_kwargs={'skip': taught_ayahs}),
}
TESTS = {k: v.shuffle(seed=7).select(range(min(TESTED, len(v)))) for k, v in TESTS.items()}
learners = whole.filter(lambda r: r['who'] not in new_voices and r['ayah'] not in new_ayahs)
# Tadabur reciters are strangers to the learners; its train ayahs avoid the held ayahs and the professional test's.
plan = tadabur_plan(new_ayahs | set(TESTS['professional']['ayah']),
                    round(len(learners) * TADABUR_SHARE / (1 - TADABUR_SHARE)))
big = Dataset.from_generator(tadabur_clips, gen_kwargs={'rows': tadabur_files(plan)})
TESTS['tadabur new voices'] = big.filter(lambda r: r['part'] == 'test')
KEPT = ['sound', 'said', 'src', 'secs']
taught = concatenate_datasets([learners.select_columns(KEPT), big.filter(lambda r: r['part'] == 'train').select_columns(KEPT)]
                              ).shuffle(seed=7)
spent = Counter()
for src, secs in zip(taught['src'], taught['secs']):
    spent[src] += secs / 3600
print(len(whole), 'learner clips of', len(ayahs), 'ayahs;', len(taught), 'to learn from; tests:',
      {k: len(v) for k, v in TESTS.items()}, flush=True)
print('hours to learn from, per source:', {k: round(v, 2) for k, v in spent.items()}, 'total', round(sum(spent.values()), 2), flush=True)
noises, rooms = noise_bank(), room_bank(rir_archive())
# Downloads out of the folder Kaggle hands back: cloud.py fetches it whole, and wants only the result.
shutil.rmtree(OUT / 'tadabur')
(OUT / 'rirs_noises.zip').unlink()
print(len(noises), 'noise clips,', len(rooms), 'rooms', flush=True)
rng = np.random.default_rng(3)

model = WhisperForConditionalGeneration.from_pretrained(NAME).cuda()
# tarteel ships no generation_config.json, so it lacks the language table; its base model has it.
model.generation_config = GenerationConfig.from_pretrained(f'openai/whisper-{SIZE}')
model.generation_config.language = 'ar'
model.generation_config.task = 'transcribe'
model.generation_config.forced_decoder_ids = None

# Marks off both sides: this measures letters. A stop changes the last vowel by rule,
# and vowels are the sureness check's job, a different model run. Pause signs (ۖ ۗ ۚ) too:
# printed apart, each was counted as a word, so a pause sign heard or not cost a whole word.
MARKS = re.compile('[ً-ْٰۖ-ۭ]')


def bare(text):
    return MARKS.sub('', text).replace('ٱ', 'ا').strip()


def export(m, folder):
    """A model as the CTranslate2 folder faster-whisper loads, made the way the served ear was.
    tokenizer.json from openai/whisper-SIZE: same words as Tarteel's, plus the timestamp marks theirs
    lacks; without the file faster-whisper silently fetches openai/whisper-tiny's."""
    merged = OUT / 'ear-merged'
    m.save_pretrained(merged)
    WhisperTokenizerFast.from_pretrained(f'openai/whisper-{SIZE}').save_pretrained(merged)
    processor.feature_extractor.save_pretrained(merged)  # the processor alone no longer writes this file
    subprocess.run(['ct2-transformers-converter', '--model', str(merged), '--output_dir', str(folder), '--force',
                    '--copy_files', 'preprocessor_config.json', 'tokenizer.json', '--quantization', 'float16'], check=True)
    shutil.rmtree(merged)  # 280 MB that would otherwise be downloaded for nothing
    return folder


def scored(ear):
    """Words wrong, in percent, per test group, heard as the app hears (one guess, untimed, each clip
    alone); and what was heard. Scored before training too, so a model that will not load fails in minutes."""
    m = WhisperModel(str(ear), device='cuda', compute_type='float16')
    heard = {k: [bare(' '.join(s.text for s in m.transcribe(np.asarray(x, dtype=np.float32), language='ar', beam_size=1,
                                                             without_timestamps=True, condition_on_previous_text=False)[0]))
                 for x in rows['sound']] for k, rows in TESTS.items()}
    return {k: round(100 * jiwer.wer([bare(t) for t in TESTS[k]['said']], heard[k]), 2) for k in TESTS}, heard


before, _ = scored(export(model, OUT / 'ear-today'))
shutil.rmtree(OUT / 'ear-today')
champion, _ = scored(CHAMPION)
print('today:', before, 'served ear:', champion, flush=True)


def gather(rows):
    # Features made per batch, not stored: 18,000 clips' features would take 17 GB.
    batch = processor([augmented(r['sound'], noises, rooms, rng) for r in rows], sampling_rate=RATE, return_tensors='pt')
    marked = processor.tokenizer([r['said'] for r in rows], padding=True, return_tensors='pt')
    # Padding is not something to say, so it is masked out of the loss.
    labels = marked['input_ids'].masked_fill(marked.attention_mask.ne(1), -100)
    # The model puts the start mark in front itself; left in, it would be there twice.
    if (labels[:, 0] == model.config.decoder_start_token_id).all():
        labels = labels[:, 1:]
    batch['labels'] = labels
    return batch


# LoRA, not a full retrain: a few hundred clips must not wash out thousands of hours.
# Attention only (q/k/v/out, encoder and decoder). Swept 2026-10-02, 7 plans on 45 ayahs: all
# within noise on new ayahs, so layers are not the lever, data is; this kept pros best and trains fastest.
tuned = get_peft_model(model, LoraConfig(r=32, lora_alpha=64, lora_dropout=0.05, bias='none',
                                         target_modules=['q_proj', 'k_proj', 'v_proj', 'out_proj']))
tuned.print_trainable_parameters()
Seq2SeqTrainer(
    model=tuned,
    args=Seq2SeqTrainingArguments(
        output_dir=str(OUT / 'ear-lora'), per_device_train_batch_size=8, gradient_accumulation_steps=2,
        learning_rate=5e-4, warmup_steps=40, num_train_epochs=EPOCHS, fp16=True, logging_steps=25,
        save_strategy='no', remove_unused_columns=False, label_names=['labels'], report_to=[],
    ),
    train_dataset=taught.select_columns(['sound', 'said']),
    data_collator=gather,
).train()

after, heard = scored(export(tuned.merge_and_unload(), OUT / 'ear-tuned'))
keep = (champion['new ayahs'] - after['new ayahs'] >= BAR
        and after['professional'] - champion['professional'] <= SLIP)
if not keep:
    shutil.rmtree(OUT / 'ear-tuned')
verdict = {'keep': keep, 'before': before, 'champion': champion, 'after': after, 'bar': BAR, 'slip': SLIP,
           'hours': {k: round(v, 2) for k, v in spent.items()},
           'taught': len(taught), 'tests': {k: len(v) for k, v in TESTS.items()},
           'still_wrong': [{'should': s, 'heard': h} for s, h in zip(TESTS['new ayahs']['said'], heard['new ayahs'])
                           if bare(s) != h][:10]}
(OUT / 'verdict.json').write_text(json.dumps(verdict, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(verdict, ensure_ascii=False, indent=1), flush=True)

