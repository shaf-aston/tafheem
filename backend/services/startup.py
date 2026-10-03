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
from backend.services import dictionary_service, recitation, root_meaning, speech, syntax
from backend.services.colloquial import loader as colloquial

logger = logging.getLogger(__name__)

def _freeze() -> None:
    # faster_whisper.audio.decode_audio runs a full gc.collect() after every
    # decode; with the dictionaries loaded that sweep walked ~470k objects that
    # never die, ~330ms per recording for a ~30ms decode. Frozen, the collector
    # skips them for good. Rejected: a hand-written decoder to dodge the sweep.
    gc.collect()
    gc.freeze()


def _recitation() -> None:
    # The model import tracks its own new objects, so they are frozen too.
    recitation.warm()
    _freeze()


STEPS: dict[str, tuple[str, Callable[[], object]]] = {
    "dictionary": ("Arabic-English dictionary", dictionary_service.load_dictionary),
    "root_meanings": ("Classical root meanings", root_meaning.load),
    "recitation": ("Recitation model", _recitation),
    "speech": ("Voice", speech.warm),
    "colloquial": ("Colloquial units", colloquial.catalogue),
    "nahw_parser": ("Nahw parser", syntax.warm),
}


def _run(name: str) -> None:
    label, load = STEPS[name]
    logger.info("Loading %s...", label)
    try:
        load()
    except Exception as exc:
        logger.warning("Failed to load %s (non-fatal): %s", label, exc)


async def run() -> None:
    """Awaits startup_wait together, freezes what they loaded, then starts startup_background."""
    settings = get_settings()
    unknown = [n for n in (*settings.startup_wait, *settings.startup_background) if n not in STEPS]
    if unknown:
        raise ValueError(f"Unknown startup step(s) {unknown}; known: {sorted(STEPS)}")
    loop = asyncio.get_running_loop()
    await asyncio.gather(*(loop.run_in_executor(None, _run, n) for n in settings.startup_wait))
    _freeze()
    for name in settings.startup_background:
        loop.run_in_executor(None, _run, name)
