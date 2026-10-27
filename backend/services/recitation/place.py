"""Which stretch of the page a recording holds. Pure: words in, a range out.

Sureness is only fair on words the recording could hold. A page word from
before the recording began scores near 0 in it because it was said in an
earlier one, not because it was said wrong. So the stretch is found first, from
what the ear wrote down, and sureness is asked only there.

The transcript places the recording and nothing more: every word inside the
stretch is then judged on sound, so a misheard word inside it is still judged.
Same placing as backend/scripts/recitation/score_recitation_checker.py, where the
three-band rule was measured.
"""
from __future__ import annotations

import difflib
import re

from backend.config import get_settings
from backend.services.text.arabic_text import bare_letters


def bare_word(word: str) -> str:
    """Arabic letters only, as the page compares: marks gone, alif forms and ى folded."""
    return re.sub("[^ء-ي]", "", bare_letters(word))


def reach(expected: list[str], heard: list[str]) -> tuple[int, int] | None:
    """(first, last + 1) of the expected words this recording holds, or None.

    None when nothing heard lines up with the page, so nothing is judged.
    Heard words left over past the outer placed ones are misheard words the
    recording does hold, so the stretch grows by as many, never past the page.
    """
    at_least = get_settings().recitation_place_min_words
    want, got = [bare_word(w) for w in expected], [bare_word(w) for w in heard]
    blocks = [b for b in difflib.SequenceMatcher(a=want, b=got, autojunk=False).get_matching_blocks()
              if b.size >= at_least]
    if not blocks:
        return None
    head, tail = blocks[0], blocks[-1]
    first = max(head.a - head.b, 0)
    last = min(tail.a + len(got) - tail.b, len(expected))
    return first, last
