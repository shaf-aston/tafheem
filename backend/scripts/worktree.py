"""Working copies that start ready to run, and a test run that sees what CI sees.

Data is not in git, so a fresh working copy has none. One shared folder, the
store (default: `tafheem-data` beside the repo), holds the newest copy of every
git-ignored data file, laid out as in the repo. A new working copy gets each file
as a hard link: instant, no extra disk. Hard links, not symlinks, because
config.data_path refuses a path that resolves outside backend/. The builders
write a scratch file and swap it in, so a rebuild inside one copy replaces only
that copy's link and the store stays as it was until you `keep` the result.

    python -m backend.scripts.worktree new NAME   # ../_wt-NAME on origin/master, data linked
    python -m backend.scripts.worktree keep [DIR] # this copy's (or DIR's) newer data into the store
    python -m backend.scripts.worktree ci         # backend tests on HEAD with no data, as on GitHub
"""
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIRS = ("backend/data", "frontend/public")
# Written while the app runs, so each copy keeps its own; and one empty stray.
NOT_SHARED = ("progress.db", "speech_cache", "__pycache__", "backend/data/corpus.db")
# The one install every copy shares (memory: worktree-junction-vite).
MAIN = ROOT.parent / "arabic-grammar-tool"


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


def shared(rel: str) -> bool:
    """False for runtime state: progress.db and its -wal/-shm, caches, the stray."""
    return rel not in NOT_SHARED and not any(p.startswith(NOT_SHARED) for p in rel.split("/"))


def ignored_files(checkout: Path) -> list[str]:
    """Every git-ignored data file in a checkout, as repo-relative posix paths."""
    out = git("ls-files", "--others", "--ignored", "--exclude-standard", *DATA_DIRS, cwd=checkout)
    return [rel for rel in out.splitlines() if shared(rel)]


def link(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.unlink(missing_ok=True)
    os.link(src, dst)


def keep(checkout: Path, store: Path) -> int:
    """Link a checkout's data into the store wherever it is newer. Returns files taken."""
    taken = 0
    for rel in ignored_files(checkout):
        src, dst = checkout / rel, store / rel
        if not dst.exists() or src.stat().st_mtime > dst.stat().st_mtime:
            link(src, dst)
            taken += 1
    return taken


def fill(target: Path, store: Path) -> int:
    """Link every store file into a working copy, never over a file git tracks there
    (an older copy may have ignored a file that is in git now). Returns files linked."""
    tracked = set(git("ls-files", *DATA_DIRS, cwd=target).splitlines())
    files = [p for p in store.rglob("*") if p.is_file() and p.relative_to(store).as_posix() not in tracked]
    for src in files:
        link(src, target / src.relative_to(store))
    return len(files)


def node_modules(target: Path) -> None:
    """Point the copy's frontend at the main install: a junction on Windows, which
    vite follows and a plain rm never empties (rmdir it), a symlink elsewhere."""
    dst, src = target / "frontend/node_modules", MAIN / "frontend/node_modules"
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(src), str(dst))
    else:
        dst.symlink_to(src, target_is_directory=True)


def new(name: str, store: Path) -> None:
    target = ROOT.parent / f"_wt-{name}"
    git("fetch", "-q", "origin")
    git("worktree", "add", "-q", "-B", name, str(target), "origin/master")
    print(f"{target}: {fill(target, store)} data files linked")
    node_modules(target)
    python = MAIN / ("venv/Scripts/python.exe" if os.name == "nt" else "venv/bin/python")
    print(f"backend:  cd {target} && {python} -m uvicorn backend.main:app --port 8001")
    print(f"frontend: cd {target / 'frontend'} && node node_modules/vite/bin/vite.js --port 5174")
    print("remove:   stop both, rmdir frontend/node_modules, then git worktree remove")


def ci() -> int:
    """The backend suite on this commit in a copy with no data, which is what
    GitHub has. A test that passes here only because data is on this computer fails."""
    scratch = Path(tempfile.mkdtemp(prefix="tafheem-ci-"))
    git("worktree", "add", "-q", "--detach", str(scratch), "HEAD")
    try:
        return subprocess.run([sys.executable, "-m", "pytest", "tests", "-q", "-p", "no:cacheprovider"], cwd=scratch).returncode
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
        git("worktree", "prune")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--store", type=Path, default=ROOT.parent / "tafheem-data")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("new").add_argument("name")
    sub.add_parser("keep").add_argument("checkout", type=Path, nargs="?", default=ROOT)
    sub.add_parser("ci")
    a = ap.parse_args()
    if a.cmd == "ci":
        return ci()
    if a.cmd == "keep":
        print(f"{keep(a.checkout.resolve(), a.store)} files taken into {a.store}")
    else:
        if not a.store.is_dir():
            sys.exit(f"no store at {a.store}: run `keep` from a checkout that has the data")
        new(a.name, a.store)
    return 0


if __name__ == "__main__":
    sys.exit(main())
