"""Tafheem, FastAPI application entry point."""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.config import get_settings
from backend.routers import (
    analysis, colloquial, daleel, dawah, dictionary, grow, hadith, journal, listen, morphology, nahw_notes, practice, progress, quran,
    rijal, speak, tamreen, tarkeeb, timelines,
)
from backend.services import ai as ai_service
from backend.services import dictionary_service, provenance, quran_service, recitation, root_meaning, speech, startup, syntax
from backend.services.morphology import get_engine_name

BACKEND_ROOT = Path(__file__).resolve().parent
LOG_PATH = BACKEND_ROOT.parent / "backend.log"

# Windows consoles default to CP1252 which cannot encode Arabic characters.
# Reconfigure stdout to UTF-8 so log lines with Arabic text don't raise
# UnicodeEncodeError and produce "--- Logging error ---" noise.
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass  # read-only or already correct, safe to ignore

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s - %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await startup.run()

    # Log which engines are active so the operator knows the mode at a glance
    logger.info("NLP engine   : %s", get_engine_name())
    logger.info("AI backend   : %s", ai_service.get_backend_name())
    logger.info("Ear          : %s", recitation.ears.active())
    logger.info("Backend startup complete")
    yield


def create_app() -> FastAPI:
    settings = get_settings()  # validates .env; warns on bad key, never crashes

    app = FastAPI(
        title="Tafheem",
        description=(
            "I'raab analysis, Sarf breakdown, Quranic corpus lookup, and an Arabic-English dictionary. "
            "Works offline with local NLP; uses AI (Groq or Ollama) when available."
        ),
        version="2.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(GZipMiddleware, minimum_size=1000)  # hadith books run to hundreds of KB
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    for router in (
        analysis.router,
        morphology.router,
        quran.router,
        dictionary.router,
        practice.router,
        tarkeeb.router,
        daleel.router,
        listen.router,
        journal.router,
        progress.router,
        tamreen.router,
        nahw_notes.router,
        timelines.router,
        colloquial.router,
        grow.router,
        hadith.router,
        rijal.router,
        dawah.router,
        speak.router,
    ):
        app.include_router(router)

    # The access log has the path and status of every request; a crash also says
    # whose record it was, so one learner's report can be found. Never the body.
    # The traceback follows from the server's own log.
    @app.exception_handler(Exception)
    async def log_crash(request: Request, error: Exception) -> JSONResponse:
        logger.error("%s %s failed for profile %r: %r", request.method, request.url.path,
                     request.headers.get("x-tafheem-profile", "local"), error)
        return JSONResponse(status_code=500, content={"detail": "The server hit an error."})

    @app.get("/api/health")
    async def health(response: Response) -> dict:
        # 503 until the background loads finish: see services/startup.py's `loading`.
        if startup.loading:
            response.status_code = 503
        return {
            "status": "loading" if startup.loading else "ok",
            "loading": sorted(startup.loading),
            "nlp_engine": get_engine_name(),
            "ai_backend": ai_service.get_backend_name(),
            # Which ear would answer a spoken search right now. Here for the
            # same reason ai_backend is: an engine that quietly stopped working
            # should be visible, not guessed at from how slow the app feels.
            "ear": recitation.ears.active(),
            # Words and a search are heard by the same chain now, so this is
            # the same ear as "ear" above, named as the recitation model asks
            # for it (its Qur'an model rather than its general one, when the
            # answering ear is the one on this machine).
            "recite_ear": recitation.ears.active(reciting=True),
            # Which voice would say a new word (GET /api/speak), or why none would.
            "voice": speech.active(),
            # How sure the ear is of each word is always scored by the model on
            # this machine (see services/recitation/ears.py's "Word sureness"),
            # whichever ear wrote the words down, so it is named on its own.
            # The trial model's name when one is installed, else empty; the
            # page offers the "Trial" listening choice only when this is set.
            "recite_trial": recitation.listen.trial_model(),
            "recite_sure": recitation.ears.named("here").name(reciting=True),
            # How many readings a minute the page may ask for, all keys
            # together; lib/recitingSession.js paces itself by it.
            "listen_per_minute": recitation.ears.per_minute(),
            "corpus_loaded": quran_service.is_loaded(),
            "dictionary_loaded": dictionary_service.is_loaded(),
            "root_meaning_status": root_meaning.status(),
            "parser": syntax.status(),
        }

    # Everything the app is built on, in one list. Sits beside /api/health
    # rather than in a router because it is the same kind of thing: a fact
    # about the app itself, not an answer about a word someone typed.
    @app.get("/api/sources")
    async def sources() -> dict:
        return {"sources": provenance.all_sources()}

    return app


app = create_app()
