"""Request and reply types for routers/quran.py."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models.common import Correction, Source


class WordSegment(BaseModel):
    """One piece of a word, a prefix, the word itself, an ending."""
    arabic: str
    grammar: list[str] = Field(default_factory=list)


class QuranWord(BaseModel):
    position: str
    arabic: str
    pos: str | None = None
    root: str | None = None
    lemma: str | None = None
    grammar: list[str] = Field(default_factory=list)   # plain-English grammar
    segments: list[WordSegment] = Field(default_factory=list)
    meaning: str | None = None   # word-by-word English
    uthmani: str | None = None   # printed spelling, waqf marks included


class QuranAyah(BaseModel):
    surah: int
    ayah: int
    arabic_text: str
    words: list[QuranWord]
    end_mark: str | None = None   # the ring-and-number that closes the printed ayah
    source: Source | None = None


class RootForm(BaseModel):
    lemma: str
    pos: str
    uses: int


class RootOccurrence(BaseModel):
    surah: int
    ayah: int
    arabic: str
    grammar: list[str] = Field(default_factory=list)


class RootResponse(BaseModel):
    """Everything the Qur'an does with one root, the link between the tabs."""
    root: str
    total: int
    forms: list[RootForm] = Field(default_factory=list)
    occurrences: list[RootOccurrence] = Field(default_factory=list)
    source: Source | None = None


class SurahAyah(BaseModel):
    """One ayah as the reader sees it. `words` is filled only when the full
    grammar was asked for, reading a surah does not need it, and it is roughly
    fifty times the payload."""
    ayah: int
    arabic: str
    english: str = ""
    words: list[QuranWord] | None = None
    # The page of the 604-page Madani mushaf this ayah begins on. None where the
    # layout has never been built, which is what tells a reader to fall back to
    # sizing a page by word count rather than printing a page number that is a
    # guess. See services/quran_layout.py.
    page: int | None = None


class QuranSurah(BaseModel):
    surah: int
    name_en: str = ""
    name_ar: str = ""
    ayah_count: int
    ayahs: list[SurahAyah]
    source: Source | None = None


class SurahGlosses(BaseModel):
    """A whole surah's word-by-word English, for showing a word's meaning on hover.

    Words in reading order per ayah, not keyed by number, because the reader
    lines them up against the ayah's own words in the same order. An ayah whose
    gloss count does not match its printed words is left out entirely rather
    than shipped to be mis-aligned: the reader then shows that ayah plain.

    Separate from QuranSurah, and small enough to be: al-Baqarah, the longest,
    is 121KB. Folding it into the reading response would put it on every caller
    of that route, including ones that never draw a word.
    """
    surah: int
    ayahs: dict[int, list[str]]
    # Each word's dictionary form, same order and same left-out ayahs, for the learnt marks.
    lemmas: dict[int, list[list[str]]] = {}


class Edition(BaseModel):
    """One book of text hung on the ayahs: a tafsir, a translation.

    Described once, for the picker and for the reference list, so that the
    passage shape below does not have to repeat a book's licence on every ayah
    the reader opens.
    """
    id: str
    kind: str
    language: str
    name: str
    short: str
    author: str
    licence: str
    origin: str
    passages: int
    ayahs: int
    source: Source | None = None


class Passage(BaseModel):
    """What one book says about one ayah.

    `covers` is every ayah this same passage was written about. A tafsir often
    takes a run of ayahs together, and a reader shown commentary on ten of them
    is entitled to know that rather than to think it was written about one.
    """
    edition: str
    kind: str
    language: str
    name: str
    author: str
    surah: int
    ayah: int
    # How this passage is cited: the ayah it opens on, "78:1". Stable, and the
    # same string the library stores it under.
    passage: str
    text: str
    covers: list[int]
    source: Source | None = None


class SurahEdition(BaseModel):
    """One book's text for a whole surah, keyed by ayah number.

    A dictionary rather than a list because the caller draws one surah's ayahs
    and looks each one up; ayahs the book says nothing about are simply absent,
    which is what lets a line be drawn only where there is one.
    """
    surah: int
    edition: str
    ayahs: dict[int, str]


class AyahEditions(BaseModel):
    """Every book that has something on one ayah, in the library's own order."""
    surah: int
    ayah: int
    passages: list[Passage]


class QuranSearchResult(BaseModel):
    surah: int
    ayah: int
    arabic_text: str
    # Which of the two searches found it: the hand-tagged corpus on this
    # machine, or Quran.com over the network. One list can hold either.
    source: Source | None = None


class QuranSearchResponse(BaseModel):
    hits: list[QuranSearchResult]
    # Set when the words as typed found nothing and their likeliest meant words were searched instead.
    corrected: list[Correction] = []


class SimilarPartner(BaseModel):
    """A verse that reads almost like another, with where the two differ."""
    key: str
    surah: int
    ayah: int
    text: str
    diff_self: list[list[int]]   # [start, end) word positions in the asked verse
    diff_other: list[list[int]]  # the same, in this partner
    change_type: str = ""
    sources: list[Source]


class SimilarAyah(BaseModel):
    surah: int
    ayah: int
    text: str
    partners: list[SimilarPartner]


class SimilarGroup(BaseModel):
    id: int
    keys: list[str]
    change_type: str = ""
    sources: list[Source]


class SimilarSurah(BaseModel):
    surah: int
    ayahs: list[int]  # the ayahs of this surah that have a twin
    groups: list[SimilarGroup]
