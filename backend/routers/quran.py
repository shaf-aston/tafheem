"""Quranic ayah lookup and full-text search."""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, Path, Query

from backend.config import get_settings
from backend.models.schemas import (
    AyahEditions,
    Edition,
    Passage,
    QuranAyah,
    QuranSearchResult,
    QuranSurah,
    QuranWord,
    RootResponse,
    Source,
    SurahEdition,
    SurahGlosses,
    TarkeebTree,
)
from backend.services import arabic_text, provenance, quran_corpus, quran_library, quran_service
from backend.services import quran_search
from backend.services import tarkeeb
from backend.services import tarkeeb_store
from backend.utils import normalize_text

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/quran", tags=["quran"])

# Bounds on the two numbers every Qur'an route takes. Not decoration: an
# unbounded int goes straight to SQLite, and one long enough to overflow a C
# integer came back as a 500 rather than as "there is no such ayah".
SURAHS = 114
LONGEST_SURAH = 286   # al-Baqarah, and so the largest ayah number there can be


# Declared before /{surah}/{ayah}: both are two segments, and the first route
# that matches wins.
@router.get("/root/{root}", response_model=RootResponse)
async def get_root(root: str) -> RootResponse:
    """Everywhere one root appears in the Qur'an, and the words built from it.

    This is what joins the tabs together: the same root the dictionary defines and
    the conjugator builds a table for.
    """
    # The tagger writes a root as ك-ت-ب and the corpus stores كتب; accept either
    # so a link from another tab always lands.
    root = arabic_text.normalize_root(normalize_text(root, "Root"))
    found = await asyncio.to_thread(
        quran_corpus.occurrences_of_root, root, get_settings().root_occurrence_limit
    )
    if not found["total"]:
        raise HTTPException(status_code=404, detail=f"The root {root} does not occur in the Qur'an")
    return RootResponse(**found, source=Source(**provenance.of("corpus")))


# Declared before /{surah}/{ayah} for the same reason /root/ is: both are two
# segments, and the first route that matches wins.
@router.get("/surah/{surah}", response_model=QuranSurah)
async def get_surah(surah: int, words: bool = False) -> QuranSurah:
    """A whole surah at once, for reading it end to end.

    `words=false` (the default) is the reading view: the text and its English,
    which is two local queries however long the surah is. `words=true` adds the
    word-by-word grammar, and is meant for one ayah being studied rather than a
    whole surah being skimmed.
    """
    data = await asyncio.to_thread(quran_service.get_surah, surah, words)
    if data is None:
        raise HTTPException(status_code=404, detail=f"There is no surah {surah}")
    return QuranSurah(**data, source=Source(**provenance.of("corpus")))


# Three segments, so it cannot collide with /surah/{surah} above.
@router.get("/surah/{surah}/glosses", response_model=SurahGlosses)
async def get_surah_glosses(surah: int = Path(..., ge=1, le=SURAHS)) -> SurahGlosses:
    """A surah's word-by-word English, for showing a word's meaning on hover.

    An empty answer is valid and means the meanings database was never built.
    The reader then draws the surah exactly as it did before.
    """
    glosses = await asyncio.to_thread(quran_service.glosses_for_surah, surah)
    return SurahGlosses(surah=surah, ayahs=glosses)


@router.get("/editions", response_model=list[Edition])
async def get_editions(kind: str = Query("", pattern="^(tafsir|translation)?$")) -> list[Edition]:
    """Which books are installed. Asked once, so the picker can be drawn.

    An empty list is a valid answer and means the library has not been imported
    yet. The panel says so; it does not pretend the books are loading.
    """
    books = await asyncio.to_thread(quran_library.of_kind, kind) if kind \
        else await asyncio.to_thread(quran_library.editions)
    return [
        Edition(**book, source=Source(**provenance.for_edition(book)))
        for book in books
    ]


