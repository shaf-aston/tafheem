"""Reading big Hugging Face parquet sets cheaply: index the small columns, choose rows, then fetch only their files."""
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import HfFileSystem, hf_hub_download, list_repo_files

from . import settings as S


def index(repo, want, columns, read):
    """(shard, row, who, ayah) for every usable row of `want` train files spread evenly over the set.
    read(row) -> (who, ayah) or None. A file giving nothing usable is passed over for the next one."""
    fs = HfFileSystem()
    files = sorted(f for f in list_repo_files(repo, repo_type='dataset') if f.startswith('data/train-'))
    step = max(1, len(files) // want)
    spread = files[step // 2::step]
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


def fetch(repo, plan):
    """Each planned row's recording saved as its own file, as (row, path).
    A file of these sets is one big block (Tadabur 2.4 GB): streamed from the hub it was re-read per batch and
    the run was killed for memory. Downloaded, read once, its wanted rows written out, then deleted.
    Done before the dataset is built: the builder fingerprints its generator's code, and walking
    hf_hub_download's wrappers overflows (RecursionError, datasets 5.1 / huggingface_hub 2.2)."""
    rows, folder = [], S.OUT / 'parquet-clips'
    folder.mkdir(exist_ok=True)
    for shard in sorted({p[0] for p in plan}):
        want = {p[1]: p for p in plan if p[0] == shard}
        path = Path(hf_hub_download(repo, shard, repo_type='dataset', local_dir=S.OUT / 'parquet-files'))
        at = 0
        for batch in pq.ParquetFile(path).iter_batches(batch_size=50, columns=['audio']):
            for audio in batch.column('audio').to_pylist():
                if at in want:
                    rows.append((want[at], str(folder / f'{repo.replace("/", "_")}-{len(rows)}.audio')))
                    Path(rows[-1][1]).write_bytes(audio['bytes'])
                at += 1
        path.unlink()
    return rows
