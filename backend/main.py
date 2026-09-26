"""Tafheem, FastAPI application entry point."""
from __future__ import annotations

import asyncio
import gc
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import get_settings
from backend.routers import (
    analysis, daleel, dictionary, journal, listen, morphology, nahw_notes, practice, progress, quran, tamreen,
    tarkeeb, timelines,
)
from backend.services import ai as ai_service
from backend.services import dictionary_service, provenance, quran_service, recitation, root_meaning
from backend.services.morphology import get_engine_name

BACKEND_ROOT = Path(__file__).resolve().parent
LOG_PATH = BACKEND_ROOT.parent / "backend.log"
NAHW_RULES_PATH = BACKEND_ROOT / "data" / "nahw_rules" / "rules.json"

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


def _load_optional(label: str, loader: Callable[[], None]) -> None:
    """Run a startup loader; log but never abort on failure."""
    logger.info("Loading %s...", label)
    try:
        loader()
    except Exception as exc:
        logger.warning("Failed to load %s (non-fatal): %s", label, exc)


def _warm_and_freeze() -> None:
    """Load the recitation model, then set it aside from the collector too.

    warm() lazily imports faster_whisper/ctranslate2, which tracks its own new
    objects; without a second freeze those cost the same sweep the dictionaries
    below were frozen to avoid.
    """
    _load_optional("Recitation", recitation.warm)
    gc.collect()
    gc.freeze()


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Run all three loaders concurrently to speed up startup
    loop = asyncio.get_running_loop()
    await asyncio.gather(
        loop.run_in_executor(None, lambda: _load_optional("Nahw rules", lambda: ai_service.load_nahw_rules(str(NAHW_RULES_PATH)))),
        loop.run_in_executor(None, lambda: _load_optional("Arabic-English dictionary", dictionary_service.load_dictionary)),
        loop.run_in_executor(None, lambda: _load_optional("Classical root meanings", root_meaning.load)),
    )

    # faster_whisper.audio.decode_audio runs a full gc.collect() after every
    # decode. With the dictionaries above loaded, that sweep walks ~470k
    # gc-tracked objects that never die, costing ~330ms per recording for a
    # ~30ms decode. Freezing them here moves them out of the collector's reach
    # for good. Rejected: a hand-written decoder to dodge the library's sweep,
    # which would duplicate faster-whisper's own file-reading code.
    gc.collect()
    gc.freeze()

    # Not awaited. The listening model takes about a second to load and nothing
    # on any page needs it until somebody presses the microphone, so it is
    # started and left to finish: waiting for it here would only move the delay
    # from the first recitation to every startup.
    if get_settings().recitation_warm:
        loop.run_in_executor(None, _warm_and_freeze)

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
    ):
        app.include_router(router)

    @app.get("/api/health")
    async def health() -> dict:
        return {
            "status": "ok",
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
            # How sure the ear is of each word is always scored by the model on
            # this machine (see services/recitation/ears.py's "Word sureness"),
            # whichever ear wrote the words down, so it is named on its own.
            "recite_sure": recitation.ears.named("here").name(reciting=True),
            # How many readings a minute the page may ask for, all keys
            # together; lib/recitingSession.js paces itself by it.
            "listen_per_minute": recitation.ears.per_minute(),
            "corpus_loaded": quran_service.is_loaded(),
            "dictionary_loaded": dictionary_service.is_loaded(),
            "root_meaning_status": root_meaning.status(),
        }

    # Everything the app is built on, in one list. Sits beside /api/health
    # rather than in a router because it is the same kind of thing: a fact
    # about the app itself, not an answer about a word someone typed.
    @app.get("/api/sources")
    async def sources() -> dict:
        return {"sources": provenance.all_sources()}

    return app


app = create_app()
