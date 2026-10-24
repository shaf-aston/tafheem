"""One-time harvest: every line of a printed mushaf, word for word, stored in git.

Run once:  python backend/scripts/quran/build_mushaf.py

Why this exists
---------------
The Qur'an tab can show the surah as the pages of a printed mushaf, the page a
reader who memorises by the page knows by sight. Where a line breaks is a fact
about one printing, so it is fetched from something that knows that printing:
Quran.com gives each word of the 604-page Madani 1421 printing its page and its
line, and the King Fahd Complex's own Unicode spelling of the word, which is the
text its QPC Hafs font is drawn for.

The words come back with their line numbers only; a surah's name and its
basmala have no words, so they are the gaps. A gap of two before a first ayah is
the name and the basmala, a gap of one is the name alone (al-Fatihah's basmala
is its first ayah, at-Tawbah has none). Checked below for the whole printing:
6,236 ayahs, 114 names, 112 basmalas, 15 lines on every page but the first two (8).

The answer is a small JSON file kept in git (backend/data/quran/mushaf/), not a
database, so the server's sync copies it like any other tracked data file.
services/quran/mushaf.py is the only reader of it. Safe to re-run: written to a
temporary file and swapped in only once every check has passed.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "quran"
OUT = DATA_DIR / "mushaf" / "madani-1421.json"  # its entry is in mushaf/printings.json

API = "https://api.quran.com/api/v4"
PAUSE_SECONDS = 0.25
TIMEOUT_SECONDS = 30.0
RETRIES = 3

TOTAL_PAGES = 604
SURAHS = 114
AYAHS = 6236
NO_BASMALA_LINE = {1, 9}  # al-Fatihah's basmala is its first ayah; at-Tawbah has none


def lines_on(page: int) -> int:
    """The first two pages are framed, with 8 lines; every other page has 15."""
    return 8 if page <= 2 else 15


def _get(client: httpx.Client, path: str, **params) -> dict:
    """One API call, retried on the transient failures a long run will hit."""
    for attempt in range(1, RETRIES + 1):
        try:
            response = client.get(f"{API}{path}", params=params, timeout=TIMEOUT_SECONDS)
            response.raise_for_status()
            return response.json()
        except (httpx.HTTPError, ValueError) as exc:
            if attempt == RETRIES:
                raise
            wait = attempt * 2
            print(f"    {type(exc).__name__}, retrying in {wait}s ({attempt}/{RETRIES})")
            time.sleep(wait)
    raise AssertionError("unreachable")


def words_of(client: httpx.Client, page: int) -> list[tuple[int, int, int, int, int, str]]:
    """The words the API files under one page, as (page, line, surah, ayah, position, text).
    It files a verse by where it starts in one printing, so a verse running over
    a page break brings words that belong to the next page; each word's own page
    is kept, and build() sorts them onto their pages. An ayah's end mark is a word
    too: its number, which the font draws in its circle."""
    words = []
    next_page = 1
    while next_page:
        payload = _get(
            client, f"/verses/by_page/{page}", words="true", per_page=50, page=next_page,
            word_fields="text_qpc_hafs,line_v2,v2_page,position", fields="verse_key",
        )
        for verse in payload["verses"]:
            surah, ayah = (int(n) for n in verse["verse_key"].split(":"))
            for word in verse["words"]:
                words.append((word["v2_page"], word["line_v2"], surah, ayah, word["position"], word["text_qpc_hafs"]))
        next_page = (payload.get("pagination") or {}).get("next_page")
        time.sleep(PAUSE_SECONDS)
    return words


def lines_of(page: int, words: list[tuple[int, int, int, str]], carried: int) -> tuple[list[list], int]:
    """One page's lines, each one of:
         ["ayah", [[surah, ayah, "word word …"], …]]   runs of one ayah's words
         ["surah", surah]                                 the surah's name
         ["basmala"]
    A surah can begin at the foot of a page with its name, its basmala and first
    ayah overleaf (page 76 → 77). `carried` is how many of the next surah's header
    lines the last page already printed; the count this page leaves is returned.
    """
    by_line: dict[int, list[list]] = {}
    for line, surah, ayah, text in words:
        runs = by_line.setdefault(line, [])
        if runs and runs[-1][0] == surah and runs[-1][1] == ayah:
            runs[-1][2] += " " + text
        else:
            runs.append([surah, ayah, text])
    total = lines_on(page)
    if not set(by_line) <= set(range(1, total + 1)):
        raise ValueError(f"page {page}: line numbers {sorted(by_line)} outside 1..{total}")
    last = max(by_line)
    next_surah = by_line[last][-1][0] + 1
    lines: list[list] = []
    n = 1
    while n <= total:
        if n in by_line:
            lines.append(["ayah", by_line[n]])
            n += 1
            continue
        gap_end = n
        while gap_end <= total and gap_end not in by_line:
            gap_end += 1
        after = by_line.get(gap_end)
        surah = after[0][0] if after else next_surah
        if after and after[0][1] != 1:
            raise ValueError(f"page {page}: lines {n}-{gap_end - 1} are empty and no surah starts after them")
        header = [["surah", surah]] + ([] if surah in NO_BASMALA_LINE else [["basmala"]])
        printed = carried if n == 1 else 0
        left = header[printed:] if after else header[:gap_end - n]
        if len(left) != gap_end - n:
            raise ValueError(f"page {page}: {gap_end - n} empty lines before surah {surah}, expected {len(left)}")
        lines.extend(left)
        n = gap_end
    return lines, (total - last if last < total else 0)


def build() -> None:
    pages: list[list] = []
    with httpx.Client() as client:
        every = set()
        for page in range(1, TOTAL_PAGES + 1):
            every.update(words_of(client, page))
            if page % 50 == 0:
                print(f"  page {page}")
    on_page: dict[int, list] = {}
    for page, line, surah, ayah, position, text in sorted(every, key=lambda w: (w[2], w[3], w[4])):
        on_page.setdefault(page, []).append((line, surah, ayah, text))
    if len({(w[2], w[3]) for w in every}) != AYAHS:
        raise SystemExit(f"Not every ayah came back: {len({(w[2], w[3]) for w in every})} of {AYAHS}")
    if sorted(on_page) != list(range(1, TOTAL_PAGES + 1)):
        raise SystemExit(f"Not every page has words: {TOTAL_PAGES - len(on_page)} missing")
    carried = 0
    for page in range(1, TOTAL_PAGES + 1):
        lines, carried = lines_of(page, on_page[page], carried)
        pages.append(lines)

    names = [line[1] for page in pages for line in page if line[0] == "surah"]
    basmalas = sum(1 for page in pages for line in page if line[0] == "basmala")
    if names != list(range(1, SURAHS + 1)) or basmalas != SURAHS - len(NO_BASMALA_LINE):
        raise SystemExit(f"Not the whole printing: {len(names)} surah names, {basmalas} basmalas")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUT.with_suffix(".building")
    payload = {
        "_about": "Madani 1421 (KFGQPC V2), 604 pages. Built by backend/scripts/quran/build_mushaf.py from "
                  "api.quran.com (line_v2, text_qpc_hafs); read only by backend/services/quran/mushaf.py.",
        "pages": pages,
    }
    temporary.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    temporary.replace(OUT)
    print(f"Built {OUT}: {TOTAL_PAGES} pages, {len(names)} surahs")


if __name__ == "__main__":
    try:
        build()
    except Exception as exc:  # noqa: BLE001, a build script reports and stops
        sys.exit(f"Build failed: {exc}")
