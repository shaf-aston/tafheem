"""Hear a recitation. Sound in, words out, and the ayahs those words came from.

Thin on purpose: it checks the recording is a recording, hands it to the
recitation service, and shapes the answer. Nothing about Whisper, models,
languages or matching is decided here.

One endpoint for the words rather than two, because the tabs that use it want
different halves of the same work and the recording must only be uploaded once.
Daleel wants the words, to search with. The Qur'an tab wants the ayahs. `match`
says which. How sure the ear is of each word is a second, separate question,
`POST /api/listen/check` below: it costs the CPU on this machine whichever ear
wrote the words down, and a reciter reading on must never wait for it.

Every request is filed under a reading id, the page's own (`X-Reading-Id`) when
it sent one, otherwise one made here, echoed back on every answer so the page
can ask again with the id it was given. The recite journal (services/journal)
uses it to line server-side and page-side events up as one story.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
import traceback
import uuid
from collections.abc import Iterator
from contextlib import contextmanager

from fastapi import APIRouter, File, HTTPException, Query, Request, Response, UploadFile
from starlette.concurrency import run_in_threadpool

from backend.config import get_settings
from backend.models.schemas import Heard, HeardAyah, Sureness
from backend.services import journal, recitation
from backend.services.recitation import NotInstalled, Unreadable

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/listen", tags=["listen"])

AYAH_KEY = re.compile("[0-9]{1,3}:[0-9]{1,3}")
# A reading id, the page's own or one made here: letters, digits, and the few
# separators an id reasonably has. Anything else is ignored rather than
# trusted, since it flows straight into a log line.
READING_ID = re.compile("[A-Za-z0-9._:-]{1,64}")

# One recitation read at a time on this machine, and none that nobody is
# waiting for.
#
# Two things, and they only work together. The model is given most of this
# machine's cores, so two readings at once ask for twice the cores there are
# and both take longer than either would have waited: measured through the real
# page, readings that take five seconds alone took twenty to forty when they
# piled up. And a recitation asks about the same recording again as it grows,
# so a reading is often already out of date before its turn comes; the page
# gives up on those, but giving up at the page only stops the page waiting, it
# does not stop this machine working. Dropping them here is what actually gives
# the time back.
#
# Here rather than inside the engine because it has to be waited for without
# holding a worker thread, and because whether a reading is still wanted is
# something only the request knows.
#
# Words only wait here when the ear on this machine is the one that would
# answer: `ears.would_answer_locally()` says so. Groq answering costs this
# machine's CPU nothing to queue behind, so a reading heard on Groq skips this
# entirely. `/check` always waits here: scoring is always this machine's model,
# whichever ear wrote the words down. A search-box word never waits here at
# all, quick already, and making it wait behind seconds of someone else's
# reading would cost it exactly the fairness this queue exists to give
# recitations; the processor it shares is guarded instead by
# services/recitation/listen.py's own lock around the model itself.
_turn = asyncio.Lock()


def is_audio(body: bytes) -> bool:
    """What browsers record (webm, ogg, mp4) and what people upload (wav, mp3, flac),
    told by the file's first bytes, not the name or type it claims."""
    return (body.startswith((b"\x1a\x45\xdf\xa3", b"OggS", b"fLaC", b"ID3"))
            or (body[:4] == b"RIFF" and body[8:12] == b"WAVE")
            or body[4:8] == b"ftyp"
            or (len(body) > 1 and body[0] == 0xFF and body[1] & 0xE0 == 0xE0))


def _reading_id(request: Request) -> str:
    """The id this reading is filed under: the page's own, when it sent one and
    it is shaped like an id, otherwise one made here."""
    given = request.headers.get("x-reading-id", "")
    if given and READING_ID.fullmatch(given):
        return given
    return uuid.uuid4().hex[:16]


