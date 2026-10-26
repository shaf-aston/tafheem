"""Hear a recitation. Sound in, words out, and the ayahs those words came from.

Thin on purpose: it checks the recording is a recording, hands it to the
recitation service, and shapes the answer. Nothing about Whisper, models,
languages or matching is decided here.

One endpoint for the words (search wants words, the Qur'an tab ayahs: `match`
says which), so a recording uploads once. Word sureness is `/check`, separate so
a reciter never waits for local scoring.

Every request carries a reading id (`X-Reading-Id`, the page's or made here),
echoed back, so the recite journal lines up server and page events.
"""
from __future__ import annotations

import asyncio
import logging
import re
import time
import traceback
import uuid
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager, contextmanager

from fastapi import APIRouter, File, HTTPException, Query, Request, Response, UploadFile
from starlette.concurrency import run_in_threadpool

from backend.config import get_settings
from backend.models.listen import Heard, HeardAyah, HeardPlace, Sureness
from backend.services import recitation
from backend.services.learner import journal
from backend.services.recitation import NotInstalled, Unreadable
from backend.services.recitation.recording import kind_of

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/listen", tags=["listen"])

AYAH_KEY = re.compile("[0-9]{1,3}:[0-9]{1,3}")
# A reading id, the page's own or one made here: letters, digits, and the few
# separators an id reasonably has. Anything else is ignored rather than
# trusted, since it flows straight into a log line.
READING_HEADER = "X-Reading-Id"
READING_ID = re.compile("[A-Za-z0-9._:-]{1,64}")

# One local reading at a time, and none the page gave up on. The model uses most
# cores, so two at once each run 4-8x slower; dropping stale ones here frees the
# CPU, which giving up at the page does not. Words wait here only when this
# machine's ear answers (ears.would_answer_locally); /check always waits, since
# scoring is always local. Search words skip it; whisper.engine_lock guards them.
_turn = asyncio.Lock()


def is_audio(body: bytes) -> bool:
    """What browsers record (webm, ogg, mp4) and what people upload (wav, mp3, flac),
    told by the file's first bytes, not the name or type it claims."""
    return kind_of(body) is not None


def _reading_id(request: Request) -> str:
    """The id this reading is filed under: the page's own, when it sent one and
    it is shaped like an id, otherwise one made here."""
    given = request.headers.get(READING_HEADER, "")
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
        response.headers[READING_HEADER] = self.id

    def done(self, status: int) -> None:
        ms = round((time.perf_counter() - self.started) * 1000)
        journal.note(f"{self.name}.done", ms=ms, status=status, reading=self.id)

    def fail(self, status: int, detail: str, stage: str, exc: Exception | None = None) -> HTTPException:
        """Journal the failure and return the error, so each site reads `raise filed.fail(...)`."""
        journal.note(
            f"{self.name}.failed", stage=stage,
            error=type(exc).__name__ if exc else "",
            message=journal.scrub(str(exc)) if exc else detail,
            traceback=journal.scrub("".join(traceback.format_exception(exc))) if exc else "",
        )
        self.done(status)
        return HTTPException(status_code=status, detail=detail, headers={READING_HEADER: self.id})


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


async def _read_recording(audio: UploadFile, filed: _Filed) -> bytes:
    """The uploaded recording, or the reason it is refused. Empty is not refused:
    a quiet room is an ordinary answer, and each route says what nothing means.

    Both routes take a recording the same way, so the limit and what counts as
    one are written once."""
    limit_mb = get_settings().recitation_max_mb
    limit = limit_mb * 1024 * 1024
    body = await audio.read(limit + 1)
    if len(body) > limit:
        raise filed.fail(413, f"That recording is over {limit_mb}MB. Record a shorter passage.", "validate")
    return body


def _refuse_unless_audio(body: bytes, filed: _Filed) -> None:
    if not is_audio(body):
        raise filed.fail(415, "That file is not a sound recording.", "validate")


@asynccontextmanager
async def _my_turn(request: Request, name: str) -> AsyncIterator[bool]:
    """Hold `_turn` for one request. Yields False when the page gave up while it
    waited, so the caller answers with nothing instead of spending the model."""
    queued = time.perf_counter()
    async with _turn:
        waited = (time.perf_counter() - queued) * 1000
        # The wait a reciter feels is this plus the work, and only this one
        # grows when readings pile up, so when a mark arrives late this line
        # says whether the machine was slow or merely busy.
        if waited >= 100:
            log.info("queued  %.0fms", waited)
        journal.note(f"{name}.queued", ms=round(waited))
        if await request.is_disconnected():
            log.info("the page gave up on that %s before its turn came", name)
            journal.note(f"{name}.dropped")
            yield False
            return
        yield True


