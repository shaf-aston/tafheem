"""Turn lexicon.db into the three files the quiz fetches.

    python backend/scripts/export_quiz_words.py

Writes frontend/public/words/:

  words.json  every word once, in one array
  cuts.json   which words are in each cut, as positions into that array
  index.json  the surah and juz lists, and what to call each set

Why positions rather than words
-------------------------------
Every cut used to carry its own copy of every word it held, so the same 3,657
words filled 145 files and 3.9 MB: a word in surah 2 was written again for juz 1,
and again for every other cut that reached it. A cut is now a list of numbers
pointing into one array of words, which is the same information without the
copies, and it means the browser holds one word per word; so "all" stops being
a merge with duplicates to remove and becomes simply no filter.

What a cut is
-------------
A named selection: a whole set (everyday, book, quran), one of the book's groups,
one surah, or one juz. Surah and juz cuts leave out what the book already
teaches, so picking one is always the words that cut has and the book does not; 
the same rule the browser used to apply at load time.
"""
from __future__ import annotations

import json
import sqlite3
import urllib.request
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "backend" / "data"
QURAN = DATA / "quran"
OUT_DIR = ROOT / "frontend" / "public" / "words"

CONFIG = json.loads((DATA / "quiz_words.config.json").read_text("utf-8"))
JUZ_CACHE = QURAN / "juz.json"
# A question shows this many options, so a group needs this many of a type to
# ask a word of that type on its own.
OPTION_COUNT = json.loads((ROOT / "frontend" / "src" / "quiz.json").read_text("utf-8"))["option-count"]
USER_AGENT = "tafheem export_quiz_words"
URDU_LINKS = DATA / "urdu_links.json"
URDU_OVERRIDES = DATA / "urdu_links.overrides.json"


def urdu_links() -> dict[str, dict]:
    """What an Urdu speaker already knows, and what will trick them, by Arabic
    spelling.

    Only the words a person has actually checked. build_urdu_links.py compares
    two English glosses and calls that a verdict, which is right often enough to
    be worth reading and nowhere near right enough to teach from; the overrides
    file is where someone who reads Urdu says which ones are real. Both files
    missing is normal and means nothing is shipped, not that something failed.
    """
    if not (URDU_LINKS.exists() and URDU_OVERRIDES.exists()):
        return {}

    confirmed = json.loads(URDU_OVERRIDES.read_text("utf-8"))
    candidates = {link["ar"]: link for link in json.loads(URDU_LINKS.read_text("utf-8"))["links"]}

    shipped = {}
    for kind in ("false-friend", "cognate"):
        for entry in confirmed.get(kind, []):
            # A bare spelling, or that spelling with the sense written out. There
            # is no free Urdu-language dictionary to download, so the sense from
            # Wiktionary is in English; whoever checks the word can write it in
            # Urdu here instead, and then the whole note is in one language.
            spelling = entry["ar"] if isinstance(entry, dict) else entry
            link = candidates.get(spelling)
            if link is None:
                raise SystemExit(
                    f"urdu_links.overrides.json names {spelling}, which urdu_links.json does not have."
                    " Re-run build_urdu_links.py, or correct the spelling."
                )
            sense = entry.get("sense") if isinstance(entry, dict) else None
            shipped[spelling] = {
                "kind": kind,
                "sense": sense or "; ".join(link["urduSenses"][:2]),
            }
    return shipped


