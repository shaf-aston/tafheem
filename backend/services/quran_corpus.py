"""The Qur'an's grammar, read from the hand-tagged corpus.

This module is the only thing that opens corpus.db. Everything else asks it.

Two jobs:

  1. Turn the corpus's shorthand into words a learner can read. The corpus writes
     `N` and `PN|ROOT:أله|NOM`; a reader needs "proper noun · nominative · from the
     root أ-ل-ه". The shorthand's meaning lives in data/quran/tags.json, not here,
     because it is reference data and someone may want to reword it.

  2. Answer the two questions the app asks: what is in this ayah, and where else
     does this root appear. The second is what links the five tabs together, a
     root found in an ayah is the same root the dictionary and the conjugator use.

What is not here: syntax. This database holds morphology only, nothing in it
says which word governs which. So the tarkeeb tree cannot be looked up; it is
derived from these tags by rule in tarkeeb.py, which reads them through
tags_for_ayah.
"""
from __future__ import annotations

import json
import sqlite3
from functools import lru_cache
from itertools import groupby
from pathlib import Path

from backend.services import arabic_text
from backend.services.readonly_db import ReadOnlyDb

DATA_DIR = Path(__file__).parent.parent / "data" / "quran"
DATABASE = DATA_DIR / "corpus.db"
TAGS_FILE = DATA_DIR / "tags.json"

# A prefix or suffix is glued to the word it belongs to; only the middle piece
# carries the word's own identity.
_ATTACHED = ("PREF", "SUFF")


