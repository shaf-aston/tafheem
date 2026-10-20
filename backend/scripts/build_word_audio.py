"""Build frontend/public/words/word_audio.json: quiz word -> where a reciter says it.

    python backend/scripts/build_word_audio.py

Quran.com has a recording of every Qur'an word on its own. A quiz word found in
the Qur'an can therefore be spoken by a real reciter instead of a synthetic
voice. lib/speak.js reads the output as a plain lookup, so all spelling logic
lives here, once.

Words and file addresses both come from quran.com's own word list (cached in
backend/data/quran/wbw_words.json after one fetch). File numbers skip where a
pause mark sits, so an address cannot be worked out from the word's position.

Matching is strict, because a recording of a different word is worse than a
computer voice:
- letters must be identical after folding Uthmani spelling (ٱ is ا, a dagger
  alef is a full alef, small Qur'anic marks go);
- every letter the quiz word vowels must carry the same vowels in the Qur'an,
  and a quiz sukun means the Qur'an letter has no vowel (أَكْل is not أَكَلَ);
  a letter the quiz leaves bare accepts anything;
- the last letter follows the same rule, so a bare dictionary ending accepts the
  Qur'an's case ending but a written one must match (شَكَّ is not شَكٍّ).
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


def compatible(quiz: list, quran: list) -> bool:
    # A word with no vowels at all cannot say which word it is (كتب: kataba or kutiba?).
    if not any(marks for _, marks in quiz):
        return False
    if [c for c, _ in quiz] != [c for c, _ in quran]:
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
        return json.loads(CACHE.read_text(encoding="utf-8"))
    words = []
    for surah in range(1, 115):
        page = 1
        while page:
            req = urllib.request.Request(API.format(s=surah, p=page), headers={"User-Agent": "Mozilla/5.0"})
            body = json.load(urllib.request.urlopen(req, timeout=30))
            for verse in body["verses"]:
                words += [{"text": w["text_uthmani"], "audio": w["audio_url"]}
                          for w in verse["words"] if w["char_type_name"] == "word" and w["audio_url"]]
            page = body["pagination"]["next_page"]
            time.sleep(0.2)
    CACHE.write_text(json.dumps(words, ensure_ascii=False), encoding="utf-8")
    return words


def quran_words() -> dict[str, list]:
    """Bare-letter skeleton -> [(audio path, letters)], first occurrence first."""
    by_skeleton: dict[str, list] = {}
    for word in fetch():
        parsed = letters(word["text"])
        by_skeleton.setdefault("".join(c for c, _ in parsed), []).append((word["audio"], parsed))
    return by_skeleton


def build() -> dict[str, str]:
    index = quran_words()
    found: dict[str, str] = {}
    for entry in json.loads(WORDS.read_text(encoding="utf-8"))["words"]:
        ar = entry["ar"]
        parsed = letters(ar)
        for loc, form in index.get("".join(c for c, _ in parsed), []):
            if compatible(parsed, form):
                found[ar] = loc
                break
    return found


if __name__ == "__main__":
    found = build()
    total = len({w["ar"] for w in json.loads(WORDS.read_text(encoding="utf-8"))["words"]})
    OUT.write_text(json.dumps(found, ensure_ascii=False, sort_keys=True), encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"{len(found)} of {total} quiz words have a recording -> {OUT.relative_to(ROOT)}")