def _tuned_model(tuned: bool, filed: _Filed) -> str | None:
    """The tuned model when asked for; a tuned model that cannot run is said, never swapped for another ear."""
    if not tuned:
        return None
    if not (model := recitation.whisper.tuned_model()):
        raise filed.fail(503, "No tuned listening model is set on this machine.", "validate")
    return model


@router.post("", response_model=Heard)
async def listen(
    request: Request,
    response: Response,
    audio: UploadFile = File(..., description="A recording, as the browser made it"),
    match: bool = Query(False, description="Also return the ayahs these words came from; heard as a recitation, like recite"),
    recite: bool = Query(False, description="Qur'an being recited: heard in Arabic by the Qur'an ear, no ayahs looked up"),
    fusha: bool = Query(True, description="Lean towards classical Arabic; off hears any Arabic"),
    near: str | None = Query(
        None, pattern=f"^{AYAH_KEY.pattern}-{AYAH_KEY.pattern}$",
        description="The open page's first and last ayah, 2:1-2:5: also say where in the Qur'an this was",
    ),
    before: str = Query(
        "", description="The words of the last reading whose place was not sure, so this one is placed with them in front",
    ),
) -> Heard:
    """What was said, and optionally which ayahs it was.

    Hearing nothing is not an error. A microphone that picked up a quiet room
    returns empty words and no ayahs, and the page says so; a 500 there would
    read as the feature being broken when it is working exactly as it should.
    """
    with _filing(request, response, "reading") as filed:
        # The same cap as /check's heard text: both are one reading's words.
        if len(before) > get_settings().recitation_check_heard_max_chars:
            raise filed.fail(
                422, f"before must be at most {get_settings().recitation_check_heard_max_chars} characters.", "validate",
            )
        body = await _read_recording(audio, filed)
        is_recitation = recite or match
        journal.note("reading.received", bytes=len(body), recite=is_recitation)

        if not body:
            filed.done(200)
            return Heard(text="", ayahs=[])
        _refuse_unless_audio(body, filed)
        # Checked before the ear is paid for, so a bad page never costs a reading.
        span = None
        if near:
            first, last = (tuple(map(int, key.split(":"))) for key in near.split("-"))
            try:
                span = await run_in_threadpool(recitation.page_span, first, last)
            except ValueError as exc:
                raise filed.fail(422, f"{near} is not a page of the Qur'an", "place", exc) from None

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
            async with _my_turn(request, "reading") as wanted:
                if not wanted:
                    filed.done(200)
                    return Heard(text="", ayahs=[])
                text, hits = await do_hear()
        else:
            text, hits = await do_hear()

        place = None
        if span and text:
            found = await run_in_threadpool(recitation.find_place, text, span, before)
            place = found and HeardPlace(surah=found.surah, ayah=found.ayah, sure=found.sure, home=found.home)

        filed.done(200)
        return Heard(
            text=text,
            place=place,
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
    check: str = Query("", description="Ayahs being recited, as 1:1,1:2; each word's sureness comes back in `sure`, its weakest piece and second in `detail`"),
    tuned: bool = Query(False, description="Score with the tuned model; 503 when none is installed"),
) -> Sureness:
    """How sure the ear is of each word, asked separately from writing them down.

    Always this machine's model (see services/recitation/ears.py's "Word
    sureness"), whichever ear wrote the words down, so this always waits at
    `_turn`: it is exactly the CPU cost that queue exists to share out.

    A check past `_turn` runs to the end even if the page gives up; the page
    sends one check at a time, which bounds the cost.
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

        model = _tuned_model(tuned, filed)
        body = await _read_recording(audio, filed)
        journal.note("check.received", bytes=len(body), ayahs=len(checked))

        if not body or not checked or not heard:
            filed.done(200)
            return Sureness(sure={})
        _refuse_unless_audio(body, filed)

        async with _my_turn(request, "check") as wanted:
            if not wanted:
                filed.done(200)
                return Sureness(sure={})

            try:
                sure, detail = await run_in_threadpool(recitation.check, body, heard, checked, model)
            except Exception as exc:
                log.exception("checking failed")
                raise filed.fail(
                    500,
                    f"The app failed while checking this recording (reading {filed.id}). "
                    "Your recitation was not the problem.",
                    "check", exc,
                ) from None

        filed.done(200)
        return Sureness(sure=sure, detail=detail)