def juz_verses() -> dict[int, set[tuple[int, int]]]:
    """Which (surah, ayah) each juz holds. Fetched once, then read from disk."""
    if not JUZ_CACHE.exists():
        print(f"Fetching the juz list from {CONFIG['juz-api']}")
        # The API refuses a request that does not name itself.
        ask = urllib.request.Request(CONFIG["juz-api"], headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(ask, timeout=60) as response:
            payload = json.load(response)
        # The API lists every juz twice (two ids per juz_number); keep one each.
        one_each = {j["juz_number"]: j for j in payload["juzs"]}
        payload["juzs"] = sorted(one_each.values(), key=lambda j: j["juz_number"])
        JUZ_CACHE.write_text(json.dumps(payload), "utf-8")

    holds: dict[int, set[tuple[int, int]]] = defaultdict(set)
    for juz in json.loads(JUZ_CACHE.read_text("utf-8"))["juzs"]:
        for surah, span in juz["verse_mapping"].items():
            first, last = (int(n) for n in span.split("-"))
            holds[juz["juz_number"]].update((int(surah), a) for a in range(first, last + 1))
    return holds


def already_taught(identity: dict[int, tuple[str, str]], book: set[int]) -> set[int]:
    """Every word the book covers, including a second spelling of one it names.

    Two rows are the same word to a reader when they are the same letters AND
    the same type of word: the book's رَحْمَٰن and the corpus's are one word
    written twice, while هُدًى (guidance, a noun) and هَدَى (he guided, a verb)
    share their letters and are two. Matching on the letters alone quietly
    deletes the second of every such pair from the surah and juz cuts, which is
    why the rule is a function with its own test rather than a line inside the
    loop below.
    """
    taught = {identity[word_id] for word_id in book}
    return {word_id for word_id, key in identity.items() if key in taught}


def main() -> None:
    lexicon = sqlite3.connect(DATA / "lexicon.db")
    links = urdu_links()

    # One array of words, and the position of each so a cut can point at it.
    words, position, same_word = [], {}, {}
    for word_id, ar, bare, en, ur, meaning_key, word_type, times, attached in lexicon.execute(
        "SELECT id, ar, bare, en, ur, meaning_key, word_type, times_in_quran, attached"
        " FROM word ORDER BY id"
    ):
        position[word_id] = len(words)
        # What counts as the same word, see already_taught above.
        same_word[word_id] = (bare, word_type)
        words.append(
            {
                "ar": ar,
                "en": en,
                # Written only where there is one. A key that is absent is what
                # tells the quiz this word cannot be asked in Urdu; an empty
                # string would put a blank option on the screen instead.
                **({"ur": ur} if ur else {}),
                "meaningKey": meaning_key,
                # Only what a question needs. Everything else the table knows, 
                # the root, which source each word came from; stays in the table
                # until a feature asks for it, rather than shipping unread.
                **({"wordType": word_type} if word_type else {}),
                **({"timesInQuran": times} if times else {}),
                **({"attached": True} if attached else {}),
                # Only on a word somebody checked; see urdu_links() above.
                **({"urdu": links[ar]} if ar in links else {}),
            }
        )

    # A tag is a cut: 'everyday' and 'quran' name a whole set, 'book:faith' one
    # of the book's groups. Group names already carry their set's prefix, so the
    # two axes share one namespace without colliding.
    tagged: dict[str, list[int]] = defaultdict(list)
    for axis, value, word_id in lexicon.execute(
        "SELECT axis, value, word_id FROM word_tag ORDER BY word_id"
    ):
        tagged[value].append(position[word_id])
        if axis == "group":
            # Carried on the word as well, because a wrong option is more
            # tempting when it shares the answer's topic.
            words[position[word_id]].setdefault("groups", []).append(value)

    # The book is the set every Qur'anic cut is measured against: it is the one
    # you are meant to work through, so a word it already covers should not come
    # back at you from a surah or a juz.
    book = {word_id for (word_id,) in lexicon.execute(
        "SELECT word_id FROM word_tag WHERE axis = 'set' AND value = 'book'"
    )}
    in_the_book = {position[word_id] for word_id in already_taught(same_word, book)}

    where: dict[tuple[int, int], list[int]] = defaultdict(list)
    for word_id, surah, ayah in lexicon.execute(
        "SELECT word_id, surah, ayah FROM word_place"
    ):
        where[(surah, ayah)].append(position[word_id])

    def cut(ayahs: set[tuple[int, int]]) -> list[int]:
        """The words that cut has and the book does not, each one once."""
        found = {index for ayah in ayahs for index in where.get(ayah, ())}
        return sorted(found - in_the_book)

    cuts = {name: sorted(members) for name, members in tagged.items()}

    chapters = sqlite3.connect(QURAN / "meanings.db").execute(
        "SELECT id, name_en, name_ar, ayahs FROM surah ORDER BY id"
    ).fetchall()
    surahs = []
    for surah, name_en, name_ar, ayah_count in chapters:
        cuts[f"surah:{surah}"] = cut({(surah, a) for a in range(1, ayah_count + 1)})
        surahs.append(
            {
                "id": surah,
                "name": name_en,
                "arabic": name_ar,
                "words": len(cuts[f"surah:{surah}"]),
            }
        )

    juz = []
    for number, ayahs in sorted(juz_verses().items()):
        cuts[f"juz:{number}"] = cut(ayahs)
        juz.append({"id": number, "words": len(cuts[f"juz:{number}"])})

    def read_meta(key: str) -> str:
        return lexicon.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()[0]

    index = {
        "_comment": "Built by backend/scripts/export_quiz_words.py. Do not edit by hand.",
        # Which build of the table these files came from. A rebuilt table that
        # was never re-exported leaves this behind, and a test says so.
        "builtFrom": read_meta("content"),
        "sets": json.loads(read_meta("sets")),
        "surahs": surahs,
        "juz": juz,
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for stale in OUT_DIR.glob("*.json"):
        stale.unlink()
    (OUT_DIR / "words.json").write_text(
        json.dumps({"words": words}, ensure_ascii=False), "utf-8"
    )
    (OUT_DIR / "cuts.json").write_text(json.dumps(cuts, ensure_ascii=False), "utf-8")
    (OUT_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), "utf-8"
    )

    written = sorted(OUT_DIR.glob("*.json"))
    total = sum(f.stat().st_size for f in written)
    print(f"{len(words)} words, {len(cuts)} cuts")
    print(f"  urdu: {len(links)} words checked by a person" if links else "  urdu: nothing checked yet, so nothing shipped")
    print(f"  sets: {', '.join(f'{k} {len(cuts[k])}' for k in ('everyday', 'book', 'quran'))}")
    print(f"  {len(written)} files, {total / 1_000_000:.2f} MB in {OUT_DIR}")

    # Wrong options must be the same type as the answer, so a word whose type has
    # almost no company in its own group cannot fill a question there. It is
    # still asked from wider cuts, but a group meant to be worked through on its
    # own is worth knowing about, so it is named rather than quietly skipped.
    lonely = []
    for name, members in sorted(cuts.items()):
        if not name.startswith("book:"):
            continue
        by_type: dict[str, list[str]] = defaultdict(list)
        for at in members:
            by_type[words[at].get("wordType", "?")].append(words[at]["ar"])
        for word_type, spellings in by_type.items():
            if len(spellings) < OPTION_COUNT:
                lonely.append(f"{name}: {len(spellings)} {word_type} ({', '.join(spellings)})")
    if lonely:
        print(f"  {len(lonely)} groups too thin in one type to ask it on its own:")
        for line in lonely:
            print(f"    {line}")


if __name__ == "__main__":
    main()
