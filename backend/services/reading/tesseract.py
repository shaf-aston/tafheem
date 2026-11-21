"""Tesseract, on this computer: a picture's Arabic as text, with how sure it is of it.

The program, not a Python binding: one process a picture, its TSV output read here, so nothing
is added to the server but the apt packages (deploy/setup.sh: tesseract-ocr tesseract-ocr-ara).
"""
from __future__ import annotations

import csv
import io
import logging
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from functools import lru_cache

from backend.config import get_settings

logger = logging.getLogger(__name__)

# One thread each: the server runs several processes, and Tesseract's own threads on top of
# them only fight over the same cores (its docs advise this for parallel runs).
_ENV = {**os.environ, "OMP_THREAD_LIMIT": "1"}


@dataclass(frozen=True)
class Reading:
    text: str
    confidence: float  # the mean of its words' own confidences, 0-100; 0 when it found no words


@lru_cache(maxsize=1)
def available() -> bool:
    """Tesseract is installed and has its Arabic. Asked once a run: neither appears while it runs."""
    if not shutil.which("tesseract"):
        return False
    try:
        listed = subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("page reader  tesseract would not start: %s", exc)
        return False
    return "ara" in listed.stdout.split()


def read(picture: bytes) -> Reading | None:
    """Its reading of the picture, or None when Tesseract failed or ran out of time (logged): the
    vision model may still read it, so a failure here is not the request's."""
    try:
        done = subprocess.run(
            ["tesseract", "stdin", "stdout", "-l", "ara", "tsv"],
            input=picture, capture_output=True, timeout=get_settings().read_seconds, env=_ENV, check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("page reader  tesseract failed on a picture: %s", exc)
        return None
    return from_tsv(done.stdout.decode("utf-8", "replace"))


_TURN = re.compile(r"^Rotate: (\d+)", re.M)
_TURN_SURE = re.compile(r"^Orientation confidence: ([\d.]+)", re.M)
# Tesseract's own guide: an orientation guess under about 2 is no guess.
_SURE_ENOUGH = 2.0


def upright(picture: bytes) -> int:
    """How far to turn the picture, counter-clockwise, for its text to stand upright: 0, 90, 180 or 270.
    Tesseract's orientation check (--psm 0, its osd data), about a second; 0 when unsure or it failed."""
    try:
        done = subprocess.run(
            ["tesseract", "stdin", "stdout", "--psm", "0"],
            input=picture, capture_output=True, timeout=get_settings().read_seconds, env=_ENV, check=True,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        logger.info("page reader  no orientation for a picture: %s", exc)
        return 0
    said = done.stdout.decode("utf-8", "replace")
    turn, sure = _TURN.search(said), _TURN_SURE.search(said)
    if not turn or not sure or float(sure.group(1)) < _SURE_ENOUGH:
        return 0
    return (360 - int(turn.group(1))) % 360


def from_tsv(tsv: str) -> Reading:
    """Its words back into lines and paragraphs, as they sat on the page, and their mean confidence.

    A row is a word when its level is 5; block, paragraph and line number say where it sat.
    """
    paragraphs: dict[tuple[str, str], dict[str, list[str]]] = {}
    sure: list[float] = []
    for row in csv.DictReader(io.StringIO(tsv), delimiter="\t", quoting=csv.QUOTE_NONE):
        word = (row.get("text") or "").strip()
        if row.get("level") != "5" or not word:
            continue
        lines = paragraphs.setdefault((row["block_num"], row["par_num"]), {})
        lines.setdefault(row["line_num"], []).append(word)
        sure.append(max(float(row.get("conf") or 0), 0.0))
    text = "\n\n".join("\n".join(" ".join(words) for words in lines.values()) for lines in paragraphs.values())
    return Reading(text=text, confidence=sum(sure) / len(sure) if sure else 0.0)
