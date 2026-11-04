"""How sure the Qur'an ear is of each word the page expects. Checking, not transcribing.

The ear (whisper.py) is handed the words and asked how likely each is given the
sound; this file turns that into one verdict a word, and says which piece of the
word was weakest. Kept apart from the ear because how pieces become a verdict is
a rule, and a rule belongs where it can be measured and changed.
"""
from __future__ import annotations

import numpy as np

from backend.config import get_settings
from backend.services.core.timing import timed
from backend.services.recitation import whisper
from backend.services.recitation.errors import local_lock

# The ear hears thirty seconds at a time: 3,000 frames of 10ms.
_WINDOW_FRAMES = 3000


def padded_frames(frames: int, block: int) -> int:
    """How long a stretch to hand the ear for a recording this long.

    The recording's own length rounded up to a whole block, and never more than
    the thirty seconds the ear can hold. Silence costs the ear exactly what
    sound costs, so padding a six second recording out to thirty was paying six
    times over for nothing; see recitation_window_block in config.
    """
    return min(_WINDOW_FRAMES, max(block, -(-frames // block) * block))


def scores(audio: bytes, words: list[str], model: str | None = None) -> list[dict]:
    """What the Qur'an ear makes of each of `words`, in order, given the sound.

    Per word: `probs`, how likely each piece of it was, 0 to 1; `weak`, the
    text of its least likely piece (see weakest); and `at`, the second of the
    recording the word's last piece lines up with, or None when the ear gave
    no position for it.

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
    model = whisper.engine(model or settings.recitation_model)
    features = model.feature_extractor(whisper.sound_of(audio))
    frames = min(features.shape[-1], _WINDOW_FRAMES)
    padded = np.zeros((features.shape[0], padded_frames(frames, settings.recitation_window_block)),
                      dtype=features.dtype)
    padded[:, :frames] = features[:, :frames]
    tokenizer = Tokenizer(model.hf_tokenizer, True, task="transcribe", language=settings.recitation_language)
    # The first word has no space before it, as the ear writes it.
    pieces = [tokenizer.encode(("" if i == 0 else " ") + w) for i, w in enumerate(words)]
    # Two separate costs, and they answer different questions. "encoded" is the
    # ear listening to the sound and does not care how many words are asked
    # about; "scored" is it weighing those words and grows with them. A slow
    # check is one or the other, and one line each says which without guessing.
    with local_lock:
        listened = timed("encoded", model.encode, padded, s=round(frames / 100, 1))
        answer = timed(
            "scored",
            lambda: model.model.align(
                listened, tokenizer.sot_sequence, [[t for p in pieces for t in p]], frames,
            ),
            words=len(words), rule=get_settings().recitation_sure_of_word,
        )[0]
    # align gives one (piece, position) pair per piece, in the model's own
    # tokens per second (50: an encoder position is two hundredths of a second).
    where = dict(answer.alignments)
    out, at = [], 0
    for piece in pieces:
        end = at + len(piece)
        probs = [float(p) for p in answer.text_token_probs[at:end]]
        out.append({
            "probs": probs,
            "weak": weakest(piece, probs, tokenizer.decode),
            "at": round(where[end - 1] / model.tokens_per_second, 2) if end - 1 in where else None,
        })
        at = end
    return out


def weakest(piece: list[int], probs: list[float], decode) -> dict | None:
    """A word's least likely piece, for a word card to point at: its `text` and
    `start`, the characters of the word before it.

    None for a word of one piece (the piece is the whole word), for a piece
    that is half a letter (Arabic letters are sometimes split into bytes, and
    decoding half of one gives a replacement mark, which says nothing), and for
    pieces and likelihoods that do not pair up, so a bad answer cannot fail a check.
    """
    if len(piece) < 2 or len(probs) != len(piece):
        return None
    k = probs.index(min(probs))
    text = decode([piece[k]]).strip()
    if not text or "�" in text:
        return None
    # A word after the first is encoded with a space in front of it, which is
    # not part of the word.
    before = decode(piece[:k]).lstrip()
    return {"text": text, "start": len(before)}


def weigh(audio: bytes, words: list[str], model: str | None = None) -> list[dict]:
    """What the ear makes of each word: `sure`, one number at the rule in config,
    and the `weak` piece ({text, start}) and `at` second that scores() found."""
    rule = get_settings().recitation_sure_of_word
    return [
        {"sure": aggregate(word["probs"], rule), "weak": word["weak"], "at": word["at"]}
        for word in scores(audio, words, model)
    ]


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
