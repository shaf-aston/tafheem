"""Hearing a recitation and finding the ayah.

Five pieces, each with one job, so any of them can be replaced without the
others noticing:

    hosted.py   sound  -> words        the same job, done on Groq's machines
    listen.py   sound  -> words        the engine on this computer
    ears.py     the two above as one interface, and the order they are tried in
    match.py    words  -> ayahs        pure, no files, no network
    place.py    words  -> page stretch pure, where a recording sits on a page
    this file   asks for words, and hands the corpus to the matcher

Which ear answers is ears.py's business and nothing above this package knows
there is a choice at all. It used to be one `if` here; it is an interface and an
ordered chain now, the same shape services/ai already uses for the backends that
explain grammar, so a rejected key is struck off once instead of retried on
every recording.

The corpus is read from quran_corpus, which is already the only module that
opens it. Nothing here keeps a second copy of the Qur'an.
"""
from __future__ import annotations

import json
import logging
from functools import lru_cache

from backend.config import data_path, get_settings
from backend.services import quran_corpus
from backend.services.timing import timed
from backend.services.recitation import ears, letters, listen, match, place
# Re-exported so a caller catches them from the package it already talks
# to. Which piece in here raises which is this package's own business,
# and a route that imports them by submodule has to know.
from backend.services.recitation.ears import Unreadable
from backend.services.recitation.listen import NotInstalled
from backend.services.recitation.spelling import as_heard
from backend.services.recitation.match import Match

log = logging.getLogger(__name__)

SURAHS = 114


@lru_cache(maxsize=1)
def _ayahs() -> tuple:
    """Every ayah, read once and folded once, ready to match against.

    Cached because it is the same 6,236 lines every time, the matcher walks all
    of them on every recitation, and folding them is most of the work. Roughly a
    megabyte of text. Read through quran_corpus, which is already the only
    module that opens the corpus, so there is no second copy of the Qur'an here.
    """
    return match.prepare(
        (surah, ayah, text)
        for surah in range(1, SURAHS + 1)
        for ayah, text in quran_corpus.ayah_texts(surah)
    )


def warm() -> None:
    """Do both slow first-time jobs now, so the first recitation does not.

    Two things are slow exactly once: loading the model, about a second, and
    folding the Qur'an, about another. Both were landing on whoever pressed the
    microphone first, on top of their own recitation. Never raises: a machine
    that cannot listen is still a machine that runs the rest of the app.

    The Qur'an model is loaded whatever the key situation: a recitation is
    heard here even when Groq is available, and the first one
    was paying ten seconds for the load on top of its own reading. The general
    model is not: it answers a search box, only ever without Groq, and the
    first such search pays about a second.
    """
    listen.warm()
    if "letters" in get_settings().recitation_ears:
        letters.warm()
    try:
        _ayahs()
    except Exception:  # pragma: no cover, a corpus that is not built yet
        pass


def transcribe(audio: bytes, language: str | None = None, hint: str = "") -> str:
    """What was said, as words. Empty when nothing could be made out.

    Name a language to hear it in that one; leave it out and it is heard in
    whichever of the dictation languages the recording sounds like.

    A recitation is heard the same way anything else is: the ears in the order
    config names, the quick one first and this machine last. Checking a
    recitation's sureness is a separate question, asked of the model on this
    machine directly (see `check`), not routed through the ears at all.
    """
    if not audio:
        return ""
    return ears.hear(audio, language, hint)


def find(heard: str, limit: int = 5) -> list[Match]:
    """The ayahs closest to what was heard, best first."""
    return match.best(heard, _ayahs(), limit=limit)


def hear(audio: bytes, match_ayahs: bool, recite: bool = False, fusha: bool = True) -> tuple[str, list[Match]]:
    """Words, plus the ayahs they came from when asked.

    Rules live here, beside the ears, not in the route:
    - `match_ayahs`, `recite`: either makes it a recitation, Arabic and no
      language guess; the first also looks the ayahs up. A search is either.
    - `fusha`: the reader's switch; on sends the register hint, off sends none.
      A recitation never gets it either way: the Qur'an model hears worse with it.
    """
    settings = get_settings()
    text = transcribe(
        audio,
        language=settings.recitation_language if match_ayahs or recite else None,
        hint=settings.recitation_fusha_hint if fusha else "",
    )
    if not text or not match_ayahs:
        return text, []
    return text, find(text, limit=settings.recitation_matches)


@lru_cache(maxsize=1)
def _plain() -> dict[str, str]:
    """Every ayah in the ear's own spelling source, by "surah:ayah". Read once."""
    return json.loads(data_path("quran_imlaei_path").read_text(encoding="utf-8"))


def check(audio: bytes, heard: str, ayahs: list[str]) -> dict[str, list[float | None]]:
    """How sure the ear is of each word of these ayahs, from this recording.

    Per ayah, one number per word, 0 to 1, or None for a word this recording
    does not reach: it was said in another one, and scoring it here would call
    it unsaid. Nothing at all when the recording does not place on these ayahs,
    or places on more words than one recording can hold. The page words are
    Uthmani and the ear is only fair to its own spelling, which is why the
    ayahs are named rather than their words sent (see quran_imlaei_path).
    """
    settings = get_settings()
    plain = _plain()
    words, owner = [], []
    for key in ayahs:
        spelt = as_heard(plain.get(key, ""))
        words += spelt
        owner += [key] * len(spelt)
    span = place.reach(words, heard.split())
    if span is None:
        return {}
    first, last = span
    # On to the end of the ayah it stops in. The transcript drops a word it is
    # unsure of, most often the last one said, and that is exactly the word
    # this is here to check: al-Fatihah's last word, recited perfectly, was
    # left unwritten and scored 1.00. A word not said yet mostly scores low
    # (cut recordings: the next word 0.1 or more one time in six, later words
    # one in twenty, none 0.9), so the page lets a later reading replace it.
    while last < len(words) and owner[last] == owner[last - 1]:
        last += 1
    if last - first > settings.recitation_sure_max_words:
        log.info("placed on %d words, more than one recording holds; not checked", last - first)
        return {}
    sure = timed("checked", listen.sureness, audio, words[first:last], words=last - first)
    out = {key: [None] * owner.count(key) for key in dict.fromkeys(owner)}
    for i, score in zip(range(first, last), sure):
        key = owner[i]
        out[key][i - owner.index(key)] = round(score, 3)
    return out
