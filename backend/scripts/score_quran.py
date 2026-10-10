"""Score the typed-sentence analyser on the Qur'an, with its own Qur'an lookup switched off.

Each ayah goes in as a reader would type it (the plain vowelled imlaei spelling,
pause marks removed), and the rules alone answer: the treebank record a typed
ayah is normally drawn from is turned off, so nothing is looked up.
Two answer keys, both scholars' work the rules never read:
  case   the Quranic Arabic Corpus morphology: a noun's NOM/ACC/GEN and an
         imperfect verb's mood, every word that has one; past and command verbs are mabni.
         A particle's ACC is not a case: the corpus tags إِنَّ and its sisters ACC.
         The corpus gives a mabni noun its place (يَٰٓأَيُّهَا: أَيُّ ACC) where a card says mabni.
         It tags a vowel that serves two cases by the vowel (sign_only), so jarr against
         nasb is not scored there; the treebank role still judges those words.
  role   the Quranic Treebank's role for each word's own column, compared by
         family (answer_key.json) or by name. Not scored where it names a whole
         phrase and a card names the word's own particle: its مُتَعَلِّقٌ, or عَلَيْهِمْ
         filed as نائب فاعل where the card says حرف جر; nor its صلة, the relative's
         clause on its verb. Its ظرف زمان / ظرف مكان is the book's مفعول فيه.
A fifth of the ayahs (by a fixed hash) is "hold": look at "tune" while fixing rules,
and read "hold" only to check the fix carried over.

    venv/Scripts/python -m backend.scripts.score_quran --every 10
    venv/Scripts/python -m backend.scripts.score_quran --surah 2 --out quran_misses.txt
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
import zlib
from collections import Counter
from unittest import mock

from backend.config import data_path
from backend.scripts.score_iraab import family, plain_role
from backend.services import iraab, quran_corpus, tarkeeb_store
from backend.services.arabic_text import bare_letters, strip_diacritics
from backend.services.harakat import has_tanween, typed_case

PAUSE = re.compile("[ۖ-ۭ]")
# the plain text writes the vocative and هَا apart; the corpus joins them to the next word
JOINED_ON = {"يا", "ويا", "ها"}
NOUN_CASE = {"NOM": "raf'", "ACC": "nasb", "GEN": "jarr"}
MOOD = {"MOOD:IND": "raf'", "MOOD:SUBJ": "nasb", "MOOD:JUS": "jazm"}
# the treebank names a phrase here, not the word's own job: a جار ومجرور's attachment, a relative's clause
UNSCORED_ROLES = {"متعلق", "صلة"}
# the treebank's name for a role the book calls otherwise
SAME_ROLE = {"ظرف زمان": "مفعول فيه", "ظرف مكان": "مفعول فيه"}


def case_key(tag: dict) -> str | None:
    """The corpus's case for one word: its stem's case or mood, or None where it gives none."""
    feats = tag["features"].split("|")
    if tag["pos"] == "V":
        return next((MOOD[f] for f in feats if f in MOOD), "mabni")
    if tag["pos"] != "N":
        return None
    return next((NOUN_CASE[f] for f in feats if f in NOUN_CASE), None)


def sign_only(tag: dict, typed: str) -> bool:
    """A word whose vowel serves two cases, where the corpus tags the vowel, not the case:
    a ـات kasra is nasb too (وَعَمِلُوا الصَّالِحَاتِ: GEN), a diptote's fatha jarr too (إِنَّ جَهَنَّمَ: GEN)."""
    if any("SUFF" in seg["features"] for seg in tag["segments"]):
        return False
    bare, shown = strip_diacritics(typed), typed_case(typed)
    return (shown == "i" and bare.endswith("ات")) or (shown == "a" and not has_tanween(typed) and not bare.startswith("ال"))


def corpus_index(typed: list[str], corpus_len: int) -> list[int | None] | None:
    """For each typed word, the corpus word it is (None for a joined يا/ها); None if they never line up."""
    extra, out, at = len(typed) - corpus_len, [], 0
    for word in typed:
        if extra > 0 and bare_letters(word) in JOINED_ON:
            extra -= 1
            out.append(None)
            continue
        out.append(at)
        at += 1
    return out if at == corpus_len else None


class _Failures(logging.Handler):
    """Which ayahs the parser gave up on: their words are left unnamed, so say so."""

    def __init__(self) -> None:
        super().__init__(logging.ERROR)
        self.ayah, self.ayahs = "", []

    def emit(self, record: logging.LogRecord) -> None:
        self.ayahs.append(self.ayah)


def held(surah: int, ayah: int) -> bool:
    return zlib.crc32(f"{surah}:{ayah}".encode()) % 5 == 0


