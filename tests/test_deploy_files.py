"""The server gets backend/ and only the frontend files deploy/sync.sh names.

A backend module that reads a frontend file the sync does not copy works on
every laptop and fails on the server: checked practice sentences were a 500
there for exactly this. Every frontend path the backend builds must be one the
sync copies.
"""
import re
from pathlib import Path

from backend.services import sentence_check

ROOT = Path(__file__).resolve().parents[1]
SYNC = (ROOT / "deploy" / "sync.sh").read_text("utf-8")
# "frontend" / "public" / "words" / "words.json", across line breaks.
PATH = re.compile(r'"frontend"((?:\s*/\s*"[^"]+")+)')


def frontend_paths_read():
    found = set()
    for source in (ROOT / "backend").rglob("*.py"):
        # One-off build scripts run on a laptop, not by the server.
        if "scripts" in source.parts:
            continue
        for parts in PATH.findall(source.read_text("utf-8")):
            found.add("/".join(["frontend", *re.findall(r'"([^"]+)"', parts)]))
    # Built from WORDS rather than spelled out, so the pattern above misses it.
    found.add(str(sentence_check.COVERAGE.relative_to(ROOT)))
    return found


def test_the_backend_reads_some_frontend_files():
    assert "frontend/public/words/words.json" in frontend_paths_read()


def test_every_frontend_file_the_backend_reads_is_deployed():
    missing = sorted(path for path in frontend_paths_read() if path not in SYNC)
    assert not missing, f"deploy/sync.sh does not copy {missing}"
