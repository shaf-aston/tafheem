"""The classical, origin sense of a root; what the lughawi books say three
letters have meant before any one word was built from them.

This is not the dictionary. The dictionary says what a *word* means today; this
says what the *root* has meant since the beginning. They answer different
questions, so they are kept apart rather than merged into one search.

The book is not shipped. Ibn Faris's Maqayees al-Lugha is being extracted
separately, and until that lands there is nothing here to read. This module is
the seam it drops into: one shape a provider must satisfy, one factory, one
JSON-file reader. A different book, or a second one, means writing another
provider, not touching the router, the response, or the UI.

Nothing here ever invents a meaning. A root the book does not cover comes back
empty and says so; a book that is not installed says *that*, which is a
different sentence and must never be shown as the first one.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from backend.config import get_settings
from backend.services.arabic_text import normalize_root
from backend.services import root_english, root_gloss

logger = logging.getLogger(__name__)

_BACKEND_ROOT = Path(__file__).resolve().parent.parent

# What the file can be in. Reported as-is so the reader is told which of the
# three situations they are in, never a guess that flatters the app:
#   missing, no file on this machine; the book was never installed
#   broken: a file is there but could not be read; something is wrong, say so
#   ready: loaded, and a miss really means the book has no entry
MISSING, BROKEN, READY = "missing", "broken", "ready"


class RootMeaningProvider(Protocol):
    """What any classical-meaning book must be able to do."""

    source_key: str

    def load(self) -> None:
        """Read the book into memory. Called once at startup, never per request."""

    def status(self) -> str:
        """MISSING, BROKEN or READY; see above."""

    def resolve(self, root: str) -> str | None:
        """The spelling the book files this root under, or None if it has none."""

    def lookup(self, root: str) -> dict | None:
        """This root's entry, or None if the book does not cover it."""

    def roots(self) -> list[str]:
        """Every root the book files, under the spelling it files them by.

        For work that goes through the whole book, putting the entries into
        English ahead of time, so nothing has to reach past this interface into
        how a particular book happens to be stored.
        """


SPELLING_FILE = "spelling.json"


def read_fold(folder: Path) -> dict[int, int]:
    """Which spellings count as the same letter, as a str.translate table.

    Kept beside the book rather than in code, and read by the builder too, so
    the file and the search can never disagree about what أ and ا are. Absent is
    not fatal: searches then match only the spelling the book itself uses, and
    the log says so rather than the app quietly finding less.
    """
    path = folder / SPELLING_FILE
    try:
        fold = json.loads(path.read_text(encoding="utf-8"))["fold"]
        return str.maketrans({k: v for k, v in fold.items() if isinstance(v, str)})
    # AttributeError included on purpose: a "fold" that is a list or a string has
    # no .items(), and without it that one shape escapes to load()'s catch-all
    # and reports the book itself as unreadable, blaming a file that is fine.
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        logger.warning(
            "No usable %s beside the book (%s): a root will only be found under the "
            "exact spelling the book uses", path, exc,
        )
        return {}


def _line(value: object) -> str:
    """One line of the book, or nothing.

    Only text counts as text. A number or a nested list is the file being the
    wrong shape, and str() would print `['a', 'b']` in Arabic type with Ibn
    Faris's name under it.
    """
    return value.strip() if isinstance(value, str) else ""


