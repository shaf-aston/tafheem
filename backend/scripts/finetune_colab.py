#!/usr/bin/env -S colab run --gpu T4 --keep --timeout 3600
"""Teach the recitation ear on real voices, on Google's free graphics card.

Run it from this machine, with no browser tab anywhere:

    colab run --gpu T4 --keep --timeout 3600 backend/scripts/finetune_colab.py
    colab download ear-tuned.zip ear-tuned.zip   # only if the verdict says keep

The browser notebook this replaces died twice, both times for the same reason:
Colab's free machine is taken back when the tab stops talking to it, and the
Run all queue lives in the tab rather than on Google's side, so a reload
cancels every cell after the one running. Nothing here needs a tab.

It takes the model the app already uses, plays it about a thousand recordings
of ordinary people reciting, and checks whether it comes out hearing them
better than it went in. Nothing costs money and nothing is uploaded from this
machine: the recordings are pulled straight from the internet on Google's.

The rule is fixed before the run, so a small wobble cannot be read as a win:
keep the new model only if it gets at least BAR points fewer words wrong on
recordings it was never trained on.

Model: tarteel-ai/whisper-base-ar-quran (Apache 2.0), the original of the one
the app runs. Recordings: sobolev210/quran-recitation-errors (MIT) and
MuazAhmad7/Surah_Ikhlas-Labeled_Dataset (CC BY 4.0), both public.
"""
import subprocess
import sys

# At most this many clips of any one ayah: two thirds of everything here is
# surah al-Ikhlas, which left alone would teach the model that one surah and
# nothing else.
PER_AYAH = 40
# Points of word error the taught model must win by to be worth keeping.
BAR = 1.5
RATE = 16000
NAME = 'tarteel-ai/whisper-base-ar-quran'


def say(*bits):
    """Printed the moment it happens, not when the buffer fills. Without this
    a run that is working looks exactly like a run that has hung, which is the
    thing that cost the most time here."""
    print(*bits, flush=True)


say('graphics card: checking')
import torch  # noqa: E402

if not torch.cuda.is_available():
    raise SystemExit('No graphics card. Rent the machine with --gpu T4.')
say('graphics card:', torch.cuda.get_device_name(0))

say('installing the tools')
subprocess.run(
    [sys.executable, '-m', 'pip', 'install', '-q', '-U', 'transformers>=4.44',
     'datasets', 'accelerate', 'peft', 'jiwer', 'librosa', 'soundfile', 'ctranslate2'],
    check=True,
)
say('tools installed')

import re  # noqa: E402
from collections import Counter  # noqa: E402

import numpy as np  # noqa: E402
import requests  # noqa: E402
import jiwer  # noqa: E402
from datasets import Audio, Dataset, load_dataset  # noqa: E402
from transformers import WhisperForConditionalGeneration, WhisperProcessor  # noqa: E402

# Plain vowelled spelling, the spelling this model writes. The app's Uthmani
# text scores right words as wrong, so it must not be used as the answer here.
verses = requests.get('https://api.quran.com/api/v4/quran/verses/imlaei', timeout=60).json()['verses']
IMLAEI = {v['verse_key']: v['text_imlaei'] for v in verses}
say(len(IMLAEI), 'ayahs of text')

errors = load_dataset('sobolev210/quran-recitation-errors', split='train').cast_column(
    'audio', Audio(sampling_rate=RATE))
ikhlas = load_dataset('MuazAhmad7/Surah_Ikhlas-Labeled_Dataset', split='train').cast_column(
    'audio', Audio(sampling_rate=RATE))
say(len(errors), 'marked clips,', len(ikhlas), 'al-Ikhlas clips')


def clean_pairs():
    """Only the recitations a reviewer marked nothing on. On a clip where the
    person really did recite wrong, the printed ayah is not what was said, and
    training on it would teach the model to hear a mistake as the right word."""
    seen = Counter()
    for row in errors:
        if row.get('riwayah') != 'Hafs':
            continue
        if any(v for v in (row.get('errors') or {}).values()):
            continue
        key = f"{int(row['surah'])}:{int(row['ayah'])}"
        if key in IMLAEI and seen[key] < PER_AYAH:
            seen[key] += 1
            yield {'sound': row['audio']['array'], 'said': IMLAEI[key], 'ayah': key}
    for row in ikhlas:
        if row.get('label') == 0:
            continue
        key = f"112:{row['verse_number']}"
        if key in IMLAEI and seen[key] < PER_AYAH:
            seen[key] += 1
            yield {'sound': row['audio']['array'], 'said': IMLAEI[key], 'ayah': key}


pairs = list(clean_pairs())
say(len(pairs), 'clean recitations,', len({p['ayah'] for p in pairs}), 'different ayahs')

# A fifth held back, split by clip. The model is scored only on recordings it
# never trained on, which is the only score that means anything.
whole = Dataset.from_list(pairs).shuffle(seed=7)
cut = len(whole) // 5
held, taught = whole.select(range(cut)), whole.select(range(cut, len(whole)))
say(len(taught), 'to learn from,', len(held), 'held back to be scored on')

