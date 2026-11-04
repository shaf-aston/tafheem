"""Run the ear/ package on Kaggle's free graphics card from this computer, and bring back what it decided.

    python backend/scripts/recitation/finetune_ear/cloud.py          send this folder, wait, fetch the result
    python backend/scripts/recitation/finetune_ear/cloud.py --fetch  wait for the last run, then fetch its result
    python backend/scripts/recitation/finetune_ear/cloud.py --ship   upload a kept ear-tuned/ to Hugging Face and serve it
    python backend/scripts/recitation/finetune_ear/cloud.py --loop finetune_sounds   any of the above, for another loop folder

The result lands in backend/data/models/<loop folder, dashed>/. The whole loop and its keys: README.md here.
"""
import base64
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

HERE = Path(__file__).parent
# The loop to run: a folder beside this one holding kernel-metadata.json and one package with a run.py.
LOOP = HERE.parent / (sys.argv[sys.argv.index('--loop') + 1] if '--loop' in sys.argv else HERE.name)
PACKAGE = next(p.name for p in LOOP.iterdir() if (p / 'run.py').exists())
KERNEL = json.loads((LOOP / 'kernel-metadata.json').read_text())['id']
SHARED = HERE.parents[2] / 'services' / 'recitation' / 'sound_compare.py'
LANDS = HERE.parents[2] / 'data' / 'models' / LOOP.name.replace('_', '-')
# The served ear's one name: master's config.py pin, "repo@revision". The judge reads the same line.
PIN = re.compile(r'(recitation_tuned_model: str = "([^@"]+)@)[^"]*"')
EVERY = 60  # seconds between status checks
ENDED = ('COMPLETE', 'ERROR', 'CANCEL')
# Without these the CLI writes the Arabic log in Windows' own code page and fails half way.
ENV = {**os.environ, 'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'}
# Kaggle runs one file, so every loop's package travels inside it as a zip Python imports from directly
# (zipimport); a loop may import another's (sounds reuses ear's sound and parquet readers).
LAUNCH = """import base64, pathlib, sys, tempfile
bundle = pathlib.Path(tempfile.mkdtemp()) / 'loops.zip'
bundle.write_bytes(base64.b64decode('{}'))
sys.path.insert(0, str(bundle))
import {}.run
"""


def kaggle(*args):
    done = subprocess.run(['kaggle', 'kernels', *args], env=ENV, capture_output=True, text=True, encoding='utf-8')
    if done.returncode:
        sys.exit(f'kaggle kernels {args[0]} failed: {(done.stderr or done.stdout).strip()[-800:]}')
    return done.stdout.strip()


def status():
    """The run's state, or '' when the check itself failed (a dropped connection, a busy server)."""
    try:
        return kaggle('status', KERNEL)
    except subprocess.CalledProcessError:
        return ''


def bundle(folder):
    """A copy of kernel-metadata.json and the one file it names, holding every loop's package whole, ready to push."""
    meta = json.loads((LOOP / 'kernel-metadata.json').read_text())
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(HERE.parent.glob('finetune_*/*/*.py')):
            if (f.parent / '__init__.py').exists():  # packages only; checks/ stays on this PC
                z.write(f, f'{f.parent.name}/{f.name}')
        z.write(SHARED, SHARED.name)  # the server's own word judge, so training and serving mean the same by "wrong"
    (folder / meta['code_file']).write_text(LAUNCH.format(base64.b64encode(packed.getvalue()).decode(), PACKAGE))
    (folder / 'kernel-metadata.json').write_text(json.dumps(meta))
    return folder


def git(*args):
    return subprocess.run(['git', *args], cwd=HERE, capture_output=True, text=True, check=True).stdout.strip()


def ship():
    """Upload a kept ear and pin it in config.py on master; the server's 5-minute pull of master serves it."""
    from huggingface_hub import HfApi
    verdict = json.loads((LANDS / 'verdict.json').read_text(encoding='utf-8'))
    if not verdict['keep']:
        sys.exit('verdict.json says not to keep this ear, so nothing is uploaded')
    scores = f"words wrong: served ear {verdict['champion']}, this one {verdict['after']}"
    # A copy of master beside this checkout, so --ship runs from any branch and touches nothing here.
    tree = Path(tempfile.mkdtemp()) / 'master'
    git('fetch', '-q', 'origin', 'master')
    git('worktree', 'add', '-q', '--detach', str(tree), 'origin/master')
    try:
        config = tree / 'backend' / 'config.py'
        text = config.read_text(encoding='utf-8')
        done = HfApi().upload_folder(repo_id=PIN.search(text)[2], folder_path=LANDS / 'ear-tuned',
                                     commit_message=scores)
        config.write_text(PIN.sub(rf'\g<1>{done.oid}"', text), encoding='utf-8')
        git('-C', str(tree), 'commit', '-q', '-m', f'Serve the ear {done.oid}\n\n{scores}', '--', 'backend/config.py')
        git('-C', str(tree), 'push', '-q', 'origin', 'HEAD:master')
    finally:
        git('worktree', 'remove', '--force', str(tree))
    print(f'serving {done.oid} within 5 minutes')


if '--ship' in sys.argv:
    if LOOP != HERE:
        sys.exit('--ship moves the served ear, which only the finetune_ear loop makes')
    ship()
    sys.exit()
if '--fetch' not in sys.argv:
    with tempfile.TemporaryDirectory() as folder:
        print(kaggle('push', '-p', str(bundle(Path(folder)))), f'\nlive: https://www.kaggle.com/code/{KERNEL}', flush=True)
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
