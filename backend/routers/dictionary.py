"""Arabic-English dictionary search."""

import asyncio
import re

from fastapi import APIRouter, HTTPException, Query

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
)
from backend.services import ai as ai_service
from backend.services import (
    dictionary_service,
    lexicons,
    provenance,
    root_english,
    root_gloss,
    root_meaning,
)
from backend.services.arabic_text import normalize_root, spelled_out
from backend.utils import call_service, normalize_text, require_arabic

router = APIRouter(prefix="/api/dictionary", tags=["dictionary"])

_SEARCHERS = {
    "ar": dictionary_service.search_arabic,
    "en": dictionary_service.search_english,
}


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

    return DictionaryResponse(
        query=query,
        lang=language,
        results=[DictionaryEntry(**entry) for entry in searcher(query)],
        source=Source(**provenance.of("wiktionary")),
    )


@router.get("/root-meaning", response_model=RootMeaningResponse)
async def get_root_meaning(
    root: str = Query(..., min_length=1, max_length=50, description="Arabic root letters"),
) -> RootMeaningResponse:
    """What the classical books say this root means at its origin.

    Answers with the letters it actually searched, so a root written one way here
    and another way in the book shows up as a mismatch rather than as silence.
    """
    # Checked before normalising, because normalising drops everything that is not
    # an Arabic letter: "ktb" would otherwise come back as "the book has no entry
    # under those letters", which reads as a fact about the book rather than about
    # the question. Same check, and the same status code, as everywhere else.
    typed = normalize_text(root, "Root")
    require_arabic(typed, "Root")
    key = normalize_root(typed)

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
        meaning=RootMeaning(**entry.meaning),
        source=Source(**provenance.of(entry.source_key)),
        english_source=(
            Source(**provenance.of(entry.english_source_key))
            if entry.english_source_key else None
        ),
    )


@router.get("/lexicons", response_model=LexiconsResponse)
async def get_lexicons(
    root: str = Query(..., min_length=1, max_length=50, description="Arabic root letters"),
) -> LexiconsResponse:
    """Whole entries for this root, from every classical dictionary that has one.

    The long answer to the short one root-meaning gives. Thin on purpose: the
    letters are checked, the service is asked, and each entry is handed its
    book's credit. Which books exist and how a root is matched to an entry are
    both decided in services/lexicons.py.
    """
    typed = normalize_text(root, "Root")
    require_arabic(typed, "Root")
    key = normalize_root(typed)

    state = lexicons.status()
    if state != lexicons.READY:
        return LexiconsResponse(root=key, status=state)

    return LexiconsResponse(
        root=key,
        status=state,
        entries=[
            LexiconEntry(
                **{field: value for field, value in entry.items() if field != "source"},
                source=Source(**provenance.of(entry["source"])),
            )
            for entry in lexicons.entries_for(key)
        ],
    )


