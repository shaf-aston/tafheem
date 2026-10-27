"""The local ear: faster-whisper on this machine, for writing words down and for
scoring how sure each word is (the base or tuned model). Free, no key, nothing
leaves the computer. Loaded once and warmed at startup (`warm()`).

A recitation is asked for in Arabic by name: a few seconds is too short for
detection, and a wrong guess returns another language. A spoken search picks
between config's `dictation_languages` only (Arabic by name spelt "knowledge"
as نالج), at one extra pass.

Speed (16 real recitations, ~4 s to ~1 s, same ayahs found): the base model,
one beam, silence trimmed (an empty result is re-read untrimmed), and no word
timestamps (see recitation_word_min in config).
"""
from __future__ import annotations

import io
import logging
import time

from backend.config import confined, get_settings
from backend.services.core.timing import timed
from backend.services.recitation import loudness
from backend.services.recitation.errors import NotInstalled, Unreadable, local_lock

log = logging.getLogger(__name__)

# Only the steps costing whole seconds are timed: decoded / loaded / read / encoded / scored.

_models: dict = {}
# The last recording decoded, and the sound in it. See sound_of.
_last: tuple | None = None
def sound_of(audio: bytes):
    """The sound in a recording, at a workable loudness, decoded once.

    Once per recording, not once per question. The app asks a recording two
    things, "write down what you heard" and "how sure are you of these words",
    and each was writing the same bytes to its own temporary file and decoding
    them again. Same bytes, same sound, and decoding is not free.

    Only the last recording is kept, because the questions about one come one
    after the other and the next recording is a different one. Keeping more
    would be holding somebody's voice in memory for no reason.

    Decoded straight from memory. It used to be written to a temporary file
    and deleted again for every recording, a trip to the disk that bought
    nothing: the decoder reads a file object as readily as a path, and this
    way nothing a microphone picked up ever touches the disk at all.

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

    global _last
    if _last is not None and _last[0] == audio:
        return _last[1]

    try:
        # PyAV, in this process. Not free, and the reason a recording is only
        # opened once however many questions are asked about it.
        sound = timed("decoded", decode_audio, io.BytesIO(audio), kb=len(audio) // 1024)
    except Exception as exc:
        raise Unreadable("That recording could not be read. Record it again.") from exc

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


def engine(name: str):
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
    # A folder inside backend/ is loaded as it is, and a broken one fails here with its own error;
    # anything else is a model name, "repo@revision" pinning one upload of a tuned ear
    # (scripts/recitation/finetune_ear/cloud.py --ship), so a new upload is a new name, never a stale copy.
    folder = confined("recitation_model", name)
    if folder.is_dir():
        _models[name] = WhisperModel(str(folder), **build)
    else:
        repo, _, revision = name.partition("@")
        build.update(revision=revision or None)
        try:
            # The copy already on this machine, without asking the internet whether
            # there is a newer one. That question costs a second every startup and
            # the answer never changes; more to the point, this app works with the
            # network unplugged and loading a model should not be the exception.
            _models[name] = WhisperModel(repo, local_files_only=True, **build)
        except Exception:
            # Not on this machine yet. Fetching it is a one-off of a few hundred
            # megabytes, and after that the line above is the one that runs.
            log.info("downloading the %s model, once", name)
            _models[name] = WhisperModel(repo, **build)
    log.info("loaded  model=%s  threads=%d  %.0fms", name, settings.recitation_threads,
             (time.perf_counter() - started) * 1000)
    return _models[name]


def tuned_model() -> str:
    """The tuned model as configured (a folder or "repo@revision"), or "" when none is set."""
    return get_settings().recitation_tuned_model


def warm() -> None:
    """Load the model now, so nobody waits for it later. Never raises.

    Called at startup on a background thread. A machine without the engine
    installed is an ordinary machine, not a broken one: it says so in the log
    and the app carries on, and the first person to press the microphone gets
    the plain "not installed" answer they would have got anyway.
    """
    try:
        engine(get_settings().recitation_model)
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
    with local_lock:
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

    _, _, chances = engine(get_settings().dictation_model).detect_language(sound)
    scored = dict(chances)
    spoken = max(allowed, key=lambda name: scored.get(name, 0.0))
    log.info("heard as %s (%s)", spoken, ", ".join(
        f"{name} {scored.get(name, 0.0):.2f}" for name in allowed))
    return spoken


def _read(sound, trim: bool, model: str, language: str, hint: str, word_min: float, no_speech_max: float) -> str:
    """One pass of the named model over the sound. The words, joined, or nothing."""
    settings = get_settings()
    segments, _ = engine(model).transcribe(
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
