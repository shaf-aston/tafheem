"""A build script that fails leaves the old file whole; one that ends clean replaces it."""
import sqlite3
from contextlib import closing

import pytest

from backend.services.core.building import building


def make(path, rows):
    with closing(sqlite3.connect(path)) as db:
        db.execute("CREATE TABLE note (id INTEGER)")
        db.executemany("INSERT INTO note VALUES (?)", [(i,) for i in range(rows)])
        db.commit()


def rows_in(path):
    with closing(sqlite3.connect(path)) as db:
        return db.execute("SELECT COUNT(*) FROM note").fetchone()[0]


def test_a_failed_build_keeps_the_old_file_and_leaves_no_scratch(tmp_path):
    target = tmp_path / "x.db"
    make(target, 3)
    with pytest.raises(RuntimeError):
        with building(target) as scratch, closing(sqlite3.connect(scratch)) as db:
            db.execute("CREATE TABLE note (id INTEGER)")
            raise RuntimeError("broke halfway")
    assert rows_in(target) == 3
    assert list(tmp_path.glob("*.building")) == []


def test_a_clean_build_replaces_the_target_and_makes_its_folder(tmp_path):
    target = tmp_path / "new" / "x.db"
    with building(target) as scratch:
        make(scratch, 5)
    assert rows_in(target) == 5
    assert list(target.parent.glob("*.building")) == []


def test_a_dry_run_keeps_the_scratch_and_leaves_the_target(tmp_path):
    target = tmp_path / "x.db"
    make(target, 3)
    with building(target, dry_run=True) as scratch:
        make(scratch, 9)
    assert rows_in(target) == 3 and rows_in(scratch) == 9


def test_a_build_whose_rows_swing_past_the_ratio_is_refused_and_a_first_build_is_not(tmp_path):
    target = tmp_path / "x.db"
    with building(target, guard=(0.05, ["note"])) as scratch:   # nothing built yet
        make(scratch, 100)
    with building(target, guard=(0.05, ["note"])) as scratch:   # within the ratio
        make(scratch, 105)
    with pytest.raises(SystemExit, match="note rows went 105 to 150"):
        with building(target, guard=(0.05, ["note"])) as scratch:
            make(scratch, 150)
    assert rows_in(target) == 105
    assert list(tmp_path.glob("*.building")) == []
