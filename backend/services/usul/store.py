"""Read usul.db: where a chain's weak narrators are named, the scale they sit on, and what scholars said of a hadith.

The only reader of usul.db. Built by scripts/build_usul.py, never written
while serving. Missing is a valid state: a hadith then looks as it did before
weak points, with no notes and no scale.
"""
from __future__ import annotations

from backend.config import data_path, get_settings
from backend.services.hadith import loader
from backend.services.hadith.chain import chain_of
from backend.services.readonly_db import ReadOnlyDb
from backend.services.usul.books import page_label
from backend.services.usul.rule import rule

_db = ReadOnlyDb(lambda: data_path("usul_index_path"))


def is_built() -> bool:
    return _db() is not None


def _placed(chains: dict[str, list[list[int]]], key: str, start: int, who: int) -> bool:
    """True when `chains` (rijal.store.chains) names narrator `who` at `start` in hadith `key`."""
    return any(at == start and name == who for at, _, name in chains.get(key, ()))


def notes(collection: str, book: int, chains: dict[str, list[list[int]]]) -> dict[str, list[dict]]:
    """{"1620a": [{at, id, level, kind, grade}, ...]}: each weak narrator named in a book's hadith, in text order.

    Kept only where `chains` (rijal.store.chains of the same book) still names that
    narrator at that place, so a rijal.db rebuilt after usul.db shows no stale note."""
    db = _db()
    found: dict[str, list[dict]] = {}
    if db:
        for number, part, at, who, level, kind, grade in db.execute(
            "SELECT note.number, note.part, note.at, note.narrator_id, note.level, note.kind, narrator_level.grade "
            "FROM note JOIN narrator_level ON narrator_level.narrator_id = note.narrator_id "
            "WHERE note.collection = ? AND note.book = ? ORDER BY note.number, note.part, note.at", (collection, book)
        ):
            if not _placed(chains, f"{number}{part}", at, who):
                continue
            found.setdefault(f"{number}{part}", []).append(
                {"at": at, "id": who, "level": level, "kind": kind, "grade": grade})
    return found


def scale() -> list[dict]:
    """The twelve levels as the page prints them, none while usul.db is not built.

    A level's lift is keyed by kind: level 5 lifts for a memory fault, not for an innovation."""
    if not is_built():
        return []
    cfg = rule()
    books = {key: book["label"] for key, book in cfg["sources"].items()}
    out = []
    for row in cfg["levels"]:
        kinds = {row["kind"], *row.get("kinds", {}).values()}
        lifts = {kind: found for kind in kinds if (found := cfg["lift"].get(str(row["level"])) or cfg["lift"].get(kind))}
        out.append({
            "level": row["level"], "ar": row["ar"], "en": row["en"], "kind": row["kind"],
            "weak": row["level"] >= cfg["weak_from"], "source": books[cfg["levels_source"]],
            "lift": {kind: {"en": found["en"], "lifts": found.get("lifts", True), "quote": found["quote"],
                            "source": books[found["book"]]} for kind, found in lifts.items()},
        })
    return out


def _source(key: str) -> str:
    return rule()["sources"][key]["label"]


def links(collection: str, book: int, chains: dict[str, list[list[int]]]) -> dict[str, list[dict]]:
    """{"1620a": [{at, student, teacher, kind, sub, word, level, quote, scholar, source, page}, ...]}: each link of a
    book's chains a source puts in doubt, in text order.

    Kept only where `chains` still names the teacher at `at` with the student just before him, like `notes`."""
    db = _db()
    found: dict[str, list[dict]] = {}
    if db:
        for number, part, at, kind, sub, student, teacher, word, level, quote, scholar, source, page in db.execute(
            "SELECT number, part, at, kind, sub, student_id, teacher_id, word, level, quote, scholar, source, page "
            "FROM link WHERE collection = ? AND book = ? ORDER BY number, part, at, level DESC", (collection, book)
        ):
            key = f"{number}{part}"
            named = chains.get(key, ())
            i = next((i for i, (start, _, who) in enumerate(named) if start == at and who == teacher), 0)
            if not i or named[i - 1][2] != student:   # the student must be the name just before his teacher
                continue
            found.setdefault(key, []).append({
                "at": at, "student": student, "teacher": teacher, "kind": kind, "sub": sub, "word": word, "level": level,
                "quote": quote, "scholar": scholar, "source": _source(source) if source else "", "page": page})
    return found