def score(ayahs: list[tuple[int, int]], out_path: str | None) -> None:
    plain = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    stats = {"tune": Counter(), "hold": Counter()}
    case_mix, role_mix, misses, slow = Counter(), Counter(), [], []
    texts: dict[int, dict[int, str]] = {}
    iraab.analyze("بِسْمِ اللَّهِ")  # load the models before anything is timed
    failed = _Failures()
    logging.getLogger("backend.services.syntax").addHandler(failed)
    for surah, ayah in ayahs:
        corpus_text = texts.setdefault(surah, dict(quran_corpus.ayah_texts(surah)))[ayah]
        tags = quran_corpus.tags_for_ayah(surah, ayah)
        typed = PAUSE.sub("", plain[f"{surah}:{ayah}"]).split()
        index = corpus_index(typed, len(tags))
        row = stats["hold" if held(surah, ayah) else "tune"]
        row["ayahs"] += 1
        if index is None:
            row["unaligned"] += 1
            continue
        record = tarkeeb_store.for_sentence(corpus_text)
        roles = [r["role"] for r in record["roles"]] if record and len(record["roles"]) == len(tags) else None
        failed.ayah = f"{surah}:{ayah}"
        started = time.perf_counter()
        with mock.patch.object(tarkeeb_store, "for_sentence", lambda _sentence: None):
            cards = iraab.analyze(" ".join(typed))["words"]
        seconds = time.perf_counter() - started
        slow.append((seconds, f"{surah}:{ayah}", len(typed)))
        if len(cards) != len(typed):
            row["unaligned"] += 1
            continue
        wrong = []
        for card, at in zip(cards, index):
            if at is None:
                continue
            word = strip_diacritics(card["word"])
            want = case_key(tags[at])
            if want in ("jarr", "nasb") and card.get("case") in ("jarr", "nasb") and sign_only(tags[at], card["word"]):
                row["sign only"] += 1
            elif want:
                kind = "verb" if tags[at]["pos"] == "V" else "noun"
                row[f"{kind} cases"] += 1
                if card.get("case") == want:
                    row[f"{kind} right"] += 1
                else:
                    case_mix[(kind, want, card.get("case"))] += 1
                    wrong.append(f"{word}: case {card.get('case')} (corpus {want})")
            want_role = plain_role(roles[at]) if roles else ""
            want_role = SAME_ROLE.get(want_role, want_role)
            if not want_role or want_role in UNSCORED_ROLES:
                continue
            if tags[at]["pos"] == "P" and family(want_role) != "harf":
                row["phrase roles"] += 1  # the treebank names the phrase, the card its particle
                continue
            have = plain_role(card.get("role"))
            row["roles"] += 1
            if have == want_role or (family(have) and family(have) == family(want_role)):
                row["roles right"] += 1
            else:
                row["role gaps" if not have else "roles wrong"] += 1
                role_mix[(want_role, have or "blank")] += 1
                wrong.append(f"{word}: {have or 'blank'} (treebank {want_role})")
        if wrong:
            misses.append(f"{surah}:{ayah}  " + " | ".join(wrong))

    def pct(c: Counter, right: str, of: str) -> str:
        return f"{c[right]}/{c[of]} = {c[right] / c[of]:.1%}" if c[of] else "-"

    for name, c in stats.items():
        print(f"{name:<5} ayahs {c['ayahs']} (unaligned {c['unaligned']})  noun case {pct(c, 'noun right', 'noun cases')} "
              f"(jarr/nasb by one vowel, not scored {c['sign only']})  verb mood {pct(c, 'verb right', 'verb cases')}  role {pct(c, 'roles right', 'roles')}  "
              f"(blank {c['role gaps']}, wrong {c['roles wrong']}, phrase roles not scored {c['phrase roles']})")
    if failed.ayahs:
        print(f"parser failed, every word left unnamed: {len(failed.ayahs)} ayahs {failed.ayahs[:20]}")
    times = sorted(slow, reverse=True)
    if times:
        print(f"speed: mean {sum(t for t, *_ in times) / len(times):.2f}s an ayah, slowest {times[0][0]:.1f}s "
              f"({times[0][1]}, {times[0][2]} words)")
    print("Case mix-ups (kind, corpus -> app):")
    for (kind, want, have), n in case_mix.most_common(12):
        print(f"  {n:>5}  {kind}: {want} -> {have}")
    print("Role mix-ups (treebank -> app):")
    for (want, have), n in role_mix.most_common(25):
        print(f"  {n:>5}  {want} -> {have}")
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(misses))
        print(f"{len(misses)} ayahs with a miss written to {out_path}")


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--surah", type=int, help="only this surah")
    parser.add_argument("--every", type=int, default=1, help="score every nth ayah, for a quick sample")
    parser.add_argument("--out", help="write each ayah's misses to this file")
    args = parser.parse_args()
    if args.every < 1 or (args.surah is not None and not 1 <= args.surah <= 114):
        parser.error("--every must be 1 or more and --surah 1 to 114")
    surahs = [args.surah] if args.surah else range(1, 115)
    ayahs = [(s, a) for s in surahs for a, _ in quran_corpus.ayah_texts(s)]
    score(ayahs[:: args.every], args.out)


if __name__ == "__main__":
    main()
