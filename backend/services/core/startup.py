"""What loads when the backend starts, by name; config decides which and when.

Every loader sits in STEPS under one name. settings.startup_wait lists the ones
finished before the first request is served; settings.startup_background the
ones started and left to finish. Adding a loader is one line here and its name
in config; turning one off on a small machine is removing its name. A loader
that fails is logged and skipped, never fatal. An unknown name is fatal: a typo
in config would otherwise leave a tab slow with nothing saying why.
"""
from __future__ import annotations

import asyncio
import gc
import logging
from typing import Callable

from backend.config import get_settings
from backend.services import recitation, speech
from backend.services.colloquial import loader as colloquial
from backend.services.daleel import search as daleel
from backend.services.dictionary import root_meaning
from backend.services.dictionary import service as dictionary_service
from backend.services.hadith import meaning as hadith_meaning
from backend.services.learner import progress_store
from backend.services.nahw import syntax
from backend.services.sarf import verb_reader

logger = logging.getLogger(__name__)

def _freeze() -> None:
    # faster_whisper.audio.decode_audio runs a full gc.collect() after every
    # decode; with everything loaded that sweep walks ~340k objects that never
    # die, ~200ms per recording for a ~14ms decode (measured on the server).
    # Frozen, the collector skips them for good. Every step freezes what it
    # loaded: freezing only after the recitation step left the parser, Daleel
    # and the rest unfrozen, and the sweep came back. Rejected: a hand-written
    # decoder to dodge the sweep.
    gc.collect()
    gc.freeze()


STEPS: dict[str, tuple[str, Callable[[], object]]] = {
    "dictionary": ("Arabic-English dictionary", dictionary_service.load_dictionary),
    "root_meanings": ("Classical root meanings", root_meaning.load),
    "recitation": ("Recitation model", recitation.warm),
    "speech": ("Voice", speech.warm),
    "colloquial": ("Colloquial units", colloquial.catalogue),
    "nahw_parser": ("Nahw parser", syntax.warm),
    "sarf_reader": ("Sarf verb reader", verb_reader.warm),
    "hadith_meaning": ("Hadith meaning search", hadith_meaning.warm),
    "daleel": ("Daleel search", daleel.warm),
    "guest_sweep": ("Idle guest records", progress_store.sweep),
}


# Steps not finished yet. /api/health answers 503 while any remain, so the proxy
# and the deploy's rolling restart keep sending visitors to the copy already warm
# (a cold Analyze waited ~40s for the parser on the 2-core server).
loading: set[str] = set()


def _run(name: str) -> None:
    label, load = STEPS[name]
    logger.info("Loading %s...", label)
    try:
        load()
    except Exception as exc:
        logger.warning("Failed to load %s (non-fatal): %s", label, exc)
    finally:
        _freeze()
        loading.discard(name)


async def run() -> None:
    """Awaits startup_wait together, freezes what they loaded, then starts startup_background."""
    settings = get_settings()
    unknown = [n for n in (*settings.startup_wait, *settings.startup_background) if n not in STEPS]
    if unknown:
        raise ValueError(f"Unknown startup step(s) {unknown}; known: {sorted(STEPS)}")
    loading.update(settings.startup_background)
    loop = asyncio.get_running_loop()
    await asyncio.gather(*(loop.run_in_executor(None, _run, n) for n in settings.startup_wait))
    for name in settings.startup_background:
        loop.run_in_executor(None, _run, name)
