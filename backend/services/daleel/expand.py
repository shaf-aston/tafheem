"""Turn what someone typed into the terms worth searching for. Pure.

This is the whole of Daleel's "understands what you meant", and there is no
intelligence in it. It is four lookups in mappings that already exist:

  root      كتاب and كاتب and مكتوب are one root, ك-ت-ب. Arabic says so itself;
            the corpus already has the root on every word.
  synonym   the dictionary already lists them, entry by entry.
  English   the dictionary is already indexed both ways, so an English word
            reaches the Arabic ones it defines.
  trigram   a misspelling shares most of its three-letter runs with the word
            that was meant. SQLite's own index does this; nothing is computed
            here beyond deciding a query is long enough to be worth it.

Nothing in this file reads a file, opens a database or calls anything over a
network. The mappings arrive as a Lexicon the caller supplies, which is what
lets the whole of this be tested against a handful of made-up words and lets
search.py decide, once, where the real ones come from.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from backend.services.arabic_text import bare_letters, has_arabic, normalize_root


# Words that carry no question. Asked as they are, each one is looked up in the
# dictionary and comes back with six Arabic words of its own, so "what does the
# Qur'an say about patience" was searched as roughly forty terms and took three
# seconds to answer something the last two words already asked. They are the
# English words with no Arabic content, nothing cleverer than that; the list is
# deliberately short, because a word wrongly on it is a word nobody can search
# for.
_NOISE = frozenset("""
a an and are as at be but by can did do does for from had has have how i if in
is it its me my no not of on or say says shall should so than that the their
them then there these they this to was we were what when where which who why
will with would you your
""".split())


class Lexicon(Protocol):
    """The already-made mappings, however the caller happens to hold them."""

    def root_of(self, word: str) -> str:
        """The word's root, or "" when nothing knows it."""
        ...

    def synonyms_of(self, word: str) -> tuple[str, ...]:
        """Words the dictionary lists as meaning the same thing."""
        ...

    def arabic_for(self, english_word: str) -> tuple[str, ...]:
        """Arabic words this English word is used to define."""
        ...


@dataclass(frozen=True)
class Expansion:
    """What to look for, split by how strong a match each kind counts as.

    Kept apart rather than merged into one list because the difference is what
    the reader is told: a `typed` hit is a clean find and a `loose` hit is
    "this is probably what you meant", and the screen must not present the
    second as the first.

    `related` earns its own field the hard way. When synonyms were treated as
    equal to the typed word, searching كتب put Ibn Faris on رسم at the top,
    because رسم is a listed synonym and his entry uses it as a whole word. A
    synonym is worth searching for and is not worth outranking the word
    somebody actually typed.
    """

    typed: tuple[str, ...]
    related: tuple[str, ...]
    roots: tuple[str, ...]
    loose: tuple[str, ...]

    def is_empty(self) -> bool:
        return not (self.typed or self.related or self.roots or self.loose)

    @property
    def all_terms(self) -> tuple[str, ...]:
        """Every word worth putting to the index, strongest first."""
        return (*self.typed, *self.related)


def expand(
    query: str,
    lexicon: Lexicon,
    *,
    max_expand: int,
    max_translations: int,
    min_trigram_len: int,
) -> Expansion:
    """The terms worth searching for, given what was typed.

    `max_expand` caps the fan-out per word. A word like قول has a large family
    and a large synonym list, and without a cap one ordinary question becomes a
    hundred-term search that finds everything and therefore means nothing.
    `max_translations` is the same cap for an English word's Arabic.
    """
    words = _words(query)

    if content := [word for word in words if word not in _NOISE]:
        words = tuple(content)

    typed: list[str] = []
    related: list[str] = []
    roots: list[str] = []
    loose: list[str] = []

    for word in words:
        _add(typed, word)

        if has_arabic(word):
            if root := normalize_root(lexicon.root_of(word) or word):
                _add(roots, root)
            for synonym in lexicon.synonyms_of(word)[:max_expand]:
                _add(related, bare_letters(synonym))
        else:
            # Single-word translations first, so the cap keeps them. An idiom
            # the dictionary files under the word (لا سمح الله under "god")
            # contains it rather than translates it.
            arabic_words = sorted((bare_letters(a) for a in lexicon.arabic_for(word)),
                                  key=lambda a: " " in a)
            for folded in arabic_words[:max_translations]:
                # Folded before the root is asked for, not after: every other
                # lookup here is made on the folded spelling, and asking this
                # one on the book's spelling made أب and اب two different words.
                _add(related, folded)
                # A root belongs to one word, as on the Arabic side. Asked of a
                # phrase, the lookup fell back to the phrase with its spaces
                # squeezed out, and "god" searched for انشاءالربوعشنا as a root.
                if " " in folded:
                    continue
                if root := normalize_root(lexicon.root_of(folded) or folded):
                    _add(roots, root)

        # Short words share their three-letter runs with far too much to be
        # worth matching loosely, so they are only ever matched exactly.
        if len(word) >= min_trigram_len:
            _add(loose, word)

    # A word cannot be both. If someone typed it, that is what it is.
    related = [term for term in related if term not in typed]

    return Expansion(tuple(typed), tuple(related), tuple(roots), tuple(loose))


def _words(query: str) -> tuple[str, ...]:
    """The query as separate words, folded, in the order they were typed.

    Folding here rather than at each use means a word is compared in exactly
    one spelling, whichever of the several ways Arabic writes it was typed.
    """
    folded = bare_letters(query).strip().lower()
    seen: list[str] = []
    for word in folded.split():
        _add(seen, word)
    return tuple(seen)


def _add(into: list[str], value: str) -> None:
    """Append when it is worth appending. Order kept, duplicates dropped."""
    value = value.strip()
    if value and value not in into:
        into.append(value)
