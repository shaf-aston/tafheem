#!/usr/bin/env python3
"""Render every page of the teacher's Nahw notes to a picture.

The notes are read by eye (several are photographs of handwriting with no text
inside), so every page becomes one PNG. Pictures are derived data: delete the
folder and run this again.

    python backend/scripts/render_note_pages.py <folder with the PDFs> [note-id ...]

Writes `backend/data/nahw_notes/images/<note-id>-NN.png` and prints a line per
note. `notes.json` names each PDF and holds the render knobs; the folder is
given here rather than stored, since it is a path on one person's computer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pypdfium2 as pdfium

ROOT = Path(__file__).resolve().parents[1] / "data" / "nahw_notes"


def manifest() -> dict:
    return json.loads((ROOT / "notes.json").read_text(encoding="utf-8"))


def render(note: dict, source_dir: Path, images: Path, dpi: int, max_width: int) -> int:
    pdf_path = source_dir / note["pdf"]
    if not pdf_path.exists():
        raise SystemExit(f"missing pdf: {pdf_path}")
    pdf = pdfium.PdfDocument(str(pdf_path))
    for i, page in enumerate(pdf):
        scale = dpi / 72
        if page.get_width() * scale > max_width:
            scale = max_width / page.get_width()
        out = images / f"{note['id']}-{i:02d}.png"
        page.render(scale=scale).to_pil().save(out)
    return len(pdf)


def main(source: str, wanted: list[str]) -> None:
    conf = manifest()
    source_dir = Path(source)
    if not source_dir.is_dir():
        raise SystemExit(f"not a folder: {source_dir}")
    images = ROOT / "images"
    images.mkdir(parents=True, exist_ok=True)
    dpi, max_width = conf["render"]["dpi"], conf["render"]["max_width"]
    notes = [n for n in conf["notes"] if not wanted or n["id"] in wanted]
    if wanted and len(notes) != len(wanted):
        raise SystemExit(f"unknown note id in {wanted}")
    total = 0
    for note in notes:
        pages = render(note, source_dir, images, dpi, max_width)
        total += pages
        print(f"{note['id']:28s} {pages:3d} pages")
    print(f"{len(notes)} notes, {total} pages -> {images}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2:])
