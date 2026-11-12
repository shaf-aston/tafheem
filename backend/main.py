"""Tafheem, FastAPI application entry point."""
from __future__ import annotations

import logging
import re
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.config import get_settings
from backend.routers import (
    analyze, colloquial, daleel, dawah, dictionary, grow, hadith, journal, listen, morphology, nahw_notes, practice, progress, quran,
    recordings, speak, tamreen, tarkeeb, timelines,
)
from backend.services import ai as ai_service
from backend.services import recitation, speech
from backend.services.dictionary import service as dictionary_service
from backend.services.core import audit, provenance
from backend.services.core.headers import ApiHeaders, SameOrigin, crash_headers
from backend.services.core.ratelimit import visitor
from backend.services.quran import service as quran_service
from backend.services.dictionary import root_meaning
from backend.services.core import startup
from backend.services.nahw import syntax
from backend.services.hadith.usul import store as usul
from backend.services.sarf.morphology import get_engine_name
from backend.identity import GUEST_HEADER, PROFILE_HEADER
from backend.services.learner.username import GUEST

# Answers that are the same for everyone and change only when the app does, so
# a browser or Vercel's edge may keep them for a day. An allow-list, not a
# default: anything per-learner (progress, journal), anything typed (search,
# analyze) or anything that reports on the server (health) must never be here.
# Nor the list of installed translations: an import adds to it.
CACHEABLE = re.compile(
    r"/api/(?:"
    r"quran/surah/\d+(?:/glosses)?"
    r"|quran/similar/(?:surah/\d+|\d+/\d+)"
    r"|quran/editions/surah/\d+"
    r"|hadith/collections"
    r"|hadith/[^/]+/books(?:/\d+)?"
    r"|timelines(?:/[^/]+/[^/]+/asbab)?"
    r"|dawah|tamreen|notes|sources"
    r"|grow/(?:paths|worlds/[a-z-]+)"
    r"|tarkeeb/examples"
    r"|daleel/books"
    r"|colloquial(?:/[^/]+/[^/]+)?"
    r")"
)
CACHE_ONE_DAY = "public, max-age=86400"

# Every header the page sends (frontend/src: profile, device, the recitation's reading id, the
# speaking queue's hint, the recording studio's key). A new one is added here or the dev server refuses it.
CORS_HEADERS = [
    "Content-Type", "X-Request-ID", PROFILE_HEADER, GUEST_HEADER, "X-Reading-Id", "X-Speak-Ahead", "X-Recorder-Key",
]


def cacheable(method: str, status: int, path: str, existing: str | None) -> bool:
    """Whether this response may be given a day's cache, and has no opinion of its own."""
    return method == "GET" and status == 200 and not existing and CACHEABLE.fullmatch(path) is not None


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
logging.getLogger("httpx").addFilter(audit.NoQuery())  # a learner's search rides out as ?q=
logging.getLogger("httpx2").addFilter(audit.NoQuery())  # its successor (huggingface_hub uses it today)


@asynccontextmanager
async def lifespan(_: FastAPI):
    usul.glossary()  # a broken glossary stops the app here, as the dawah file does at its first read
    await startup.run()

    # Log which engines are active so the operator knows the mode at a glance
    logger.info("NLP engine   : %s", get_engine_name())
    logger.info("AI backend   : %s", ai_service.get_backend_name())
    logger.info("Ear          : %s", recitation.health()["ear"])
    if not get_settings().cookie_secure:  # right for a dev server on plain http, wrong anywhere else
        logger.warning("COOKIE_SECURE is off: the log-in cookie may travel over plain http. Dev only.")
    logger.info("Backend startup complete")
    yield


def create_app() -> FastAPI:
    settings = get_settings()  # validates .env; a bad or unknown key stops startup

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

    # Added after GZip, so it wraps it and sets the header on the finished response.
    @app.middleware("http")
    async def cache_fixed_answers(request: Request, call_next):
        response = await call_next(request)
        if cacheable(request.method, response.status_code, request.url.path, response.headers.get("cache-control")):
            response.headers["Cache-Control"] = CACHE_ONE_DAY
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        # No credentials: the device-token cookie (backend/identity.py) is the page's own, sent only to its
        # own address, never on a request from another site. Live, the page calls its own address
        # (vercel.json rewrites /api), and the dev server proxies /api, so this list only matters for a
        # page served from elsewhere in development.
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=CORS_HEADERS,
        expose_headers=["X-Request-ID"],
    )

    # Last added, so outermost: it sees every answer, CORS refusals included, and stamps each with
    # X-Request-ID. The visitor is decided by the rate limiter's rule, one place for which proxy to trust.
    app.add_middleware(SameOrigin)  # no write to /api from another site's page; inside ApiHeaders, so its 403 is stamped
    app.add_middleware(ApiHeaders)  # nosniff, a dead-page CSP and no-referrer on every /api answer
    app.add_middleware(audit.SecurityLog, client=lambda scope: visitor(Request(scope)))

    for router in (
        analyze.router,
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
        dawah.router,
        speak.router,
        recordings.router,
    ):
        app.include_router(router)

    # The access log has the path and status of every request; a crash also says
    # whose record it was, so one learner's report can be found. Never the body.
    # The traceback follows from the server's own log.
    @app.exception_handler(Exception)
    async def log_crash(request: Request, error: Exception) -> JSONResponse:
        logger.error("%s %s failed for profile %r: %r", request.method, request.url.path,
                     request.headers.get(PROFILE_HEADER, GUEST), error)
        # The id lets a learner's report be matched to the security log's line for it.
        return JSONResponse(status_code=500, content={"detail": "The server hit an error."},
                            headers=crash_headers(getattr(request.state, "request_id", "")))

    @app.get("/api/health")
    async def health(response: Response) -> dict:
        # 503 until the background loads finish: see services/core/startup.py's `loading`.
        if startup.loading:
            response.status_code = 503
        return {
            "status": "loading" if startup.loading else "ok",
            "loading": sorted(startup.loading),
            "nlp_engine": get_engine_name(),
            "ai_backend": ai_service.get_backend_name(),
            **recitation.health(),
            # Which voice would say a new word (GET /api/speak), or why none would.
            "voice": speech.active(),
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
