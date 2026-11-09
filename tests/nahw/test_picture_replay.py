"""Every recorded case draws the picture it was recorded with, from the inputs it was recorded with.

The cases are the sentences that catch a break in `syntax/picture/` (backend/scripts/nahw/picture_cases.py
says how they were chosen and how to redraw them after a deliberate change). The parser is not run,
so a failure here is the picture code alone.
"""
import pytest

from backend.scripts.nahw import picture_cases
from tests.nahw_helpers import needs_camel

pytestmark = needs_camel  # the picture asks the dictionary a few word facts

CASES = picture_cases.load()


@pytest.mark.parametrize("case", CASES, ids=[f"{c['from']}-{i}" for i, c in enumerate(CASES)])
def test_the_picture_is_the_one_recorded(case):
    assert picture_cases.drawn(case) == case["tree"], case["sentence"]
