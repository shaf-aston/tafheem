"""Teach the recitation ear on ordinary voices, on a free cloud graphics card.

Plays the app's own Qur'an model recordings of ordinary people reciting, then
checks whether it hears them better than before. Started from this computer by
cloud.py (next to this file); on Lightning.ai or Colab, run `python finetune_ear.py`
on a GPU machine. Everything it writes goes to the folder it was started in.

Scored on three groups it never trained on:
  new voices    people it never heard, reciting ayahs it trained on
  new ayahs     ayahs it never trained on: the only proof it learnt listening, not text
  professional  everyayah reciters on unseen ayahs: what the app hears well today

The rule is fixed before the run, so a wobble cannot be read as a win: keep the new
model only if it gets at least BAR points fewer words wrong on new ayahs and at most
SLIP points more wrong on professionals. verdict.json says which; ear-tuned/ exists
only on a win, and is the folder `recitation_model` (backend/config.py) points at.

Model: tarteel-ai/whisper-SIZE-ar-quran (Apache 2.0); base is the original of the
CTranslate2 export the app runs, tiny the faster one. Recordings: MuazAhmad7/Surah_Ikhlas-Labeled_Dataset
(CC BY 4.0), RetaSy/quranic_audio_dataset and Tarteel v1 (learners; no licence stated, so a
model taught on it is an experiment until its authors say otherwise).
"""
# ruff: noqa: E402  (the tools are installed before they are imported)
import json
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
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'peft', 'jiwer', 'ctranslate2'], check=True)
# Kaggle's image carries a torchao too old for the new peft, which then refuses to start.
subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', '-q', 'torchao'], check=True)

import jiwer
import numpy as np
import requests
import torch
from datasets import Audio, Dataset, load_dataset
from peft import LoraConfig, get_peft_model
from transformers import GenerationConfig, Seq2SeqTrainer, Seq2SeqTrainingArguments, WhisperForConditionalGeneration, WhisperProcessor

SIZE = 'base'  # 'tiny': two thirds the time at home, pros 1.2 points worse; tuned on 45 ayahs it slipped 3 more
NAME = f'tarteel-ai/whisper-{SIZE}-ar-quran'
RATE = 16000
LONGEST = 30 * RATE  # Whisper hears 30 seconds at most; a longer clip's text would be cut short
PER_AYAH = 40  # two thirds of the clips are al-Ikhlas; uncapped it teaches that one surah
HELD = 5  # one voice in HELD and one ayah in HELD are never trained on
BAR = 1.5  # points fewer words wrong on new ayahs the new model must win by
SLIP = 1.0  # points more wrong on professionals it may lose; more means it forgot
PROS = 40  # professional clips, 5 to 20 words each
TESTED = 600  # clips per test group at most: 3,000 held clips heard twice would cost an hour
EPOCHS = 2  # 18,000 clips: two passes is already ten times the steps four passes over 45 ayahs took
TARTEEL_V1 = 'tarteel-v1'
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
    for name, (clean, ayah, who) in SOURCES.items():
        # Judged with the sound still undecoded, so rejected clips cost nothing.
        rows = (rows_of(name).cast_column('audio', Audio(decode=False))
                .filter(lambda r: clean(r) and ayah(r) in IMLAEI)
                .map(lambda r, at: {'who': f'{name}:{who(r) or at}'}, with_indices=True))
        damaged = 0
        for row in rows:
            key = ayah(row)
            if seen[key] >= PER_AYAH:
                continue
            # Decoded one at a time: a damaged file is counted and skipped, not fatal to the run.
            try:
                sound = sound_of(row['audio']['bytes'] or Path(row['audio']['path']).read_bytes())
            except subprocess.CalledProcessError:
                damaged += 1
                continue
            if 0 < len(sound) <= LONGEST:
                seen[key] += 1
                yield {'sound': sound, 'said': IMLAEI[key], 'ayah': key, 'who': row['who']}
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
        yield {'sound': sound_of(mp3.content), 'said': IMLAEI[key], 'ayah': key, 'who': who}


