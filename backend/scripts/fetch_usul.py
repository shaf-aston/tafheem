"""Download the narrator books build_usul.py reads, from OpenITI on GitHub.

    python backend/scripts/fetch_usul.py          fetch what is not here yet
    python backend/scripts/fetch_usul.py --again  fetch every book again

The books and where each lives are in data/usul/usul.json (`books`); they are
saved as <key>.txt under usul_books_dir, which git ignores. A book already
there is left alone, so a run costs nothing once they are all here.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.config import data_path  # noqa: E402, needs the path above
from backend.services.usul.rule import rule  # noqa: E402


def fetch(again: bool = False) -> list[Path]:
    """The path of each book, downloading those not on disk (all of them with `again`)."""
    cfg = rule()["books"]
    folder = data_path("usul_books_dir")
    folder.mkdir(parents=True, exist_ok=True)
    saved = []
    for key, book in cfg.items():
        if key == "base":
            continue
        target = folder / f"{key}.txt"
        if again or not target.exists():
            url = cfg["base"] + book["path"]
            print(f"  downloading {key}: {url}")
            reply = httpx.get(url, timeout=rule()["fetch_timeout_seconds"], follow_redirects=True)
            reply.raise_for_status()
            scratch = target.with_suffix(".part")
            scratch.write_bytes(reply.content)
            scratch.replace(target)
        print(f"  {key}: {target.stat().st_size:,} bytes")
        saved.append(target)
    return saved


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--again", action="store_true", help="download every book again")
    fetch(parser.parse_args().again)
