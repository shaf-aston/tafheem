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

Every quote in usul.json that names a book and a page is first found in that book and its page checked
against the one the book's markers give (check_pages); any mismatch stops the build.

For each hadith number told more than once it counts the narrators at each place of the chains and
compares the words of the tellings (services/usul/family.py), and prints the families with a picture
and those left without one, by reason. `--sample FILE` also writes families laid out for checking by hand.

Rebuilding is safe at any time: it writes a fresh file beside the old one and
moves it into place at the end, like build_rijal.py. It stops, leaving the old
file, if the number of notes moves more than `max_change_ratio` against it.
"""
from __future__ import annotations

import json
import sqlite3
import sys
import argparse
import difflib
import itertools
import random
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services.hadith import chain, loader  # noqa: E402
from backend.services.hadith.chain import chain_of  # noqa: E402
from backend.services.usul import books, facts, family, jami, match, mukhtalitin, names, ruling, rung, taqrib, tarif  # noqa: E402
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
CREATE TABLE ruling (
    collection TEXT NOT NULL, hbook INTEGER NOT NULL, number INTEGER NOT NULL, part TEXT NOT NULL, book TEXT NOT NULL,
    kind TEXT NOT NULL,
    scholar TEXT NOT NULL, quote TEXT NOT NULL, asked TEXT NOT NULL, chapter TEXT NOT NULL, page TEXT NOT NULL,
    unit INTEGER NOT NULL, score REAL NOT NULL,
    PRIMARY KEY (collection, number, part, book, kind, scholar, quote)
) WITHOUT ROWID;
CREATE INDEX ruling_by_kind ON ruling (kind, collection, number, part);
CREATE INDEX ruling_by_book ON ruling (collection, hbook);
CREATE TABLE family_place (
    collection TEXT NOT NULL, number INTEGER NOT NULL, place INTEGER NOT NULL, count INTEGER NOT NULL, ids TEXT NOT NULL,
    PRIMARY KEY (collection, number, place)
) WITHOUT ROWID;
CREATE TABLE family_word (
    collection TEXT NOT NULL, number INTEGER NOT NULL, part TEXT NOT NULL, at INTEGER NOT NULL, word TEXT NOT NULL,
    kind TEXT NOT NULL, other TEXT NOT NULL,
    PRIMARY KEY (collection, number, part, at)
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


def add_notes(conn: sqlite3.Connection, mentions: dict[tuple, list], found: dict, weak_from: int) -> int:
    """One note per place a weak narrator is named."""
    for key, men in mentions.items():
        for start, _, who in men:
            level, _, kind, _ = found.get(who, (0, None, None, None))
            if level >= weak_from:
                conn.execute("INSERT OR IGNORE INTO note VALUES (?, ?, ?, ?, ?, ?, ?, ?)", (*key, start, who, level, kind))
    return conn.execute("SELECT COUNT(*) FROM note").fetchone()[0]


def guard_change(target: Path, table: str, now: int, ratio: float) -> None:
    """Stop the build when `table` of the built file `target` would change by more than `ratio` of its rows."""
    if not target.exists():
        return
    before = sqlite3.connect(f"file:{target}?mode=ro", uri=True)
    try:
        was = before.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    except sqlite3.OperationalError:   # a file built before this table existed
        was = 0
    before.close()
    if was and abs(now - was) / was > ratio:
        raise SystemExit(f"{table} rows went {was:,} to {now:,}, more than {ratio:.0%}. Old file kept; "
                         "delete it to accept the new count.")


def read_texts(cfg: dict) -> dict[str, str]:
    """The text of each book fetch_usul.py saved; a missing file stops the build."""
    folder = data_path("usul_books_dir")
    found = {}
    for key in cfg["books"]:
        if key == "base":
            continue
        path = folder / f"{key}.txt"
        if not path.exists():
            raise SystemExit(f"no {path.name}. Run: python backend/scripts/fetch_usul.py")
        found[key] = path.read_text(encoding="utf-8")
    return found


def read_books(cfg: dict, texts: dict[str, str]) -> dict[str, list[books.Entry]]:
    """Every entry of each book whose config says how its entries open; the rest are only quoted from."""
    return {key: books.entries(texts[key], spec) for key, spec in cfg["books"].items() if "entry" in spec}


def cited(node, path: str = ""):
    """(path, dict) for every dict in the config that quotes a book and names its page."""
    if isinstance(node, dict):
        if all(isinstance(node.get(key), str) for key in ("quote", "book", "page")):
            yield path, node
        for key, value in node.items():
            yield from cited(value, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from cited(value, f"{path}[{i}]")


def check_pages(cfg: dict, texts: dict[str, str]) -> list[str]:
    """One line per quote the books do not bear out: its path, the page the config gives and the one the book gives."""
    problems = []
    for path, node in cited(cfg):
        found = books.locate(texts[node["book"]], node["quote"], cfg["verify"])
        if found != node["page"]:
            problems.append(f"{path}: book {node['book']}, config {node['page']!r}, derived "
                            + ("not found" if found is None else repr(found)))
    return problems


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


def our_hadith() -> list[tuple[tuple, str, int]]:
    """((collection, number, part), Arabic, book number) for every hadith in hadith.db."""
    return [((collection, number, part), arabic, book) for collection, book, number, part, arabic in loader.every_hadith()]


def narrators_by_hadith(rijal: sqlite3.Connection, rows: dict[int, dict]) -> dict[tuple, list[list[tuple[str, ...]]]]:
    """{(collection, number, part): the name forms (match.forms) of each narrator its chain names}."""
    forms = {who: match.forms(row) for who, row in rows.items()}
    found: dict[tuple, dict[int, list]] = {}
    for collection, number, part, who in rijal.execute("SELECT collection, number, part, narrator_id FROM mention"):
        found.setdefault((collection, number, part), {})[who] = forms.get(who, [])
    return {key: list(men.values()) for key, men in found.items()}


def mentions_by_hadith(rijal: sqlite3.Connection) -> dict[tuple, list[tuple[int, int, int]]]:
    """{(collection, book, number, part): its mentions (start, end, narrator id) in text order, one per start}."""
    found: dict[tuple, dict[int, tuple]] = {}
    for collection, book, number, part, start, end, who in rijal.execute(
            "SELECT collection, book, number, part, start, end, narrator_id FROM mention "
            "ORDER BY collection, book, number, part, ord"):
        found.setdefault((collection, book, number, part), {}).setdefault(start, (start, end, who))
    return {key: list(men.values()) for key, men in found.items()}


def add_links(conn: sqlite3.Connection, mentions: dict[tuple, list], cfg: dict, tarif_level: dict[int, int],
              pairs_by: dict[tuple[int, int], list], exempt: list[dict]) -> tuple[Counter, Counter]:
    """Link notes for every rung of every chain: (what each rung got or why not, why two names were no rung)."""
    outcomes: Counter = Counter()
    skipped: Counter = Counter()
    for (collection, book), hadith in itertools.groupby(mentions.items(), key=lambda kv: kv[0][:2]):
        arabic = {(h["number"], h["part"]): h["arabic"] for h in loader.hadiths(collection, book)}
        for (_, _, number, part), men in hadith:
            if (number, part) not in arabic:
                continue
            found, left = rung.rungs(arabic[number, part], men)
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


def read_rulings(units: dict[str, list[books.Entry]], cfg: dict) -> tuple[list[tuple], Counter, Counter]:
    """([(kind, book, entry, ruling, the unit's chain words, its matn words)], units unread by (book, why), rulings
    with no matn by book): what each unit of each ruling book says and the hadith it says it of, as words."""
    rl, knobs = cfg["rulings"], cfg["rulings"]["match"]
    todo, unread, thin = [], Counter(), Counter()
    for kind, kc in rl["kinds"].items():
        for entry in units[kc["book"]]:
            found, why = ruling.read(entry, kind, rl)
            unread[kc["book"], why] += not found
            for r in found:
                chain_text, matn = match.split_hadith(r.head, {**rl["shared"], **kc}, rl["shared"]["matn_quote"])
                words = match.tokens(matn)
                if len(words) < knobs["gram"]:
                    thin[kc["book"]] += 1
                    continue
                todo.append((kind, kc["book"], entry, r, names.words(" ".join(chain.name_tokens(chain_text))), words))
    return todo, unread, thin


def add_rulings(conn: sqlite3.Connection, units: dict[str, list[books.Entry]], hadith: list[tuple[tuple, str, int]],
                narrators_of: dict[tuple, list[list[tuple[str, ...]]]], everyone: list[list[tuple[str, ...]]], cfg: dict
                ) -> list[str]:
    """A row of `ruling` for each hadith of ours a ruling book's unit is about (services/usul/ruling.py reads the unit,
    match.py finds the hadith). Returns the report: per book the units, what was read and what became of it.

    hadith: ((collection, number, part), its Arabic, its book number); narrators_of: the name forms of each hadith's narrators, by key;
    everyone: every narrator's name forms, once each, for how many men carry a name."""
    rl, knobs = cfg["rulings"], cfg["rulings"]["match"]
    todo, unread, thin = read_rulings(units, cfg)
    if not todo:
        return []
    wanted = set().union(*(match.grams(words, knobs["gram"]) for *_, words in todo))
    index = match.Index({key: match.tokens(chain.chain_of(arabic).body) for key, arabic, _ in hadith}, knobs["gram"], wanted)
    book_of = {key: number for key, _, number in hadith}
    men = match.Names([f for forms in narrators_of.values() for f in forms], everyone, knobs["min_name_words"],
                      knobs["rare_name"], knobs["rare_men"], knobs["name_stop"], knobs["name_run"])
    fate: dict[str, Counter] = {book: Counter() for book in units}
    for kind, book, entry, r, unit_names, words in todo:
        chosen, how = match.choose(
            index.scores(words, knobs["df_max"]), index.possible(words, knobs["df_max"]),
            lambda key: men.shares(unit_names, [f for forms in narrators_of.get(key, ()) for f in forms]), knobs)
        fate[book][how] += 1
        fate[book]["tied"] += len(chosen) > 1
        where = entry.where(r.at) if rl["kinds"][kind]["numbered"] else books.page_label(entry.page_at(r.at))
        for (collection, number, part), score in chosen:
            conn.execute("INSERT OR IGNORE INTO ruling VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                         (collection, book_of[collection, number, part], number, part, book, kind, r.scholar, r.quote,
                          r.asked, r.chapter, where, entry.n, round(score, 1)))
    conn.executemany("INSERT INTO gap VALUES ('ruling_unit', ?, ?)",
                     [(f"{book}: {why}", n) for (book, why), n in unread.items() if n])
    conn.executemany("INSERT INTO gap VALUES ('ruling_no_matn', ?, ?)", list(thin.items()))
    for book, counts in fate.items():
        conn.executemany("INSERT INTO gap VALUES ('ruling_match', ?, ?)",
                         [(f"{book}: {how}", counts[how]) for how in ("below_floor", "rejected") if counts[how]])
    by_kind = dict(conn.execute("SELECT kind, COUNT(*) FROM ruling GROUP BY kind"))
    report = []
    for kind, kc in rl["kinds"].items():
        book, entries = kc["book"], units[kc["book"]]
        numbers = {e.n for e in entries}
        absent = [n for n in range(1, max(numbers, default=0) + 1) if n not in numbers] if kc["numbered"] else []
        counts = fate[book]
        why_not = ", ".join(f"{why} {n}" for (b, why), n in sorted(unread.items()) if b == book and n)
        report.append(
            f"{book}: {len(entries):,} units"
            + (f", {len(absent)} numbers of the book's own sequence missing {absent[:10]}" if absent else "")
            + f"; {sum(1 for _ in entries) - sum(n for (b, _), n in unread.items() if b == book):,} read"
            + (f" (unread: {why_not})" if why_not else "")
            + f"; of {sum(counts[h] for h in ('matched', 'rejected', 'below_floor')) + thin[book]:,} rulings read: "
            f"matched {counts['matched']:,} (tied {counts['tied']:,}), rejected by c2 {counts['rejected']:,}, "
            f"below floor {counts['below_floor']:,}, no matn {thin[book]:,}; {by_kind.get(kind, 0):,} {kind} rows")
    return report