def rulings(collection: str, book: int) -> dict[str, list[dict]]:
    """{"1620a": [{kind, label, quote_label, scholar, quote, asked, chapter, source, page}, ...]}: what a classical ruling
    book says of each hadith of a book of ours, in the order of usul.json `rulings.kinds`. The quote is the scholar's own
    sentence. A row of a kind the config no longer names is left out."""
    db = _db()
    found: dict[str, list[dict]] = {}
    if db:
        kinds = rule()["rulings"]["kinds"]
        for number, part, kind, scholar, quote, asked, chapter, source, page in db.execute(
            "SELECT number, part, kind, scholar, quote, asked, chapter, book, page FROM ruling "
            "WHERE collection = ? AND hbook = ? ORDER BY number, part, page", (collection, book)
        ):
            if kind in kinds:
                found.setdefault(f"{number}{part}", []).append({
                    "kind": kind, "label": kinds[kind]["label"], "quote_label": kinds[kind].get("quote_label", ""),
                    "scholar": scholar, "quote": quote, "asked": asked, "chapter": chapter, "source": _source(source), "page": page})
        order = list(kinds)
        for rows in found.values():
            rows.sort(key=lambda row: order.index(row["kind"]))
    return found


def terms() -> list[dict]:
    """[{kind, label, say, count}]: each sort of ruling in usul.db with how many of our hadith carry it. Empty while
    usul.db is not built."""
    db = _db()
    if not db:
        return []
    count = dict(db.execute("SELECT kind, COUNT(*) FROM (SELECT DISTINCT kind, collection, number, part FROM ruling) "
                            "GROUP BY kind"))
    return [{"kind": kind, "label": row["label"], "say": row["say"], "count": count[kind]}
            for kind, row in rule()["rulings"]["kinds"].items() if kind in count]


def term(kind: str, offset: int, limit: int) -> tuple[int, list[dict]] | None:
    """(how many hadith carry a ruling of this kind, a page of them as {collection, book, number, part}), or None where
    the config names no such kind. A limit of 0 is the configured page; none goes past the configured maximum."""
    if kind not in rule()["rulings"]["kinds"]:
        return None
    db = _db()
    if not db:
        return 0, []
    settings = get_settings()
    limit = min(limit or settings.usul_term_page, settings.usul_term_max)
    total = db.execute("SELECT COUNT(*) FROM (SELECT DISTINCT collection, number, part FROM ruling WHERE kind = ?)",
                       (kind,)).fetchone()[0]
    return total, [{"collection": collection, "book": book, "number": number, "part": part} for collection, book, number, part in db.execute(
        "SELECT DISTINCT collection, hbook, number, part FROM ruling WHERE kind = ? "
        "ORDER BY collection, number, part LIMIT ? OFFSET ?", (kind, limit, offset))]


def link_rules() -> dict:
    """What the links say, from usul.json: by kind (a tadlis kind, or the sort of statement a scholar made) and, for
    tadlis, by the Ta'rif level of the one who says the word. Empty while usul.db is not built."""
    if not is_built():
        return {}
    cfg = rule()
    cite = lambda row: {"source": _source(row["book"]), "page": page_label(row["page"])}  # noqa: E731
    return {
        "kinds": {**{kind: {"label": row["label"], "say": row["say"], "quote": row["quote"], **cite(row)}
                     for kind, row in cfg["tadlis"]["kinds"].items()},
                  **{kind: {"label": row["label"], "say": row["say"]} for kind, row in cfg["jami"]["kinds"].items()}},
        "levels": {level: {"say": row["say"], "quote": row["quote"], **cite(row)}
                   for level, row in cfg["tadlis"]["levels"].items() if row["notes"]},
    }


