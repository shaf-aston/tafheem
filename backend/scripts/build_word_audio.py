"""Build frontend/public/words/word_audio.json: quiz word -> where a reciter says it.

    python backend/scripts/build_word_audio.py

Quran.com has a recording of every Qur'an word on its own. A quiz word found in
the Qur'an can therefore be spoken by a real reciter instead of a synthetic
voice. lib/speech/speak.js reads the output as a plain lookup, so all spelling logic
lives here, once.

Words come from quran.com's own word list (cached in
backend/data/quran/wbw_words.json after one fetch). A file is named by the
word's place in its ayah: 004_088_014 is the 14th word of 4:88. The list's own
`audio_url` is not used: it counts ۞ and the pause marks (ۚ ۖ) as words, so after
one it names the next word's file (4:88's أَضَلَّ pointed at وَمَن), which put a
wrong word on 638 of 1,805 quiz words.

Matching is strict, because a recording of a different word is worse than a
computer voice:
- letters must be identical after folding Uthmani spelling (ٱ is ا, a dagger
  alef is a full alef, small Qur'anic marks go);
- every letter the quiz word vowels must carry the same vowels in the Qur'an,
  and a quiz sukun means the Qur'an letter has no vowel (أَكْل is not أَكَلَ);
  a letter the quiz leaves bare accepts anything;
- the last letter is stricter: the reciter says the ending the ayah needs, so a
  bare dictionary ending only matches a Qur'an word with no vowel there either
  (أَثِيم is not أَثِيمٍ, heard as athīmin), and a written one must match
  (شَكَّ is not شَكٍّ);
- a Qur'an word opening on a joining alif (ٱ) is never used: mid-ayah the
  reciter runs over it, so ٱبْتَغَىٰ is heard as btaghā.
Words with no match are left out and fall through to the next voice.
"""
from __future__ import annotations

import json
import sys
import time
import unicodedata
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "backend/data/quran/wbw_words.json"
API = "https://api.quran.com/api/v4/verses/by_chapter/{s}?words=true&word_fields=text_uthmani&per_page=50&page={p}"
WORDS = ROOT / "frontend/public/words/words.json"
OUT = ROOT / "frontend/public/words/word_audio.json"

SUKUN, SHADDA, DAGGER, UTHMANI_SUKUN = "ْ", "ّ", "ٰ", "ۡ"
VOWELS = set("ًٌٍَُِ")  # short vowels and tanween
MARKS = VOWELS | {SHADDA, SUKUN}
DROP = ({chr(c) for c in range(0x06D6, 0x06EE)} - {UTHMANI_SUKUN}) | {"ـ", "ٓ"}


def letters(word: str) -> list[tuple[str, frozenset[str]]]:
    """Each letter with the marks on it, Uthmani spelling folded."""
    out: list[tuple[str, set[str]]] = []
    for ch in unicodedata.normalize("NFC", word).replace("ٱ", "ا"):
        if ch == UTHMANI_SUKUN:
            ch = SUKUN
        if ch in DROP:
            continue
        if ch == DAGGER:
            # عَلَىٰ: the mark only lengthens ى or و; elsewhere it is a written-out alef.
            if out and out[-1][0] not in "ىو":
                out.append(("ا", set()))
        elif ch in MARKS:
            if out:
                out[-1][1].add(ch)
        elif "؀" <= ch <= "ۿ":
            out.append((ch, set()))
    return [(c, frozenset(m)) for c, m in out]


def matches(quiz: str, quran: str) -> bool:
    """Whether the reciter saying `quran` in its ayah says exactly the word `quiz` shows."""
    if quran.startswith("ٱ"):
        return False
    return compatible(letters(quiz), letters(quran))


def compatible(quiz: list, quran: list) -> bool:
    # A word with no vowels at all cannot say which word it is (كتب: kataba or kutiba?).
    if not any(marks for _, marks in quiz):
        return False
    if [c for c, _ in quiz] != [c for c, _ in quran]:
        return False
    if not quiz[-1][1] and quran[-1][1] & VOWELS:
        return False
    return all(_same(q, r) for (_, q), (_, r) in zip(quiz, quran))


def _same(quiz: frozenset[str], quran: frozenset[str]) -> bool:
    if not quiz:
        return True
    if quiz == {SUKUN}:
        return not quran & VOWELS
    return quiz - {SUKUN} == quran - {SUKUN}


def fetch() -> list[dict]:
    """quran.com's word list, fetched once and kept."""
    if CACHE.exists():
        words = json.loads(CACHE.read_text(encoding="utf-8"))
        if words and "position" in words[0]:  # a list kept before files went by position is refetched
            return words
    words = []
    for surah in range(1, 115):
        page = 1
        while page:
            req = urllib.request.Request(API.format(s=surah, p=page), headers={"User-Agent": "Mozilla/5.0"})
            body = json.load(urllib.request.urlopen(req, timeout=30))
            for verse in body["verses"]:
                words += [{"text": w["text_uthmani"], "position": w["position"],
                           "audio": audio_path(verse["verse_key"], w["position"])}
                          for w in verse["words"] if w["char_type_name"] == "word" and w["audio_url"]]
            page = body["pagination"]["next_page"]
            time.sleep(0.2)
    CACHE.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    return words


def audio_path(verse_key: str, position: int) -> str:
    """The reciter's file for the word at `position` (from 1) in ayah `verse_key` ("4:88")."""
    surah, ayah = verse_key.split(":")
    return f"wbw/{int(surah):03d}_{int(ayah):03d}_{position:03d}.mp3"


def quran_words() -> dict[str, list]:
    """Bare-letter skeleton -> [(audio path, Uthmani text)], first occurrence first."""
    by_skeleton: dict[str, list] = {}
    for word in fetch():
        skeleton = "".join(c for c, _ in letters(word["text"]))
        by_skeleton.setdefault(skeleton, []).append((word["audio"], word["text"]))
    return by_skeleton


def build() -> dict[str, str]:
    index = quran_words()
    found: dict[str, str] = {}
    for entry in json.loads(WORDS.read_text(encoding="utf-8"))["words"]:
        ar = entry["ar"]
        for loc, form in index.get("".join(c for c, _ in letters(ar)), []):
            if matches(ar, form):
                found[ar] = loc
                break
    return found


if __name__ == "__main__":
    found = build()
    total = len({w["ar"] for w in json.loads(WORDS.read_text(encoding="utf-8"))["words"]})
    OUT.write_text(json.dumps(found, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{len(found)} of {total} quiz words have a recording -> {OUT.relative_to(ROOT)}")