def add_families(conn: sqlite3.Connection, mentions: dict[tuple, list], hadith: list[tuple[tuple, str, int]],
                 rows: dict[int, dict], cfg: dict) -> tuple[list[str], list[dict]]:
    """family_place and family_word for every hadith number told more than once (the parts rijal.db names).

    Returns (the report, one dict per family for the sample: parts, chains, places, marks, why)."""
    fc = cfg["family"]
    generations = json.loads((data_path("rijal_dir") / "rijal.json").read_text(encoding="utf-8"))["generations"]
    companions = set(next(g["tabaqat"] for g in generations if g["key"] == fc["companion_group"]))
    generation = {who: row["generation_ar"] for who, row in rows.items()}
    arabic = {key: text for key, text, _ in hadith}
    told: dict[tuple, dict[str, list[tuple[int, int, int]]]] = {}
    for (collection, _, number, part), men in mentions.items():
        told.setdefault((collection, number), {})[part] = men
    families = {key: sorted(by_part) for key, by_part in told.items() if len(by_part) >= 2}
    # Every telling's matn words, cut like the app cuts them; the weight of a word is read off all of them.
    matn_of = {(c, n, p): chain_of(arabic.get((c, n, p), "")) for (c, n), parts in families.items() for p in parts}
    keys_of = lambda words: {k for w in words if (k := family.word_key(w, fc))}  # noqa: E731
    weight = family.weights([keys_of(cut.body.split()) for cut in matn_of.values()])
    why_place, why_word, mark_kinds = Counter(), Counter(), Counter()
    picture_n = alone_n = compared_n = marked_n = 0
    results = []
    for (collection, number), parts in families.items():
        by_part = told[collection, number]
        chains, reasons = {}, {}
        for part in parts:
            chains[part], reasons[part] = family.chain_ids(arabic.get((collection, number, part), ""),
                                                           by_part[part], generation, companions, fc["joiner"])
        why = next((r for r in reasons.values() if r), "")
        shown = {"collection": collection, "number": number, "parts": parts, "chains": chains, "why": why, "places": [],
                 "marks": {}, "matns": {}, "left": {}, "shares": {},
                 "arabic": {p: arabic.get((collection, number, p), "") for p in parts}}
        if why:
            why_place[why] += 1
        else:
            sets = family.places(list(chains.values()))
            picture_n += 1
            alone_n += sum(len(s) == 1 for s in sets)
            shown["places"] = sets
            conn.executemany("INSERT INTO family_place VALUES (?, ?, ?, ?, ?)",
                             [(collection, number, i, len(s), json.dumps(sorted(s))) for i, s in enumerate(sets)])
        matns = {}
        for part in parts:
            cut = matn_of[collection, number, part]
            if not cut.chain:
                why_word["no_chain_cut"] += 1
            elif reasons[part] == "name_after_cut":   # chain words in the text would be marked as its own
                why_word["name_after_cut"] += 1
            else:
                matns[part] = cut.body.split()
        found, left = family.marks(matns, fc, weight)
        why_word.update(left.values())
        compared_n += len(matns) - len(left) >= 2
        if "different_text" in left.values():
            shown["shares"] = family.shares({p: keys_of(matns[p]) for p in matns if left.get(p) != "short_matn"}, weight)
        for part, row in found.items():
            marked_n += 1
            mark_kinds.update(m.kind for m in row)
            conn.executemany("INSERT INTO family_word VALUES (?, ?, ?, ?, ?, ?, ?)",
                             [(collection, number, part, m.at, m.word, m.kind, m.other) for m in row])
        shown.update(marks=found, matns=matns, left=left)
        results.append(shown)
    say = fc["reasons"]
    conn.executemany("INSERT INTO gap VALUES ('family_place', ?, ?)", [(say[k], n) for k, n in why_place.items()])
    conn.executemany("INSERT INTO gap VALUES ('family_word', ?, ?)", [(say[k], n) for k, n in why_word.items()])
    ranked = lambda counts: ", ".join(f"{say[k]} {v:,}" for k, v in sorted(counts.items(), key=lambda kv: -kv[1]))  # noqa: E731
    report = [f"families (a number told more than once): {len(families):,}; with a picture of its places: {picture_n:,} "
              f"({alone_n:,} places held by one narrator in every narration)",
              "families left without a picture (gap family_place): " + ranked(why_place),
              f"word differences: {compared_n:,} families compared; {marked_n:,} tellings marked; "
              + ", ".join(f"{k} {v:,}" for k, v in sorted(mark_kinds.items())),
              "word differences left out (gap family_word, tellings): " + ranked(why_word)]
    return report, results


