import os
import sqlite3

from backend.services.readonly_db import ReadOnlyDb


def _make(path, value):
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE t (v TEXT)")
    db.execute("INSERT INTO t VALUES (?)", (value,))
    db.commit()
    db.close()


def test_missing_file_is_none_not_an_error(tmp_path) -> None:
    assert ReadOnlyDb(lambda: tmp_path / "absent.db")() is None


def test_same_file_reuses_the_connection(tmp_path) -> None:
    path = tmp_path / "a.db"
    _make(path, "one")
    get = ReadOnlyDb(lambda: path)
    assert get() is get()
    assert get().execute("SELECT v FROM t").fetchone()["v"] == "one"


def test_replaced_file_is_read_fresh(tmp_path) -> None:
    path, fresh = tmp_path / "a.db", tmp_path / "b.db"
    _make(path, "old")
    get = ReadOnlyDb(lambda: path)
    first = get()
    assert first.execute("SELECT v FROM t").fetchone()["v"] == "old"

    _make(fresh, "new")
    first.close()  # Windows will not replace an open file; the app side sees the same thing
    os.replace(fresh, path)
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    assert get().execute("SELECT v FROM t").fetchone()["v"] == "new"


def test_pointing_at_another_path_opens_that_one(tmp_path) -> None:
    a, b = tmp_path / "a.db", tmp_path / "b.db"
    _make(a, "a")
    _make(b, "b")
    target = {"path": a}
    get = ReadOnlyDb(lambda: target["path"])
    assert get().execute("SELECT v FROM t").fetchone()["v"] == "a"
    target["path"] = b
    assert get().execute("SELECT v FROM t").fetchone()["v"] == "b"