def facts(narrator_id: int) -> dict[str, list[dict]]:
    """{"reliability": [{text, ar, quote, rule, book, page}, ...], "habits": ..., "life": ..., "books": ...}

    The lines the narrator books and our hadith give for one narrator. Empty while usul.db is not built."""
    groups: dict[str, list[dict]] = {name: [] for name in rule()["fact_groups"]}
    db = _db()
    if not db:
        return groups
    cfg = rule()
    level = db.execute("SELECT level, grade FROM narrator_level WHERE narrator_id = ?", (narrator_id,)).fetchone()
    for group, kind, value, quote, book, page in db.execute(
            "SELECT grp, kind, value, quote, book, page FROM narrator_fact WHERE narrator_id = ? ORDER BY rowid",
            (narrator_id,)):
        line = {"text": "", "ar": "", "quote": quote, "rule": None, "book": _source(book), "page": page}
        if kind == "level":
            line["text"] = cfg["facts"][kind].format(value=value, en=next(r["en"] for r in cfg["levels"] if r["level"] == int(value)))
            line["ar"] = level[1] if level else ""
        elif kind == "generation":
            line["text"], line["ar"] = cfg["facts"][kind].format(value=value), cfg["taqrib"]["generations"][int(value) - 1]
        elif kind == "death_hundreds":
            death = cfg["taqrib"]["death"]
            line["text"] = cfg["facts"][kind].format(value=value)
            line["rule"] = {"say": death["bands_say"], "quote": death["quote"], "book": _source("taqrib"), "page": page_label(death["page"])}
        elif kind == "tadlis":
            row = cfg["tadlis"]["levels"][value]
            line["text"] = cfg["facts"][kind].format(value=value)
            line["rule"] = {"say": row["say"], "quote": row["quote"], "book": _source(row["book"]), "page": page_label(row["page"])}
        elif kind in cfg["jami"]["kinds"]:
            line["text"], line["ar"] = cfg["facts"][kind], value
        else:
            line["text"] = cfg["facts"][kind].format(value=value)
        groups[group].append(line)
    return groups


def family_places(collection: str, number: int, narrations: int) -> dict | None:
    """{heading, note, places: [{label, count, alone}]}: the narrators at each place of the chains the book gives under
    this number, the Companion first, as usul.json `family.places` words it. `alone` is set where one narrator carries
    all `narrations`. None while usul.db is not built or when the build left the family without a picture."""
    db = _db()
    counts = [r[0] for r in db.execute(
        "SELECT count FROM family_place WHERE collection = ? AND number = ? ORDER BY place", (collection, number))] if db else []
    if not counts:
        return None
    words = rule()["family"]["places"]
    book = loader.collection_name(collection) or collection
    return {"heading": words["heading"].format(book=book, n=narrations, number=number), "note": words["note"],
            "places": [{"label": words["first"] if i == 0 else words["next"].format(n=i + 1), "count": count,
                        "alone": words["alone"].format(n=narrations) if count == 1 else ""}
                       for i, count in enumerate(counts)]}


def family_words(collection: str, number: int) -> dict | None:
    """{label, legend, parts: {"b": {words, marks: [{at, kind, other}, ...]}}}: each telling the build marked words in,
    with its matn's words (the Arabic after the chain's own cut, chain.chain_of, split as the build split it) as served
    now, and usul.json `family.words` naming the view. None while no telling has a mark.

    A mark stays only where that matn still has its word at `at`, like `notes`; a telling left with none is not given."""
    db = _db()
    marked: dict[str, list[tuple]] = {}
    if db:
        for part, at, word, kind, other in db.execute(
                "SELECT part, at, word, kind, other FROM family_word WHERE collection = ? AND number = ? ORDER BY part, at",
                (collection, number)):
            marked.setdefault(part, []).append((at, word, kind, other))
    if not marked:
        return None
    arabic = {row[3]: row[4] for row in loader.numbered(collection, number)[1]}
    found: dict[str, dict] = {}
    for part, row in marked.items():
        tokens = chain_of(arabic.get(part, ""))[1].split()
        kept = [{"at": at, "kind": kind, "other": other} for at, word, kind, other in row
                if at < len(tokens) and tokens[at] == word]
        if kept:
            found[part] = {"words": tokens, "marks": kept}
    return {**rule()["family"]["words"], "parts": found} if found else None