@lru_cache(maxsize=1)
def tags() -> dict:
    return json.loads(TAGS_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _families_by_bare_spelling() -> dict:
    """The verb families, keyed by their spelling with the vowel marks removed.

    The two sides disagree on vowelling for the same word: tags.json writes كان
    bare, the corpus writes كَان with a fatha. Matching the literal spelling threw
    KeyError on 1,283 ayahs; a fifth of the Qur'an, so both sides are reduced to
    the same bare form before they meet.
    """
    return {arabic_text.strip_diacritics(k): v for k, v in tags()["families"].items()}


def is_loaded() -> bool:
    return DATABASE.exists()


# Callers check is_loaded() first, so the None for "not built" never reaches them.
_db = ReadOnlyDb(lambda: DATABASE)


# ── Reading the shorthand ────────────────────────────────────────────────────

def _person_gender_number(token: str) -> list[str]:
    """"3MP" -> ["غائب", "مذكر", "جمع"], or [] if not one."""
    parts = tags()["person_gender_number"]
    if not token or any(letter not in parts for letter in token):
        return []
    return [parts[letter]["ar"] for letter in token]


def _verb_pattern(number: str, root: str) -> str:
    """VF:1 -> the baab, written the way a Sarf student would recognise it."""
    patterns = tags()["verb_patterns"]
    shapes = patterns["four_letter" if len(root) == 4 else "three_letter"]
    index = int(number) - 1
    return f"وزن {shapes[index]}" if 0 <= index < len(shapes) else f"الباب {number}"


def describe(pos: str, features: str, root: str = "") -> list[str]:
    """The grammar of one segment, as a list of Arabic terms.

    The terms stand alone on the page (اسم, مرفوع, مضارع), the way every other
    tab prints them; the English column of tags.json is for a reader of that
    file, not for the screen.

    A tag can mean two things depending on the word it sits on, ACC is the
    accusative case on a noun but an accusative particle on a letter, so the
    part of speech decides which table is read.
    """
    table = tags()
    said: list[str] = []

    def say(phrase: str) -> None:
        if phrase and phrase not in said:
            said.append(phrase)

    # The part of speech first, unless a later tag names it more precisely.
    base = table["types"].get(pos)
    tokens = [token for token in features.split("|") if token]
    refined = any(token in table["types"] for token in tokens)
    if base and not refined:
        say(base["ar"])

    for token in tokens:
        name, _, value = token.partition(":")

        if name in _ATTACHED:
            say(table["structure"][name.replace("PREF", "PREFIX").replace("SUFF", "SUFFIX")]["ar"])
        elif name == "VF":
            say(_verb_pattern(value, root))
        elif name == "MOOD":
            say(table["mood"][value]["ar"])
        elif name == "FAM":
            if family := _families_by_bare_spelling().get(arabic_text.strip_diacritics(value)):
                say(family["ar"])
        elif name in table["types"]:
            say(table["types"][name]["ar"])
        elif name in table["noun_forms"]:
            say(table["noun_forms"][name]["ar"])
        elif name in table["attrs"]:
            say(table["attrs"][name]["ar"])
        elif name == "DET":
            say(table["structure"]["DET"]["ar"])
        # ACC and IMPV live in two tables; the part of speech says which.
        elif name in table["case"] and pos == "N":
            say(table["case"][name]["ar"])
        elif name in table["tense"] and pos == "V":
            say(table["tense"][name]["ar"])
        elif name in table["particles"] and pos == "P":
            say(table["particles"][name]["ar"])
        elif parts := _person_gender_number(name):
            for part in parts:
                say(part)

    return said


# ── The two questions the app asks ───────────────────────────────────────────

def _stem_of(segments: list[sqlite3.Row]) -> sqlite3.Row:
    """The piece of a word that carries its identity, not the glued-on ones.

    Testing for a root instead would pick the prefix of بِسْمِ, because بِ carries
    a dictionary form of its own, and the word would lose its root سمو.
    """
    def attached(segment: sqlite3.Row) -> bool:
        return any(tag in segment["features"].split("|") for tag in _ATTACHED)

    return next(
        (s for s in segments if not attached(s)),
        next((s for s in segments if s["root"]), segments[0]),
    )


def _word_from(segments: list[sqlite3.Row]) -> dict:
    """Several segments, a prefix, a stem, a suffix; read as one word."""
    stem = _stem_of(segments)
    return {
        "position": f"{stem['surah']}:{stem['ayah']}:{stem['word']}",
        "arabic": "".join(s["form"] for s in segments),
        "root": stem["root"],
        "lemma": stem["lemma"],
        "pos": stem["pos"],
        "grammar": describe(stem["pos"], stem["features"], stem["root"]),
        # Every piece kept separately, so the UI can show how the word is built up
        #, the prefix, the word itself, the ending; instead of one flat label.
        "segments": [
            {
                "arabic": s["form"],
                "grammar": describe(s["pos"], s["features"], s["root"]),
            }
            for s in segments
        ],
    }


def words_for_ayah(surah: int, ayah: int) -> list[dict]:
    """Every word of one ayah, in order, with its verified grammar."""
    rows = _db().execute(
        "SELECT * FROM segment WHERE surah = ? AND ayah = ? ORDER BY word, segment",
        (surah, ayah),
    ).fetchall()

    words: list[dict] = []
    current: list[sqlite3.Row] = []
    for row in rows:
        if current and row["word"] != current[0]["word"]:
            words.append(_word_from(current))
            current = []
        current.append(row)
    if current:
        words.append(_word_from(current))
    return words


def tags_for_ayah(surah: int, ayah: int) -> list[dict]:
    """The same ayah, but as the tags themselves rather than wording.

    words_for_ayah turns the corpus shorthand into English a reader can follow.
    The tarkeeb rules need the shorthand, "GEN", "DET", because that is what
    they test, and reading it back out of a sentence would be guesswork.
    """
    rows = _db().execute(
        "SELECT * FROM segment WHERE surah = ? AND ayah = ? ORDER BY word, segment",
        (surah, ayah),
    ).fetchall()
    return [
        _tags_from(list(segments))
        for _, segments in groupby(rows, key=lambda r: r["word"])
    ]


def _tags_from(segments: list[sqlite3.Row]) -> dict:
    """One word's raw tags, with its pieces kept separate.

    Both levels are needed: a word's case sits on its stem, while the definite
    article and a glued-on preposition are segments of their own.
    """
    stem = _stem_of(segments)
    return {
        "arabic": "".join(s["form"] for s in segments),
        "pos": stem["pos"],
        "features": stem["features"],
        "root": stem["root"],
        # The dictionary form: كُنتُمْ is still كَانَ, and nahw names a governor by it.
        "lemma": stem["lemma"],
        "segments": [
            {"arabic": s["form"], "pos": s["pos"], "features": s["features"]}
            for s in segments
        ],
    }


def ayah_texts(surah: int) -> list[tuple[int, str]]:
    """Just the words of each ayah, joined; no grammar worked out at all.

    Reading a surah does not need the segment-by-segment grammar, and building it
    anyway is most of the cost: describing all 10,374 of al-Baqarah's segments
    takes ~240ms, while the text alone takes ~12ms. The grammar is derived only
    for the one ayah a reader actually opens.
    """
    # Two levels, because the two joins differ: a word's segments run together
    # with nothing between them (بِ + سْمِ is one word), while the words are
    # separated by a space. Each inner query is ordered so the pieces come back
    # in the order they are written.
    rows = _db().execute(
        """SELECT ayah, group_concat(word_text, ' ') AS text FROM (
               SELECT ayah, word, group_concat(form, '') AS word_text FROM (
                   SELECT ayah, word, segment, form FROM segment
                   WHERE surah = ? ORDER BY ayah, word, segment
               ) GROUP BY ayah, word ORDER BY ayah, word
           ) GROUP BY ayah ORDER BY ayah""",
        (surah,),
    ).fetchall()
    return [(row["ayah"], row["text"]) for row in rows]


def words_for_surah(surah: int) -> list[tuple[int, list[dict]]]:
    """Every ayah of one surah, in order, as (ayah number, its words).

    One query for the whole surah rather than one per ayah. The difference is not
    small: al-Baqarah's 10,374 segments come back in about 30ms this way, where
    286 separate calls spend most of their time on overhead.
    """
    rows = _db().execute(
        "SELECT * FROM segment WHERE surah = ? ORDER BY ayah, word, segment", (surah,)
    ).fetchall()

    # The rows arrive sorted, so each ayah is one run and each word a run inside
    # it, exactly what groupby consumes. Segments stay in their original order
    # within a word, which is what _word_from relies on to glue them together.
    return [
        (
            ayah,
            [
                _word_from(list(segments))
                for _, segments in groupby(ayah_rows, key=lambda r: r["word"])
            ],
        )
        for ayah, ayah_rows in groupby(rows, key=lambda r: r["ayah"])
    ]


def occurrences_of_root(root: str, limit: int) -> dict:
    """Where a root appears in the Qur'an, and which words are built from it.

    This is the link between the tabs: a root seen in an ayah is the same root the
    dictionary looks up and the conjugator builds a table for.
    """
    db = _db()
    total = db.execute("SELECT COUNT(*) FROM segment WHERE root = ? AND root <> ''", (root,)).fetchone()[0]
    if not total:
        return {"root": root, "total": 0, "forms": [], "occurrences": []}

    forms = db.execute(
        """SELECT lemma, pos, COUNT(*) AS uses FROM segment
           WHERE root = ? AND root <> '' AND lemma <> '' GROUP BY lemma, pos ORDER BY uses DESC""",
        (root,),
    ).fetchall()

    places = db.execute(
        """SELECT surah, ayah, word, form, pos, features FROM segment
           WHERE root = ? AND root <> '' ORDER BY surah, ayah, word LIMIT ?""",
        (root, limit),
    ).fetchall()

    return {
        "root": root,
        "total": total,
        "forms": [
            {"lemma": f["lemma"], "pos": f["pos"], "uses": f["uses"]}
            for f in forms
        ],
        "occurrences": [
            {
                "surah": p["surah"],
                "ayah": p["ayah"],
                "arabic": p["form"],
                "grammar": describe(p["pos"], p["features"], root),
            }
            for p in places
        ],
    }