# A held voice is never trained on, nor a held ayah by anyone.
whole = Dataset.from_list(list(learner_clips()))
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
    'professional': Dataset.from_list(list(professional_clips(taught_ayahs))),
}
TESTS = {k: v.shuffle(seed=7).select(range(min(TESTED, len(v)))) for k, v in TESTS.items()}
taught = whole.filter(lambda r: r['who'] not in new_voices and r['ayah'] not in new_ayahs).shuffle(seed=7)
print(len(whole), 'learner clips of', len(ayahs), 'ayahs;', len(taught), 'to learn from; tests:',
      {k: len(v) for k, v in TESTS.items()}, flush=True)

processor = WhisperProcessor.from_pretrained(NAME, language='ar', task='transcribe')
model = WhisperForConditionalGeneration.from_pretrained(NAME).cuda()
# tarteel ships no generation_config.json, so it lacks the language table; its base model has it.
model.generation_config = GenerationConfig.from_pretrained(f'openai/whisper-{SIZE}')
model.generation_config.language = 'ar'
model.generation_config.task = 'transcribe'
model.generation_config.forced_decoder_ids = None

# Marks off both sides: this measures letters. A stop changes the last vowel by rule,
# and vowels are the sureness check's job, a different model run.
MARKS = re.compile('[ً-ْٰ]')


def bare(text):
    return MARKS.sub('', text).replace('ٱ', 'ا').strip()


def listen(m, rows, batch=8):
    """What the model writes for each clip, marks off."""
    heard = []
    m.eval()
    for at in range(0, len(rows), batch):
        part = rows[at:at + batch]
        feats = processor([np.asarray(s, dtype=np.float32) for s in part['sound']],
                          sampling_rate=RATE, return_tensors='pt').input_features.cuda()
        with torch.no_grad():
            out = m.generate(input_features=feats, max_new_tokens=180)
        heard += [bare(t) for t in processor.batch_decode(out, skip_special_tokens=True)]
    return heard


def scored(m):
    """Words wrong, in percent, per test group; and what was heard."""
    heard = {k: listen(m, rows) for k, rows in TESTS.items()}
    return {k: round(100 * jiwer.wer([bare(t) for t in TESTS[k]['said']], heard[k]), 2) for k in TESTS}, heard


before, _ = scored(model)
print('today:', before, flush=True)


def gather(rows):
    # Features made per batch, not stored: 18,000 clips' features would take 17 GB.
    batch = processor([np.asarray(r['sound'], dtype=np.float32) for r in rows], sampling_rate=RATE, return_tensors='pt')
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

after, heard = scored(tuned)
keep = (before['new ayahs'] - after['new ayahs'] >= BAR
        and after['professional'] - before['professional'] <= SLIP)
verdict = {'keep': keep, 'before': before, 'after': after, 'bar': BAR, 'slip': SLIP,
           'taught': len(taught), 'tests': {k: len(v) for k, v in TESTS.items()},
           'still_wrong': [{'should': s, 'heard': h} for s, h in zip(TESTS['new ayahs']['said'], heard['new ayahs'])
                           if bare(s) != h][:10]}
(OUT / 'verdict.json').write_text(json.dumps(verdict, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(verdict, ensure_ascii=False, indent=1), flush=True)

if keep:
    # Folded back in and converted the way the shipped ear was, so only recitation_model changes at home.
    merged = OUT / 'ear-merged'
    tuned.merge_and_unload().save_pretrained(merged)
    processor.tokenizer.save_pretrained(merged)
    processor.feature_extractor.save_pretrained(merged)  # the processor alone no longer writes this file
    subprocess.run(['ct2-transformers-converter', '--model', str(merged), '--output_dir', str(OUT / 'ear-tuned'),
                    '--copy_files', 'preprocessor_config.json', '--quantization', 'float16'], check=True)
    shutil.rmtree(merged)  # 280 MB that would otherwise be downloaded for nothing
