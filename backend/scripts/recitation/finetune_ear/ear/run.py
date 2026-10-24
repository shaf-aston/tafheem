"""One ear run, on a GPU machine: hold out the test clips, score the untuned and served ears, then walk
settings.PLAN, keeping each candidate only if the judge says it beats the ear held so far.
Writes verdict.json, and ear-tuned/ when the held ear is no longer the served one."""
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

import torch

if not torch.cuda.is_available():
    raise SystemExit('No graphics card: on Kaggle, Settings > Accelerator > GPU T4.')
print('graphics card:', torch.cuda.get_device_name(0), flush=True)

from . import ears, judge, split
from . import settings as S
from .text import bare
from .train import train

tests, taught, hours = split.build()
folder = {}  # every ear folder made; each is 145 MB Kaggle would hand back, so all go at the end, crash or not
try:
    untuned = folder['untuned'] = ears.export(ears.trainable(), S.OUT / 'ear-untuned')
    repo, revision = ears.served()
    served = folder['served'] = ears.download(repo, revision, S.OUT / 'ear-served')
    ears.as_trainable(untuned, served)  # raises now, not hours in, if the served ear cannot be trained on
    heard = {'untuned': judge.hear(untuned, tests), 'served': judge.hear(served, tests)}
    print('untuned:', judge.scores(heard['untuned']), 'served:', judge.scores(heard['served']), flush=True)
    # The one answer known before any candidate exists: no ear beats itself. The untuned ear's verdict against
    # the served one is recorded, not enforced: if it ever wins, that is news about the served ear, not the judge.
    if judge.verdict(heard['served'], heard['served'], heard['untuned'])['keep']:
        raise SystemExit('judge is broken: an ear beat itself')
    untuned_check = judge.verdict(heard['served'], heard['untuned'], heard['untuned'])

    held, steps = 'served', []
    for n, (kind, share) in enumerate(S.PLAN, 1):
        name = f'blend {share}' if kind == 'blend' else f'trained {n}'
        path = S.OUT / f'ear-{name.replace(" ", "-")}'
        if kind == 'blend':  # always a blend of the served ear, so the strengths stay comparable
            folder[name] = ears.blend(untuned, served, share, path)
        else:  # from the held ear, so a round builds on the last one instead of starting over
            folder[name] = ears.export(train(ears.as_trainable(untuned, folder[held]), taught), path)
            torch.cuda.empty_cache()
        heard[name] = judge.hear(folder[name], tests)
        v = judge.verdict(heard[held], heard[name], heard['untuned'])
        steps.append({'ear': name, 'against': held, 'scores': judge.scores(heard[name]), **v})
        print(json.dumps(steps[-1], ensure_ascii=False), flush=True)
        if v['keep']:
            held = name
    if held != 'served':
        shutil.copytree(folder[held], S.OUT / 'ear-tuned')
finally:
    for path in folder.values():
        shutil.rmtree(path, ignore_errors=True)
    shutil.rmtree(S.OUT / 'ear-lora', ignore_errors=True)

last = heard[held]
verdict = {'keep': held != 'served', 'ear': held, 'before': judge.scores(heard['untuned']),
           'champion': judge.scores(heard['served']), 'after': judge.scores(last), 'steps': steps,
           'untuned_vs_served': untuned_check,
           'rules': {'margin': S.MARGIN, 'forget': S.FORGET, 'sure': S.SURE}, 'hours': hours, 'taught': len(taught),
           'tests': {k: len(v) for k, v in tests.items()},
           'still_wrong': [{'should': s, 'heard': h} for s, h in zip(tests['new ayahs']['said'], last['new ayahs']['heard'])
                           if bare(s) != h][:10]}
(S.OUT / 'verdict.json').write_text(json.dumps(verdict, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps(verdict, ensure_ascii=False, indent=1), flush=True)
