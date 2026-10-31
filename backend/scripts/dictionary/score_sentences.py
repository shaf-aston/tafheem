"""How well the dictionary reads a typed phrase or sentence, word by word, on a fixed set.

The set (data/dictionary/sentence_set.json) is 1000 Arabic inputs already in this
repository, so it scores anywhere the grammar runs, CI included:

  fusha   phrases from the Fusha course (data/colloquial), each with the course's
          English, which the words' English should cover
  nahw    the Nahw tab's scored sentences (data/nahw_rules), Qur'an, hadith and
          book Arabic with no English, there to catch a reading that breaks

Each input goes through sentence_meaning.translate, as a typed one does, with the
language model stood in for (it is not what is scored, and it is not free) and a
throwaway store, so nothing is filed anywhere. What is counted:

  broke       inputs that raised; must stay 0
  aligned     inputs with one row per typed Arabic word
  english     rows with some English
  junk        rows whose English is a tag, not a word ("N." for إن read as an abbreviation)
  covered     of the fusha English's content words, how many some row's English has
  facts       inputs whose model prompt had one line per row
  ms_p50/p95  time to read an input, printed, never checked (machines differ)

--quran also scores the Qur'an where its databases are built (meanings.db and the
search index, both gitignored): `quran_set` ayahs' rows against the Qur'an's own
word-by-word English (rows_hit), and a run of words cut from each, which
quran_search.ayah_run should find (run_found) with that English (run_right).

--check fails (exit 1) when a count is worse than data/dictionary/sentence_baseline.json;
CI runs it through tests/dictionary/test_sentence_set.py. After a change that rightly
moves a count, --save-baseline writes the new ones. --write-set rebuilds the set from
its sources (it is kept as a file so an edit to them does not move the yardstick).

    python -m backend.scripts.dictionary.score_sentences
    python -m backend.scripts.dictionary.score_sentences --quran --show 20
    python -m backend.scripts.dictionary.score_sentences --check
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

from backend.services import ai
from backend.services.dictionary import sentence_meaning
from backend.services.dictionary import service as dictionary_service
from backend.services.learner import progress_store
from backend.services.quran import search as quran_search
from backend.services.text.arabic_text import words

DATA = Path(__file__).resolve().parent.parent.parent / "data"
SET = DATA / "dictionary" / "sentence_set.json"
BASELINE = DATA / "dictionary" / "sentence_baseline.json"

# Counts where more is better; "junk" and "broke" are the two where less is.
HIGHER = ("aligned", "english", "covered", "facts", "rows_hit", "run_found", "run_right")
LOWER = ("junk", "broke")

# English that is a tag CAMeL carries, not a word a reader should see.
_JUNK_RE = re.compile(r"(^|\s)(N\.|\[[^\]]*\]|<[^>]*>)(\s|$)")
# Words too small to say whether two English renderings agree.
_FILLER = {"a", "an", "the", "of", "is", "are", "be", "was", "were", "to", "it", "and", "you", "i"}
_FUSHA, _TOTAL = 600, 1000  # the rest of the total is Nahw's
_NAHW_SETS = ("hadith_sentences", "exam_sentences", "blind_sentences", "fresh_sentences", "checked_sentences")


def content(english: str) -> set[str]:
    """An English rendering's words worth comparing, each cut to five letters so "praises" meets "praise"."""
    english = re.sub(r"\([^)]*\)|\[[^\]]*\]", " ", english.lower())
    return {w[:5] for w in re.findall(r"[a-z]+", english) if w not in _FILLER}


@contextmanager
def offline():
    """The model stood in for (recording the facts it is handed), the store a throwaway file, and
    the gitignored Qur'an index and dictionary left out, so a laptop and CI score alike; all put
    back afterwards. The Qur'an paths are scored by score_quran instead."""
    handed: list[str] = []
    real = (ai.translate_sentence, progress_store.data_path, quran_search.whole_ayah, quran_search.ayah_run,
            dictionary_service.meaning_of)
    with tempfile.TemporaryDirectory() as folder:
        ai.translate_sentence = lambda text, facts: handed.append(facts) or {"english": "-"}
        progress_store.data_path = lambda _name: Path(folder) / "progress.db"
        quran_search.whole_ayah = quran_search.ayah_run = lambda _text: None
        dictionary_service.meaning_of = lambda _word: ""
        progress_store.reset_connection()
        try:
            yield handed
        finally:
            (ai.translate_sentence, progress_store.data_path, quran_search.whole_ayah, quran_search.ayah_run,
             dictionary_service.meaning_of) = real
            progress_store.reset_connection()