class JsonFileProvider:
    """A book kept as one JSON file: {"ك ت ب": {core_meaning, sarf_pattern, variances}}.

    The whole file is read at startup, not on the first click, so the first
    lookup after installing it is instant rather than stalling on a parse.
    """

    source_key = "maqayees"

    def __init__(self, path: Path) -> None:
        self._path = path
        self._entries: dict[str, dict] = {}
        self._folded: dict[str, str] = {}
        self._fold: dict[int, int] = {}
        self._status = MISSING

    def load(self) -> None:
        """Read the book, and never fail silently into "not installed".

        Any unexpected failure here is the book being broken, not absent. The
        two get different sentences on screen, and the wrong one would tell the
        reader to go and install a file that is already sitting there.
        """
        try:
            self._read()
        except Exception as exc:  # noqa: BLE001, every failure is "broken", never "missing"
            self._status = BROKEN
            self._entries = {}
            logger.warning("Classical root book at %s could not be loaded: %s", self._path, exc)

    def _read(self) -> None:
        # is_file, not exists: a folder path; the likeliest way to mistype the
        # one setting, is no book at all, and must not read as an unreadable one.
        if not self._path.is_file():
            self._status = MISSING
            logger.info("No classical root book at %s, the panel will say so", self._path)
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            self._status = BROKEN
            logger.warning("Classical root book at %s could not be read: %s", self._path, exc)
            return
        if not isinstance(raw, dict):
            self._status = BROKEN
            logger.warning(
                "Classical root book at %s must be an object keyed by root, not %s",
                self._path, type(raw).__name__,
            )
            return
        # One spelling per root, so the letters typed in the box match the letters
        # printed in the book however either side wrote the separators.
        self._entries = {
            key: entry for root, entry in raw.items()
            if isinstance(entry, dict) and (key := normalize_root(root))
        }
        self._folded = self._index_by_folded_spelling()
        self._status = READY
        # Counting only the keys that differ: every root trivially folds onto
        # itself, so the raw size of the index would be a number that cannot fail
        # and would tell someone debugging the fold nothing.
        alternates = sum(folded != owner for folded, owner in self._folded.items())
        logger.info(
            "Loaded %d classical root entries, %d of them also findable under a second spelling",
            len(self._entries), alternates,
        )

    def _index_by_folded_spelling(self) -> dict[str, str]:
        """A second way in, for a reader who writes هدى where the book wrote هدي.

        Built once at startup, and only where the answer is beyond doubt: two
        roots that fold together are two different roots, هنأ and هنا, and
        neither may answer for the other, so the pair is left out entirely
        rather than resolved by whichever happened to be read first.
        """
        self._fold = read_fold(self._path.parent)
        if not self._fold:
            return {}
        claims: dict[str, set[str]] = {}
        for key in self._entries:
            claims.setdefault(key.translate(self._fold), set()).add(key)
        return {
            folded: next(iter(owners))
            for folded, owners in claims.items() if len(owners) == 1
        }

    def status(self) -> str:
        return self._status

    def roots(self) -> list[str]:
        return list(self._entries)

    def resolve(self, root: str) -> str | None:
        """The spelling the book files this root under, or None if it has none.

        The letters typed answer for themselves first. Only when the book has
        nothing under them is a second spelling tried, so a root the book really
        does hold can never be answered by a different one that merely looks
        like it.
        """
        key = normalize_root(root)
        if key in self._entries:
            return key
        return self._folded.get(key.translate(self._fold)) if self._fold else None

    def lookup(self, root: str) -> dict | None:
        key = self.resolve(root)
        entry = self._entries.get(key) if key else None
        if entry is None:
            return None
        # Read the fields by name, and only where they are text. Spreading the
        # file straight through would let one bad row rewrite which root, or
        # which source, the app claims.
        core = _line(entry.get("core_meaning"))
        if not core:
            # Nothing to read is a miss, not an entry: an entry with a blank
            # meaning would print an empty Arabic line under Ibn Faris's name.
            return None
        rows = entry.get("variances")
        return {
            "core_meaning": core,
            "sarf_pattern": _line(entry.get("sarf_pattern")),
            "variances": [line for v in (rows if isinstance(rows, list) else []) if (line := _line(v))],
            "body": _line(entry.get("body")),
            # Kept apart from the Arabic on purpose. This one field was read off
            # a page image rather than typed by a person, and the card badges it
            # as the weaker source; folding it in with the rest would make that
            # impossible to say.
            "english": _line(entry.get("english")),
        }


_provider: RootMeaningProvider | None = None


def get_provider() -> RootMeaningProvider:
    """The classical book this install is using. One per process."""
    global _provider
    if _provider is None:
        configured = Path(get_settings().root_meaning_path)
        _provider = JsonFileProvider(configured if configured.is_absolute() else _BACKEND_ROOT / configured)
    return _provider


def load() -> None:
    """Startup loader, matching the other optional data files."""
    get_provider().load()


def status() -> str:
    return get_provider().status()


def roots() -> list[str]:
    return get_provider().roots()


def resolve(root: str) -> str | None:
    return get_provider().resolve(root)


def lookup(root: str) -> dict | None:
    return get_provider().lookup(root)


@dataclass(frozen=True)
class Entry:
    """A root's entry, ready to be shown, with every credit already decided.

    Not a Pydantic model on purpose. Schemas are the web layer's vocabulary, and
    the whole point of this type is that the decision below no longer depends on
    the web layer to make it.
    """

    # The spelling the book files this entry under, sent only when it is not the
    # one that was typed. Naming the same letters back would read as a
    # correction that was never made.
    book_root: str | None
    meaning: dict
    # Who to credit for the Arabic, and separately for the English beside it.
    # One badge over both would vouch for the weaker with the authority of the
    # stronger, which is the thing this app promises never to do.
    source_key: str
    english_source_key: str | None


def entry_for(key: str) -> Entry | None:
    """The book's entry for these letters, with the better English already chosen.

    There can be two English glosses of the same sentence and they are not worth
    the same. Where the whole entry has already been put into English from the
    typed Arabic, its opening sentence is that gloss, made properly, so it beats
    the one a model read off a photograph of the page, and it carries the better
    badge. That judgement is about the book, so it lives here beside the book and
    not in whatever happens to be asking.

    None means the book has no entry under these letters. It is not the same
    answer as `status()` saying the book is not installed at all.
    """
    filed_under = resolve(key)
    entry = lookup(key)
    if entry is None:
        return None

    read_from_the_book = root_gloss.opening_of(root_english.get(filed_under or key) or "")
    if read_from_the_book:
        entry["english"] = read_from_the_book

    return Entry(
        book_root=filed_under if filed_under != key else None,
        meaning=entry,
        source_key=get_provider().source_key,
        english_source_key=(
            ("maqayees_translation" if read_from_the_book else "maqayees_english")
            if entry.get("english") else None
        ),
    )
