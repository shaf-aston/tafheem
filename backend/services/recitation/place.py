"""Which stretch of the page a recording holds. Pure: words in, a range out.

Sureness is only fair on words the recording could hold. A page word from
before the recording began scores near 0 in it because it was said in an
earlier one, not because it was said wrong. So the stretch is found first, from
what the ear wrote down, and sureness is asked only there.

The transcript places the recording and nothing more: every word inside the
stretch is then judged on sound, so a misheard word inside it is still judged.
Same placing as backend/scripts/score_recitation_checker.py, where the
three-band rule was measured.
"""
from __future__ import annotations

import difflib
import re

# A run of this many words heard in order places the recording. One shared word
# does not: النَّاسِ is in every ayah of an-Nas.
PLACES_IT = 2


def letters(word: str) -> str:
    """Letters only, as the page compares: marks gone, alif forms and ى folded."""
    word = re.sub("[أإآٱ]", "ا", word).replace("ى", "ي")
    return re.sub("[^ء-ي]", "", word)


def reach(expected: list[str], heard: list[str], at_least: int = PLACES_IT) -> tuple[int, int] | None:
    """(first, last + 1) of the expected words this recording holds, or None.

    None when nothing heard lines up with the page, so nothing is judged.
    Heard words left over past the outer placed ones are misheard words the
    recording does hold, so the stretch grows by as many, never past the page.
    """
    want, got = [letters(w) for w in expected], [letters(w) for w in heard]
    blocks = [b for b in difflib.SequenceMatcher(a=want, b=got, autojunk=False).get_matching_blocks()
              if b.size >= at_least]
    if not blocks:
        return None
    head, tail = blocks[0], blocks[-1]
    first = max(head.a - head.b, 0)
    last = min(tail.a + len(got) - tail.b, len(expected))
    return first, last
