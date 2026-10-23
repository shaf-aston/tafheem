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
from backend.services.arabic_text import (  # noqa: E402
    as_root_letters,
    root_letters_in_order,
    strip_diacritics,
)

DATA_DIR = Path(__file__).parent.parent / "data"
SOURCE = DATA_DIR / "wiktionary-arabic.jsonl"
OUTPUT = DATA_DIR / "arabic_dictionary.json"

ARABIC_LETTER = re.compile(r"[ء-ي]")
# The forms a row writes its stem in, as against its endings (مُعْتَلِّين's ي is no radical).
STEM_FORMS = {"canonical", "non-past", "noun-from-verb"}
# Arabic's own root category only: a page's Tunisian or Moroccan root sits beside it.
ROOT_CATEGORY = re.compile(r"^Arabic terms belonging to the root ([ء-يـ ]+)$")
# Wiktionary marks entries that only point elsewhere; they carry no meaning.
SKIP_GLOSS = re.compile(r"^(plural|singular|dual|feminine|masculine) of ", re.I)
# "verbal noun of فَهِمَ (fahima) (form I)" also only points. Dropped when a real
# definition stands beside it; when it is the whole entry (2,103 nouns) it is
# kept, cut to "verbal noun of فَهِمَ", so the word still has an entry.
POINTER_GLOSS = re.compile(r"^verbal noun of (\S+).*", re.I)
# "Derived from the active participle of اِشْتَاقَ": the word an entry comes
# from, named in its etymology. Wiktionary tags مُشْتَاق with no root but tags
# اِشْتَاقَ ش و ق, so a rootless entry takes the root of the word it names.
SOURCE_WORD = re.compile(r"\bof ([ء-ي][ء-ي\u064B-\u0652\u0670]*)")

# A headword needs at least one real definition to be worth an entry.
MIN_DEFINITIONS = 1
MAX_DEFINITIONS = 8
# Synonyms are a sideline, not the answer: past a handful they crowd out the
# definition they belong to.
MAX_SYNONYMS = 5


def root_of(entry: dict) -> str:
    """The three-letter root, read off the categories Wiktionary already tags.

    Nearly always tagged on the sense rather than the entry, so both are read.
    A page with two words spelled alike hands both their roots to each (قَالَ, say,
    and قَالَ, nap, each carry ق و ل and ق ي ل), so the root kept is the one the
    row's own forms spell: its present يَقُولُ and noun قَوْل hold ق و ل, not ق ي ل.
    """
    groups = [entry.get("categories", [])]
    groups += [sense.get("categories", []) for sense in entry.get("senses", [])]
    names = (category if isinstance(category, str) else category.get("name", "")
             for categories in groups for category in categories)
    found = list(dict.fromkeys(match.group(1).replace("ـ", "").strip()
                               for name in names if (match := ROOT_CATEGORY.match(name))))
    if len(found) < 2:
        return next(iter(found), "")
    stems = [form.get("form", "") for form in entry.get("forms", []) if STEM_FORMS & set(form.get("tags", []))]
    spelt = [as_root_letters(word) for word in [entry.get("word", ""), *stems]]

    def carried(root: str) -> int:
        letters = as_root_letters(root)
        return max(root_letters_in_order(letters, form) for form in spelt)

    return max(found, key=carried)  # max keeps the first of equals: the order Wiktionary gave


def source_words(entry: dict) -> list[str]:
    """The words Wiktionary says this entry is a form of or comes from, bare."""
    named = SOURCE_WORD.findall(entry.get("etymology_text") or "")
    named += [form.get("word", "") for sense in entry.get("senses", [])
              for form in sense.get("form_of", []) or []]
    return [bare for word in named if (bare := strip_diacritics(word))]


def fits(root: str, word: str) -> bool:
    """Whether every strong letter of `root` is in `word`.

    An etymology names more than the word an entry is built on: إله is "a
    variant of" something else, تاب is "cognate with" ثاب. A root that does not
    sit in the word's own letters came from one of those, so it is not taken.
    Weak letters and hamza are let through: قال holds no و of ق و ل.
    """
    letters = strip_diacritics(word)
    return all(letter in letters or letter in "اويءى" for letter in root.split())


def inherit_roots(by_word: dict[str, dict], sources: dict[str, list[str]]) -> int:
    """Give each rootless entry the root of the word it comes from; how many got one.

    Followed down the chain: مَرَّتَيْن comes from مَرَّة, which has a root only from مُرّ.
    """
    filled = 0
    while True:
        rooted = {strip_diacritics(word): e["root"] for word, e in by_word.items() if e["root"]}
        this_pass = 0
        for word, entry in by_word.items():
            if entry["root"]:
                continue
            named = (rooted[w] for w in sources.get(word, ()) if w in rooted)
            if root := next((r for r in named if fits(r, word)), ""):
                entry["root"] = root
                this_pass += 1
        if not this_pass:
            return filled
        filled += this_pass


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
    sources: dict[str, list[str]] = defaultdict(list)
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

            sources[word] += source_words(entry)
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

    inherited = inherit_roots(by_word, sources)

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
        f"({with_root} with a root, {inherited} of them from the word it comes from, {with_pos} with a part of speech, "
        f"{with_synonyms} with a synonym, {with_verbs} with a verb form, "
        f"{with_bab} with a Form I bab)."
    )
    print(f"Wrote {output} ({output.stat().st_size / 1_000_000:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT))