@router.get("/root-meaning/english", response_model=RootEntryEnglishResponse)
async def explain_root_meaning(
    root: str = Query(..., min_length=1, max_length=50, description="Arabic root letters"),
) -> RootEntryEnglishResponse:
    """The whole entry retold in English, for a reader who cannot read the Arabic.

    A separate request from the entry itself, made only when the reader asks for
    it: it costs a call to a model, and the answer is a guess where the entry
    above it is the book's own words.
    """
    typed = normalize_text(root, "Root")
    require_arabic(typed, "Root")
    key = normalize_root(typed)

    if root_meaning.status() != root_meaning.READY:
        raise HTTPException(
            status_code=503,
            detail="The classical entries are not loaded, so there is nothing to put into English.",
        )

    # Kept under the spelling the book files, which is what the whole-book run
    # used. A reader who writes هدى where the book wrote هدي reaches the same
    # entry, and must reach the same reading of it rather than paying a model to
    # make a second one and filing it under a second name.
    filed_under = root_meaning.resolve(key) or key
    entry = root_meaning.lookup(key)
    arabic = (entry or {}).get("body", "")
    if not arabic:
        # Nothing to retell is not a failure of the model, and must not be
        # reported as one, the print itself has no entry, or leaves it blank.
        raise HTTPException(
            status_code=404,
            detail="The book prints no entry under those letters, so there is nothing to put into English.",
        )

    # Read once, kept for good. Most roots will already be here, and an entry
    # that is here costs nothing and needs no AI at all.
    if kept := root_english.get(filed_under):
        # The card already prints the opening sentence as the origin sense
        # (root_meaning reads it off this same translation), so the panel below
        # carries only what follows, the way the Arabic beside it does. A
        # one-sentence reading is kept whole rather than answered with nothing.
        rest = kept.removeprefix(root_gloss.opening_of(kept)).lstrip() or kept
        return _english_answer(key, rest, arabic, made_carefully=True)

    if not await asyncio.to_thread(ai_service.is_ai_available):
        raise HTTPException(
            status_code=503,
            detail="No AI is reachable, so the entry cannot be put into English right now. "
                   "The Arabic above is unaffected.",
        )

    answer = await call_service(
        ai_service.explain_root_entry,
        key,
        arabic,
        operation="English reading of a Maqayees entry",
        timeout_msg="The AI took too long. The Arabic entry above is unaffected.",
    )
    english = str(answer.get("english", "")).strip()
    if not english:
        raise HTTPException(status_code=502, detail="The AI answered with nothing to show.")

    await asyncio.to_thread(root_english.put, filed_under, english)
    return _english_answer(key, english, arabic, made_carefully=False)


@router.get("/root-meaning/english/lines", response_model=RootEntryLinesResponse)
async def explain_root_meaning_lines(
    root: str = Query(..., min_length=1, max_length=50, description="Arabic root letters"),
) -> RootEntryLinesResponse:
    """The rest of the entry with one English line under each Arabic line.

    Covers what the card's "rest of the entry" panel shows: the body after the
    origin sense, which already has its own English higher up the card. The
    backend owns the split, and the answer carries the Arabic and English
    already paired, so the screen never has to line the two up itself.
    """
    typed = normalize_text(root, "Root")
    require_arabic(typed, "Root")
    key = normalize_root(typed)

    if root_meaning.status() != root_meaning.READY:
        raise HTTPException(
            status_code=503,
            detail="The classical entries are not loaded, so there is nothing to put into English.",
        )

    filed_under = root_meaning.resolve(key) or key
    entry = root_meaning.lookup(key)
    arabic = _rest_of(entry or {})
    if not arabic:
        raise HTTPException(
            status_code=404,
            detail="The book prints nothing after the origin sense here, "
                   "so there is nothing to line up.",
        )

    lines, truncated = _line_budget(arabic)

    # Kept under the book's own spelling, like the prose reading, and trusted
    # only while it still matches the entry line for line: a book file that has
    # changed shape since makes the kept reading a mispairing, not a saving.
    kept = root_english.get_lines(filed_under)
    if kept is None or len(kept) != len(lines):
        kept = await _lines_from_ai(key, lines)
        await asyncio.to_thread(root_english.put_lines, filed_under, kept)

    return RootEntryLinesResponse(
        root=key,
        lines=[EntryLine(arabic=a, english=e) for a, e in zip(lines, kept)],
        truncated=truncated,
        source=Source(**provenance.of("ai")),
    )


# The same two rules RootMeaningCard.jsx uses to find "the rest of the entry",
# kept in step by the test that pins them: the panel and this endpoint must
# agree on what the rest is, or the lines would pair against a different text
# than the one on screen.
_LEADING_PUNCTUATION = re.compile(r"^[.،؛:\s]+")
_HAS_WORDS = re.compile(r"[^.،؛:\s]")


def _rest_of(entry: dict) -> str:
    """The entry body after the origin sense, or nothing if only punctuation is left."""
    body = str(entry.get("body", ""))
    core = str(entry.get("core_meaning", ""))
    tail = body[len(core):] if core and body.startswith(core) else body
    return _LEADING_PUNCTUATION.sub("", tail) if _HAS_WORDS.search(tail) else ""


