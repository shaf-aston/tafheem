"""Check that the ONNX disambiguator picks what CAMeL's own torch one picks.

    venv/Scripts/python -m backend.scripts.check_disambig_parity [--ayahs 600]

Runs both over the same sentences and compares, word by word, the whole chosen
analysis (every field, not just the tag). Prints the match rate and each
difference. Needs torch and CAMeL's ~440 MB BERT model, so it is a build-time
check, never part of the app: run it after build_disambig_onnx.py, especially
with --int8.

Sentences: every book example and every checked sentence the i'raab scorer uses
(score_iraab.py), plus --ayahs Qur'an verses spread evenly over the whole book,
plus runs of consecutive verses joined into one sentence longer than BERT's 510
word pieces, which is the one path (cutting into segments) a short sentence
never takes.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys

import onnxruntime  # noqa: F401, must precede camel_tools (Windows DLL load-order bug, see catib_onnx.py)

from backend.config import data_path, get_settings
from backend.scripts.score_iraab import book_sentences, checked_sentences
from backend.services.arabic_text import words as split_words
from backend.services.syntax.disambiguator_onnx import OnnxDisambiguator

LONG_RUNS = 3          # how many over-long joined sentences to test
LONG_RUN_AYAHS = 40    # consecutive verses per over-long sentence


def quran_sentences(count: int) -> list[list[str]]:
    con = sqlite3.connect(data_path("quran_search_index_path"))
    verses = [r[0] for r in con.execute("SELECT arabic FROM verse ORDER BY surah, ayah")]
    step = max(1, len(verses) // max(count, 1))
    short = [split_words(v) for v in verses[::step]]
    # runs from the start of the Qur'an, from the middle, and from the end
    starts = [0, len(verses) // 2, len(verses) - LONG_RUN_AYAHS]
    long = [split_words(" ".join(verses[s:s + LONG_RUN_AYAHS])) for s in starts[:LONG_RUNS]]
    return [w for w in short + long if w]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ayahs", type=int, default=600, help="how many Qur'an verses to include")
    args = ap.parse_args()

    from camel_tools.disambig.bert import BERTUnfactoredDisambiguator
    old = BERTUnfactoredDisambiguator.pretrained("msa", top=1, use_gpu=False)
    new = OnnxDisambiguator(data_path("catib_disambig_dir"), get_settings().catib_analyzer_cache)

    sentences = [split_words(s["sentence"]) for s in book_sentences() + checked_sentences()]
    sentences += quran_sentences(args.ayahs)
    sentences = [s for s in sentences if s]

    same = total = 0
    differences: list[str] = []
    for n, ws in enumerate(sentences):
        want = [d.analyses[0].analysis for d in old.disambiguate(ws)]
        got = new.best_analyses(ws)
        if len(want) != len(got):
            differences.append(f"sentence {n}: {len(want)} words from CAMeL, {len(got)} from ONNX")
        for i, (a, b) in enumerate(zip(want, got)):
            total += 1
            if a == b:
                same += 1
            else:
                keys = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
                differences.append(f"sentence {n} word {i} {ws[i]}: differs in {keys}: "
                                   f"{ {k: a.get(k) for k in keys} } vs { {k: b.get(k) for k in keys} }")
        if (n + 1) % 100 == 0:
            print(f"  {n + 1}/{len(sentences)} sentences", file=sys.stderr)

    print(f"{len(sentences)} sentences, {total} words: {same} identical = {same / total:.4%}")
    print(*differences[:50], sep="\n")
    sys.exit(1 if differences else 0)


if __name__ == "__main__":
    main()
