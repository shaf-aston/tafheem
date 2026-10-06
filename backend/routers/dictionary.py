"""Arabic-English dictionary search."""

import asyncio
import sys
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.config import get_settings
from backend.models.schemas import (
    Correction,
    DictionaryEntry,
    DictionaryResponse,
    EntryLine,
    LexiconEntry,
    LexiconsResponse,
    RootEntryEnglishResponse,
    RootEntryLinesResponse,
    RootMeaning,
    RootMeaningResponse,
    SentenceResponse,
    SentenceWord,
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
    sentence_meaning,
    verb_forms,
)
from backend.services.arabic_text import normalize_root, not_arabic, spelled_out
from backend.utils import arabic_sentence, call_service, normalize_text, require_arabic

router = APIRouter(prefix="/api/dictionary", tags=["dictionary"])

_SEARCHERS = {
    "ar": dictionary_service.search_arabic,
    "en": dictionary_service.search_english,
}

_ARABIC_UNHARMED = "The Arabic above is unaffected."


def _asked_root(
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


Root = Annotated[str, Depends(_asked_root)]


@router.get("/search", response_model=DictionaryResponse)
async def search_dictionary(
    q: str = Query(..., min_length=1, max_length=get_settings().search_max_query_chars, description="Search query"),
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
    corrected = []
    # Nothing at all, not even inside a longer word: most likely a slip, so the
    # word it was likeliest meant to be is looked up, and the page says so.
    if not found and (used := await asyncio.to_thread(dictionary_service.meant, query, language)):
        found = await asyncio.to_thread(searcher, used)
        corrected, query = [Correction(typed=query, used=used)], used
    return DictionaryResponse(
        query=query,
        lang=language,
        results=[DictionaryEntry(**entry) for entry in found],
        source=Source(**provenance.of("wiktionary")),
        corrected=corrected,
    )



@router.get("/sentence", response_model=SentenceResponse)
async def translate_sentence(
    q: str = Query(..., min_length=1, max_length=get_settings().search_max_query_chars, description="Arabic phrase or sentence"),
) -> SentenceResponse:
    """More than one word: the sense of the whole, then each word on its own."""
    text = arabic_sentence(q, "Sentence")
    found = await asyncio.to_thread(sentence_meaning.translate, text)
    return SentenceResponse(
        query=text,
        kind=found["kind"],
        meaning=found["meaning"],
        source=Source(**provenance.of(found["source"])) if found["source"] else None,
        ref=found["ref"],
        words=[SentenceWord(**w) for w in found["words"]],
        words_source=Source(**provenance.of(found["words_source"])),
        left_out=not_arabic(q),
    )

@router.get("/babs", response_model=VerbVerdict)
async def get_root_babs(root: Root) -> VerbVerdict:
    """The باب a root's Form I verb takes, as Lane and Wiktionary state it.

    Asked by root, not by the word on screen, so every word on the root shows
    the same fact. No readings means no source records one.
    """
    return VerbVerdict.of(await asyncio.to_thread(verb_forms.babs_of, root))


@router.get("/root-meaning", response_model=RootMeaningResponse)
async def get_root_meaning(root: Root) -> RootMeaningResponse:
    """What the classical books say this root means at its origin.

    Answers with the letters it actually searched, so a root written one way here
    and another way in the book shows up as a mismatch rather than as silence.
    """
    state = root_meaning.status()
    if state != root_meaning.READY:
        return RootMeaningResponse(root=root, status=state)

    entry = root_meaning.entry_for(root)
    if entry is None:
        # No entry means no book to credit: a source badge with nothing above it
        # reads as though the book had been consulted and had answered.
        return RootMeaningResponse(root=root, status=state)

    return RootMeaningResponse(
        root=root,
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
async def get_lexicons(root: Root) -> LexiconsResponse:
    """Whole entries for this root, from every classical dictionary that has one.

    The long answer to the short one root-meaning gives. Thin on purpose: which
    books exist and how a root is matched to an entry are both decided in
    services/lexicons.py; this hands each entry its book's source.
    """
    state = lexicons.status()
    # A worker thread: a common root is a hundred kilobytes to unpack.
    found = await asyncio.to_thread(lexicons.entries_for, root) if state == lexicons.READY else []
    if found is None:
        # The database stopped answering mid-read. "No entry" here would be a
        # claim about the books, made because of a failure.
        state, found = lexicons.BROKEN, []

    return LexiconsResponse(
        root=root,
        status=state,
        entries=[
            LexiconEntry(
                **{field: value for field, value in entry.items() if field != "source"},
                source=Source(**provenance.of(entry["source"])),
            )
            for entry in found
        ],
    )


def _book_entry(root: str) -> tuple[str, dict]:
    """(the spelling the book files it under, its entry), or 503 with no book.

    Readings are kept under the book's spelling: a reader who writes هدى where
    the book wrote هدي reaches the same entry and the same English of it.
    """
    if root_meaning.status() != root_meaning.READY:
        raise HTTPException(
            status_code=503,
            detail="The classical entries are not loaded, so there is nothing to put into English.",
        )
    return root_meaning.book_root_of(root) or root, root_meaning.lookup(root) or {}


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
async def get_root_entry_english(root: Root) -> RootEntryEnglishResponse:
    """The entry retold in English, for a reader who cannot read the Arabic.

    Made only when the reader asks for it. The card already prints the opening
    sentence as the origin sense, so the answer carries only what follows, the
    way the Arabic beside it does; a one-sentence answer is kept whole rather
    than answered with nothing.
    """
    book_root, entry = _book_entry(root)
    arabic = entry.get("body", "")
    if not arabic:
        # Nothing to retell is not a failure of the model, and must not be
        # reported as one: the print itself has no entry, or leaves it blank.
        raise HTTPException(
            status_code=404,
            detail="The book prints no entry under those letters, so there is nothing to put into English.",
        )

    # The whole-book run has read every root. English made here, on the spot
    # by whichever model answers, is shown under its own badge and never kept:
    # kept, it would come back next time wearing the whole-book run's badge.
    english, source = root_english.get(book_root), "maqayees_translation"
    if english is None:
        answer = await _ask_ai(
            ai_service.explain_root_entry, root, arabic, operation="English of a Maqayees entry",
        )
        english, source = str(answer.get("english", "")).strip(), "ai"
        if not english:
            raise HTTPException(status_code=502, detail="The AI answered with nothing to show.")

    return RootEntryEnglishResponse(
        root=root,
        english=english.removeprefix(root_gloss.opening_of(english)).lstrip() or english,
        truncated=len(arabic) > get_settings().root_entry_truncate_chars,
        source=Source(**provenance.of(source)),
    )


@router.get("/root-meaning/english/lines", response_model=RootEntryLinesResponse)
async def get_root_entry_lines(root: Root) -> RootEntryLinesResponse:
    """The rest of the entry with one English line under each Arabic line.

    Covers what the card's "rest of the entry" panel shows. The backend owns the
    split and pairs the two, so the screen never lines them up itself. English
    kept for every line of the entry (the shipped whole-book run) is answered
    whole; only when none is kept is the opening cut to what the model can read
    and asked for on the spot.
    """
    book_root, entry = _book_entry(root)
    rest = root_gloss.rest_of(entry)
    every_line, _ = root_gloss.line_budget(rest, sys.maxsize)
    if not every_line:
        raise HTTPException(
            status_code=404,
            detail="The book prints nothing after the origin sense here, so there is nothing to line up.",
        )

    # Trusted only while it still matches the entry line for line: a book file
    # that has changed shape since makes the kept English a mispairing.
    kept = root_english.get_lines(book_root, len(every_line))
    if kept is not None:
        return RootEntryLinesResponse(
            root=root,
            lines=[EntryLine(arabic=a, english=e) for a, e in zip(every_line, kept)],
            truncated=False,
            source=Source(**provenance.of("ai")),
        )

    lines, truncated = root_gloss.line_budget(rest, get_settings().root_entry_truncate_chars)
    kept = root_english.get_lines(book_root, len(lines))
    if kept is None:
        answer = await _ask_ai(
            ai_service.explain_root_entry_lines, root, lines,
            operation="line-by-line English of a Maqayees entry",
        )
        made = answer.get("lines")
        kept = [str(line).strip() for line in made] if isinstance(made, list) else []
        if len(kept) != len(lines) or not all(kept):
            # English under the wrong Arabic is a false claim about the book;
            # the prose English is still there, so the card loses only this view.
            raise HTTPException(
                status_code=502,
                detail="The English could not be lined up with the Arabic this time, "
                       "so it is not shown. The English of the whole entry is unaffected.",
            )
        await asyncio.to_thread(root_english.put_lines, book_root, kept)

    return RootEntryLinesResponse(
        root=root,
        lines=[EntryLine(arabic=a, english=e) for a, e in zip(lines, kept)],
        truncated=truncated,
        source=Source(**provenance.of("ai")),
    )
