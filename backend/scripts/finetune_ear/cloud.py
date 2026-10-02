"""Run finetune_ear.py on Kaggle's free graphics card from this computer, and bring back what it decided.

    python backend/scripts/finetune_ear/cloud.py          send this folder, wait, fetch the result
    python backend/scripts/finetune_ear/cloud.py --fetch  fetch the last run's result only

Needs the Kaggle CLI signed in (`kaggle` reads ~/.kaggle). Watch a run live at
https://www.kaggle.com/code/<id in kernel-metadata.json>. The result lands in
backend/data/models/finetune-ear/: verdict.json, the run's log, and ear-tuned/ on a win.
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
KERNEL = json.loads((HERE / 'kernel-metadata.json').read_text())['id']
LANDS = HERE.parents[1] / 'data' / 'models' / 'finetune-ear'
EVERY = 60  # seconds between status checks
ENDED = ('COMPLETE', 'ERROR', 'CANCEL')
# Without these the CLI writes the Arabic log in Windows' own code page and fails half way.
ENV = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'}


def kaggle(*args):
    return subprocess.run(['kaggle', 'kernels', *args], env=ENV, capture_output=True,
                          text=True, encoding='utf-8', check=True).stdout.strip()


if '--fetch' not in sys.argv:
    print(kaggle('push', '-p', str(HERE)), f'\nlive: https://www.kaggle.com/code/{KERNEL}', flush=True)
    time.sleep(EVERY)  # right after a push the status can still be the last run's
    while not any(end in kaggle('status', KERNEL) for end in ENDED):
        time.sleep(EVERY)
status = kaggle('status', KERNEL)
print(status)
kaggle('output', KERNEL, '-p', str(LANDS), '--force')
log = json.loads((LANDS / f'{KERNEL.split("/")[1]}.log').read_text(encoding='utf-8'))
sys.stdout.reconfigure(encoding='utf-8')
print(''.join(part['data'] for part in log if part['stream_name'] == 'stdout'))
if 'ERROR' in status:  # the why is in the warnings stream, at its end
    print(''.join(part['data'] for part in log if part['stream_name'] == 'stderr')[-3000:])