# The end of a claim: a full stop with white space after it, or at the very end
# of a paragraph. Only the full stop, deliberately. The book's commas and its
# ؛ separate clauses inside one claim, and cutting at those would put half a
# thought on a line of its own with half an English sentence beside it.
_SENTENCE_END = re.compile(r"(?<=\.)\s+")

# The gap the book prints down the middle of a verse, between its two halves.
# The same string the card's layout looks for (frontend/src/lib/entryLines.js);
# both must read the book the same way or a verse would be one thing on screen
# and two to the model.
VERSE_GAP = " ... "


def _reading_lines(arabic: str) -> list[str]:
    """The entry cut into the pieces the reader reads one at a time.

    The printing's own breaks are paragraphs, not lines: Harun breaks where a
    verse ends, so one break can hold six lines of prose. Paired at that size
    the screen shows a wall of Arabic and then a wall of English, which is the
    one thing a line-by-line view exists to avoid. So a paragraph is cut again
    at its full stops, which brings the usual piece to about one claim.

    A verse is never cut. It is one thought printed in two halves with a gap
    down the middle, the book writes that gap as " ... ", and half a verse is
    not something anyone reads or translates on its own.
    """
    pieces: list[str] = []
    for paragraph in (p.strip() for p in arabic.split("\n")):
        if not paragraph:
            continue
        if VERSE_GAP in paragraph:
            pieces.append(paragraph)
            continue
        pieces.extend(s.strip() for s in _SENTENCE_END.split(paragraph) if s.strip())
    return pieces


def _line_budget(arabic: str) -> tuple[list[str], bool]:
    """The entry's lines, whole ones only, within what the model can be given.

    The prose reading cuts the entry at a character count; cutting a line in
    half here would make the model translate half a line and file it as the
    whole, so the budget is spent line by line and the first line that does not
    fit ends the list.
    """
    budget = get_settings().root_entry_truncate_chars
    lines = _reading_lines(arabic)
    kept: list[str] = []
    spent = 0
    for line in lines:
        spent += len(line) + 1
        if kept and spent > budget:
            return kept, True
        kept.append(line)
    return kept, False


async def _lines_from_ai(key: str, lines: list[str]) -> list[str]:
    """One English line per Arabic line, or a refusal, never a misfit answer."""
    if not await asyncio.to_thread(ai_service.is_ai_available):
        raise HTTPException(
            status_code=503,
            detail="No AI is reachable, so the entry cannot be put into English right now. "
                   "The Arabic above is unaffected.",
        )
    answer = await call_service(
        ai_service.explain_root_entry_lines,
        key,
        lines,
        operation="line-by-line English of a Maqayees entry",
        timeout_msg="The AI took too long. The Arabic entry above is unaffected.",
    )
    made = answer.get("lines")
    made = [str(line).strip() for line in made] if isinstance(made, list) else []
    if len(made) != len(lines) or not all(made):
        # The one refusal this endpoint exists for. English under the wrong
        # Arabic is a false claim about the book; the prose reading is still
        # there, so the card loses nothing but this view.
        raise HTTPException(
            status_code=502,
            detail="The English could not be lined up with the Arabic this time, "
                   "so it is not shown. The paragraph reading is unaffected.",
        )
    return made


def _english_answer(
    root: str, english: str, arabic: str, *, made_carefully: bool
) -> RootEntryEnglishResponse:
    """The reading, badged by who actually made it.

    Kept and fresh are not the same claim. A kept reading was translated
    against the Arabic and read back before it was stored. A fresh one was
    made in the second the reader pressed the button, by whichever model the
    app can reach, a fast one, checked by nobody. Badging both as the book's
    own words would lend the second the standing of the first.
    """
    return RootEntryEnglishResponse(
        root=root,
        english=english,
        truncated=len(arabic) > get_settings().root_entry_truncate_chars,
        source=Source(**provenance.of("maqayees_translation" if made_carefully else "ai")),
    )
