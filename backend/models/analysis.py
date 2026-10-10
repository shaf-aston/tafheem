"""Request and reply types for routers/analysis.py."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models.common import Source
from backend.models.tarkeeb import TarkeebTree
from backend.services.arabic_text import shown_root


# Trust-boundary caps: user text flows into LLM prompts and NLP engines, 
# unbounded input is a token-cost / latency attack surface. Reject loud (422).
class AnalyzeRequest(BaseModel):
    sentence: str = Field(min_length=1, max_length=2000)


# Every role name the word grid knows how to colour. The role itself is written
# in Arabic for the reader; this is the stable name beside it, the same idea as
# a tarkeeb node's `tone`. The frontend owns the actual colours (`role.*` in
# theme.json), this list only says which roles exist.
ROLE_KEYS = frozenset({
    "fil",      # the verb
    "fail",     # doer; and the pronoun standing in for one
    "mubtada",  # subject of a nominal sentence, and the ism of inna
    "khabar",   # what is said about it
    "mafool",   # object
    "sifah",    # na't / adjective following its noun
    "haal",     # circumstantial
    "mudaf",    # first of a genitive pair
    "harf",     # particle, and whatever it governs
    "mansub",   # the other nasb extras: time and place, the called, the excepted
    "tabi",     # a follower that copies the word before it: عطف, توكيد, بدل
})


# Every word type a card can carry, as frontend/src/grammar.json `types` names them
# (punc is the one the page never labels). tests/test_rule_engine.py holds the two together.
WORD_TYPES = frozenset({"ism", "fi'l", "harf", "damir", "zarf", "punc"})


class WordAnalysis(BaseModel):
    word: str
    root: str | None = None
    type: str | None = None
    role: str | None = None
    # The stable name of that role, for the one job the Arabic prose above cannot
    # do: telling the grid which colour to draw it in. Unset means "not settled",
    # which stays uncoloured rather than being given a plausible colour.
    role_key: str | None = None
    case: str | None = None
    sign: str | None = None
    reason: str | None = None
    notes: str | None = None
    # The book's divisions that named the role (اسم ← ... (تسهيل النحو 3.1 p60)): the proof's source.
    book: str | None = None
    # The typed word this one takes its case from, by index: its عامل, or for a تابع the
    # word it follows. Unset where the parser drew no such word.
    governor: int | None = None
    follows: int | None = None

    @classmethod
    def from_raw(cls, w: dict) -> "WordAnalysis":
        """One card from the analyser's word dict. A colour key or word type the page does
        not know is dropped, so a typo goes uncoloured instead of wearing another role's colour."""
        key = w.get("role_key")
        # A particle has no root in nahw, whatever CAMeL filed for it, and a
        # root that is a code rather than letters is no root at all. Judged by
        # the word's own type: role_key "harf" also covers the noun a
        # preposition governs, which does have a root.
        root = "" if w.get("type") == "harf" else shown_root(w.get("root"))
        return cls(
            word=w.get("word", ""),
            root=root or None,
            type=w.get("type") if w.get("type") in WORD_TYPES else None,
            role=w.get("role"),
            role_key=key if key in ROLE_KEYS else None,
            case=w.get("case"),
            sign=w.get("sign"),
            reason=w.get("reason"),
            notes=w.get("notes"),
            book=w.get("book"),
            governor=w.get("governor"),
            follows=w.get("follows"),
        )


class AnalyzeResponse(BaseModel):
    sentence: str
    words: list[WordAnalysis]
    summary: str | None = None
    source: Source | None = None
    # The same reading drawn as brackets: which words join, and what the unit
    # does. Unset when the parser could join nothing, so the cards stand alone.
    tree: TarkeebTree | None = None
