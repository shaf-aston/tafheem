"""Build the weak-points database from rijal.db and the rule in usul.json.

    python backend/scripts/build_usul.py

Levels every narrator from his grade (services/usul/level.py), then keeps a
note for each place a narrator at or below `weak_from` is named in a chain.
A narrator whose name, generation and grade all agree with one Taqrib entry is
levelled from the entry's own wording instead. The narrator books that
fetch_usul.py downloaded add: what each says of a narrator (facts), and the
links of a chain they put in doubt, a possible tadlis and a scholar's "did not
hear from" (services/usul/rung.py, jami.py). Prints the narrators levelled, the
notes per level, the wordings no term took and every join with the rows it left
over, so what the rule cannot read is seen and never guessed.

Rebuilding is safe at any time: it writes a fresh file beside the old one and
moves it into place at the end, like build_rijal.py. It stops, leaving the old
file, if the number of notes moves more than `max_change_ratio` against it.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services.hadith import loader  # noqa: E402
from backend.services.usul import books, facts, jami, mukhtalitin, names, rung, taqrib, tarif  # noqa: E402
from backend.services.usul.level import kind_of, level_of  # noqa: E402
from backend.services.usul.rule import rule  # noqa: E402

# Lists are JSON. A note is keyed by where its narrator's name starts in the hadith's Arabic.
_SCHEMA = """
CREATE TABLE narrator_level (
    narrator_id INTEGER PRIMARY KEY, level INTEGER NOT NULL, terms TEXT NOT NULL, kind TEXT NOT NULL, grade TEXT NOT NULL
);
CREATE TABLE note (
    collection TEXT NOT NULL, book INTEGER NOT NULL, number INTEGER NOT NULL, part TEXT NOT NULL,
    at INTEGER NOT NULL, narrator_id INTEGER NOT NULL, level INTEGER NOT NULL, kind TEXT NOT NULL,
    PRIMARY KEY (collection, book, number, part, at)
) WITHOUT ROWID;
CREATE TABLE gap (what TEXT NOT NULL, text TEXT NOT NULL, count INTEGER NOT NULL);
CREATE TABLE narrator_fact (
    narrator_id INTEGER NOT NULL, grp TEXT NOT NULL, kind TEXT NOT NULL, value TEXT NOT NULL, quote TEXT NOT NULL,
    book TEXT NOT NULL, page TEXT NOT NULL
);
CREATE INDEX narrator_fact_by_narrator ON narrator_fact (narrator_id);
CREATE TABLE link (
    collection TEXT NOT NULL, book INTEGER NOT NULL, number INTEGER NOT NULL, part TEXT NOT NULL,
    at INTEGER NOT NULL, kind TEXT NOT NULL, sub TEXT NOT NULL, student_id INTEGER NOT NULL, teacher_id INTEGER NOT NULL,
    word TEXT NOT NULL, level INTEGER NOT NULL, quote TEXT NOT NULL, scholar TEXT NOT NULL, source TEXT NOT NULL,
    page TEXT NOT NULL,
    PRIMARY KEY (collection, book, number, part, at, kind, quote)
) WITHOUT ROWID;
"""


def level_narrators(rijal: sqlite3.Connection, levels: list[dict]) -> tuple[dict[int, tuple[int, list[str], str, str]], Counter]:
    """({narrator id: (level, terms, kind, his grade)}, the wordings no term took by (what, text)).

    what is "left" for words beside a matched term and "none" for a grade with no match at all."""
    found: dict[int, tuple[int, list[str], str, str]] = {}
    gaps: Counter = Counter()
    for who, grade in rijal.execute("SELECT id, grade_ar FROM narrator WHERE grade_ar != ''"):
        level, matched, left = level_of(grade, levels)
        if level is None:
            gaps["none", grade] += 1
            continue
        found[who] = (level, matched, kind_of(level, matched, levels), grade)
        if left:
            gaps["left", left] += 1
    return found, gaps


def add_notes(conn: sqlite3.Connection, rijal: sqlite3.Connection, found: dict, weak_from: int) -> int:
    """One note per place a weak narrator is named; a mention placed twice at the same start is one note."""
    for collection, book, number, part, start, who in rijal.execute(
            "SELECT collection, book, number, part, start, narrator_id FROM mention ORDER BY collection, book, number, part, ord"):
        level, _, kind, _ = found.get(who, (0, None, None, None))
        if level >= weak_from:
            conn.execute("INSERT OR IGNORE INTO note VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                         (collection, book, number, part, start, who, level, kind))
    return conn.execute("SELECT COUNT(*) FROM note").fetchone()[0]


def read_books(cfg: dict) -> dict[str, list[books.Entry]]:
    """Every entry of each narrator book fetch_usul.py saved."""
    folder = data_path("usul_books_dir")
    found = {}
    for key, spec in cfg["books"].items():
        if key == "base":
            continue
        path = folder / f"{key}.txt"
        if not path.exists():
            raise SystemExit(f"no {path.name}. Run: python backend/scripts/fetch_usul.py")
        found[key] = books.entries(path.read_text(encoding="utf-8"), spec)
    return found


def narrator_rows(rijal: sqlite3.Connection) -> dict[int, dict]:
    columns = ("id", "name_ar", "lineage_ar", "nisba_ar", "kunya_ar", "grade_ar", "generation_ar")
    return {row[0]: dict(zip(columns, row)) for row in rijal.execute(f"SELECT {', '.join(columns)} FROM narrator")}


def level_from_taqrib(found: dict, rows: dict[int, dict], parsed: dict, joined: dict, levels: list[dict]) -> list[str]:
    """Level each narrator joined to a Taqrib entry from the entry's wording, replacing what his grade gave.
    Returns the report: levels before and after, then the narrators who moved."""
    before = Counter(v[0] for v in found.values())
    moved = []
    for n, who in joined.items():
        level, matched, _ = level_of(parsed[n].wording, levels)
        if level is None:
            continue
        old = found.get(who)
        if old is None or old[0] != level:
            moved.append((who, old[0] if old else None, level, matched))
        found[who] = (level, matched, kind_of(level, matched, levels), rows[who]["grade_ar"] or " ".join(matched))
    after = Counter(v[0] for v in found.values())
    report = [f"levels before the Taqrib entries -> after ({len(moved):,} narrators moved):"]
    report += [f"  level {n:>2}: {before[n]:>6,} -> {after[n]:>6,}" for n in range(1, len(levels) + 1)]
    report += [f"  moved {who} {rows[who]['name_ar']}: {old} -> {new} ({' + '.join(matched)})"
               for who, old, new, matched in moved[:rule()["gap_print"]]]
    return report


def add_gaps(conn: sqlite3.Connection, what: str, why: dict) -> None:
    """The reasons rows of a join were left out, counted: `what` names the join, each reason is the text."""
    conn.executemany("INSERT INTO gap VALUES (?, ?, ?)", [(what, reason, n) for reason, n in Counter(why.values()).items()])


def tarif_report(entries: list[books.Entry], level: dict, joined: dict, why: dict, rows: dict) -> list[str]:
    report = [f"Ta'rif entries joined: {len(joined)} of {len(entries)}"]
    for e in entries:
        who = joined.get(e.n)
        shown = " ".join(e.text.split()[:6])
        report.append(f"  {e.n:>3} level {level[e.n]} " + (f"= {who} {rows[who]['name_ar']}" if who else f"gap ({why[e.n]})")
                      + f"   {shown}")
    return report


def add_links(conn: sqlite3.Connection, rijal: sqlite3.Connection, cfg: dict, tarif_level: dict[int, int],
              pairs_by: dict[tuple[int, int], list], exempt: list[dict]) -> tuple[Counter, Counter]:
    """Link notes for every rung of every chain: (what each rung got or why not, why two names were no rung)."""
    outcomes: Counter = Counter()
    skipped: Counter = Counter()
    places: dict[tuple, dict[tuple, dict[int, tuple]]] = {}   # a mention written twice at one start is one
    for collection, book, number, part, start, end, who in rijal.execute(
            "SELECT collection, book, number, part, start, end, narrator_id FROM mention "
            "ORDER BY collection, book, number, part, ord"):
        places.setdefault((collection, book), {}).setdefault((number, part), {}).setdefault(start, (start, end, who))
    for (collection, book), hadith in places.items():
        arabic = {(h["number"], h["part"]): h["arabic"] for h in loader.hadiths(collection, book)}
        for (number, part), mentions in hadith.items():
            if (number, part) not in arabic:
                continue
            found, left = rung.rungs(arabic[number, part], list(mentions.values()))
            skipped.update(left)
            for r in found:
                kind, why = rung.tadlis(r, collection, tarif_level.get(r.student), cfg["tadlis"], exempt)
                outcomes[kind or why] += 1
                if kind:
                    conn.execute("INSERT OR IGNORE INTO link VALUES (?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?, '', '', '', '')",
                                 (collection, book, number, part, r.at, kind, r.student, r.teacher, r.word,
                                  tarif_level[r.student]))
                for pair in pairs_by.get((r.student, r.teacher), ()):
                    conn.execute("INSERT OR IGNORE INTO link VALUES (?, ?, ?, ?, ?, 'not_heard', ?, ?, ?, ?, 0, ?, ?, ?, ?)",
                                 (collection, book, number, part, r.at, pair.kind, r.student, r.teacher, r.word,
                                  pair.quote, pair.scholar, cfg["jami"]["book"], pair.page))
                    outcomes["not_heard"] += 1
    return outcomes, skipped


def build() -> None:
    source = data_path("rijal_index_path")
    if not source.exists():
        raise SystemExit(f"no {source.name}. Run: python backend/scripts/build_rijal.py")
    cfg = rule()
    entries = read_books(cfg)
    size, window = cfg["join"]["name_words"], cfg["join"]["nisba_window"]
    target = data_path("usul_index_path")
    scratch = target.with_suffix(".building.db")
    scratch.unlink(missing_ok=True)
    rijal = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    conn = sqlite3.connect(scratch)
    try:
        conn.executescript(_SCHEMA)
        rows = narrator_rows(rijal)
        people = [names.person(row) for row in rows.values()]
        by_id = {p.id: p for p in people}
        found, gaps = level_narrators(rijal, cfg["levels"])
        fact_rows: list[facts.Fact] = []

        # Taqrib: the entry a narrator's name, generation and grade all agree with gives his level, generation, death.
        taqrib_entries = {e.n: e for e in entries["taqrib"]}
        parsed = {n: taqrib.parse(e.text, cfg["taqrib"]) for n, e in taqrib_entries.items()}
        taqrib_joined, taqrib_why = taqrib.join(parsed, people, cfg["taqrib"], size)
        print(f"Taqrib entries joined: {len(taqrib_joined):,} of {len(taqrib_entries):,} (left out: "
              f"{', '.join(f'{k} {v:,}' for k, v in sorted(Counter(taqrib_why.values()).items()))})")
        print("\n".join(level_from_taqrib(found, rows, parsed, taqrib_joined, cfg["levels"])))
        add_gaps(conn, "taqrib_join", taqrib_why)
        joined_to = {who: n for n, who in taqrib_joined.items()}
        unread = 0
        for who in {*found, *joined_to}:
            if who in joined_to:
                n = joined_to[who]
                fact_rows += facts.taqrib_facts(who, taqrib_entries[n], parsed[n], found[who][0] if who in found else None,
                                                cfg["taqrib"])
                unread += facts.died_unread(parsed[n], cfg["taqrib"])
            else:   # no entry of his own was joined: his sunnah.com grade, placed on the preface's levels
                fact_rows.append(facts.Fact(who, "reliability", "level", str(found[who][0]), "", "grade", ""))
        dead = Counter(parsed[n].death_why or "read" for n in taqrib_joined)
        conn.executemany("INSERT INTO gap VALUES ('taqrib_death', ?, ?)",
                         [(k, v) for k, v in {**dead, "hundreds unknown": unread}.items() if k != "read" and v])
        print(f"death years of the joined: read {dead['read'] - unread:,}; hundreds unknown (generation 3 or 4) {unread:,}; "
              f"not read: " + ", ".join(f"{k} {v:,}" for k, v in sorted(dead.items()) if k != "read"))

        # Ta'rif: a mudallis's level; only 3 and 4 put a rung in doubt.
        tarif_entries = entries["tarif"]
        level_of_entry = {e.n: tarif.level_of(e, cfg["tarif"]) for e in tarif_entries}
        tarif_joined, tarif_why = tarif.join({e.n: tarif.written_name(e, cfg["tarif"]) for e in tarif_entries},
                                             people, size, window)
        tarif_level = {who: level_of_entry[n] for n, who in tarif_joined.items()}
        print("\n".join(tarif_report(tarif_entries, level_of_entry, tarif_joined, tarif_why, rows)))
        add_gaps(conn, "tarif_join", tarif_why)
        by_n = {e.n: e for e in tarif_entries}
        fact_rows += [facts.tarif_fact(who, by_n[n], level_of_entry[n]) for n, who in tarif_joined.items()]
        exempt = [{"tellers": {tarif.resolve(t, people, size, window) for t in r["tellers"]},
                   "via": tarif.resolve(r["via"], people, size, window),
                   "teacher": tarif.resolve(r["teacher"], people, size, window) if r["teacher"] else None}
                  for r in cfg["tadlis"]["unless"]]

        # Jami' al-Tahsil: a scholar's "did not hear from", joined to the narrator's own teachers.
        teachers: dict[int, list] = {}
        for teacher, student in rijal.execute("SELECT teacher_id, student_id FROM tie"):
            if teacher in by_id:
                teachers.setdefault(student, []).append((teacher, by_id[teacher].names))
        jami_entries = {e.n: e for e in entries["jami"]}
        jami_joined, jami_why = jami.join(jami_entries, people, size, window)
        vocab = frozenset(w for p in people for form in p.names for w in form)
        pair_list, left = jami.pairs([(who, jami_entries[n], teachers.get(who, [])) for n, who in jami_joined.items()],
                                     cfg["jami"], vocab)
        add_gaps(conn, "jami_join", jami_why)
        conn.executemany("INSERT INTO gap VALUES ('jami_statement', ?, ?)", [(f"{k} {w}", n) for (k, w), n in left.items()])
        fact_rows += [facts.pair_fact(p, rows[p.teacher]["name_ar"], cfg["jami"]["book"]) for p in pair_list]
        print(f"Jami' entries joined: {len(jami_joined):,} of {len(jami_entries):,} (left out: "
              f"{', '.join(f'{k} {v:,}' for k, v in sorted(Counter(jami_why.values()).items()))})")
        print(f"Jami' statements read and joined to a teacher: {len(pair_list):,} ("
              + ", ".join(f"{k} {v}" for k, v in sorted(Counter(p.kind for p in pair_list).items())) + ")")
        print("Jami' statements left out: " + ", ".join(f"{k} {w} {n}" for (k, w), n in sorted(left.items())))

        # Mukhtalitin: memory changed late in life, his entry's own sentences.
        mukh_entries = {e.n: e for e in entries["mukhtalitin"]}
        mukh_joined, mukh_why = mukhtalitin.join(mukh_entries, people, size, window)
        add_gaps(conn, "mukhtalitin_join", mukh_why)
        fact_rows += [facts.mukhtalit_fact(who, mukh_entries[n]) for n, who in mukh_joined.items()]
        print(f"Mukhtalitin entries joined: {len(mukh_joined)} of {len(mukh_entries)}")
        for n, reason in mukh_why.items():
            print(f"  gap {n} ({reason}) {mukh_entries[n].head}")

        conn.executemany("INSERT INTO narrator_level VALUES (?, ?, ?, ?, ?)",
                         [(who, level, json.dumps(terms, ensure_ascii=False), kind, grade)
                          for who, (level, terms, kind, grade) in found.items()])
        conn.executemany("INSERT INTO gap VALUES (?, ?, ?)", [(what, text, n) for (what, text), n in gaps.items()])
        notes = add_notes(conn, rijal, found, cfg["weak_from"])
        if target.exists():
            before = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
            was = before.execute("SELECT COUNT(*) FROM note").fetchone()[0]
            before.close()
            if was and abs(notes - was) / was > cfg["max_change_ratio"]:
                raise SystemExit(f"notes went {was:,} to {notes:,}, more than {cfg['max_change_ratio']:.0%}. Old file kept; "
                                 "delete it to accept the new count.")

        pairs_by: dict[tuple[int, int], list] = {}
        for p in pair_list:
            pairs_by.setdefault((p.student, p.teacher), []).append(p)
        outcomes, skipped = add_links(conn, rijal, cfg, tarif_level, pairs_by, exempt)
        conn.executemany("INSERT INTO gap VALUES ('not_a_rung', ?, ?)", list(skipped.items()))

        # What the page counts of him in our books.
        weak: dict[int, set] = {}
        for who, collection, number, part in conn.execute("SELECT narrator_id, collection, number, part FROM note"):
            weak.setdefault(who, set()).add((collection, number, part))
        for student, teacher, collection, number, part in conn.execute(
                "SELECT student_id, teacher_id, collection, number, part FROM link"):
            for who in (student, teacher):
                weak.setdefault(who, set()).add((collection, number, part))
        for who, n in rijal.execute("SELECT narrator_id, COUNT(*) FROM (SELECT DISTINCT narrator_id, collection, number, part "
                                    "FROM mention) GROUP BY narrator_id"):
            fact_rows.append(facts.Fact(who, "books", "hadith_count", str(n), "", "ours", ""))
            fact_rows.append(facts.Fact(who, "books", "weak_points", str(len(weak.get(who, ()))), "", "ours", ""))
        conn.executemany("INSERT INTO narrator_fact VALUES (?, ?, ?, ?, ?, ?, ?)", fact_rows)
        per_level = conn.execute("SELECT level, COUNT(*) FROM note GROUP BY level ORDER BY level").fetchall()
        totals = conn.execute(
            "SELECT kind, collection, COUNT(*) FROM link GROUP BY kind, collection ORDER BY kind, collection").fetchall()
        conn.commit()
    except BaseException:
        conn.close()
        scratch.unlink(missing_ok=True)
        raise
    finally:
        rijal.close()
    conn.close()
    scratch.replace(target)

    print(f"narrators levelled: {len(found):,}")
    print(f"notes: {notes:,}")
    for level, n in per_level:
        print(f"  level {level}: {n:,}")
    print("link notes by kind and collection:")
    for kind, collection, n in totals:
        print(f"  {kind:<12} {collection:<10} {n:,}")
    print("rungs: " + ", ".join(f"{k} {n:,}" for k, n in sorted(outcomes.items())))
    print("name pairs that were no rung: " + ", ".join(f"{k} {n:,}" for k, n in sorted(skipped.items())))
    print("wordings no term took (narrators):")
    for (what, text), n in gaps.most_common(cfg["gap_print"]):
        print(f"  {n:>5}  {what:<4} {text}")
    print(f"  {len(gaps):,} wordings in all, in the gap table")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # the wordings are Arabic
    build()
