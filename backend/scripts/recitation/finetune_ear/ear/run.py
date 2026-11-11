"""One ear run, on a GPU machine: hold out the test clips, score the untuned and champion ears, then walk
settings.PLAN, keeping each candidate only if the judge says it beats the ear held so far.
Writes verdict.json after every step (done: true at the end), and ear-tuned/ as soon as a candidate wins."""
# ruff: noqa: E402  (the tools are installed before they are imported)
import os
import subprocess
import sys

# One card: two T4s would split each batch for no gain on a model this small.
os.environ.setdefault('CUDA_VISIBLE_DEVICES', '0')
subprocess.run([sys.executable, '-m', 'pip', 'install', '-q', 'peft', 'jiwer', 'faster-whisper'], check=True)
# Kaggle's image carries a torchao too old for the new peft, which then refuses to start.
subprocess.run([sys.executable, '-m', 'pip', 'uninstall', '-y', '-q', 'torchao'], check=True)

import json
import shutil
from importlib.metadata import version

import torch
import transformers

if not torch.cuda.is_available():
    raise SystemExit('No graphics card: on Kaggle, Settings > Accelerator > GPU T4.')
print('graphics card:', torch.cuda.get_device_name(0), flush=True)

from . import ears, judge, sources, split
from . import settings as S
from .text import bare
from .train import train

if S.TLOG_SHARE:
    sources.tlog_files()  # a missing copy stops the run now, not after 45 minutes of building the other sources
transformers.set_seed(S.SEED)  # LoRA's starting numbers too, not only the trainer's shuffle
tests, taught, hours = split.build()
# What this run was, so a bad ear can be traced: library versions and every knob that shapes the result.
run = {'libraries': {m: version(m) for m in ('torch', 'transformers', 'peft', 'faster-whisper', 'datasets')},
       'untuned': S.NAME, 'champion': S.CHAMPION, 'plan': S.PLAN, 'lora': S.LORA, 'learning_rate': S.LEARNING_RATE,
       'epochs': S.EPOCHS, 'seed': S.SEED, 'rough_p': S.ROUGH_P, 'tlog_share': S.TLOG_SHARE,
       'iqra': {'slips': S.IQRA_SLIPS_SHARE, 'real': S.IQRA_REAL_SHARE, 'quran_part': S.IQRA_QURAN_PART}, 'lone': S.LONE_SHARE,
       'rules': {'margin': S.MARGIN, 'forget': S.FORGET, 'sure': S.SURE},
       'hours': hours, 'taught': len(taught), 'tests': {k: len(v) for k, v in tests.items()}}
heard, steps, held = {}, [], 'champion'


def record(done):
    """verdict.json after every step, so a crash hours in still hands back every score made so far."""
    verdict = {'done': done, 'keep': held != 'champion', 'ear': held, 'run': run, 'steps': steps,
               **{k: judge.scores(heard[k]) for k in ('untuned', 'champion') if k in heard}}
    if done:
        verdict['after'] = judge.scores(heard[held])
        verdict['still_wrong'] = [{'should': s, 'heard': h} for s, h in
                                  zip(tests['new ayahs']['said'], heard[held]['new ayahs']['heard']) if bare(s) != h][:10]
    (S.OUT / 'verdict.json').write_text(json.dumps(verdict, ensure_ascii=False, indent=1), encoding='utf-8')
    return verdict


folder = {}  # every ear folder made; each is 145 MB Kaggle would hand back, so all go at the end, crash or not
try:
    untuned = folder['untuned'] = ears.export(ears.trainable(), S.OUT / 'ear-untuned')
    champion = folder['champion'] = ears.download(*S.CHAMPION.split('@'), S.OUT / 'ear-champion')
    ears.as_trainable(untuned, champion)  # raises now, not hours in, if the champion cannot be trained on
    heard.update(untuned=judge.hear(untuned, tests), champion=judge.hear(champion, tests))
    print('untuned:', judge.scores(heard['untuned']), 'champion:', judge.scores(heard['champion']), flush=True)
    # The one answer known before any candidate exists: no ear beats itself. The untuned ear's verdict against
    # the champion is recorded, not enforced: if it ever wins, that is news about the champion, not the judge.
    if judge.verdict(heard['champion'], heard['champion'], heard['untuned'])['better']:
        raise SystemExit('judge is broken: an ear beat itself')
    run['untuned_vs_champion'] = judge.verdict(heard['champion'], heard['untuned'], heard['untuned'])
    record(done=False)

    for n, (kind, share) in enumerate(S.PLAN, 1):
        name = f'blend {share}' if kind == 'blend' else f'trained {n}'
        path = S.OUT / f'ear-{name.replace(" ", "-")}'
        if kind == 'blend':  # always a blend of the champion, so the strengths stay comparable
            folder[name] = ears.blend(untuned, champion, share, path)
        else:  # from the held ear, so a round builds on the last one instead of starting over
            folder[name] = ears.export(train(ears.as_trainable(untuned, folder[held]), taught), path)
            torch.cuda.empty_cache()
        heard[name] = judge.hear(folder[name], tests)
        v = judge.verdict(heard[held], heard[name], heard['untuned'])
        steps.append({'ear': name, 'against': held, 'scores': judge.scores(heard[name]), **v})
        print(json.dumps(steps[-1], ensure_ascii=False), flush=True)
        if v['keep']:  # saved the moment it wins, so a later crash cannot take it
            held = name
            shutil.rmtree(S.OUT / 'ear-tuned', ignore_errors=True)
            shutil.copytree(folder[held], S.OUT / 'ear-tuned')
        record(done=False)
finally:
    for path in folder.values():
        shutil.rmtree(path, ignore_errors=True)
    shutil.rmtree(S.OUT / 'ear-lora', ignore_errors=True)

print(json.dumps(record(done=True), ensure_ascii=False, indent=1), flush=True)
