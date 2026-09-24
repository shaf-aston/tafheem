"""Download the marked recitations named in recitation_checks/sources.json.

    python backend/scripts/fetch_recitation_checks.py

Run by hand, once. Public sets, no account. Everything lands in downloads/,
which is never committed.

Each set is fetched as Hugging Face's own parquet copy, a few large files with
the audio and the marks inside. The original is a thousand small files, and
without an account Hugging Face stops answering partway through those.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402

HERE = Path(__file__).resolve().parents[1] / "data" / "recitation_checks"
DOWNLOADS = HERE / "downloads"
PARQUET_LIST = "https://datasets-server.huggingface.co/parquet"
TIMEOUT_S = 120
# Hugging Face also rate-limits an address for a few minutes; wait it out.
WAIT_S = 120
TRIES = 15


def fetch(url: str, to: Path, size: int | None = None) -> None:
    if to.exists() and (size is None or to.stat().st_size == size):
        print(f"    have {to.name}")
        return
    part = to.with_suffix(".part")
    for attempt in range(1, TRIES + 1):
        with httpx.stream("GET", url, follow_redirects=True, timeout=TIMEOUT_S) as got:
            if got.status_code == 429 and attempt < TRIES:
                print(f"    rate limited, waiting {WAIT_S}s ({attempt}/{TRIES})", flush=True)
                time.sleep(WAIT_S)
                continue
            got.raise_for_status()
            with part.open("wb") as out:
                for block in got.iter_bytes(1 << 20):
                    out.write(block)
            break
    # A short file would be read as a smaller set, not as a failed download.
    if size is not None and part.stat().st_size != size:
        raise SystemExit(f"    {to.name} is {part.stat().st_size} bytes, expected {size}")
    part.replace(to)
    print(f"    got {to.name}")


def main() -> None:
    sources = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
    for item in sources["sets"]:
        print(f"  {item['id']} from {item['repo']}")
        listing = httpx.get(PARQUET_LIST, params={"dataset": item["repo"]}, timeout=TIMEOUT_S)
        listing = listing.raise_for_status().json()
        if listing.get("partial") or listing.get("pending") or listing.get("failed"):
            raise SystemExit(f"    the parquet copy of {item['repo']} is incomplete; nothing fetched")
        folder = DOWNLOADS / item["id"]
        folder.mkdir(parents=True, exist_ok=True)
        for part in listing["parquet_files"]:
            fetch(part["url"], folder / f"{part['split']}-{part['filename']}", part["size"])

    text = sources["text"]
    verses = httpx.get(text["url"], timeout=TIMEOUT_S).raise_for_status().json()["verses"]
    # 6,236 ayahs; fewer means a short answer, and a missing ayah would score as a mistake.
    if len(verses) != 6236:
        raise SystemExit(f"  {text['id']} came back with {len(verses)} ayahs, not 6236; nothing written")
    ayahs = {v["verse_key"]: v["text_imlaei"] for v in verses}
    data_path("quran_imlaei_path").write_text(json.dumps(ayahs, ensure_ascii=False), encoding="utf-8")
    print(f"  {text['id']}: {len(ayahs)} ayahs")


if __name__ == "__main__":
    main()