class _Filed:
    """One request as the journal sees it: its id, how long it took, how it ended.

    Both routes file a request the same way under their own name, `reading` or
    `check`, so a change to how a failure is written down is made once, here.
    """

    def __init__(self, request: Request, response: Response, name: str) -> None:
        self.id = _reading_id(request)
        self.name = name
        self.started = time.perf_counter()
        response.headers["X-Reading-Id"] = self.id

    def done(self, status: int) -> None:
        ms = round((time.perf_counter() - self.started) * 1000)
        journal.note(f"{self.name}.done", ms=ms, status=status, reading=self.id)

    def fail(self, status: int, detail: str, stage: str, exc: Exception | None = None) -> HTTPException:
        """Journal the failure and build the error to raise.

        Returns rather than raises, so every call site reads `raise filed.fail(...)`:
        that is what makes it obvious at each site that control does not
        continue past it, the same reason the standard library's own
        exceptions are built and then raised rather than raising themselves.
        """
        journal.note(
            f"{self.name}.failed", stage=stage,
            error=type(exc).__name__ if exc else "",
            message=journal.scrub(str(exc)) if exc else detail,
            traceback=journal.scrub("".join(traceback.format_exception(exc))) if exc else "",
        )
        self.done(status)
        return HTTPException(status_code=status, detail=detail, headers={"X-Reading-Id": self.id})


@contextmanager
def _filing(request: Request, response: Response, name: str) -> Iterator[_Filed]:
    """A request filed under its id for as long as it runs; every journal line
    written meanwhile carries that id without being told it."""
    filed = _Filed(request, response, name)
    token = journal.reading_id.set(filed.id)
    try:
        yield filed
    finally:
        journal.reading_id.reset(token)


@router.post("", response_model=Heard)
async def listen(
    request: Request,
    response: Response,
    audio: UploadFile = File(..., description="A recording, as the browser made it"),
    match: bool = Query(False, description="Also return the ayahs these words came from; heard as a recitation, like recite"),
    recite: bool = Query(False, description="Qur'an being recited: heard in Arabic by the Qur'an ear, no ayahs looked up"),
    fusha: bool = Query(True, description="Lean towards classical Arabic; off hears any Arabic"),
) -> Heard:
    """What was said, and optionally which ayahs it was.

    Hearing nothing is not an error. A microphone that picked up a quiet room
    returns empty words and no ayahs, and the page says so; a 500 there would
    read as the feature being broken when it is working exactly as it should.
    """
    settings = get_settings()
    with _filing(request, response, "reading") as filed:
        limit = settings.recitation_max_mb * 1024 * 1024
        body = await audio.read(limit + 1)
        if len(body) > limit:
            raise filed.fail(
                413,
                f"That recording is over {settings.recitation_max_mb}MB. Record a shorter passage.",
                "validate",
            )

        is_recitation = recite or match
        journal.note("reading.received", bytes=len(body), recite=is_recitation)

        if not body:
            filed.done(200)
            return Heard(text="", ayahs=[])
        if not is_audio(body):
            raise filed.fail(415, "That file is not a sound recording.", "validate")

        async def do_hear() -> tuple[str, list]:
            try:
                heard_started = time.perf_counter()
                text, hits = await run_in_threadpool(
                    recitation.hear, body, match_ayahs=match, recite=recite, fusha=fusha,
                )
                journal.note(
                    "reading.heard", ms=round((time.perf_counter() - heard_started) * 1000), chars=len(text),
                )
                return text, hits
            except Unreadable as exc:
                # The recording, not the listening. It carried a real webm
                # header and nothing playable behind it, so is_audio above let
                # it through; only opening it finds out. Told apart because
                # "record it again" is something the reader can actually do,
                # where "could not make that out" reads as the feature broken.
                raise filed.fail(415, str(exc), "hear", exc) from exc
            except NotInstalled as exc:
                # A missing engine is a machine that was never set up, not a
                # bad request.
                raise filed.fail(503, str(exc), "hear", exc) from exc
            except Exception as exc:
                log.exception("listening failed")
                raise filed.fail(
                    500,
                    f"The app failed while reading this recording (reading {filed.id}). "
                    "Your recitation was not the problem.",
                    "hear", exc,
                ) from None

        # `_turn` protects this machine's own CPU, so it is only worth queuing
        # behind when this machine is the one about to spend it. A reading
        # Groq will answer costs this machine nothing to wait for.
        if is_recitation and recitation.ears.would_answer_locally():
            # How long this reading queued behind another. The wait a reciter
            # feels is this plus the work, and only this one grows when
            # readings pile up, so when a mark arrives late this line says
            # whether the machine was slow or merely busy.
            queued = time.perf_counter()
            async with _turn:
                waited = (time.perf_counter() - queued) * 1000
                if waited >= 100:
                    log.info("queued  %.0fms", waited)
                journal.note("reading.queued", ms=round(waited))
                if await request.is_disconnected():
                    log.info("the page gave up on that reading before its turn came")
                    journal.note("reading.dropped")
                    filed.done(200)
                    return Heard(text="", ayahs=[])
                text, hits = await do_hear()
        else:
            text, hits = await do_hear()

        filed.done(200)
        return Heard(
            text=text,
            ayahs=[
                HeardAyah(
                    surah=hit.surah,
                    ayah=hit.ayah,
                    arabic=hit.arabic,
                    score=round(hit.score, 3),
                    heard_of_ayah=round(hit.heard_of_ayah, 3),
                )
                for hit in hits
            ],
        )


