"""Which ayah was that? Given roughly-right words, rank the ayahs. Pure.

Nothing here records, listens, or opens a file. Text in, ranked ayahs out, which
is what makes it testable without a microphone: the hard cases are typed in as
strings in tests/test_recitation.py.

Why matching has to be fuzzy
----------------------------
What comes back from listening is never the corpus's own spelling. Three things
are always different, and all three are normal rather than errors:

  spelling   The Qur'an writes ٱلْكِتَٰب; anyone transcribing writes الكتاب. The app
             already folds that away, so this reuses arabic_text rather than
             inventing a second idea of when two spellings are one word.

  hearing    A word comes back as a near neighbour: أوى heard as أول, لدنك as
             لدن ك. The words around it are still right, so a score built on how
             much is shared survives one wrong word.

  extras     Whisper numbers long passages, so "17. الله لا إله إلا هو" arrives
             with a 17 in it. Anything that is not an Arabic letter is dropped.

So an exact match is not the goal. The goal is that the right ayah is first, and
that the reader can see how sure it was.

What "closest" means here, and why it is two numbers
----------------------------------------------------
Two different mistakes are possible and one number cannot avoid both:

  Judge only how much of the *recitation* is in the ayah, and every long ayah
  that happens to contain those words ties. Reciting الحمد لله رب العالمين is
  ranked equally against 1:2 and against 6:45, which really does end with those
  same five words.

  Judge only how much of the *ayah* was recited, and somebody who stops halfway
  through Ayat al-Kursi is marked down for the words they had not reached, so
  the whole of 2:255 loses to the much shorter 20:8 that shares its opening.

Both were watched happening. So an ayah is scored on how much of the recitation
it holds, and that is then weighed by how much of the ayah was actually said:
containing the words is what makes an ayah a candidate, and being mostly the
thing that was said is what makes it the answer.

What this does not do yet
-------------------------
It matches one ayah at a time. Somebody who recites straight through several,
ٱلرَّحْمَٰنُ عَلَّمَ ٱلْقُرْءَانَ خَلَقَ ٱلْإِنسَٰنَ, has said something that no single ayah holds
much of, so every candidate scores low and the answer can be noise. Reciting on
past the end of an ayah is the normal thing for a reciter to do, so this is a
real limit and not an edge case.

The fix is to offer runs of consecutive ayahs as candidates too, reported by the
ayah they start at, and it belongs in `prepare` alone: nothing outside this file
would have to change. It is not done here because it roughly triples both the
memory and the time, which is a trade worth making deliberately rather than in
passing.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher

from backend.services.arabic_text import alef_written_out, bare_letters

# Only Arabic letters and the spaces between them survive. This is what removes
# the numbers Whisper writes into long recitations, and any stray Latin.
_NOT_ARABIC = re.compile(r"[^ء-ي\s]+")

# The length of the runs compared in the first pass. Three is the same size
# SQLite's trigram index uses for the app's other Arabic search, so the two agree
# on what "nearly the same words" means.
_RUN = 3

# How much of the ayah having been recited counts for, once it is known to hold
# the words. At 0 the two ayahs ending in the same phrase are indistinguishable;
# at 1 anybody stopping halfway is punished for it. Half of each keeps the right
# answer first in both.
_COVERAGE_WEIGHT = 0.5


def _clean(letters: str) -> str:
    return " ".join(_NOT_ARABIC.sub(" ", letters).split())


def spellings(text: str) -> tuple[str, str]:
    """The same words folded both ways, because neither way is right alone.

    The Qur'an writes a long "aa" as a small mark above a letter rather than as
    the letter ا, and anybody transcribing writes the letter. Dropping the mark
    turns ٱلْكِتَٰب into الكتب, which no transcription matches; writing it out as a
    full alef turns ذَٰلِكَ into ذالك, which no transcription matches either. The
    word that needs one is beside the word that needs the other in the very same
    ayah: ذَٰلِكَ ٱلْكِتَٰبُ.

    So both are kept and an ayah is judged on whichever fits better, which is the
    same answer build_quran_search_index.py already came to for typed search.

    Folded first, cleaned second, and that order matters: the marks and the alef
    wasla sit outside the plain Arabic letters, so clearing those out first does
    not tidy a word, it dismantles it into loose letters.
    """
    body = text or ""
    return _clean(bare_letters(body)), _clean(bare_letters(alef_written_out(body)))


def folded(text: str) -> str:
    """One spelling, for the places that only need something comparable."""
    return spellings(text)[0]


def _runs(text: str) -> frozenset[str]:
    packed = text.replace(" ", "")
    return frozenset(packed[i:i + _RUN] for i in range(len(packed) - _RUN + 1))


@dataclass(frozen=True)
class Ready:
    """One ayah, folded once and kept, because every recitation walks all of them."""

    surah: int
    ayah: int
    arabic: str
    folds: tuple[str, ...]   # the same ayah spelled both ways
    runs: frozenset[str]     # the runs of both, so neither spelling is missed


@dataclass(frozen=True)
class Match:
    """One candidate ayah, and how sure the app is that this was it."""

    surah: int
    ayah: int
    arabic: str
    score: float  # 0 to 1
    heard_of_ayah: float  # how much of the ayah was recited, 0 to 1


def prepare(ayahs) -> tuple[Ready, ...]:
    """Fold the Qur'an once, ready to be matched against many times.

    Separate from the matching because folding 6,236 ayahs takes most of a
    second and the answer never changes: done per recitation it was nine tenths
    of the wait, done once it is nothing.
    """
    ready = []
    for surah, ayah, arabic in ayahs:
        folds = tuple(dict.fromkeys(spellings(arabic)))
        runs = frozenset().union(*(_runs(fold) for fold in folds))
        ready.append(Ready(int(surah), int(ayah), arabic, folds, runs))
    return tuple(ready)


def best(heard: str, ayahs: tuple[Ready, ...], limit: int = 5,
         considered: int = 120) -> list[Match]:
    """The ayahs closest to what was heard, best first.

    Nothing is returned for silence, or for sound with no Arabic words in it,
    which is the ordinary result of a microphone that picked up a room rather
    than a reciter.
    """
    query = folded(heard)
    wanted = _runs(query)
    if not wanted:
        return []

    # First pass, to pick who is worth comparing properly. It has to rank the
    # same way the real scoring does, or it throws the answer away before the
    # real scoring ever sees it: ranked on the recitation alone, "قل هو الله"
    # shares everything it has with hundreds of ayahs, they all tie, and which
    # forty survive is then decided by nothing at all. Sura 112 did not survive.
    #
    # So the cheap score is shaped like the real one: how much of the recitation
    # is here, weighed by how much of the ayah that accounts for.
    def roughly(row: Ready) -> float:
        shared = len(wanted & row.runs)
        if not shared:
            return 0.0
        holds = shared / len(wanted)
        recited = shared / len(row.runs) if row.runs else 0.0
        return holds * (1 - _COVERAGE_WEIGHT + _COVERAGE_WEIGHT * recited)

    rough = sorted(ayahs, key=roughly, reverse=True)[:considered]

    scored = []
    for row in rough:
        best_score, best_recited = 0.0, 0.0
        for fold in row.folds:
            matcher = SequenceMatcher(None, query, fold, autojunk=False)
            shared = sum(block.size for block in matcher.get_matching_blocks())
            holds = shared / len(query)
            recited = shared / len(fold) if fold else 0.0
            weighed = holds * (1 - _COVERAGE_WEIGHT + _COVERAGE_WEIGHT * recited)
            if weighed > best_score:
                best_score, best_recited = weighed, recited
        scored.append(Match(
            surah=row.surah,
            ayah=row.ayah,
            arabic=row.arabic,
            score=best_score,
            heard_of_ayah=best_recited,
        ))

    scored.sort(key=lambda match: match.score, reverse=True)
    return scored[:limit]