def score(entries: list[dict], show: int = 0) -> dict:
    """The counts over `entries` ({"ar", "en"?, "from"}), and timings in milliseconds."""
    counts = dict.fromkeys(("inputs", "rows", "broke", "aligned", "english", "junk", "covered", "wanted", "facts"), 0)
    took, shown = [], 0
    with offline() as handed:
        for entry in entries:
            counts["inputs"] += 1
            asked = len(handed)
            started = time.perf_counter()
            try:
                found = sentence_meaning.translate(entry["ar"])
            except Exception as exc:  # noqa: BLE001, a break is what is being counted
                counts["broke"] += 1
                print(f"  broke  {entry['ar']}  {exc!r}", file=sys.stderr)
                continue
            took.append(1000 * (time.perf_counter() - started))
            rows = found["words"]
            counts["rows"] += len(rows)
            counts["aligned"] += len(rows) == len(words(entry["ar"]))
            counts["english"] += sum(bool(r["english"]) for r in rows)
            counts["junk"] += sum(bool(_JUNK_RE.search(r["english"])) for r in rows)
            counts["facts"] += len(handed) > asked and len(handed[-1].splitlines()) == len(rows)
            if entry.get("en"):
                wanted, have = content(entry["en"]), set().union(*map(content, (r["english"] for r in rows)))
                counts["wanted"] += len(wanted)
                counts["covered"] += len(wanted & have)
                if show and shown < show and wanted - have:
                    shown += 1
                    print(f"  {entry['ar']}  |  {entry['en']}  |  {' · '.join(r['english'] for r in rows)}")
    return {**counts, **_timing(took)}


def score_quran(keys: list[str], show: int = 0) -> dict | None:
    """Rows against the Qur'an's own English, and runs cut from each ayah found again; None unbuilt."""
    from backend.services.quran import meanings

    ayah_run = quran_search.ayah_run
    if not meanings.is_built() or ayah_run("الحمد لله رب العالمين") is None:
        return None
    counts = dict.fromkeys(("ayahs", "rows_words", "rows_hit", "runs", "run_found", "run_right"), 0)
    took, shown = [], 0
    picker = random.Random(0)
    for key in keys:
        surah, ayah = map(int, key.split(":"))
        arabic, english = meanings.uthmani_for_ayah(surah, ayah), meanings.for_ayah(surah, ayah)
        if not arabic or len(arabic) != len(english):
            continue
        counts["ayahs"] += 1
        started = time.perf_counter()
        rows, _ = sentence_meaning.read_words(" ".join(arabic[n] for n in sorted(arabic)))
        took.append(1000 * (time.perf_counter() - started))
        if len(rows) == len(english):
            for n, row in enumerate(rows, 1):
                counts["rows_words"] += 1
                hit = bool(content(row["english"]) & content(english[n])) or row["english"].lower() == english[n].lower()
                counts["rows_hit"] += hit
                if show and shown < show and not hit:
                    shown += 1
                    print(f"  {key}  {row['arabic']}  ours: {row['english']}  the Qur'an's: {english[n]}")
        if len(arabic) >= 3:
            size = picker.randint(2, min(6, len(arabic) - 1))
            start = picker.randint(1, len(arabic) - size + 1)
            counts["runs"] += 1
            if found := ayah_run(" ".join(arabic[start + n] for n in range(size))):
                hit, first = found
                counts["run_found"] += 1
                theirs = meanings.for_ayah(hit.surah, hit.ayah)
                counts["run_right"] += all(theirs.get(first + n) == english[start + n] for n in range(size))
    return {**counts, **_timing(took)}