@router.post("/check", response_model=Sureness)
async def listen_check(
    request: Request,
    response: Response,
    audio: UploadFile = File(..., description="The same recording the words reading already heard"),
    heard: str = Query(..., description="What that reading wrote down, to be scored by sound"),
    check: str = Query("", description="Ayahs being recited, as 1:1,1:2; each word's sureness comes back in `sure`"),
) -> Sureness:
    """How sure the ear is of each word, asked separately from writing them down.

    Always this machine's model (see services/recitation/ears.py's "Word
    sureness"), whichever ear wrote the words down, so this always waits at
    `_turn`: it is exactly the CPU cost that queue exists to share out.

    A check already running on this machine's model cannot be cancelled
    mid-way: once past `_turn` it holds the turn to the end even if the page
    gives up on it (see the is_disconnected check above `_turn`, which only
    catches one still waiting). The page never sends more than one check at a
    time (lib/recitingSession.js), which is what bounds the cost.
    """
    settings = get_settings()
    with _filing(request, response, "check") as filed:
        checked = [key for key in check.split(",") if key]
        if (len(checked) > settings.recitation_check_ayahs_max or len(set(checked)) != len(checked)
                or not all(AYAH_KEY.fullmatch(key) for key in checked)):
            raise filed.fail(
                422,
                f"check must be up to {settings.recitation_check_ayahs_max} different ayahs, as 1:1,1:2.",
                "validate",
            )
        if len(heard) > settings.recitation_check_heard_max_chars:
            raise filed.fail(
                422,
                f"heard must be at most {settings.recitation_check_heard_max_chars} characters.",
                "validate",
            )

        limit = settings.recitation_max_mb * 1024 * 1024
        body = await audio.read(limit + 1)
        if len(body) > limit:
            raise filed.fail(
                413,
                f"That recording is over {settings.recitation_max_mb}MB. Record a shorter passage.",
                "validate",
            )

        journal.note("check.received", bytes=len(body), ayahs=len(checked))

        if not body or not checked or not heard:
            filed.done(200)
            return Sureness(sure={})
        if not is_audio(body):
            raise filed.fail(415, "That file is not a sound recording.", "validate")

        queued = time.perf_counter()
        async with _turn:
            waited = (time.perf_counter() - queued) * 1000
            if waited >= 100:
                log.info("queued  %.0fms", waited)
            journal.note("check.queued", ms=round(waited))
            if await request.is_disconnected():
                log.info("the page gave up on that check before its turn came")
                journal.note("check.dropped")
                filed.done(200)
                return Sureness(sure={})

            try:
                sure = await run_in_threadpool(recitation.check, body, heard, checked)
            except Exception as exc:
                log.exception("checking failed")
                raise filed.fail(
                    500,
                    f"The app failed while checking this recording (reading {filed.id}). "
                    "Your recitation was not the problem.",
                    "check", exc,
                ) from None

        filed.done(200)
        return Sureness(sure=sure)
