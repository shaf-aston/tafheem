"""Request and reply types for routers/dictionary.py."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models.common import Correction, Source


class Synonym(BaseModel):
    """Another word for one sense, and what that word itself means.

    The meaning is looked up as the entry goes out, not stored: it is the first
    definition of that word's own entry. Empty where the dictionary has no entry
    for it, a phrase or a name, and the app says so rather than guessing.
    """
    word: str
    meaning: str = ""


class VerbForm(BaseModel):
    """One verb built off this entry's spelling, as a named source states it."""
    form: str
    past: str
    babs: list[str] = Field(default_factory=list)


class DictionaryEntry(BaseModel):
    arabic: str
    root: str | None = None
    transliteration: str | None = None
    definitions: list[str] = Field(default_factory=list)
    # Other words meaning the same, one list per definition and in the same
    # order, synonyms[2] belongs to definitions[2]. A separate list rather than
    # a field on each definition, so an entry built before synonyms existed is
    # still a valid entry with none.
    synonyms: list[list[Synonym]] = Field(default_factory=list)
    verbs: list[VerbForm] = Field(default_factory=list)


class ReadAs(BaseModel):
    """A typed word that is no headword, and the word and root it was read as (services/morphology.py)."""
    typed: str
    lemma: str  # "" when only its root was found
    root: str


class DictionaryResponse(BaseModel):
    query: str
    lang: str
    results: list[DictionaryEntry]
    source: Source | None = None
    # Set when the word as typed found nothing and its likeliest meant word was looked up instead.
    corrected: list[Correction] = []
    # Set when the word as typed is a form of another (مُنْتَصِرًا of مُنْتَصِر), found that way.
    read_as: ReadAs | None = None
    # The root of the word as typed, when the search knows it: what the root cards ask about.
    root: str = ""


class SentenceWord(BaseModel):
    arabic: str
    english: str
    base: str  # the word without its joined pieces, what the dictionary looks up


class SentenceResponse(BaseModel):
    """A phrase or sentence asked of the dictionary: its sense, then word by word.

    `meaning` is None when nothing could give a sense; the words still stand.
    `ref` names the ayah when the text was one whole ayah; `left_out` is what was
    typed as a word but holds no Arabic, so it was not translated."""

    query: str
    kind: str  # word | phrase | sentence
    meaning: str | None = None
    source: Source | None = None
    ref: str | None = None
    words: list[SentenceWord]
    words_source: Source
    left_out: list[str] = []


class RootMeaning(BaseModel):
    core_meaning: str
    sarf_pattern: str = ""
    variances: list[str] = Field(default_factory=list)
    # The rest of the entry after the origin sense (services/root_gloss.rest_of):
    # the examples, the Qur'an verses and their references, the poetry. Prose,
    # never split into senses: Ibn Faris marks where one ends in only a minority.
    rest: str = ""
    # A plain English gloss of the origin sense. Read off a page image by a
    # machine, unlike everything above it, so it carries its own weaker badge on
    # the card and must never be presented as the book's own words.
    english: str = ""


class RootMeaningResponse(BaseModel):
    """A root's classical origin sense, and, when there isn't one, which kind of
    nothing it is. "The book isn't installed" and "the book has no entry for this
    root" are different sentences and are never allowed to look the same."""

    root: str          # the exact letters searched, so a mismatch is visible
    status: str        # missing | broken | ready, see services/root_meaning.py
    # The spelling the book itself files this entry under, sent only when it is
    # not the one searched. Typing بدا reaches the entry printed بدأ, and without
    # saying so the reader takes an answer about one root as an answer about the
    # letters they typed.
    book_root: str | None = None
    meaning: RootMeaning | None = None
    source: Source | None = None
    # A second badge, for the one field that came from somewhere weaker. Sent
    # only when there is English to badge, so the card never shows a credit for
    # something it is not displaying.
    english_source: Source | None = None


class LexiconEntry(BaseModel):
    """One dictionary's whole entry for a root, as that dictionary wrote it."""

    book: str          # lisan | taj | maqayis | lane
    title: str         # the book's own name, in its own language
    english: str       # what that name means, for a reader who cannot read it
    author: str
    died: int | None = None   # the year the author died, AH for the Arabic books
    language: str      # ar | en, which decides how the entry is set on the page
    # The spelling this book files the root under, sent only when it differs from
    # the letters searched, so "filed under أمر" can be said rather than leaving
    # the reader to wonder why the letters changed.
    book_root: str | None = None
    text: str
    source: Source


class LexiconsResponse(BaseModel):
    """What the classical dictionaries say about one root.

    Empty entries with status ready means the books were read and none of them
    covers this root. That is a fact about the root; "missing" is a fact about
    this machine. The two must never be shown as the same sentence.
    """

    root: str
    status: str        # missing | broken | ready, see services/lexicons.py
    entries: list[LexiconEntry] = []


class RootEntryEnglishResponse(BaseModel):
    """A whole Maqayees entry retold in English, asked for one root at a time.

    Deliberately not part of RootMeaningResponse. The entry above it is the
    book's own words; this is a machine reading them, it costs a call to make,
    and it is only ever fetched because a reader asked for it. Keeping it a
    separate answer keeps those two apart on the wire as well as on the page."""

    root: str
    english: str
    # True when the entry was longer than the model was given. The card says so:
    # a retelling that stops early must not look like the whole entry.
    truncated: bool = False
    source: Source


class EntryLine(BaseModel):
    """One line of the entry with its English, paired on the wire.

    Paired here, not on the screen: only the backend splits the Arabic, so the
    two sides cannot drift and put a translation under the wrong line."""

    arabic: str
    english: str


class RootEntryLinesResponse(BaseModel):
    """The rest of a Maqayees entry, one English line under each Arabic line.

    Only ever sent with as many English lines as Arabic ones: an answer that
    could not be lined up is refused by the backend, and the card falls back to
    the prose reading it already has."""

    root: str
    lines: list[EntryLine]
    # True when the entry was longer than the model was given: the lines cover
    # its opening, and the card says so.
    truncated: bool = False
    source: Source
