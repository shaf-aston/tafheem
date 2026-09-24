"""Every Form I verb whose bab Lane's Lexicon states, read out of lexicons.db.

Lane writes each verb as "⁨كَتَبَهُ⁩ , aor. ⁨كَتُبَ⁩": the past, then the past
respelt with the present tense's middle vowel. Doubled roots come as
"⁨شَبِ⁩3⁨َ⁩" (the 3 is the dump's shaddah), weak ones as the full present
"⁨يَعِدُ⁩". In every case the bab vowel is the first short vowel after the
token's second letter, so one rule reads all three.

Only the Form I section (Lane's "1" heading, or the text before any heading)
is read; a verb whose letters do not match the entry's root is dropped rather
than kept. Output: data/sarf/lane_verbs.json, bare past -> list of
{form, past, babs}, the same shape Wiktionary's verbs take in the dictionary.
Ends by counting agreement with Wiktionary, so a bad parse shows as a number.

Run from tafheem/:  python -m backend.scripts.build_lane_verbs
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
import zlib
from collections import defaultdict
from pathlib import Path

from backend.services import conjugation, verb_forms
from backend.services.arabic_text import normalize_root

DATA = Path(__file__).resolve().parent.parent / "data"
LEXICONS = DATA / "lexicons.db"
OUTPUT = DATA / "sarf" / "lane_verbs.json"
DICTIONARY = DATA / "arabic_dictionary.json"

FSI, PDI = "⁨", "⁩"  # the bidi isolates the dump wraps every Arabic run in
RUN = re.compile(f"{FSI}([^{PDI}]+){PDI}")
# A form heading, anchored as frontend/src/lib/laneEntry.js anchors it.
HEADING = re.compile(f"(?:^|(?<=[.:)\\]{PDI}]\\s))(\\d{{1,2}}) (?={FSI})")
# "aor. ⁨X⁩" then any number of ", and ⁨Y⁩"; "aor. as above" has no run and is skipped.
AOR = re.compile(f"\\[?aor\\.\\s*{FSI}([^{PDI}]+){PDI}((?:\\s*(?:,|and|or)\\s*{FSI}[^{PDI}]+{PDI})*)")
VOWEL = {"َ": "a", "ُ": "u", "ِ": "i"}
SHORT = "".join(VOWEL)
SUKUN = "ْ"
HAMZA_TO_ALIF = str.maketrans("أإآ", "ااا")  # Lane files أكل under اكل


def form_one(body: str) -> str:
    """The stretch of the entry that describes Form I, or "" if there is none."""
    heads = list(HEADING.finditer(body))
    if starts := [h for h in heads if h.group(1) == "1"]:
        after = [h.start() for h in heads if h.start() > starts[0].end()]
        return body[starts[0].end():min(after, default=len(body))]
    return body[: heads[0].start()] if heads else body


def bab_vowel(token: str) -> str | None:
    """First short vowel after the second letter; alif counts as a fatha."""
    letters = 0
    for ch in token:
        if ch.isalpha():
            letters += 1
            if letters > 2 and ch == "ا":
                return "a"
        elif letters >= 2 and ch in SHORT:
            return VOWEL[ch]
    return None


def same_root(word: str, root: str) -> bool:
    """Letters match, allowing the alif a hollow past shows where the root has و or ي."""
    letters = normalize_root(word).translate(HAMZA_TO_ALIF)
    return len(letters) == len(root) and all(
        a == b or (a == "ا" and b in "وي") for a, b in zip(letters, root))


def past_word(token: str, root: str) -> str | None:
    """The bare-of-suffix past: the root's letters and the marks on them, كَتَبَهُ -> كَتَبَ.

    None when the run is not this root's past: a verbal noun (ضَرْع, sukun
    inside), a phrase starting with another word, or a bare unvowelled form.
    """
    word, letters = "", 0
    for ch in token.split()[0]:
        if ch.isalpha():
            if letters == len(root):
                break
            letters += 1
        if ch.isalpha() or ch in SHORT + SUKUN + "ّ":  # the dump's ^ and @ split words
            word += ch
    if SUKUN in word or not same_root(word, root) or not bab_vowel(word):
        return None
    return word


def verbs_of(root: str, body: str) -> list[dict]:
    """Every (past, babs) Lane states for this root's Form I."""
    section = form_one(body)
    known = conjugation.babs()["babs"]
    found: dict[str, list[str]] = defaultdict(list)
    for hit in AOR.finditer(section):
        before = RUN.findall(section[: hit.start()])
        past = past_word(before[-1], root) if before else None
        if not past:
            continue
        present = [hit.group(1), *RUN.findall(hit.group(2))]
        for code in (f"{bab_vowel(past)}~{bab_vowel(p)}" for p in present):
            # A pair babs.json does not name (u~a) is a misread run, not a seventh bab.
            if code in known and code not in found[past]:
                found[past].append(code)
    records = (verb_forms.record("I", past, babs) for past, babs in found.items())
    return [r for r in records if r is not None]


def main(output: Path = OUTPUT) -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    db = sqlite3.connect(LEXICONS)
    by_word: dict[str, list[dict]] = defaultdict(list)
    roots = 0
    for root, blob in db.execute("select root, body from entry where book = 'lane'"):
        body = zlib.decompress(blob).decode() if blob[:1] == b"x" else blob.decode("utf-8", "replace")
        verbs = verbs_of(root, body)
        roots += bool(verbs)
        for verb in verbs:
            # Two Lane roots can spell one past (بَاعَ under بيع and بوع): one entry, all its babs.
            if twins := [v for v in by_word[conjugation.bare(verb["past"])] if v["past"] == verb["past"]]:
                twins[0]["babs"] += [c for c in verb["babs"] if c not in twins[0]["babs"]]
            else:
                by_word[conjugation.bare(verb["past"])].append(verb)
    output.write_text(json.dumps(by_word, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Lane: {roots} roots, {sum(map(len, by_word.values()))} Form I verbs -> {output}")

    wiktionary: dict[str, set[str]] = defaultdict(set)
    for entry in json.loads(DICTIONARY.read_text(encoding="utf-8")):
        for verb in entry.get("verbs") or []:
            if verb["form"] == "I" and verb["babs"]:
                wiktionary[conjugation.bare(verb["past"])].update(verb["babs"])
    shared = [w for w in by_word if w in wiktionary]
    agree = [w for w in shared if {c for v in by_word[w] for c in v["babs"]} & wiktionary[w]]
    print(f"Wiktionary: {len(wiktionary)} words; shared {len(shared)}, agree on at least one bab "
          f"{len(agree)} ({100 * len(agree) / (len(shared) or 1):.1f}%), Lane-only {len(by_word) - len(shared)}")
    for w in [w for w in shared if w not in agree][:15]:
        print("  ", w, [(v["past"], v["babs"]) for v in by_word[w]], "wiktionary", sorted(wiktionary[w]))


if __name__ == "__main__":
    main(Path(sys.argv[1]) if len(sys.argv) > 1 else OUTPUT)
