"""The store keeps the newest data, never runtime state, and never covers a file git tracks."""
import os
import subprocess
import time

from backend.scripts import worktree


def repo(path):
    subprocess.run(["git", "init", "-q", str(path)], check=True)
    (path / ".gitignore").write_text("*.db\n*.db-wal\nspeech_cache/\n")
    return path


def write(path, text, age=0):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    os.utime(path, (time.time() - age, time.time() - age))


def test_keep_takes_newer_data_and_leaves_runtime_state(tmp_path):
    a, store = repo(tmp_path / "a"), tmp_path / "store"
    write(a / "backend/data/hadith.db", "old", age=100)
    write(a / "backend/data/progress.db-wal", "mine")
    write(a / "backend/data/speech_cache/x.db", "cache")
    assert worktree.keep(a, store) == 1
    b = repo(tmp_path / "b")
    write(b / "backend/data/hadith.db", "rebuilt")
    assert worktree.keep(b, store) == 1
    assert (store / "backend/data/hadith.db").read_text() == "rebuilt"
    write(a / "backend/data/hadith.db", "older", age=200)
    assert worktree.keep(a, store) == 0  # the same file again changes nothing
    assert sorted(p.name for p in store.rglob("*") if p.is_file()) == ["hadith.db"]


def test_fill_links_everything_but_a_file_git_tracks(tmp_path):
    store, target = tmp_path / "store", repo(tmp_path / "t")
    write(store / "backend/data/hadith.db", "data")
    write(store / "backend/data/usul/usul.db", "stale ignored copy")
    write(target / "backend/data/usul/usul.db", "tracked")
    subprocess.run(["git", "add", "-f", "backend/data/usul/usul.db"], cwd=target, check=True)
    assert worktree.fill(target, store) == 1
    assert (target / "backend/data/usul/usul.db").read_text() == "tracked"
    assert os.path.samefile(target / "backend/data/hadith.db", store / "backend/data/hadith.db")
