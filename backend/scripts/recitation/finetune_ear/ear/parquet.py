"""Reading big Hugging Face parquet sets cheaply: index the small columns, choose rows, then fetch only their files."""
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem, hf_hub_download, list_repo_files

from . import settings as S
from .sound import decoded
from .spread import evenly

FILES, CLIPS = S.OUT / 'parquet-files', S.OUT / 'parquet-clips'  # whole files while read; each wanted clip


def index(repo, want, columns, read):
    """(shard, row, who, ayah) for every usable row of `want` train files spread evenly over the set.
    read(row) -> (who, ayah) or None. A file giving nothing usable is passed over for the next one."""
    fs = HfFileSystem()
    files = sorted(f for f in list_repo_files(repo, repo_type='dataset') if f.startswith('data/train-'))
    spread = evenly(files, want)
    found, used = [], 0
    for shard in spread + [f for f in files if f not in spread]:
        if used == want:
            break
        rows = pq.ParquetFile(fs.open(f'datasets/{repo}/{shard}')).read(columns=columns).to_pylist()
        got = [(shard, at, *hit) for at, r in enumerate(rows) if (hit := read(r))]
        used += bool(got)
        found += got
    print(f'{repo}: {len(found)} usable rows from {used} files', flush=True)
    return found


def balanced(found, target, pick):
    """At most `each` rows per reciter, the smallest each that reaches target, then target rows at most."""
    by = {}
    for f in found:
        by.setdefault(f[2], []).append(f)
    if not by:
        return []
    each = 1
    while sum(min(each, len(c)) for c in by.values()) < target and each < max(map(len, by.values())):
        each += 1
    rows = [f for who in sorted(by) for f in pick.sample(by[who], min(each, len(by[who])))]
    return pick.sample(rows, min(target, len(rows)))


def nonempty(rows, what):
    """Fail at planning, minutes in, rather than when the empty set is used hours later."""
    if not rows:
        raise SystemExit(f'no {what}: check the source and its settings')
    return rows


def saved(rows, row, name, sound):
    """One clip kept decoded, as 16-bit, until the dataset is built; appends (row, path) to rows.
    Decoded, not as the file's bytes: a Tadabur ayah is ~2.4 MB as stored, ~0.4 MB at 16 kHz 16-bit."""
    path = CLIPS / f'{name}-{len(rows)}.npy'
    np.save(path, (np.clip(sound, -1, 1) * 32767).astype(np.int16))
    rows.append((row, str(path)))


def fetch(repo, plan):
    """Each planned row's recording saved as its own file, as (row, path); one that will not decode is left out.
    A file of these sets is one big block (Tadabur 2.4 GB): streamed from the hub it was re-read per batch and
    the run was killed for memory. Downloaded, read once, its wanted rows written out, then deleted.
    Done before the dataset is built: the builder fingerprints its generator's code, and walking
    hf_hub_download's wrappers overflows (RecursionError, datasets 5.1 / huggingface_hub 2.2)."""
    rows = []
    CLIPS.mkdir(exist_ok=True)
    for shard in sorted({p[0] for p in plan}):
        want = {p[1]: p for p in plan if p[0] == shard}
        path = Path(hf_hub_download(repo, shard, repo_type='dataset', local_dir=FILES))
        hits = []  # the planned row of each recording handed to decoded(), in order

        def wanted():
            audios = (a for batch in pq.ParquetFile(path).iter_batches(batch_size=50, columns=['audio'])
                      for a in batch.column('audio').to_pylist())
            for at, audio in enumerate(audios):
                if at in want:
                    hits.append(want[at])
                    yield audio['bytes']
        for n, sound in enumerate(decoded(wanted())):
            if sound is not None:
                saved(rows, hits[n], repo.replace('/', '_'), sound)
        path.unlink()
    return rows