# Declared before /editions/{surah}/{ayah}, which is also three segments: the
# first route that matches wins, and "surah" is not a number.
@router.get("/editions/surah/{surah}", response_model=SurahEdition)
async def get_surah_edition(
    surah: int = Path(..., ge=1, le=SURAHS),
    id: str = Query(..., max_length=64),
) -> SurahEdition:
    """One translation's text for a whole surah, for the reading view.

    One request rather than one per ayah. Asking al-Baqarah an ayah at a time is
    286 requests, which is exactly what the surah endpoint beside this one exists
    to avoid, and a translation is needed on every line of it.

    Translations only, and not because commentary is unwelcome: a translation is
    one line per ayah, so a surah of it is a few pages. A commentary's passage
    covers a run of ayahs and would be sent once per ayah of that run, so a
    surah of a long Arabic tafsir is several megabytes of the same paragraphs
    repeated. The panel that shows commentary asks for one ayah at a time, which
    is the shape that suits it.
    """
    if id not in {book["id"] for book in await asyncio.to_thread(quran_library.of_kind, "translation")}:
        raise HTTPException(status_code=404, detail=f"No translation called {id!r} is installed")
    text = await asyncio.to_thread(quran_library.for_surah, surah, id)
    return SurahEdition(surah=surah, edition=id, ayahs=text)


# Declared before /{surah}/{ayah} for the same reason /root/ and /surah/ are:
# both are two segments, and the first route that matches wins.
@router.get("/editions/{surah}/{ayah}", response_model=AyahEditions)
async def get_ayah_editions(
    surah: int = Path(..., ge=1, le=SURAHS),
    ayah: int = Path(..., ge=1, le=LONGEST_SURAH),
    ids: str = Query("", max_length=400, description="Comma-separated edition ids; blank means all"),
) -> AyahEditions:
    """What every book says about one ayah, commentary and translation both.

    An ayah no book has anything on returns an empty list rather than a 404.
    Absent commentary is not a missing page: the reader asked a real question
    about a real ayah, and "nothing here" is the honest answer to it.
    """
    wanted = [part.strip() for part in ids.split(",") if part.strip()] or None
    found = await asyncio.to_thread(quran_library.for_ayah, surah, ayah, wanted)
    return AyahEditions(
        surah=surah,
        ayah=ayah,
        passages=[
            Passage(**passage, source=Source(**provenance.for_edition(passage)))
            for passage in found
        ],
    )


@router.get("/{surah}/{ayah}/tarkeeb", response_model=TarkeebTree)
async def get_tarkeeb(surah: int, ayah: int) -> TarkeebTree:
    """How the ayah's words assemble, the bracket tree, not the case endings.

    Two sources, and the badge always says which. The treebank is what scholars
    recorded and covers most of the Qur'an; where it has nothing, the rules work
    out what they can from the corpus tags and leave the rest as open brackets.
    """
    recorded = await asyncio.to_thread(tarkeeb_store.for_ayah, surah, ayah)
    result = recorded or await asyncio.to_thread(tarkeeb.for_ayah, surah, ayah)
    if not result["words"]:
        raise HTTPException(status_code=404, detail=f"There is no ayah {surah}:{ayah}")
    source = provenance.of("treebank" if recorded else "tarkeeb")
    return TarkeebTree(surah=surah, ayah=ayah, **result, source=Source(**source))


@router.get("/{surah}/{ayah}", response_model=QuranAyah)
async def get_ayah(surah: int, ayah: int) -> QuranAyah:
    """Return an ayah's word-by-word grammar from the corpus."""
    result = await asyncio.to_thread(quran_service.get_ayah, surah, ayah)
    if result is None:
        raise HTTPException(status_code=404, detail=f"There is no ayah {surah}:{ayah}")

    words = [QuranWord(**word) for word in result["words"]]
    return QuranAyah(
        surah=surah,
        ayah=ayah,
        arabic_text=" ".join(word.arabic for word in words),
        words=words,
        end_mark=result["end_mark"],
        source=Source(**provenance.of("corpus")),
    )


@router.get("/search", response_model=list[QuranSearchResult])
async def search_quran(q: str = Query(..., min_length=1, max_length=200)) -> list[QuranSearchResult]:
    query = normalize_text(q, "Search query")
    hits = await asyncio.to_thread(quran_search.search, query)
    # The badge is per hit, not per response: one search can be answered by the
    # local corpus and the next by Quran.com, and a reader is entitled to know
    # which text is in front of them.
    return [
        QuranSearchResult(
            surah=hit.surah,
            ayah=hit.ayah,
            arabic_text=hit.arabic_text,
            source=Source(**provenance.of(hit.source)),
        )
        for hit in hits
    ]
