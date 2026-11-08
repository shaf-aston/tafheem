"""Run the ear/ package on Kaggle's free graphics card from this computer, and bring back what it decided.

    python backend/scripts/recitation/finetune_ear/cloud.py          send this folder, wait, fetch the result
    python backend/scripts/recitation/finetune_ear/cloud.py --fetch  wait for the last run, then fetch its result
    python backend/scripts/recitation/finetune_ear/cloud.py --ship   upload a kept ear-tuned/ to Hugging Face and serve it
    python backend/scripts/recitation/finetune_ear/cloud.py --tlog   copy the tlog clips a run hears into a private Kaggle dataset
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

from ear import settings as S
from ear.spread import evenly

HERE = Path(__file__).resolve().parent
# The loop to run: a folder beside this one holding kernel-metadata.json and one package with a run.py.
LOOP = HERE.parent / (sys.argv[sys.argv.index('--loop') + 1] if '--loop' in sys.argv else HERE.name)
PACKAGE = next(p.name for p in LOOP.iterdir() if (p / 'run.py').exists())
KERNEL = json.loads((LOOP / 'kernel-metadata.json').read_text())['id']
SHARED = HERE.parents[2] / 'services' / 'recitation' / 'sound_compare.py'
# The app's spelling of each word, so the ear is taught the words the checker will ask it about.
SPELLING = HERE.parents[2] / 'services' / 'recitation' / 'spelling.py'
LANDS = HERE.parents[2] / 'data' / 'models' / LOOP.name.replace('_', '-')
RUNS = LANDS.parent / f'{LANDS.name}-runs'  # every fetched run's verdict and log, kept: the next fetch empties LANDS
# The two lines a ship moves: the run's champion, and the one checker the app serves.
CHAMPION = re.compile(r"CHAMPION = '([^@']+)@[^']*'")
SERVED = re.compile(r'recitation_model: str = "([^"]+)"')
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


def kaggle(*args, timeout=None):
    done = subprocess.run(['kaggle', *args], env=ENV, capture_output=True, text=True, encoding='utf-8', timeout=timeout)
    if done.returncode:
        raise RuntimeError(f'kaggle {" ".join(args[:2])} failed: {(done.stderr or done.stdout).strip()[-800:]}')
    return done.stdout.strip()


def status(kind='kernels', ref=KERNEL):
    """A run's or dataset's state, or '' when the check itself failed (a dropped connection, a busy server)."""
    try:
        return kaggle(kind, 'status', ref, timeout=EVERY)
    except (RuntimeError, subprocess.TimeoutExpired):
        return ''


def bench_phrases():
    """The phrases the IqraEval bench says, so training leaves them out (it never trains on the bench)."""
    import pyarrow.parquet as pq
    path = HERE.parents[2] / 'data' / 'recitation_checks' / 'downloads' / 'iqra' / 'data' / 'train-00000-of-00001.parquet'
    if not path.exists():
        sys.exit(f'no bench file at {path}: run backend/scripts/recitation/ear_bench once to fetch it')
    return sorted(set(pq.read_table(path, columns=['sentence']).column('sentence').to_pylist()))


def bundle(folder):
    """A copy of kernel-metadata.json and the one file it names, holding every loop's package whole, ready to push."""
    meta = json.loads((LOOP / 'kernel-metadata.json').read_text())
    if LOOP == HERE and S.TLOG_SHARE:
        meta['dataset_sources'].append(S.TLOG_COPY)
    packed = io.BytesIO()
    with zipfile.ZipFile(packed, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(HERE.parent.glob('finetune_*/*/*.py')):
            if (f.parent / '__init__.py').exists():  # packages only; checks/ stays on this PC
                z.write(f, f'{f.parent.name}/{f.name}')
        z.write(SHARED, SHARED.name)  # the server's own word judge, so training and serving mean the same by "wrong"
        z.write(SPELLING, 'ear/spelling.py')
        z.writestr(f'ear/{S.BENCH_PHRASES}', json.dumps(bench_phrases(), ensure_ascii=False))
    (folder / meta['code_file']).write_text(LAUNCH.format(base64.b64encode(packed.getvalue()).decode(), PACKAGE))
    (folder / 'kernel-metadata.json').write_text(json.dumps(meta))
    return folder


def copy_tlog():
    """tlog is gated and Kaggle gives a run sent from here no secrets, so the clips a run hears go up as a
    private Kaggle dataset, fetched with this computer's own Hugging Face login. One file at a time on disk."""
    import random
    import pyarrow as pa
    import pyarrow.parquet as pq
    from huggingface_hub import hf_hub_download, list_repo_files
    files = sorted(f for f in list_repo_files(S.TLOG, repo_type='dataset') if f.startswith('data/clean-'))
    pick = random.Random(19)  # the clips every run since 2026-11-04 heard
    with tempfile.TemporaryDirectory() as folder:
        up, whole = Path(folder) / 'up', Path(folder) / 'whole'
        up.mkdir()
        for n, shard in enumerate(evenly(files, S.TLOG_SHARDS)[:S.TLOG_SHARDS], 1):
            path = Path(hf_hub_download(S.TLOG, shard, repo_type='dataset', local_dir=whole))
            # From memory, not the file: Windows will not delete a file pyarrow still holds open.
            table = pq.read_table(pa.BufferReader(path.read_bytes()), columns=['audio'])
            path.unlink()
            chosen = pick.sample(range(table.num_rows), min(S.TLOG_TRY, table.num_rows))
            pq.write_table(table.take(chosen), up / f'tlog-{Path(shard).stem}.parquet')
            print(f'{n}/{S.TLOG_SHARDS} {shard}: {len(chosen)} clips', flush=True)
        shutil.rmtree(whole)
        (up / 'dataset-metadata.json').write_text(json.dumps(
            {'title': S.TLOG_COPY.split('/')[1], 'id': S.TLOG_COPY, 'licenses': [{'name': 'unknown'}]}))
        try:
            kaggle('datasets', 'status', S.TLOG_COPY)
            print(kaggle('datasets', 'version', '-p', str(up), '-m', f'{S.TLOG_SHARDS} files, {S.TLOG_TRY} clips each', '-q'))
        except RuntimeError:  # not made yet; private unless told otherwise
            print(kaggle('datasets', 'create', '-p', str(up), '-q'))
    while 'ready' not in status('datasets', S.TLOG_COPY):  # a run pushed before this sees no files
        time.sleep(EVERY)
    print('copied:', S.TLOG_COPY)


def git(*args):
    return subprocess.run(['git', *args], cwd=HERE, capture_output=True, text=True, check=True).stdout.strip()


def ship():
    """Upload a kept ear and serve it: on master, the app's recitation_model and the run's CHAMPION both move to
    it. The server's 5-minute pull of master serves it."""
    from huggingface_hub import HfApi
    verdict = json.loads((LANDS / 'verdict.json').read_text(encoding='utf-8'))
    if not verdict['keep']:
        sys.exit('verdict.json says not to keep this ear, so nothing is uploaded')
    # A copy of master beside this checkout, so --ship runs from any branch and touches nothing here.
    tree = Path(tempfile.mkdtemp()) / 'master'
    git('fetch', '-q', 'origin', 'master')
    git('worktree', 'add', '-q', '--detach', str(tree), 'origin/master')
    try:
        config, champion = tree / 'backend' / 'config.py', tree / HERE.relative_to(HERE.parents[3]) / 'ear' / 'settings.py'
        text, pins = config.read_text(encoding='utf-8'), champion.read_text(encoding='utf-8')
        # The word-error judge on Kaggle never measures slip detection, so the product's own bench decides,
        # against the ear users get today: a DROP exits non-zero and nothing is uploaded.
        subprocess.run([sys.executable, '-m', 'backend.scripts.recitation.ear_bench', SERVED.search(text)[1], str(LANDS / 'ear-tuned')],
                       cwd=HERE.parents[3], check=True, env=ENV)
        repo = CHAMPION.search(pins)[1]
        # From the winning step, so an ear saved before a later crash ships with its own scores.
        won = next(s['scores'] for s in verdict['steps'] if s['ear'] == verdict['ear'])
        scores = f"words wrong: champion {verdict['champion']}, this one {won}"
        done = HfApi().upload_folder(repo_id=repo, folder_path=LANDS / 'ear-tuned', commit_message=scores)
        config.write_text(SERVED.sub(f'recitation_model: str = "{repo}@{done.oid}"', text), encoding='utf-8')
        champion.write_text(CHAMPION.sub(f"CHAMPION = '{repo}@{done.oid}'", pins), encoding='utf-8')
        # The old pin rides in the message: reverting this commit serves it again (Hugging Face keeps every revision).
        git('-C', str(tree), 'commit', '-q', '-m', f'Serve the ear {done.oid}\n\nwas {SERVED.search(text)[1]}\n{scores}', '--',
            'backend/config.py', (HERE.relative_to(HERE.parents[3]) / 'ear' / 'settings.py').as_posix())
        git('-C', str(tree), 'push', '-q', 'origin', 'HEAD:master')
    finally:
        git('worktree', 'remove', '--force', str(tree))
    print(f'serving {done.oid} within 5 minutes')


if '--ship' in sys.argv:
    if LOOP != HERE:
        sys.exit('--ship moves the served ear, which only the finetune_ear loop makes')
    ship()
    sys.exit()
if '--tlog' in sys.argv:
    copy_tlog()
    sys.exit()
if '--fetch' not in sys.argv:
    with tempfile.TemporaryDirectory() as folder:
        print(kaggle('kernels', 'push', '-p', str(bundle(Path(folder)))), f'\nlive: https://www.kaggle.com/code/{KERNEL}', flush=True)
    time.sleep(EVERY)  # right after a push the status can still be the last run's
while not any(end in (now := status()) for end in ENDED):
    time.sleep(EVERY)
print(now)
shutil.rmtree(LANDS, ignore_errors=True)  # a failed run must not leave the last run's verdict to ship
LANDS.mkdir(parents=True)
kaggle('kernels', 'output', KERNEL, '-p', str(LANDS), '--force')
logged = LANDS / f'{KERNEL.split("/")[1]}.log'
kept = RUNS / time.strftime('%Y-%m-%d_%H%M')
kept.mkdir(parents=True)
for part in (logged, LANDS / 'verdict.json'):
    if part.exists():
        shutil.copy2(part, kept)
print('kept in', kept)
log = json.loads(logged.read_text(encoding='utf-8'))
sys.stdout.reconfigure(encoding='utf-8')
print(''.join(part['data'] for part in log if part['stream_name'] == 'stdout'))
if 'ERROR' in now:  # the why is in the warnings stream, at its end
    print(''.join(part['data'] for part in log if part['stream_name'] == 'stderr')[-3000:])
