"""One sounds run, on a GPU machine: hear the marked recordings with the untuned model, train one round on correct
recitations, hear them again, and judge. Writes verdict.json, and sounds-trained/ (the weights, kept or not)."""
# ruff: noqa: E402  (the tools are installed before they are imported)
import os
import subprocess
import sys

# One card: two T4s would split each batch for no gain on a model this size.
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'quranic-phonemizer'], check=True)

import gc
import json
import shutil
from collections import Counter

import torch
from ear.judge import gain, wrong

if not torch.cuda.is_available():
    raise SystemExit('No graphics card: on Kaggle, Settings > Accelerator > GPU T4.')
print('graphics card:', torch.cuda.get_device_name(0), flush=True)

from . import hear, judge, sources, targets, train
from . import settings as S

start = sources.attached(S.MODEL_MARKER).parent
checks, tests = sources.checks(), sources.professional_test()
refs = [targets.flat(c['ayah']) for c in tests]
print(len(checks), 'marked recordings;', len(tests), 'held professional clips by', len({c['who'] for c in tests}), 'reciters', flush=True)


def measure(folder):
    """What the model in `folder` writes for every marked recording and every held professional clip."""
    ear = hear.load(folder)
    heard = hear.hear(ear, [c['sound'] for c in checks])
    pro = judge.phoneme_errors(refs, hear.hear(ear, [c['sound'] for c in tests]))
    del ear
    gc.collect()
    torch.cuda.empty_cache()
    return heard, pro


def write(name, what):
    (S.OUT / name).write_text(json.dumps(what, ensure_ascii=False, indent=1), encoding='utf-8')
    print(name, json.dumps(what, ensure_ascii=False), flush=True)


# Untuned first: the judge must find the recorded baseline before anything is trained, and the rates here
# decide which recordings count for both models.
heard, pro_before = measure(start)
rows_before, rates = judge.tally(checks, heard)
write('untuned.json', {'flagged_or_caught': judge.self_check(rows_before), 'recordings_judged': int((rows_before[:, :, 1].sum(1) > 0).sum()),
                       'professional_per': wrong(pro_before)})

try:
    items = sources.taught(tests)
    taught = dict(Counter(i['src'] for i in items))
    print('taught:', taught, flush=True)
    train.train(start, items, S.OUT / 'sounds-trained')
finally:
    shutil.rmtree(S.OUT / 'parquet-clips', ignore_errors=True)  # the training audio: Kaggle would hand it back
    shutil.rmtree(S.OUT / 'parquet-files', ignore_errors=True)
    shutil.rmtree(S.OUT / 'sounds-trainer', ignore_errors=True)
gc.collect()
torch.cuda.empty_cache()

heard, pro_after = measure(S.OUT / 'sounds-trained')
rows_after, _ = judge.tally(checks, heard, rates)
verdict = judge.verdict(rows_before, rows_after)
verdict |= {'professional': {'untuned_per': wrong(pro_before), 'trained_per': wrong(pro_after), 'better': gain(pro_before, pro_after)},
            'rules': {'drop_min': S.DROP_MIN, 'vowel_fall_max': S.VOWEL_FALL_MAX, 'match_floor': S.MATCH_FLOOR},
            'taught': taught, 'recordings_judged': int((rows_before[:, :, 1].sum(1) > 0).sum()), 'professional_clips': len(tests)}
write('verdict.json', verdict)
