"""Request and reply types for routers/listen.py."""

from __future__ import annotations

from pydantic import BaseModel


class HeardAyah(BaseModel):
    """One ayah a recitation might have been, and how sure the app is.

    Two numbers rather than one, because they answer different questions. `score`
    is the ranking. `heard_of_ayah` is how much of that ayah was actually said,
    which is what tells a reader whether they recited the whole thing or stopped
    partway, and stops a confident-looking score hiding that only a fragment was
    matched.
    """
    surah: int
    ayah: int
    arabic: str
    score: float
    heard_of_ayah: float


class HeardPlace(BaseModel):
    """Where in the Qur'an a recitation was, asked of the page the reciter has open.

    `sure`: no other place fits nearly as well. `home`: it is on that page or
    the ayah just after it, so the reciter is carrying on rather than elsewhere.
    """
    surah: int
    ayah: int
    sure: bool
    home: bool


class Heard(BaseModel):
    """What a recording turned out to be.

    Empty words with no ayahs is the ordinary answer to silence, not a failure.
    How sure the ear is of each word is a separate question, answered by
    POST /api/listen/check (see Sureness below) rather than carried here, so a
    slow score never holds back the words a reciter is already reading by.
    """
    text: str
    ayahs: list[HeardAyah] = []
    place: HeardPlace | None = None


class WordSounds(BaseModel):
    """The letters and vowels heard in a word against the ones it should have
    (services/recitation/sounds.py). Shown, never scored."""
    heard: list[str]
    expected: list[str]
    letter_ok: bool
    vowel_ok: bool


class WordDetail(BaseModel):
    """What a word card needs of one scored word.

    `weak`: the text of its least likely piece, null when the word is a single
    piece; `weak_from`: how many characters of the word come before it.
    `at`: the second of the recording its last piece lines up with, null when
    the ear gave no position. `sounds`: null when the sounds ear is off, missing
    or has no expected sounds for the word.
    """
    weak: str | None = None
    weak_from: int | None = None
    at: float | None = None
    sounds: WordSounds | None = None


class Sureness(BaseModel):
    """How sure the ear is of each word of the ayahs POST /api/listen/check named.

    Per "surah:ayah", one number per word, or null for a word the recording
    does not reach. Empty when the recording did not place on any of them.
    `detail` is the same shape with a WordDetail (or null) in place of each number.
    """
    sure: dict[str, list[float | None]] = {}
    detail: dict[str, list[WordDetail | None]] = {}
