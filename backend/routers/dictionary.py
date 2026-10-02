"""Arabic-English dictionary search."""

import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.config import get_settings
from backend.models.schemas import (
    DictionaryEntry,
    DictionaryResponse,
    EntryLine,
    LexiconEntry,
    LexiconsResponse,
    RootEntryEnglishResponse,
    RootEntryLinesResponse,
    RootMeaning,
    RootMeaningResponse,
    Source,
    VerbVerdict,
)
from backend.services import ai as ai_service
from backend.services import (
    dictionary_service,
    lexicons,
    provenance,
    root_english,
    root_gloss,
    root_meaning,
    verb_forms,
)
from backend.services.arabic_text import normalize_root, spelled_out
from backend.utils import call_service, normalize_text, require_arabic

router = APIRouter(prefix="/api/dictionary", tags=["dictionary"])

_SEARCHERS = {
    "ar": dictionary_service.search_arabic,
    "en": dictionary_service.search_english,
}

_ARABIC_UNHARMED = "The Arabic above is unaffected."


def _root_key(
    root: str = Query(..., min_length=1, max_length=50, description="Arabic root letters"),
) -> str:
    """The root as every handler here asks about it.

    Checked for Arabic before normalising, because normalising drops everything
    that is not an Arabic letter: "ktb" would otherwise come back as "the book
    has no entry under those letters", a claim about the book rather than about
    the question.
    """
    typed = normalize_text(root, "Root")
    require_arabic(typed, "Root")
    return normalize_root(typed)


RootKey = Annotated[str, Depends(_root_key)]


@router.get("/search", response_model=DictionaryResponse)
async def search_dictionary(
    q: str = Query(..., min_length=1, max_length=200, description="Search query"),
    lang: str = Query("ar", description="Search language: 'ar' for Arabic, 'en' for English"),
) -> DictionaryResponse:
    # The answer carries the joined word, and the two classical cards ask about
    # the query the answer names, so all three read one spelling.
    query = spelled_out(normalize_text(q, "Search query"))
    language = lang.strip().lower()

    searcher = _SEARCHERS.get(language)
    if searcher is None:
        raise HTTPException(status_code=400, detail="lang must be 'ar' or 'en'")

    # A worker thread: an uncached fuzzy search scans every headword.
    found = await asyncio.to_thread(searcher, query)
    return DictionaryResponse(
        query=query,
        lang=language,
        results=[DictionaryEntry(**entry) for entry in found],
        source=Source(**provenance.of("wiktionary")),
    )


@router.get("/babs", response_model=VerbVerdict)
async def get_root_babs(key: RootKey) -> VerbVerdict:
    """The باب a root's Form I verb takes, as Lane and Wiktionary state it.

    Asked by root, not by the word on screen, so every word on the root shows
    the same fact. No readings means no source records one.
    """
    return VerbVerdict.of(await asyncio.to_thread(verb_forms.babs_of, key))


@router.get("/root-meaning", response_model=RootMeaningResponse)
async def get_root_meaning(key: RootKey) -> RootMeaningResponse:
    """What the classical books say this root means at its origin.

    Answers with the letters it actually searched, so a root written one way here
    and another way in the book shows up as a mismatch rather than as silence.
    """
    state = root_meaning.status()
    if state != root_meaning.READY:
        return RootMeaningResponse(root=key, status=state)

    entry = root_meaning.entry_for(key)
    if entry is None:
        # No entry means no book to credit: a source badge with nothing above it
        # reads as though the book had been consulted and had answered.
        return RootMeaningResponse(root=key, status=state)

    return RootMeaningResponse(
        root=key,
        status=state,
        book_root=entry.book_root,
        meaning=RootMeaning(**entry.meaning, rest=root_gloss.rest_of(entry.meaning)),
        source=Source(**provenance.of(entry.source_key)),
        english_source=(
            Source(**provenance.of(entry.english_source_key))
            if entry.english_source_key else None
        ),
    )


@router.get("/lexicons", response_model=LexiconsResponse)
async def get_lexicons(key: RootKey) -> LexiconsResponse:
    """Whole entries for this root, from every classical dictionary that has one.

    The long answer to the short one root-meaning gives. Thin on purpose: which
    books exist and how a root is matched to an entry are both decided in
    services/lexicons.py; this hands each entry its book's credit.
    """
    state = lexicons.status()
    # A worker thread: a common root is a hundred kilobytes to unpack.
    found = await asyncio.to_thread(lexicons.entries_for, key) if state == lexicons.READY else []
    if found is None:
        # The database stopped answering mid-read. "No entry" here would be a
        # claim about the books, made because of a failure.
        state, found = lexicons.BROKEN, []

    return LexiconsResponse(
        root=key,
        status=state,
        entries=[
            LexiconEntry(
                **{field: value for field, value in entry.items() if field != "source"},
                source=Source(**provenance.of(entry["source"])),
            )
            for entry in found
        ],
    )


