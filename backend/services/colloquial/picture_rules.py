"""What a lesson picture may not be of.

The module's picture rule: no photograph of a person (a learner's lesson is not the place for a
stranger's face, least of all a child's), nothing of alcohol or pork, no other faith's building or
symbol. People are drawn instead (the body and clothes boards) or shown as an emoji.

One list, two readers: the picture fetcher (scripts/colloquial/fetch_colloquial_images.py)
refuses to search for a subject on it, and the data test (tests/colloquial) fails if a saved photo
is named for one, since the fetcher's search cannot tell what a picture really shows.
"""
from __future__ import annotations

import re

FORBIDDEN_SUBJECT = re.compile(
    r"(?<![a-z])(man|men|woman|women|boy|girl|child|children|kid|kids|baby|infant|father|mother|son|daughter|"
    r"brother|sister|grandmother|grandfather|grandchildren|grandson|cousin|friend|person|people|teenager|bride|"
    r"groom|couple|smiling|sad|portrait|barber|tailor|builder|doorman|pregnant|visitor|guest|seller|"
    r"pork|wine|beer|church|crucifix|funeral|surgery|neck|chest|back)(?![a-z])"
)


def forbidden(text: str | None) -> bool:
    """Whether a search term, word or file name names a subject no lesson picture may show."""
    return bool(FORBIDDEN_SUBJECT.search((text or "").lower().replace("-", " ").replace("_", " ")))