def write_sample(path: Path, results: list[dict], rows: dict[int, dict], cfg: dict) -> None:
    """Text to check by hand: `sample` seeded random families that got a picture (each telling's chain by place with
    ids and names, the Arabic chain, the counts per place, each marked word in its sentence beside what the closest
    other telling says there), then `sample_gap` families sent to each reason that is a family's own (names joined, a
    telling of different text) with their chain text."""
    fc = cfg["family"]
    rng = random.Random(fc["sample_seed"])
    name = lambda who: f"{who} {rows[who]['name_ar']}"  # noqa: E731
    chain_text = lambda text: chain_of(text).chain or f"(no plain chain) {text[:fc['sample_text']]}"  # noqa: E731
    out = ["# Usul: families checked by hand", "",
           f"Seed {fc['sample_seed']}. Places count from the Companion (place 1). A word is marked when no other telling "
           "of its group of one report has it.", ""]
    pictured = [r for r in results if r["places"]]
    for r in rng.sample(pictured, min(fc["sample"], len(pictured))):
        n = len(r["parts"])
        out.append(f"## {r['collection']} {r['number']}: {n} narrations")
        for i, s in enumerate(r["places"], 1):
            alone = f" (one narrator in all {n} narrations)" if len(s) == 1 else ""
            out.append(f"- place {i}: {len(s)}{alone} = " + "; ".join(name(w) for w in sorted(s)))
        for part in r["parts"]:
            out.append(f"- {r['number']}{part} by place: " + " > ".join(name(w) for w in reversed(r["chains"][part])))
            out.append(f"  chain text: {chain_text(r['arabic'][part])}")
        for part in r["parts"]:
            words = r["matns"].get(part)
            if words is None:
                out.append(f"- {part}: no chain cut, not compared")
                continue
            if part in r["left"]:
                out.append(f"- {part}: {fc['reasons'][r['left'][part]]}, not compared")
                continue
            row = r["marks"].get(part, [])
            out.append(f"- {part}: {len(words)} words, {len(row)} marked")
            others = {q: w for q, w in r["matns"].items() if q != part and q not in r["left"]}
            keys = [family.word_key(w, fc) for w in words]
            theirs = {q: [family.word_key(w, fc) for w in ws] for q, ws in others.items()}
            best = max(others, key=lambda q: difflib.SequenceMatcher(None, keys, theirs[q], autojunk=False).ratio(),
                       default=None)
            ops = difflib.SequenceMatcher(None, keys, theirs[best], autojunk=False).get_opcodes() if best else []
            for m in row:
                op = next((o for o in ops if o[1] <= m.at < o[2] or o[1] == o[2] == m.at), None)
                there = " ".join(others[best][op[3]:op[4]]) if op and op[0] != "equal" else ""
                around = " ".join(words[max(0, m.at - 2): m.at]) + f" [{m.word}] " + " ".join(words[m.at + 1: m.at + 3])
                out.append(f"    - {m.kind}: {around}" + (f"   (no dots: {m.other})" if m.other else "")
                           + f"   | {best} says: {there or '(nothing there)'}")
        out.append("")
    for reason, held in (("names_joined", lambda r: r["why"] == "names_joined"),
                         ("different_text", lambda r: "different_text" in r["left"].values())):
        pool = [r for r in results if held(r)]
        out.append(f"## Sent to a gap: {fc['reasons'][reason]} ({len(pool)} families; {min(fc['sample_gap'], len(pool))} below)")
        for r in rng.sample(pool, min(fc["sample_gap"], len(pool))):
            out.append(f"- {r['collection']} {r['number']}")
            for part in r["parts"]:
                tag = f" [{fc['reasons'][r['left'][part]]}]" if part in r["left"] else ""
                out.append(f"  - {part}{tag}: {chain_text(r['arabic'][part])}")
            if reason == "different_text":
                out.append("  - share of the shorter telling's weighted words the other holds: "
                           + ", ".join(f"{p}/{q} {v:.2f}" for (p, q), v in sorted(r["shares"].items())))
        out.append("")
    path.write_text("\n".join(out), encoding="utf-8")