def _book_entry(key: str) -> tuple[str, dict]:
    """(the spelling the book files it under, its entry), or 503 with no book.

    Readings are kept under the book's spelling: a reader who writes هدى where
    the book wrote هدي reaches the same entry and the same reading of it.
    """
    if root_meaning.status() != root_meaning.READY:
        raise HTTPException(
            status_code=503,
            detail="The classical entries are not loaded, so there is nothing to put into English.",
        )
    return root_meaning.resolve(key) or key, root_meaning.lookup(key) or {}


async def _ask_ai(func, *args, operation: str) -> dict:
    """One model call, or a plain 503 when there is no model to call."""
    if not await asyncio.to_thread(ai_service.is_ai_available):
        raise HTTPException(
            status_code=503,
            detail=f"No AI is reachable, so the entry cannot be put into English right now. {_ARABIC_UNHARMED}",
        )
    return await call_service(
        func, *args, operation=operation, timeout_msg=f"The AI took too long. {_ARABIC_UNHARMED}",
    )


@router.get("/root-meaning/english", response_model=RootEntryEnglishResponse)
async def explain_root_meaning(key: RootKey) -> RootEntryEnglishResponse:
    """The entry retold in English, for a reader who cannot read the Arabic.

    Made only when the reader asks for it. The card already prints the opening
    sentence as the origin sense, so the answer carries only what follows, the
    way the Arabic beside it does; a one-sentence reading is kept whole rather
    than answered with nothing.
    """
    filed_under, entry = _book_entry(key)
    arabic = entry.get("body", "")
    if not arabic:
        # Nothing to retell is not a failure of the model, and must not be
        # reported as one: the print itself has no entry, or leaves it blank.
        raise HTTPException(
            status_code=404,
            detail="The book prints no entry under those letters, so there is nothing to put into English.",
        )

    # The whole-book run has read every root. A reading made here, on the spot
    # by whichever model answers, is shown under its own badge and never kept:
    # kept, it would come back next time wearing the whole-book run's badge.
    english, source = root_english.get(filed_under), "maqayees_translation"
    if english is None:
        answer = await _ask_ai(
            ai_service.explain_root_entry, key, arabic, operation="English reading of a Maqayees entry",
        )
        english, source = str(answer.get("english", "")).strip(), "ai"
        if not english:
            raise HTTPException(status_code=502, detail="The AI answered with nothing to show.")

    return RootEntryEnglishResponse(
        root=key,
        english=english.removeprefix(root_gloss.opening_of(english)).lstrip() or english,
        truncated=len(arabic) > get_settings().root_entry_truncate_chars,
        source=Source(**provenance.of(source)),
    )


@router.get("/root-meaning/english/lines", response_model=RootEntryLinesResponse)
async def explain_root_meaning_lines(key: RootKey) -> RootEntryLinesResponse:
    """The rest of the entry with one English line under each Arabic line.

    Covers what the card's "rest of the entry" panel shows. The backend owns the
    split and pairs the two, so the screen never lines them up itself.
    """
    filed_under, entry = _book_entry(key)
    lines, truncated = root_gloss.line_budget(
        root_gloss.rest_of(entry), get_settings().root_entry_truncate_chars,
    )
    if not lines:
        raise HTTPException(
            status_code=404,
            detail="The book prints nothing after the origin sense here, so there is nothing to line up.",
        )

    # Trusted only while it still matches the entry line for line: a book file
    # that has changed shape since makes the kept reading a mispairing.
    kept = root_english.get_lines(filed_under)
    if kept is None or len(kept) != len(lines):
        answer = await _ask_ai(
            ai_service.explain_root_entry_lines, key, lines,
            operation="line-by-line English of a Maqayees entry",
        )
        made = answer.get("lines")
        kept = [str(line).strip() for line in made] if isinstance(made, list) else []
        if len(kept) != len(lines) or not all(kept):
            # English under the wrong Arabic is a false claim about the book;
            # the prose reading is still there, so the card loses only this view.
            raise HTTPException(
                status_code=502,
                detail="The English could not be lined up with the Arabic this time, "
                       "so it is not shown. The paragraph reading is unaffected.",
            )
        await asyncio.to_thread(root_english.put_lines, filed_under, kept)

    return RootEntryLinesResponse(
        root=key,
        lines=[EntryLine(arabic=a, english=e) for a, e in zip(lines, kept)],
        truncated=truncated,
        source=Source(**provenance.of("ai")),
    )
