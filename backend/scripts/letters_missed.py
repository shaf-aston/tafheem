"""Which letters the ear mishears, counted from readings already saved.

Everything here is free: not one recording is opened and not one model is
loaded. Every reading the ears have ever given is on disk, and the correct
words are known, so lining the two up letter by letter says what a word error
rate never can. "8% of words wrong" does not tell you the ear cannot hear the
difference between two letters; this does.

Two parts:

  the letters it has  - a model can only ever write a letter its own list of
                        pieces contains. A letter absent from that list can
                        never come out, however clearly it was said.
  the letters it hears - expected against heard, aligned the way the page
                        aligns them (place.letters), counting what each letter
                        turned into.

Only recitations the reviewer marked nothing on are counted. On a clip where
the person really did recite wrong, a mismatch is the person's mistake, and
counting it would blame the ear for hearing correctly.

    python backend/scripts/letters_missed.py
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

from backend.config import data_path
from backend.services.recitation.place import letters

HERE = Path(__file__).resolve().parents[1] / "data" / "recitation_checks"
DOWNLOADS = HERE / "downloads"
REPORT = HERE / "letters-report.txt"

# The readings to judge, and where the right answer comes from for each.
SAVED = {
    "whisper": DOWNLOADS / "heard-whisper.jsonl",
    "letters": DOWNLOADS / "heard-letters.jsonl",
    "hosted": DOWNLOADS / "heard-hosted.jsonl",
}

IS_LETTER = re.compile("[ء-ي]")

# Signs in the Arabic block that a recitation never needs, so a model lacking
# them is not lacking anything: five letters borrowed by other languages, the
# stretch mark that only makes a word wider on the page, and the small alef,
# which imlaei spelling writes as a plain alef anyway.
NOT_IN_THE_QURAN = set("ػؼؽؾؿـٰ")


def named(ch: str) -> str:
    """A letter with its Unicode name, so a report is readable without a font."""
    try:
        return f"{ch} {unicodedata.name(ch).replace('ARABIC LETTER ', '').replace('ARABIC ', '').lower()}"
    except ValueError:
        return ch


def _byte_signs() -> dict[str, int]:
    """The GPT-2 sign-per-byte table, backwards.

    Whisper's vocabulary is not written in Arabic. Every piece is a run of
    bytes, and each byte is printed as one stand-in sign so the file stays
    plain text: an Arabic letter is two bytes, so two signs. Reading the file
    as text and looking for ا finds nothing and would report, wrongly, that
    the model cannot write a single Arabic letter.
    """
    plain = list(range(ord("!"), ord("~") + 1)) + list(range(0xA1, 0xAD)) + list(range(0xAE, 0x100))
    signs, spare = list(plain), 0
    for byte in range(256):
        if byte not in plain:
            plain.append(byte)
            signs.append(256 + spare)
            spare += 1
    return {chr(s): b for b, s in zip(plain, signs)}


_SIGNS = _byte_signs()


def _as_arabic(piece: str) -> str:
    """One byte-written piece, back into the letters it stands for."""
    raw = bytes(_SIGNS[c] for c in piece if c in _SIGNS)
    return raw.decode("utf-8", errors="ignore")


def pieces_of(folder: Path) -> list[str] | None:
    """Every piece a model can write, from whichever vocabulary file it keeps."""
    one = folder / "vocab.json"
    if one.is_file():
        vocab = json.loads(one.read_text(encoding="utf-8"))
        return [vocab[str(i)] for i in range(len(vocab))]
    two = folder / "vocabulary.json"
    if two.is_file():
        return [_as_arabic(p) for p in json.loads(two.read_text(encoding="utf-8"))]
    return None


def whisper_folder() -> Path | None:
    """Where the downloaded recitation model sits in the shared model cache."""
    cache = Path.home() / ".cache" / "huggingface" / "hub"
    snapshots = cache / "models--OdyAsh--faster-whisper-base-ar-quran" / "snapshots"
    if not snapshots.is_dir():
        return None
    return next((p for p in snapshots.iterdir() if p.is_dir()), None)


def has_every_letter(pieces: list[str]) -> tuple[list[str], list[str]]:
    """(letters, marks) that appear in no piece at all, so can never be written."""
    ink = "".join(pieces)
    alphabet = [chr(c) for c in range(0x0621, 0x064B)]
    harakat = [chr(c) for c in range(0x064B, 0x0653)] + ["ٰ"]
    return ([c for c in alphabet if c not in ink],
            [c for c in harakat if c not in ink])


def clean_clips() -> dict[str, list[str]]:
    """Clip id -> its expected words, for clips the reviewer marked nothing on."""
    out = {}
    for line in (DOWNLOADS / "results.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        clip = json.loads(line)
        if not clip.get("marks"):
            out[clip["id"]] = clip["words"]
    return out


def compare(expected: str, heard: str, swaps: Counter, seen: Counter,
            dropped: Counter, added: Counter) -> None:
    """One reading, letter against letter, into the four tallies."""
    want, got = letters(expected), letters(heard)
    seen.update(want)
    for how, i1, i2, j1, j2 in difflib.SequenceMatcher(a=want, b=got, autojunk=False).get_opcodes():
        if how == "replace":
            # Straight across where the two runs are the same length; a run that
            # changed length has no one-to-one pairing, so it is counted as
            # letters dropped and letters added instead of invented pairs.
            if i2 - i1 == j2 - j1:
                for a, b in zip(want[i1:i2], got[j1:j2]):
                    swaps[(a, b)] += 1
            else:
                dropped.update(want[i1:i2])
                added.update(got[j1:j2])
        elif how == "delete":
            dropped.update(want[i1:i2])
        elif how == "insert":
            added.update(got[j1:j2])


def read_benchmark() -> dict[str, tuple[Counter, ...]]:
    """The same comparison on the seven professional reciters, per ear.

    A different question from the one below it. Those recordings are ordinary
    people, where a letter can be genuinely unclear; these are clear, careful
    recitation, so a letter the ear still gets wrong here it cannot hear at all.
    """
    readings = Path(__file__).resolve().parents[2] / "frontend" / "scripts" / "ears-heard.json"
    quran = json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))
    if not readings.is_file():
        return {}
    ears: dict[str, tuple] = {}
    for key, entry in json.loads(readings.read_text(encoding="utf-8")).items():
        parts = key.split(" ")
        if len(parts) != 3 or parts[2] not in quran:
            continue
        heard = entry if isinstance(entry, str) else entry.get("text")
        if not heard:
            continue
        tallies = ears.setdefault(parts[0], (Counter(), Counter(), Counter(), Counter(), Counter()))
        compare(quran[parts[2]], heard, *tallies[:4])
        tallies[4]["clips"] += 1
    return ears


def read_saved(name: str, path: Path, expect: dict[str, list[str]]) -> tuple[Counter, ...]:
    """Every clean clip in one saved file, compared."""
    swaps, seen, dropped, added = Counter(), Counter(), Counter(), Counter()
    used = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        words = expect.get(row["id"])
        if words is None:
            continue
        compare(" ".join(words), row.get("heard") or "", swaps, seen, dropped, added)
        used += 1
    return swaps, seen, dropped, added, used


def table(name: str, swaps: Counter, seen: Counter, dropped: Counter,
          added: Counter, used: int) -> list[str]:
    """One ear's letters, worst first."""
    wrong = defaultdict(Counter)
    for (a, b), n in swaps.items():
        wrong[a][b] += n
    rows = []
    for letter, total in seen.most_common():
        swapped = sum(wrong[letter].values())
        bad = swapped + dropped[letter]
        if not total:
            continue
        became = ", ".join(f"{b} x{n}" for b, n in wrong[letter].most_common(3))
        rows.append((bad / total, total, letter, swapped, dropped[letter], became))
    rows.sort(reverse=True)
    out = [
        "",
        f"{name}: {used} recitations, {sum(seen.values())} letters expected",
        f"{'letter':<22} {'said':>7} {'swapped':>8} {'gone':>6} {'wrong':>7}   became",
    ]
    for share, total, letter, swapped, gone, became in rows:
        out.append(f"{named(letter):<22} {total:>7} {swapped:>8} {gone:>6} {share * 100:>6.1f}%   {became}")
    heard_only = ", ".join(f"{named(c)} x{n}" for c, n in added.most_common(6))
    out.append(f"letters heard that were not said: {heard_only or 'none'}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", action="store_true", help="print the report as well as writing it")
    args = parser.parse_args()

    expect = clean_clips()
    lines = [
        "Which letters the ear mishears.",
        "",
        f"Counted only on the {len(expect)} recitations a reviewer marked nothing on, so",
        "every mismatch below is the ear's and not the reciter's. 'wrong' is that",
        "letter swapped for another or dropped; 'became' names the three commonest.",
        "",
        "THE LETTERS EACH MODEL CAN WRITE AT ALL",
    ]

    for name, folder in (("letters (tilawa)", data_path("recitation_letters_path")),
                         ("whisper (recitation)", whisper_folder())):
        if folder is None or not Path(folder).is_dir():
            lines.append(f"  {name}: not on this machine, skipped")
            continue
        pieces = pieces_of(Path(folder))
        if pieces is None:
            lines.append(f"  {name}: no vocabulary file in {folder}")
            continue
        missing, marks = has_every_letter(pieces)
        qurani = [c for c in missing + marks if c not in NOT_IN_THE_QURAN]
        lines.append(f"  {name}: {len(pieces)} pieces")
        lines.append(f"    letters it can never write: {' '.join(missing) or 'none'}")
        lines.append(f"    marks it can never write:   {' '.join(marks) or 'none'}")
        lines.append(f"    of those, ones the Qur'an uses: {' '.join(qurani) or 'none'}")

    lines.append("")
    lines.append("WHAT EACH EAR HEARD FROM SEVEN PROFESSIONAL RECITERS")
    lines.append("(frontend/scripts/ears-heard.json, where the words are certain)")
    # A rare letter judged on thirty recitations swings ten points on one word,
    # so an ear with only a handful of them prints nothing rather than a number
    # that looks like an answer. Which ears those were is said, not swallowed.
    ENOUGH = 100
    bench = read_benchmark()
    for name, (swaps, seen, dropped, added, count) in sorted(bench.items()):
        if count["clips"] >= ENOUGH:
            lines += table(name, swaps, seen, dropped, added, count["clips"])
    few = [f"{n} ({c['clips']})" for n, (_, _, _, _, c) in sorted(bench.items()) if c["clips"] < ENOUGH]
    if few:
        lines.append(f"\nleft out, fewer than {ENOUGH} recitations read: {', '.join(few)}")

    lines.append("")
    lines.append("WHAT EACH EAR HEARD FROM ORDINARY PEOPLE RECITING")
    for name, path in SAVED.items():
        if not path.is_file():
            lines.append(f"\n{name}: {path.name} is not here, skipped")
            continue
        swaps, seen, dropped, added, used = read_saved(name, path, expect)
        if not used:
            lines.append(f"\n{name}: no clean recitation in {path.name}, skipped")
            continue
        lines += table(name, swaps, seen, dropped, added, used)

    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {REPORT}")
    if args.report:
        print("\n".join(lines))


if __name__ == "__main__":
    main()
