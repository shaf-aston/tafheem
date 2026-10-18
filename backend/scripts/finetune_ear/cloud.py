"""Run finetune_ear.py on Kaggle's free graphics card from this computer, and bring back what it decided.

    python backend/scripts/finetune_ear/cloud.py          send this folder, wait, fetch the result
    python backend/scripts/finetune_ear/cloud.py --fetch  wait for the last run, then fetch its result
    python backend/scripts/finetune_ear/cloud.py --ship   upload a kept ear-tuned/ to Hugging Face and serve it

The result lands in backend/data/models/finetune-ear/. The whole loop and its keys: README.md here.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
KERNEL = json.loads((HERE / 'kernel-metadata.json').read_text())['id']
LANDS = HERE.parents[1] / 'data' / 'models' / 'finetune-ear'
# Public, so a server needs no key. Named once, in the recipe, whose judge scores against it.
CHAMPION = re.search(r"^CHAMPION = '(.+?)'", (HERE / 'finetune_ear.py').read_text(encoding='utf-8'), re.M)[1]
CONFIG = HERE.parents[1] / 'config.py'
EVERY = 60  # seconds between status checks
ENDED = ('COMPLETE', 'ERROR', 'CANCEL')
# Without these the CLI writes the Arabic log in Windows' own code page and fails half way.
ENV = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'}


def kaggle(*args):
    return subprocess.run(['kaggle', 'kernels', *args], env=ENV, capture_output=True,
                          text=True, encoding='utf-8', check=True).stdout.strip()


def status():
    """The run's state, or '' when the check itself failed (a dropped connection, a busy server)."""
    try:
        return kaggle('status', KERNEL)
    except subprocess.CalledProcessError:
        return ''


def git(*args):
    return subprocess.run(['git', *args], cwd=HERE, capture_output=True, text=True, check=True).stdout.strip()


def ship():
    """Upload a kept ear and pin it in config.py on master; the server's 5-minute pull of master serves it."""
    from huggingface_hub import HfApi
    verdict = json.loads((LANDS / 'verdict.json').read_text(encoding='utf-8'))
    if not verdict['keep']:
        sys.exit('verdict.json says not to keep this ear, so nothing is uploaded')
    if git('rev-parse', '--abbrev-ref', 'HEAD') != 'master':
        sys.exit('--ship runs from master, since the pin it commits is pushed there')
    git('pull', '--ff-only', 'origin', 'master')
    scores = f"words wrong: served ear {verdict['champion']}, this one {verdict['after']}"
    hub = HfApi()
    hub.create_repo(CHAMPION, private=False, exist_ok=True)
    done = hub.upload_folder(repo_id=CHAMPION, folder_path=LANDS / 'ear-tuned', commit_message=scores)
    pin = f'{CHAMPION}@{done.oid}'
    text = CONFIG.read_text(encoding='utf-8')
    CONFIG.write_text(re.sub(r'(recitation_trial_model: str = )".*"', rf'\g<1>"{pin}"', text), encoding='utf-8')
    git('commit', '-m', f'Serve the ear {pin}\n\n{scores}', '--', str(CONFIG))
    git('push', 'origin', 'master')
    print(f'serving {pin} within 5 minutes')


if '--ship' in sys.argv:
    ship()
    sys.exit()
if '--fetch' not in sys.argv:
    print(kaggle('push', '-p', str(HERE)), f'\nlive: https://www.kaggle.com/code/{KERNEL}', flush=True)
    time.sleep(EVERY)  # right after a push the status can still be the last run's
while not any(end in (now := status()) for end in ENDED):
    time.sleep(EVERY)
print(now)
shutil.rmtree(LANDS, ignore_errors=True)  # a failed run must not leave the last run's verdict to ship
LANDS.mkdir(parents=True)
kaggle('output', KERNEL, '-p', str(LANDS), '--force')
log = json.loads((LANDS / f'{KERNEL.split("/")[1]}.log').read_text(encoding='utf-8'))
sys.stdout.reconfigure(encoding='utf-8')
print(''.join(part['data'] for part in log if part['stream_name'] == 'stdout'))
if 'ERROR' in now:  # the why is in the warnings stream, at its end
    print(''.join(part['data'] for part in log if part['stream_name'] == 'stderr')[-3000:])