processor = WhisperProcessor.from_pretrained(NAME, language='ar', task='transcribe')
model = WhisperForConditionalGeneration.from_pretrained(NAME).cuda()
model.generation_config.language = 'ar'
model.generation_config.task = 'transcribe'
model.generation_config.forced_decoder_ids = None

# Marks off both sides before counting: this measures the letters, and a
# recitation stopped on a word carries a different last vowel by rule, not by
# mistake. Vowels are the sureness score's job, and it is a different model run.
MARKS = re.compile('[ً-ْٰ]')


def bare(s):
    return MARKS.sub('', s).replace('ٱ', 'ا').strip()


def wrong_words(m, rows, batch=8):
    heard, meant = [], []
    m.eval()
    for at in range(0, len(rows), batch):
        part = rows[at:at + batch]
        feats = processor(
            [np.asarray(s, dtype=np.float32) for s in part['sound']],
            sampling_rate=RATE, return_tensors='pt',
        ).input_features.to('cuda', dtype=next(m.parameters()).dtype)
        with torch.no_grad():
            out = m.generate(feats, max_new_tokens=180)
        heard += [bare(t) for t in processor.batch_decode(out, skip_special_tokens=True)]
        meant += [bare(t) for t in part['said']]
    return 100 * jiwer.wer(meant, heard), heard


before, said_before = wrong_words(model, held)
say(f'today: {before:.1f}% of words wrong on {len(held)} recordings it has never heard')

# LoRA, not a full retrain: a small set of extra numbers alongside the model's
# own, so a thousand recordings cannot wash away everything it learned from
# thousands of hours. A full retrain on this little would do exactly that.
from dataclasses import dataclass  # noqa: E402

from peft import LoraConfig, get_peft_model  # noqa: E402
from transformers import Seq2SeqTrainer, Seq2SeqTrainingArguments  # noqa: E402


def prepared(row):
    row['input_features'] = processor(
        np.asarray(row['sound'], dtype=np.float32), sampling_rate=RATE,
    ).input_features[0]
    row['labels'] = processor.tokenizer(row['said']).input_ids
    return row


ready = taught.map(prepared, remove_columns=taught.column_names, num_proc=1)


@dataclass
class Gather:
    def __call__(self, rows):
        batch = processor.feature_extractor.pad(
            [{'input_features': r['input_features']} for r in rows], return_tensors='pt')
        marked = processor.tokenizer.pad(
            [{'input_ids': r['labels']} for r in rows], return_tensors='pt')
        # Padding must not be learned as something to say, so it is masked out.
        labels = marked['input_ids'].masked_fill(marked.attention_mask.ne(1), -100)
        if (labels[:, 0] == processor.tokenizer.bos_token_id).all():
            labels = labels[:, 1:]
        batch['labels'] = labels
        return batch


tuned = get_peft_model(model, LoraConfig(
    r=32, lora_alpha=64, lora_dropout=0.05, bias='none',
    target_modules=['q_proj', 'v_proj'],
))
tuned.print_trainable_parameters()

Seq2SeqTrainer(
    model=tuned,
    args=Seq2SeqTrainingArguments(
        output_dir='ear-lora',
        per_device_train_batch_size=8,
        gradient_accumulation_steps=2,
        learning_rate=1e-3,
        warmup_steps=40,
        num_train_epochs=4,
        fp16=True,
        logging_steps=25,
        save_strategy='no',
        remove_unused_columns=False,
        label_names=['labels'],
        report_to=[],
    ),
    train_dataset=ready,
    data_collator=Gather(),
).train()

after, said_after = wrong_words(tuned, held)
say(f'today:  {before:.1f}% of words wrong')
say(f'taught: {after:.1f}% of words wrong')
say(f'change: {before - after:+.1f} points on {len(held)} recordings it never trained on')
say('')
won = (before - after) >= BAR
say('VERDICT: keep it, and score it against the 1,950 clips at home.' if won
    else f'VERDICT: not worth keeping. The bar was {BAR} points and it did not clear it.')
say('')
say('Five it still gets wrong:')
shown = 0
for meant, heard in zip(held['said'], said_after):
    if bare(meant) != heard and shown < 5:
        shown += 1
        say(f'  should be: {meant}')
        say(f'  heard:     {heard}')

# The extra numbers are folded back into the model, then converted the way the
# one the app runs today was converted, so nothing at home has to change except
# which folder recitation_model points at. The zip is left on Google's machine
# and fetched with colab download, because a script has no browser to save to.
if not won:
    say('It did not clear the bar, so there is nothing to bring home.')
else:
    tuned.merge_and_unload().save_pretrained('ear-merged')
    processor.save_pretrained('ear-merged')
    subprocess.run(
        ['ct2-transformers-converter', '--model', 'ear-merged',
         '--output_dir', 'faster-whisper-base-ar-quran-tuned',
         '--copy_files', 'preprocessor_config.json', '--quantization', 'float16'],
        check=True,
    )
    subprocess.run(['zip', '-qr', 'ear-tuned.zip', 'faster-whisper-base-ar-quran-tuned'], check=True)
    say('READY: ear-tuned.zip is on the machine. Fetch it with')
    say('  colab download ear-tuned.zip ear-tuned.zip')
