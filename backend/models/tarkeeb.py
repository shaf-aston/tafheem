"""Request and reply types for routers/tarkeeb.py."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models.common import Source


class TarkeebNode(BaseModel):
    """One bracket of the tree.

    It says what a piece **does** (`role`) or what a unit **is** (`label`), and
    has no field for a part of speech, so "it is a noun", which answers a
    different question entirely, cannot be returned from here.

    `word` is set on a leaf and is an index into the ayah's words. `parts` are
    the joins inside a single written word (لِلَّهِ is jarr + majroor). `gap` marks
    a join the rules could not make, which the diagram draws as an open bracket.
    """
    role: str | None = None
    label: str | None = None
    tone: str | None = None
    word: int | None = None
    gap: bool = False
    # A ghair-`aamil` particle, و / ف that opens a new clause, or a bare
    # connective like ثم, governs nothing. It still gets its own name and
    # colour; the rules read this to tell it apart from a real gap.
    ghair_aamil: bool = False
    # True when the wording is the Treebank's own, not one the app checked.
    raw_wording: bool = False
    # A short, plain-language note for the hover/click detail on a role that
    # needs one. Most roles need none, so this stays unset for them.
    detail: str | None = None
    # The pronoun a doer stands for (هو inside كان), which no word writes: the diagram
    # shows it under the doer's name.
    pronoun: str | None = None
    # Understood, not written: the diagram dashes the column (ثابت in الحمد لله, an elided khabar).
    hidden: bool = False
    parts: list["TarkeebNode"] = Field(default_factory=list)
    children: list["TarkeebNode"] = Field(default_factory=list)


class Unwritten(BaseModel):
    """How a word that is understood but not written is shown, and what to call it."""
    mark: str
    note: str


class TarkeebTree(BaseModel):
    # Unset for a sentence someone typed, which belongs to no ayah
    surah: int | None = None
    ayah: int | None = None
    words: list[str]
    # The written word each column was cut from (فَـ لْـ يَصُمْهُ share one), so the
    # chart sets one word's pieces close and its Merged view can fold them back.
    written: list[int] | None = None
    tree: TarkeebNode | None = None
    # The share of words the rules placed in a named unit. The rest are gaps, and
    # this number is what keeps that visible instead of implied.
    coverage: float = 0.0
    unwritten: Unwritten | None = None
    source: Source | None = None


class TarkeebExample(BaseModel):
    """One sentence a book worked out, and the tree it drew for it."""
    id: str
    ref: str            # where in the book it is, so a reader can go and check
    topic: str          # the grammar topic it teaches, how the page is browsed
    sentence: str
    translation: str
    words: list[str]
    tree: TarkeebNode


class TarkeebTopic(BaseModel):
    """A grammar topic examples are browsed by. Shared by every book."""
    key: str
    en: str
    ar: str


class TarkeebExampleBook(BaseModel):
    key: str
    title: str
    detail: str
    examples: list[TarkeebExample]
    source: Source | None = None


class TarkeebExamples(BaseModel):
    """Every worked example the app carries: the shared topics, and the books.

    Topics sit beside the books, not inside them, because they are how the page
    is browsed, one chip gathers the same topic from every book.
    """
    topics: list[TarkeebTopic]
    books: list[TarkeebExampleBook]