def build(sample: Path | None = None) -> None:
    source = data_path("rijal_index_path")
    if not source.exists():
        raise SystemExit(f"no {source.name}. Run: python backend/scripts/build_rijal.py")
    cfg = rule()
    texts = read_texts(cfg)
    if problems := check_pages(cfg, texts):
        raise SystemExit("usul.json pages the books do not bear out:\n  " + "\n  ".join(problems))
    entries = read_books(cfg, texts)
    size, window = cfg["join"]["name_words"], cfg["join"]["nisba_window"]
    target = data_path("usul_index_path")
    scratch = target.with_suffix(".building.db")
    scratch.unlink(missing_ok=True)
    rijal = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
    conn = sqlite3.connect(scratch)
    try:
        conn.executescript(_SCHEMA)
        rows = narrator_rows(rijal)
        mentions = mentions_by_hadith(rijal)
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
        notes = add_notes(conn, mentions, found, cfg["weak_from"])
        guard_change(target, "note", notes, cfg["max_change_ratio"])

        pairs_by: dict[tuple[int, int], list] = {}
        for p in pair_list:
            pairs_by.setdefault((p.student, p.teacher), []).append(p)
        outcomes, skipped = add_links(conn, mentions, cfg, tarif_level, pairs_by, exempt)
        conn.executemany("INSERT INTO gap VALUES ('not_a_rung', ?, ?)", list(skipped.items()))

        # The ruling books: what a classical book says of a hadith, quoted, for each hadith of ours it is about.
        ruling_report = []
        if any(entries[kc["book"]] for kc in cfg["rulings"]["kinds"].values()):
            ruling_report = add_rulings(conn, entries, our_hadith(), narrators_by_hadith(rijal, rows),
                                       [match.forms(row) for row in rows.values()], cfg)
            guard_change(target, "ruling", conn.execute("SELECT COUNT(*) FROM ruling").fetchone()[0], cfg["max_change_ratio"])

        # The versions fold: narrators counted at each place of a number's chains, and words one telling alone has.
        family_report, family_results = add_families(conn, mentions, our_hadith(), rows, cfg)
        for table in ("family_place", "family_word"):
            guard_change(target, table, conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0], cfg["max_change_ratio"])

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

    print("\n".join(ruling_report))
    print("\n".join(family_report))
    if sample:
        write_sample(sample, family_results, rows, cfg)
        print(f"sample written to {sample}")
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
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=Path, help="also write families here, laid out for checking by hand")
    build(ap.parse_args().sample)
