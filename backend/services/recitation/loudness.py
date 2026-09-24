"""Sound brought up to a workable loudness. Pure: samples in, samples out.

One job and nothing else. It does not know what a recitation is, what model
reads it, or where the sound came from; it is handed the decoded sound and
hands back the same sound at a level the rest of the work expects.

Why it exists
-------------
Somebody reciting quietly, or sitting back from the microphone, records sound
that is real and perfectly clear and simply small. Every judgement downstream is
made against a fixed idea of how loud speech is: what counts as a voice, what
counts as silence to be trimmed, and how sure the ear is that a word is there.
A recitation at a fifth of the usual level fails all three and is reported as
nothing said. Making it louder first is the whole fix, and it costs one pass
over the numbers.

How loud is "workable"
----------------------
By how much sound there is on average (the root mean square), not by the single
loudest moment: one cough or one thump would otherwise set the level for a whole
recitation. The loudest moment is only used as a ceiling, so nothing is pushed
past what a recording can hold and turned into crackle.

Two things it must not do
-------------------------
Amplify a silent room into speech: below `floor` there is nothing there, and it
is handed back untouched. And amplify without limit: `most` caps how far
anything is lifted, so faint hiss stays faint hiss instead of being raised to
the level of a voice.
"""
from __future__ import annotations

import numpy as np


def loudness(sound: np.ndarray) -> float:
    """How much sound there is on average, 0 (silence) to 1 (as loud as it goes)."""
    if sound.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(np.square(sound, dtype=np.float64))))


def gain_for(sound: np.ndarray, target: float, ceiling: float, floor: float, most: float) -> float:
    """How much to multiply this sound by. 1.0 when it should be left alone.

    Never quieter than it came in: a recitation already loud enough is not
    turned down, because the only thing being fixed here is not being heard.
    """
    now = loudness(sound)
    if now < floor:
        return 1.0
    peak = float(np.max(np.abs(sound))) if sound.size else 0.0
    room = ceiling / peak if peak > 0 else most
    return float(min(max(target / now, 1.0), most, max(room, 1.0)))


def levelled(sound: np.ndarray, target: float, ceiling: float, floor: float, most: float) -> np.ndarray:
    """The same sound, brought up towards `target`. The array is not written over."""
    gain = gain_for(sound, target, ceiling, floor, most)
    return sound if gain == 1.0 else (sound * gain).astype(sound.dtype, copy=False)
