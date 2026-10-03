"""English words that carry no question. Shared by every text search.

Asked as they are, each one is looked up and matched like a real word, so
"what does the Qur'an say about patience" was searched as roughly forty terms
and took three seconds to answer what the last two words already asked. The
list is deliberately short, because a word wrongly on it is a word nobody can
search for.
"""
from __future__ import annotations

ENGLISH_NOISE = frozenset("""
a an and about are as at be but by can did do does for from had has have how i if in
is it its me my no not of on or say says shall should so than that the their
them then there these they this to was we were what when where which who why
will with would you your
""".split())
