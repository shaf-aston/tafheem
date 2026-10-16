"""The raw sunnah.com pages kept on disk (gzip), shared by the fetch and build scripts.

An empty file means the site said the page does not exist; it is kept so a
resumed fetch does not ask again.
"""
from __future__ import annotations

import gzip
import os
from pathlib import Path

from backend.config import data_path


def book_path(collection: str, book: int) -> Path:
    return data_path("rijal_pages_dir") / "books" / f"{collection}-{book}.html.gz"


def narrator_path(narrator_id: int) -> Path:
    return data_path("rijal_pages_dir") / "narrators" / f"{narrator_id}.html.gz"


def book_pages() -> list[tuple[str, int, Path]]:
    """(collection, book, file) of every cached book page."""
    found = []
    for file in sorted(book_path("", 0).parent.glob("*.html.gz")):
        collection, _, book = file.name.removesuffix(".html.gz").rpartition("-")
        found.append((collection, int(book), file))
    return found


def narrator_pages() -> list[tuple[int, Path]]:
    """(id, file) of every cached narrator page."""
    return [(int(f.name.removesuffix(".html.gz")), f) for f in sorted(narrator_path(0).parent.glob("*.html.gz"))]


def read(path: Path) -> str:
    return gzip.decompress(path.read_bytes()).decode("utf-8")


def write(path: Path, html: str) -> None:
    """Whole or not at all, so a stopped run never leaves a half page to be trusted."""
    path.parent.mkdir(parents=True, exist_ok=True)
    scratch = path.with_name(path.name + ".part")
    scratch.write_bytes(gzip.compress(html.encode("utf-8")))
    os.replace(scratch, path)
