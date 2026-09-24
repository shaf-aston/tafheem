"""Sound in, words out. The one place an engine is named.

Everything above this file asks for words and does not care how they were got,
so swapping the engine is one function. Today it is faster-whisper running on
this machine: free, no account, no key, and nothing leaves the computer. The
model it uses is already on this machine, cached under the user's own profile.

Loaded once and kept, so only the first recitation pays for it. The app also
warms it in the background as it starts, so usually nobody pays for it at all;
that is `warm()` below, and turning it off in the settings puts the cost back on
whoever speaks first.

A recitation is Arabic, asked for by name rather than detected. A few seconds of
speech is short enough that free detection guesses, and a wrong guess does not
return worse Arabic, it returns another language entirely.

A spoken search is not a recitation: the word may be said in either language, and
Arabic asked for by name wrote English words in Arabic letters, "knowledge"
coming back as نالج. So there the language is chosen from the recording, but only
ever from the two in config's `dictation_languages`, which is what stops the
guess wandering to Urdu or Persian. It costs one extra pass over the sound.

Why it is as quick as it is
---------------------------
Measured on sixteen real recitations, the wait went from about four seconds to
about one. Three things did it, and none of them changed which ayah came back;
the fourth was later given back on purpose, for strictness:

  a smaller model    base rather than small. Both found the right ayah fifteen
                     times out of sixteen. See the note in config.py.
  one reading        the model no longer weighs five wordings and picks between
                     them. The matching wants close words, not right ones.
  no silence         the quiet at each end of a browser recording is cut rather
                     than transcribed. One word said quickly can be cut along
                     with it, so a recording that comes back empty is read a
                     second time with the cutting off, which is the difference
                     between "nothing was heard" and hearing it.
  no timestamps      the fourth. It was given back for a while, to drop words
                     the model doubted, and is now off again: the transcript no
                     longer decides whether a word is wrong, and dropping words
                     broke the run of them that finds the place. Half the wait,
                     and it places better. See recitation_word_min in config.
"""
from __future__ import annotations

import logging
import tempfile
import threading
import time
from pathlib import Path

import numpy as np

from backend.config import get_settings
from backend.services.timing import timed

log = logging.getLogger(__name__)

# The model itself, not the recording. routers/listen.py already keeps two
# recitations from being read at once (_turn), but a plain search that falls
# back to this engine skips that queue on purpose, and the model is handed
# most of this machine's cores (recitation_threads): two calls into it at once
# ask for twice the cores there are, and both take longer than either would
# have waited. Held around every call into the model, transcribing and
# scoring alike, never nested: transcribe() and scores() are asked one after
# the other, never from inside each other, so a plain (non-reentrant) Lock is
# enough.
_engine_lock = threading.Lock()

# Timed here, and only here, are the steps that cost whole seconds on this
# machine: opening the recording, loading a model, reading it, and scoring the
# page words against it. Everything else in this file is arithmetic on numbers
# already in memory and timing it would only bury these lines. One grep on
# backend.log then says where a slow reading went, without measuring again.
# The lines read: decoded / loaded / read / encoded / scored.

_models: dict = {}
# The last recording decoded, and the sound in it. See sound_of.
_last: tuple | None = None
# The ear hears thirty seconds at a time: 3,000 frames of 10ms.
_WINDOW_FRAMES = 3000


class NotInstalled(RuntimeError):
    """The engine is not available on this machine. Said plainly, not guessed at."""


