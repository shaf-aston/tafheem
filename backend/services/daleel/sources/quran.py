"""The Qur'an as searchable passages, one per ayah.

corpus.db stores a word at a time, in fact a *segment* at a time: بِ and سْمِ
are two rows because the corpus tags the preposition separately from the noun.
An ayah is therefore not stored anywhere as a sentence; it is reassembled here
by putting the segments of each word back together and the words back in order.

The roots come free with it. Every segment row already carries the root its
word belongs to, hand-tagged, so the root list for an ayah is collected in the
same pass rather than worked out again later.
"""
from __future__ import annotations

import sqlite3
from typing import Iterable

from backend.services import quran_corpus, quran_meanings
from backend.services.daleel.sources.model import Passage


class QuranSource:
    """Every ayah of the Qur'an, with the corpus's own roots attached."""

    id = "corpus"

    def passages(self) -> Iterable[Passage]:
        if not quran_corpus.DATABASE.exists():
            return

        english = _english_by_ayah()

        conn = sqlite3.connect(f"file:{quran_corpus.DATABASE}?mode=ro", uri=True)
        try:
            rows = conn.execute(
                "SELECT surah, ayah, word, form, root FROM segment "
                "ORDER BY surah, ayah, word, segment"
            )

            current: tuple[int, int] | None = None
            words: list[str] = []
            roots: list[str] = []
            word_no: int | None = None

            for surah, ayah, word, form, root in rows:
                if current != (surah, ayah):
                    if current is not None:
                        yield _passage(current, words, roots, english)
                    current, words, roots, word_no = (surah, ayah), [], [], None

                # Segments of one word are glued back together; a new word
                # number starts a new word. This is the whole reassembly.
                if word == word_no:
                    words[-1] += form
                else:
                    words.append(form)
                    word_no = word

                if root and root not in roots:
                    roots.append(root)

            if current is not None:
                yield _passage(current, words, roots, english)
        finally:
            conn.close()


def _passage(
    where: tuple[int, int],
    words: list[str],
    roots: list[str],
    english: dict[tuple[int, int], str],
) -> Passage:
    surah, ayah = where
    return Passage(
        source="corpus",
        locator=f"{surah}:{ayah}",
        arabic=" ".join(words),
        english=english.get((surah, ayah), ""),
        roots=" ".join(roots),
    )


def _english_by_ayah() -> dict[tuple[int, int], str]:
    """The word-by-word English, joined back into a line per ayah.

    Read in one go rather than per ayah: it is 77,429 short strings, and one
    query beats 6,236 of them by enough to matter on every rebuild.
    """
    if not quran_meanings.DATABASE.exists():
        return {}

    conn = sqlite3.connect(f"file:{quran_meanings.DATABASE}?mode=ro", uri=True)
    try:
        out: dict[tuple[int, int], list[str]] = {}
        for surah, ayah, en in conn.execute(
            "SELECT surah, ayah, en FROM meaning ORDER BY surah, ayah, word"
        ):
            if en:
                out.setdefault((surah, ayah), []).append(en)
        return {k: " ".join(v) for k, v in out.items()}
    finally:
        conn.close()