def _timing(took: list[float]) -> dict:
    took = sorted(took) or [0.0]
    return {"ms_p50": round(took[len(took) // 2]), "ms_p95": round(took[int(0.95 * (len(took) - 1))])}


def load_set() -> dict:
    return json.loads(SET.read_text(encoding="utf-8"))


def write_set() -> None:
    """The set rebuilt from its sources: the first fusha phrases of two words or more, every
    other one so all units are in it, then the Nahw sets in order; and 400 ayahs spread
    across the Qur'an, by key only (their text and English live in meanings.db, which this needs)."""
    spine = json.loads((DATA / "colloquial" / "spine.json").read_text(encoding="utf-8"))
    english = {p["slot"]: p["english"] for u in spine["units"] for lesson in u["lessons"] for p in lesson.get("phrases", [])}
    fusha = []
    for path in sorted((DATA / "colloquial" / "fusha").glob("unit-*.json")):
        unit = json.loads(path.read_text(encoding="utf-8"))
        fusha += [{"ar": p["arabic"], "en": english[p["slot"]], "from": f"fusha/{unit['unit']}/{p['slot']}"}
                  for lesson in unit["lessons"] for p in lesson.get("phrases", [])
                  if p["slot"] in english and len(words(p["arabic"])) >= 2]
    fusha = (fusha[::2] + fusha[1::2])[:_FUSHA]
    nahw = []
    for name in _NAHW_SETS:
        rows = json.loads((DATA / "nahw_rules" / f"{name}.json").read_text(encoding="utf-8"))
        nahw += [{"ar": r["sentence"], "from": f"{name}/{r.get('id', n)}"} for n, r in enumerate(rows)]
    seen, inputs = set(), []
    for entry in fusha + nahw:  # each text once, to the total
        if entry["ar"] not in seen and len(inputs) < _TOTAL:
            seen.add(entry["ar"])
            inputs.append(entry)
    import sqlite3
    from backend.services.quran import meanings
    with sqlite3.connect(meanings.DATABASE) as db:  # every ayah key, needing meanings.db once
        keys = [f"{s}:{a}" for s, a in db.execute("SELECT DISTINCT surah, ayah FROM meaning ORDER BY surah, ayah")]
    about = ("The dictionary's sentence yardstick; see backend/scripts/dictionary/score_sentences.py. "
             "Rebuilt with --write-set, never edited by hand.")
    SET.parent.mkdir(parents=True, exist_ok=True)
    quran = [keys[n * len(keys) // 400] for n in range(400)]
    line = lambda value: json.dumps(value, ensure_ascii=False)  # noqa: E731
    SET.write_text(f'{{"_about": {line(about)},\n "inputs": [\n  '
                   + ",\n  ".join(map(line, inputs))
                   + '\n ],\n "quran": [\n  '
                   + ",\n  ".join(line(quran[n:n + 20])[1:-1] for n in range(0, 400, 20))
                   + "\n ]}\n", encoding="utf-8")
    print(f"Wrote {SET}: {len(inputs)} inputs, 400 ayahs")


def worse(now: dict, baseline: dict) -> list[str]:
    """Each count that went the wrong way against the baseline, as a line saying so."""
    found = []
    for part, counts in baseline.items():
        for name, was in counts.items():
            got = (now.get(part) or {}).get(name)
            if got is None:
                continue
            if (name in HIGHER and got < was) or (name in LOWER and got > was):
                found.append(f"{part}.{name}: {got}, was {was}")
    return found


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--quran", action="store_true", help="also score the Qur'an set (needs meanings.db and the index)")
    parser.add_argument("--show", type=int, default=0, help="print this many misses")
    parser.add_argument("--check", action="store_true", help="exit 1 when a count is worse than the baseline")
    parser.add_argument("--save-baseline", action="store_true")
    parser.add_argument("--write-set", action="store_true")
    args = parser.parse_args()
    if args.write_set:
        write_set()
        return 0
    data = load_set()
    now = {"set": score(data["inputs"], args.show)}
    if args.quran and (quran := score_quran(data["quran"], args.show)):
        now["quran"] = quran
    print(json.dumps(now, indent=1))
    if args.save_baseline:
        kept = json.loads(BASELINE.read_text(encoding="utf-8")) if BASELINE.exists() else {}  # parts not rescored stay
        kept |= {part: {k: v for k, v in counts.items() if k in HIGHER + LOWER} for part, counts in now.items()}
        BASELINE.write_text(json.dumps(kept, indent=1) + "\n", encoding="utf-8")
        print(f"Wrote {BASELINE}")
    if args.check:
        baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
        if problems := worse(now, baseline):
            print("Worse than the baseline:\n  " + "\n  ".join(problems))
            return 1
        print("No count worse than the baseline.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
