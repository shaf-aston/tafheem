"""Which quiz words an Urdu speaker already knows, and which ones will trick them.

Run:  python backend/scripts/build_urdu_links.py
      python backend/scripts/build_urdu_links.py --refresh   (re-download the Urdu dump)

Why this exists
---------------
Urdu took a great deal of its vocabulary from Arabic, so an Urdu speaker starts
this quiz already knowing some of the answers, and being confidently wrong about
others. مَكَان is a place in Arabic; مکان in Urdu is a house. That second kind is
the single most useful thing this tab can tell an Urdu speaker, and nothing else
in the app knows it.

Where each half comes from
--------------------------
Both halves are downloaded, neither is invented:

  the Arabic side   backend/data/wiktionary-arabic.jsonl, already on disk. Its
                    `descendants` field names 1,156 Arabic words that entered
                    Urdu and how they are spelled there.
  the Urdu side     the Urdu extraction of English Wiktionary, 9,000-odd words
                    with an English meaning each, downloaded once to
                    backend/data/wiktionary-urdu.jsonl and read locally after.

A word's Arabic meaning and its Urdu meaning are then compared. Agreeing is a
`cognate`; disagreeing is a `false-friend` CANDIDATE, never a finding.

Why candidates and not findings
-------------------------------
The comparison is word overlap between two English glosses, and it is wrong
often. كَبِير glossed "big" against Urdu "great" is filed as disagreeing, and
they are the same word. So this script writes candidates with both glosses
beside each other, and urdu_links.overrides.json is where a person who reads
Urdu says which ones are real. Nothing reaches the screen until they do; the
same arrangement word_kinds.json already has over three sources.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.arabic_text import strip_diacritics  # noqa: E402

DATA = Path(__file__).parent.parent / "data"
ARABIC_DUMP = DATA / "wiktionary-arabic.jsonl"
URDU_DUMP = DATA / "wiktionary-urdu.jsonl"
LEXICON = DATA / "lexicon.db"
OUT = DATA / "urdu_links.json"
OVERRIDES = DATA / "urdu_links.overrides.json"

URDU_SOURCE = "https://kaikki.org/dictionary/Urdu/kaikki.org-dictionary-Urdu.jsonl"

# Urdu writes four of its letters with a different code point from Arabic, and a
# fifth is the same sound spelled two ways. Folded here so مکان and مَكَان are one
# word; nothing else in the app compares the two scripts, so the fold lives here.
URDU_TO_ARABIC = str.maketrans({"ی": "ي", "ے": "ي", "ک": "ك", "ہ": "ه", "ھ": "ه", "ۂ": "ه", "ة": "ه"})
NOT_LETTERS = re.compile(r"[^؀-ۿ]")
ENGLISH_WORD = re.compile(r"[a-z]+")

# Words that two unrelated glosses share by accident. "to" alone would make every
# verb agree with every other verb.
IGNORED = {
    "a", "an", "the", "of", "to", "in", "on", "at", "for", "with", "by", "or",
    "and", "is", "are", "be", "one", "who", "that", "which", "as", "it", "its",
    "someone", "something", "person", "thing",
}


def fold(text: str) -> str:
    """The letters of a word, with no vowels, no script differences, nothing else."""
    return NOT_LETTERS.sub("", strip_diacritics(text or "").translate(URDU_TO_ARABIC))


# English endings that change a word's part of speech and not its meaning. One
# side of a comparison is usually a dictionary noun and the other a Qur'anic
# verb, so "he envies" against "envy" and "insects" against "insect" were being
# filed as disagreeing when they are the same word. Longest ending first, so
# "-ies" is tried before "-s".
ENDINGS = ("ations", "ation", "ings", "ies", "ing", "ers", "ed", "er", "es", "s", "y")
SHORTEST_STEM = 3


def stem(word: str) -> str:
    """A word with an ending that only changed its grammar taken off.

    Crude on purpose: it exists to stop two spellings of one meaning counting as
    two meanings, not to be a linguistics library. Left alone when the ending is
    most of the word, so "is" does not become "i".
    """
    for ending in ENDINGS:
        if word.endswith(ending) and len(word) - len(ending) >= SHORTEST_STEM:
            return word[: -len(ending)].rstrip("i")
    return word


def meaning_words(gloss: str) -> set[str]:
    """The words of a gloss that actually carry its meaning, stemmed so one
    meaning written two ways is one meaning."""
    return {stem(word) for word in ENGLISH_WORD.findall(gloss.lower()) if word not in IGNORED}


def download_urdu(refresh: bool = False) -> None:
    """Fetch the Urdu dump once. Kept beside the Arabic one it is compared with."""
    if URDU_DUMP.exists() and not refresh:
        return
    print(f"Downloading the Urdu Wiktionary extraction to {URDU_DUMP.name}…")
    with httpx.stream("GET", URDU_SOURCE, timeout=300, follow_redirects=True) as response:
        response.raise_for_status()
        building = URDU_DUMP.with_suffix(".building")
        with open(building, "wb") as out:
            for chunk in response.iter_bytes():
                out.write(chunk)
    building.replace(URDU_DUMP)
    print(f"  {URDU_DUMP.stat().st_size / 1_000_000:.1f} MB")


def urdu_senses() -> dict[str, list[str]]:
    """What each Urdu word means, in English, from the Urdu dump."""
    senses: dict[str, list[str]] = defaultdict(list)
    for line in URDU_DUMP.read_text("utf-8").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        glosses = [gloss for sense in entry.get("senses", []) for gloss in (sense.get("glosses") or [])]
        if glosses:
            senses[fold(entry["word"])].extend(glosses)
    return senses


def _urdu_descendants(nodes: list | None, found: list[str]) -> None:
    """Every Urdu spelling under a descendants tree. Urdu often sits under Persian
    rather than directly under the Arabic, so the whole tree is walked."""
    for node in nodes or []:
        if node.get("lang_code") == "ur" and node.get("word"):
            found.append(node["word"])
        _urdu_descendants(node.get("descendants"), found)


def borrowings() -> dict[str, list[str]]:
    """Arabic words English Wiktionary records as having entered Urdu, and how
    they are spelled there. The link itself is a claim somebody published, which
    is why it is read rather than guessed from the letters alone."""
    found: dict[str, list[str]] = {}
    for line in ARABIC_DUMP.read_text("utf-8").splitlines():
        if '"ur"' not in line:
            continue
        entry = json.loads(line)
        spellings: list[str] = []
        _urdu_descendants(entry.get("descendants"), spellings)
        if spellings:
            found.setdefault(fold(entry["word"]), []).extend(spellings)
    return found


def quiz_words() -> list[dict]:
    """The words the quiz can ask, with the Urdu meaning where there is one."""
    rows = sqlite3.connect(LEXICON).execute("SELECT ar, en, ur, meaning_key FROM word ORDER BY id")
    return [{"ar": ar, "en": en, "ur": ur, "meaningKey": key} for ar, en, ur, key in rows]


def verdict_for(word: dict, senses: list[str], borrowed: bool) -> dict | None:
    """One word weighed against what its letters mean in Urdu.

    `cognate` when the two meanings share a real word, `false-friend` when they
    share none. Both are candidates: the test is word overlap between two short
    English glosses and it is wrong often in both directions.
    """
    if not senses:
        return None
    arabic = meaning_words(word["en"])
    if not arabic:
        return None
    agreeing = [gloss for gloss in senses if meaning_words(gloss) & arabic]
    return {
        "ar": word["ar"],
        "en": word["en"],
        "meaningKey": word["meaningKey"],
        "verdict": "cognate" if agreeing else "false-friend",
        # Both glosses travel with the verdict: a reviewer decides by reading
        # them, and a verdict with its evidence stripped off cannot be checked.
        "urduSenses": senses[:4],
        # Whether Wiktionary actually records the word entering Urdu, as opposed
        # to the two languages happening to spell something the same way.
        "borrowed": borrowed,
    }


def build(refresh: bool = False) -> None:
    download_urdu(refresh)
    senses = urdu_senses()
    borrowed = borrowings()
    words = quiz_words()

    links = []
    for word in words:
        key = fold(word["ar"])
        found = verdict_for(word, senses.get(key, []), key in borrowed)
        if found:
            links.append(found)

    counts = defaultdict(int)
    for link in links:
        counts[link["verdict"]] += 1
        counts[f"{link['verdict']}, and a recorded borrowing"] += int(link["borrowed"])

    OUT.write_text(
        json.dumps(
            {
                "_about": (
                    "What each quiz word's letters mean in Urdu, against what they mean in Arabic."
                    " Built by backend/scripts/build_urdu_links.py from two Wiktionary dumps."
                    " EVERY ENTRY IS A CANDIDATE: the test is word overlap between two English"
                    " glosses and it is often wrong. urdu_links.overrides.json says which are real,"
                    " and only those reach the screen."
                ),
                "links": sorted(links, key=lambda link: (not link["borrowed"], link["ar"])),
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    if not OVERRIDES.exists():
        OVERRIDES.write_text(
            json.dumps(
                {
                    "_about": (
                        "Which candidates in urdu_links.json a person who reads Urdu has checked."
                        " The build never writes this file and never overrules it."
                        " Put the Arabic spelling in 'false-friend' if its Urdu meaning really is"
                        " different, or in 'cognate' if an Urdu speaker already knows it."
                        " Anything not listed here is shown to nobody."
                    ),
                    "false-friend": [],
                    "cognate": [],
                },
                ensure_ascii=False,
                indent=2,
            ) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote an empty {OVERRIDES.name}; nothing is shown until it is filled in.")

    print(f"\n{len(words)} quiz words, {len(links)} of them also Urdu words:")
    for name, count in sorted(counts.items()):
        print(f"  {count:>5}  {name}")
    print(f"\nWrote {OUT}")
    print("Every one is a candidate. Read them and fill in", OVERRIDES.name)


if __name__ == "__main__":
    build(refresh="--refresh" in sys.argv[1:])