def window_of(frames: int, block: int) -> int:
    """How long a stretch to hand the ear for a recording this long.

    The recording's own length rounded up to a whole block, and never more than
    the thirty seconds the ear can hold. Silence costs the ear exactly what
    sound costs, so padding a six second recording out to thirty was paying six
    times over for nothing; see recitation_window_block in config.
    """
    return min(_WINDOW_FRAMES, max(block, -(-frames // block) * block))


def sound_of(audio: bytes):
    """The sound in a recording, at a workable loudness, decoded once.

    Once per recording, not once per question. The app asks a recording two
    things, "write down what you heard" and "how sure are you of these words",
    and each was writing the same bytes to its own temporary file and decoding
    them again. Same bytes, same sound, and decoding is not free.

    Only the last recording is kept, because the questions about one come one
    after the other and the next recording is a different one. Keeping more
    would be holding somebody's voice in memory for no reason.

    The engine reads a file rather than bytes, so the recording is written to a
    temporary one and deleted afterwards however this ends: nothing a
    microphone picked up stays on disk after the answer is given.

    The magic bytes at the front of a recording say what it claims to be; they
    do not say the rest of it is there. A truncated browser recording carries a
    valid webm header and nothing playable behind it, and saying so is worth it
    because trying the next ear only spends more seconds reaching the same
    answer.

    And this being the one place a recording becomes sound, it is the one place
    the sound is levelled, so nothing below ever sees a recitation too quiet to
    read. loudness.py says why, and leaves a loud enough one exactly as it was.
    """
    from faster_whisper.audio import decode_audio

    from backend.services.recitation import loudness
    from backend.services.recitation.ears import Unreadable

    global _last
    if _last is not None and _last[0] == audio:
        return _last[1]

    handle = tempfile.NamedTemporaryFile(suffix=".audio", delete=False)
    try:
        handle.write(audio)
        handle.close()
        # PyAV, in this process. Not free, and the reason a recording is only
        # opened once however many questions are asked about it.
        sound = timed("decoded", decode_audio, handle.name, kb=len(audio) // 1024)
    except Exception as exc:
        raise Unreadable("That recording could not be read. Record it again.") from exc
    finally:
        Path(handle.name).unlink(missing_ok=True)

    settings = get_settings()
    lifted = loudness.levelled(
        sound,
        target=settings.recitation_loudness_target,
        ceiling=settings.recitation_loudness_ceiling,
        floor=settings.recitation_loudness_floor,
        most=settings.recitation_loudness_most,
    )
    if lifted is not sound:
        log.info("brought the recording up from %.4f to %.4f", loudness.loudness(sound),
                 loudness.loudness(lifted))
    _last = (audio, lifted)
    return lifted


def _engine(name: str):
    """The named model, loaded on first use and kept.

    Two are named in config, one for reciting and one for the search boxes,
    and each is only loaded once something asks for it.
    """
    if name in _models:
        return _models[name]

    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:  # pragma: no cover, depends on the machine
        raise NotInstalled(
            "faster-whisper is not installed, so nothing can listen. "
            "Install it with: pip install faster-whisper"
        ) from exc

    settings = get_settings()
    # Seconds, once, and it is why the first recitation after a restart is slow
    # while every one after it is not. warm() exists to spend it up front.
    started = time.perf_counter()
    build = dict(
        device=settings.recitation_device,
        compute_type=settings.recitation_compute,
        cpu_threads=settings.recitation_threads,
    )
    try:
        # The copy already on this machine, without asking the internet whether
        # there is a newer one. That question costs a second every startup and
        # the answer never changes; more to the point, this app works with the
        # network unplugged and loading a model should not be the exception.
        _models[name] = WhisperModel(name, local_files_only=True, **build)
    except Exception:
        # Not on this machine yet. Fetching it is a one-off of a few hundred
        # megabytes, and after that the line above is the one that runs.
        log.info("downloading the %s model, once", name)
        _models[name] = WhisperModel(name, **build)
    log.info("loaded  model=%s  threads=%d  %.0fms", name, settings.recitation_threads,
             (time.perf_counter() - started) * 1000)
    return _models[name]


def warm() -> None:
    """Load the model now, so nobody waits for it later. Never raises.

    Called at startup on a background thread. A machine without the engine
    installed is an ordinary machine, not a broken one: it says so in the log
    and the app carries on, and the first person to press the microphone gets
    the plain "not installed" answer they would have got anyway.
    """
    try:
        _engine(get_settings().recitation_model)
    except Exception as exc:  # pragma: no cover, depends on the machine
        log.info("listening is unavailable: %s", exc)


def transcribe(audio: bytes, language: str | None = None, hint: str = "") -> str:
    """What was said, as plain words. Empty when there was nothing to hear.

    `language` is the language to hear it in, and naming one makes this a
    recitation: the Qur'an model, no register hint, and a word it is not sure
    of left out. Leaving it out is dictation, heard by the
    general model in whichever of the dictation languages the recording sounds
    like.

    The recording becomes sound in sound_of, which is the only place it does,
    and which keeps the last one so the check that follows does not decode the
    same recording again.
    """
    if not audio:
        return ""

    settings = get_settings()
    sound = sound_of(audio)
    reciting = language is not None
    how = dict(
        model=settings.recitation_model if reciting else settings.dictation_model,
        language=language or _which_language(sound),
        hint="" if reciting else hint,
        word_min=settings.recitation_word_min if reciting else 0.0,
        # The general model returns nothing on silence by itself and rates
        # real speech up to 0.13 not-speech, so the floor is the Qur'an ear's.
        no_speech_max=settings.recitation_no_speech_max if reciting else 1.0,
    )
    # The single most expensive thing the app does. Logged with what explains a
    # slow one: which model, how many seconds of sound, and whether word timing
    # was asked for, which on its own more than doubles this line.
    seconds = round(len(sound) / 16000, 1)
    with _engine_lock:
        heard = timed("read", lambda: _read(sound, trim=settings.recitation_trim_silence, **how),
                      model=how["model"], s=seconds, timing=how["word_min"] > 0)

        # The silence trimmer decides what is speech and what is room, and on a
        # single word said quickly it has decided the whole recording was room: a
        # real 0.9 second search came back with 0.9 seconds removed and nothing
        # left to read. So an empty answer is asked again with the trimming off,
        # rather than told to the reader as "nothing was heard". Only when it was
        # on, and only when the first read found nothing, so a recording that
        # worked still costs one read.
        if not heard and settings.recitation_trim_silence:
            log.info("nothing survived the silence trim, reading it again untrimmed")
            heard = timed("read", lambda: _read(sound, trim=False, **how),
                          model=how["model"], s=seconds, trim=False)

    # The words themselves, not how many characters there were. A reader showed
    # a wrongly marked page and what the ear had actually written down had to
    # be reconstructed from the app's own behaviour, because the only record of
    # it was a length. The log file is UTF-8 (main.py).
    log.info("wrote down: %s", heard or "(nothing)")
    return heard


def scores(audio: bytes, words: list[str]) -> list[dict]:
    """What the Qur'an ear makes of each of `words`, in order, given the sound.

    Per word: `probs`, how likely each piece of it was, 0 to 1; and `at`, the
    second of the recording the word's last piece lines up with, or None when
    the ear gave no position for it.

    Checking, not transcribing: the ear is handed the words the page expects
    and asked how likely each is given the sound, so a misheard word is never
    written down and then compared. Words must be in the ear's own spelling
    (spelling.as_heard).

    The pieces, rather than one number a word: how a word's pieces become one
    verdict is a rule, and a rule belongs where it can be measured and changed,
    not buried in the one function that cannot be changed without a model run.
    `at` is what this same call has always returned alongside the likelihoods
    and what the app has always thrown away; it is where the reciter has got
    to, known from the sound rather than guessed from a transcript.

    What was tried here and does not work
    -------------------------------------
    Arabic drops a word's last vowel at a stop, so a reciter stopping on
    أَحَدٌ correctly says أَحَدْ, and asking about the written form looked like
    the reason correct reciting was being marked. It is not. Asked about the
    stopped spelling of a word a reciter had plainly stopped on, this ear
    answers 0.000, every time, while answering 1.000 for the written one. The
    number is how likely the ear finds that *text* given the sound, and no
    Arabic text writes أَحَدْ, so the spelling sinks it whatever was said. A
    stop is heard correctly here already; what marks a correct word is the rule
    that turns pieces into one number, which is why that rule is now config.
    """
    from faster_whisper.tokenizer import Tokenizer

    if not words:
        return []
    settings = get_settings()
    model = _engine(settings.recitation_model)
    features = model.feature_extractor(sound_of(audio))
    frames = min(features.shape[-1], _WINDOW_FRAMES)
    padded = np.zeros((features.shape[0], window_of(frames, settings.recitation_window_block)),
                      dtype=features.dtype)
    padded[:, :frames] = features[:, :frames]
    tokenizer = Tokenizer(model.hf_tokenizer, True, task="transcribe", language="ar")
    # The first word has no space before it, as the ear writes it.
    pieces = [tokenizer.encode(("" if i == 0 else " ") + w) for i, w in enumerate(words)]
    # Two separate costs, and they answer different questions. "encoded" is the
    # ear listening to the sound and does not care how many words are asked
    # about; "scored" is it weighing those words and grows with them. A slow
    # check is one or the other, and one line each says which without guessing.
    with _engine_lock:
        listened = timed("encoded", model.encode, padded, s=round(frames / 100, 1))
        answer = timed(
            "scored",
            lambda: model.model.align(
                listened, tokenizer.sot_sequence, [[t for p in pieces for t in p]], frames,
            ),
            words=len(words), rule=get_settings().recitation_sure_of_word,
        )[0]
    # align gives one (piece, frame) pair per piece, and two of the encoder's
    # frames are a hundredth of a second of sound.
    where = dict(answer.alignments)
    out, at = [], 0
    for piece in pieces:
        end = at + len(piece)
        out.append({
            "probs": [float(p) for p in answer.text_token_probs[at:end]],
            "at": round(where[end - 1] / 100, 2) if end - 1 in where else None,
        })
        at = end
    return out


def sureness(audio: bytes, words: list[str]) -> list[float]:
    """How sure the ear is of each word, one number each, at the rule in config."""
    rule = get_settings().recitation_sure_of_word
    return [aggregate(word["probs"], rule) for word in scores(audio, words)]


def aggregate(probs: list[float], rule: str) -> float:
    """One number for a word out of how likely each of its pieces was.

    "worst" is its least sure piece: one piece of six sinks the word, which is
    what marked correctly recited words. "mean" averages them. "worst-but-one"
    forgives a single bad piece. Which one is config's to say.
    """
    if not probs:
        return 0.0
    if rule == "mean":
        return sum(probs) / len(probs)
    if rule == "worst-but-one" and len(probs) > 1:
        return sorted(probs)[1]
    return min(probs)


def dictation_languages() -> list[str]:
    """The languages a spoken search may be in. Never empty."""
    named = [
        name.strip().lower()
        for name in get_settings().dictation_languages.split(",")
        if name.strip()
    ]
    return named or [get_settings().recitation_language]


def _which_language(sound) -> str:
    """Which of the dictation languages this recording is in.

    The model is asked how likely every language is, and the answer is taken
    only from the short list: left free it hears one English word as Urdu or
    Persian and writes it in their letters. One language on the list means there
    is nothing to choose and no encoding pass is spent on choosing it.
    """
    allowed = dictation_languages()
    if len(allowed) == 1:
        return allowed[0]

    _, _, chances = _engine(get_settings().dictation_model).detect_language(sound)
    scored = dict(chances)
    spoken = max(allowed, key=lambda name: scored.get(name, 0.0))
    log.info("heard as %s (%s)", spoken, ", ".join(
        f"{name} {scored.get(name, 0.0):.2f}" for name in allowed))
    return spoken


def _read(sound, trim: bool, model: str, language: str, hint: str, word_min: float, no_speech_max: float) -> str:
    """One pass of the named model over the sound. The words, joined, or nothing."""
    settings = get_settings()
    segments, _ = _engine(model).transcribe(
        sound,
        language=language,
        initial_prompt=hint or None,
        beam_size=settings.recitation_beam,
        repetition_penalty=settings.recitation_repetition_penalty,
        vad_filter=trim,
        # Sureness per word comes only with word timing, and timing costs about
        # a second a read and lets the model tack invented words onto a quiet
        # tail (مَا يَغْفَى, at 0.6 sure). So timing is asked for only when a
        # word floor is set to catch those; otherwise the read is timeless.
        word_timestamps=word_min > 0,
        without_timestamps=word_min == 0,
        # Each stretch of sound is read on its own. Left to itself the model
        # feeds what it just heard back in as context, which on recitation
        # makes it finish the ayah for you: it wrote out the rest of Ayat
        # al-Kursi that had not been said.
        condition_on_previous_text=False,
    )
    # Silence read untrimmed comes back as a word, and a mumble as the nearest
    # real one; the model's own doubt is what tells. See config for the numbers.
    heard = [s for s in segments if s.no_speech_prob <= no_speech_max]
    if word_min == 0:
        return " ".join(s.text.strip() for s in heard).strip()
    return " ".join(
        w.word.strip() for s in heard for w in s.words if w.probability >= word_min
    ).strip()
