"""Build the Arabic-English dictionary from the Wiktionary extract.

Hans Wehr is under copyright, so the app does not ship it. Wiktionary's Arabic
entries are CC BY-SA and carry the same thing the dictionary is for: the word,
its root, how it is pronounced, and what it means.

    1. Download once (about 512 MB):
       https://kaikki.org/dictionary/Arabic/kaikki.org-dictionary-Arabic.jsonl
       saved as backend/data/wiktionary-arabic.jsonl
    2. python backend/scripts/build_dictionary.py

Writes backend/data/arabic_dictionary.json, one entry per Arabic headword.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services import verb_forms  # noqa: E402, needs the path above
from backend.services.arabic_text import strip_diacritics  # noqa: E402

DATA_DIR = Path(__file__).parent.parent / "data"
SOURCE = DATA_DIR / "wiktionary-arabic.jsonl"
OUTPUT = DATA_DIR / "arabic_dictionary.json"

ARABIC_LETTER = re.compile(r"[ء-ي]")
ROOT_CATEGORY = re.compile(r"root ([ء-يـ ]+)")
# Wiktionary marks entries that only point elsewhere; they carry no meaning.
SKIP_GLOSS = re.compile(r"^(plural|singular|dual|feminine|masculine) of ", re.I)
# "verbal noun of فَهِمَ (fahima) (form I)" also only points. Dropped when a real
# definition stands beside it; when it is the whole entry (2,103 nouns) it is
# kept, cut to "verbal noun of فَهِمَ", so the word still has an entry.
POINTER_GLOSS = re.compile(r"^verbal noun of (\S+).*", re.I)

# A headword needs at least one real definition to be worth an entry.
MIN_DEFINITIONS = 1
MAX_DEFINITIONS = 8
# Synonyms are a sideline, not the answer: past a handful they crowd out the
# definition they belong to.
MAX_SYNONYMS = 5


def root_of(entry: dict) -> str:
    """The three-letter root, read off the categories Wiktionary already tags.

    Nearly always tagged on the sense rather than the entry, so both are read.
    """
    groups = [entry.get("categories", [])]
    groups += [sense.get("categories", []) for sense in entry.get("senses", [])]
    for categories in groups:
        for category in categories:
            name = category if isinstance(category, str) else category.get("name", "")
            if match := ROOT_CATEGORY.search(name):
                return match.group(1).replace("ـ", "").strip()
    return ""


def romanization_of(entry: dict) -> str:
    return next(
        (
            form.get("form", "")
            for form in entry.get("forms", [])
            if "romanization" in form.get("tags", [])
        ),
        "",
    )


def verb_form_of(entry: dict) -> dict | None:
    """The verb's form and bab, from the ar-verb head template, or None.

    Wiktionary states the form ("II") and, for Form I, the past and present
    vowels ("I/a~u") right in the headword template, and writes the vowelled
    past and present out among the forms. That is the bab, which nothing else
    in the app can work out from a bare root.
    """
    if entry.get("pos") != "verb":
        return None
    template = next(iter(entry.get("head_templates") or []), {})
    if template.get("name") != "ar-verb":
        return None
    parsed = verb_forms.parse_head(template.get("args", {}).get("1", ""))
    if parsed is None:
        return None
    form, babs = parsed

    def form_tagged(*tags: str) -> str:
        wanted = set(tags)
        return next(
            (f.get("form", "") for f in entry.get("forms", []) if set(f.get("tags", [])) == wanted),
            "",
        )

    # The vowelled past is the row tagged canonical plus its form.
    past = form_tagged("canonical", f"form-{form.lower()}")
    return verb_forms.record(form, past, babs) if past else None


def synonyms_of(sense: dict, headword: str) -> list[str]:
    """The Arabic words Wiktionary lists as meaning the same as this sense.

    Only the word itself is kept. The dump also carries a transliteration and an
    English gloss for each one, but a synonym is a pointer to another entry the
    reader can look up, printing its whole entry here would be a second
    dictionary inside the first.

    The headword drops out. Wiktionary builds these lists from thesaurus pages
    that name every member including this one, so صحراء arrived listing صَحْرَاء
    among its own synonyms, vowel marks the only difference, and no use to
    anyone.
    """
    bare = strip_diacritics(headword)
    out: list[str] = []
    for item in sense.get("synonyms") or []:
        word = (item.get("word") or "").strip() if isinstance(item, dict) else str(item).strip()
        if not word or not ARABIC_LETTER.search(word) or word in out:
            continue
        if strip_diacritics(word) == bare:
            continue
        out.append(word)
    return out[:MAX_SYNONYMS]


def senses_of(entry: dict) -> tuple[list[str], list[list[str]]]:
    """The definitions, and each one's synonyms in the same order.

    Two lists rather than one list of pairs: definitions are what the dictionary
    is for and every reader sees them, synonyms are an extra a reader can switch
    off. Keeping them apart means the entry a reader has always had does not
    change shape because a second thing was added beside it.
    """
    definitions: list[str] = []
    synonyms: list[list[str]] = []
    for sense in entry.get("senses", []):
        for gloss in sense.get("glosses", []):
            # This app writes no em dashes; one Wiktionary gloss carries one.
            gloss = gloss.strip().replace(" — ", ", ").replace("—", ", ")
            if not gloss or SKIP_GLOSS.match(gloss) or gloss in definitions:
                continue
            definitions.append(gloss)
            synonyms.append(synonyms_of(sense, entry.get("word", "")))
    if kept := [
        n for n, d in enumerate(definitions) if not POINTER_GLOSS.match(d)
    ]:
        definitions = [definitions[n] for n in kept]
        synonyms = [synonyms[n] for n in kept]
    else:
        definitions = [POINTER_GLOSS.sub(r"verbal noun of \1", d) for d in definitions]
    return definitions[:MAX_DEFINITIONS], synonyms[:MAX_DEFINITIONS]


def merge_row(existing: dict, entry: dict, definitions: list, synonyms: list, verb: dict | None) -> None:
    """Fold one more dump row into the entry its headword already has.

    كَتَبَ and كَتَّبَ share the bare headword, so one entry holds every form
    of it; the same form twice is one form. Definitions and synonyms grow
    together, so definition n and its synonyms stay at the same place in each.
    """
    if verb and all(v["form"] != verb["form"] or v["past"] != verb["past"] for v in existing["verbs"]):
        existing["verbs"].append(verb)
    for definition, alike in zip(definitions, synonyms):
        if definition not in existing["definitions"]:
            existing["definitions"].append(definition)
            existing["synonyms"].append(alike)
    existing["definitions"] = existing["definitions"][:MAX_DEFINITIONS]
    existing["synonyms"] = existing["synonyms"][:MAX_DEFINITIONS]
    existing["root"] = existing["root"] or root_of(entry)


def main(output: Path = OUTPUT) -> int:
    """Build to `output`; a scratch path lets a change be diffed before the
    served file is touched. Read in __main__, not at import: under pytest the
    first argv is a test path."""
    if not SOURCE.exists():
        print(f"Missing {SOURCE}. See this file's docstring for the download.")
        return 1

    by_word: dict[str, dict] = {}
    # Wiktionary writes one row per part of speech, so a headword that is both a
    # noun and a verb arrives twice. The rows are merged into one entry below;
    # this keeps what each row said it was, counted, so the entry can name its
    # parts of speech commonest-first instead of losing them in the merge.
    parts_of_speech: dict[str, Counter] = defaultdict(Counter)
    scanned = 0

    with open(SOURCE, encoding="utf-8") as handle:
        for line in handle:
            scanned += 1
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            word = entry.get("word", "")
            # The dump also carries English thesaurus rows; only Arabic headwords
            # belong in an Arabic dictionary.
            if entry.get("lang_code") != "ar" or not ARABIC_LETTER.search(word):
                continue

            definitions, synonyms = senses_of(entry)
            if len(definitions) < MIN_DEFINITIONS:
                continue

            if pos := entry.get("pos", ""):
                parts_of_speech[word][pos] += 1

            verb = verb_form_of(entry)
            if existing := by_word.get(word):
                merge_row(existing, entry, definitions, synonyms, verb)
                continue

            by_word[word] = {
                "root": root_of(entry),
                "arabic": word,
                "transliteration": romanization_of(entry),
                "definitions": definitions,
                "synonyms": synonyms,
                "verbs": [verb] if verb else [],
            }

    for word, entry in by_word.items():
        # Commonest first, so a reader that wants one answer can take the first.
        entry["pos"] = [name for name, _ in parts_of_speech[word].most_common()]

    entries = sorted(by_word.values(), key=lambda e: e["arabic"])
    with open(output, "w", encoding="utf-8") as handle:
        json.dump(entries, handle, ensure_ascii=False)

    with_root = sum(bool(e["root"])
                for e in entries)
    with_pos = sum(bool(e["pos"])
               for e in entries)
    with_synonyms = sum(any(e["synonyms"]) for e in entries)
    with_verbs = sum(bool(e["verbs"])
                 for e in entries)
    with_bab = sum(any(v["babs"] for v in e["verbs"]) for e in entries)
    print(
        f"Scanned {scanned} rows -> {len(entries)} entries "
        f"({with_root} with a root, {with_pos} with a part of speech, "
        f"{with_synonyms} with a synonym, {with_verbs} with a verb form, "
        f"{with_bab} with a Form I bab)."
    )
    print(f"Wrote {output} ({output.stat().st_size / 1_000_000:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT))
