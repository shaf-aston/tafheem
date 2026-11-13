"""Check that the ONNX disambiguator ranks every reading as CAMeL's own torch one does.

    python -m backend.scripts.nahw.check_disambig_parity [--ayahs 6236] [--sets all]

Runs both over the same sentences and compares, word by word, the tag the model
predicts (every feature) and every one of the `catib_readings` ranked readings
(score, the whole analysis, its spelling and both log probabilities). Prints how
many matched and each difference, and exits 1 on any. Needs torch and CAMeL's BERT,
so it is a build-time check, never part of the app: CI runs it after
build_disambig_onnx.py, and so should anyone changing either.

Sentences: every sentence the i'raab scorer keys (score_iraab.py), --ayahs Qur'an
verses spread evenly over the mushaf (6236 is all of them), runs of 40 consecutive
verses joined into one sentence longer than BERT's 510 word pieces (the one path,
cutting into segments, that a short sentence never takes), and a few odd inputs:
an empty sentence, blank words, a word of marks only, Latin, digits, punctuation.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time

import onnxruntime  # noqa: F401, must precede camel_tools (see catib_onnx.py)

from backend.config import data_path, get_settings
from backend.scripts.nahw.score_iraab import SETS
from backend.services.nahw.syntax.disambiguator_onnx import OnnxDisambiguator
from backend.services.quran.mushaf import DATA_DIR as MUSHAF_DIR
from backend.services.text.arabic_text import words as split_words

LONG_RUN_AYAHS = 40
ODD = [[], [""], ["كتب", "", "الولد"], ["الولد", " ", "كتب", "الدرس"], ["َ"], ["ذهب", "َّ", "الطالب"],
       ["hello", "world"], ["١٢٣", "2024", "كتب"], ["!", "؟", "«قال»", "..."], ["آمنوا", "ءامنوا", "ٱلرَّحۡمَٰنِ"],
       ["ـــ", "كـتـب"], ["x‍y", "‌"]]


def verses() -> list[str]:
    """Every verse in mushaf order, joined from the printed lines, its number dropped."""
    pages = json.loads((MUSHAF_DIR / "madani-1421.json").read_text(encoding="utf-8"))["pages"]
    text: dict[tuple[int, int], list[str]] = {}
    for page in pages:
        for kind, *body in page:  # a line is ["surah", n], ["ayah", [[surah, ayah, text], ...]] or ["basmala"]
            if kind == "ayah":
                for surah, ayah, line in body[0]:
                    text.setdefault((surah, ayah), []).append(line)
    return [re.sub(r"\s*[٠-٩]+\s*$", "", " ".join(parts)) for parts in text.values()]


def sentences(ayahs: int, sets: list[str]) -> list[list[str]]:
    rows = [row for name in sets for row in SETS[name]()]
    out = list(dict.fromkeys(tuple(split_words(row["sentence"])) for row in rows))
    all_verses = verses()
    step = max(1, len(all_verses) // max(ayahs, 1))
    out += [tuple(split_words(v)) for v in all_verses[::step][:ayahs]]
    starts = [0, len(all_verses) // 2, len(all_verses) - LONG_RUN_AYAHS]
    out += [tuple(split_words(" ".join(all_verses[s:s + LONG_RUN_AYAHS]))) for s in starts]
    return [list(s) for s in out] + ODD


def ranked(words) -> list[tuple]:
    return [(w.word, [(s.score, s.analysis, s.diac, s.pos_lex_logprob, s.lex_logprob) for s in w.analyses])
            for w in words]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ayahs", type=int, default=6236, help="how many Qur'an verses to include")
    ap.add_argument("--sets", default="all", help="score_iraab sets, comma separated, or all")
    args = ap.parse_args()
    sets = list(SETS) if args.sets == "all" else args.sets.split(",")

    from camel_tools.disambig.bert import BERTUnfactoredDisambiguator
    from camel_tools.disambig.bert.unfactored import _dediac_sentence

    top = get_settings().catib_readings
    old = BERTUnfactoredDisambiguator.pretrained("msa", top=top, use_gpu=False)
    new = OnnxDisambiguator(data_path("catib_disambig_dir"), top=top)
    todo = sentences(args.ayahs, sets)

    words = readings = 0
    took = {"torch": 0.0, "onnx": 0.0}
    differences: list[str] = []
    for n, ws in enumerate(todo):
        bare = _dediac_sentence(ws)
        want_tags = old._predict_sentence(bare)
        got_tags = [dict(t, lex=b, diac=b) for b, t in zip(bare, new._tags(bare))]
        if want_tags != got_tags:
            bad = [i for i in range(max(len(want_tags), len(got_tags)))
                   if i >= len(want_tags) or i >= len(got_tags) or want_tags[i] != got_tags[i]]
            differences.append(f"sentence {n} {' '.join(ws)[:60]!r}: tags differ at words {bad[:10]}")

        started = time.perf_counter()
        want = ranked(old.disambiguate(ws))
        took["torch"] += time.perf_counter() - started
        started = time.perf_counter()
        got = ranked(new.disambiguate(ws))
        took["onnx"] += time.perf_counter() - started

        if len(want) != len(got):
            differences.append(f"sentence {n}: {len(want)} words from CAMeL, {len(got)} from ONNX")
        for i, (a, b) in enumerate(zip(want, got)):
            words += 1
            readings += len(a[1])
            if a != b:
                differences.append(f"sentence {n} word {i} {ws[i]!r}: ranked readings differ "
                                   f"({len(a[1])} vs {len(b[1])}; first differing at "
                                   f"{next((k for k, (x, y) in enumerate(zip(a[1], b[1])) if x != y), None)})")
        if (n + 1) % 200 == 0:
            print(f"  {n + 1}/{len(todo)} sentences, {len(differences)} differences", file=sys.stderr)

    print(f"{len(todo)} sentences, {words} words, {readings} ranked readings (top {top}); "
          f"{len(differences)} differences. torch {took['torch']:.1f}s, onnx {took['onnx']:.1f}s")
    print(*differences[:50], sep="\n")
    sys.exit(1 if differences else 0)


if __name__ == "__main__":
    main()
