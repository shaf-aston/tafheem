"""Striking off a grammar backend whose key has been rejected.

The ears already had this proved next door (test_recitation_ears.py). This is
the same rule on the other side of services/fallback, and it had a hole: Groq's
own error was caught and re-raised as a plain ValueError, which carries no HTTP
status, so the chain above never learned the key was dead and every single
request paid a full round trip to be told so again.

No network: the SDK's error is built by hand, which is all the rule reads.

Run from the project root:  venv/Scripts/python -m pytest tests -q
"""
from __future__ import annotations

import httpx
import pytest
from groq import APIStatusError

from backend.services.ai.groq_backend import GroqBackend
from backend.services.fallback import permanent_failure


def rejected(status: int) -> APIStatusError:
    """The error the Groq SDK raises for that status, shaped as it really is."""
    return APIStatusError(
        f"Error code: {status}",
        response=httpx.Response(status, request=httpx.Request("POST", "https://api.groq.com/x")),
        body=None,
    )


@pytest.mark.parametrize("status, settled", [
    (401, True), (403, True),
    # An allowance spent for the minute is not a dead key; it fixes itself.
    (429, False), (500, False),
])
def test_the_status_survives_the_backend_and_the_chain_can_read_it(status, settled):
    backend = GroqBackend()

    def refused():
        raise rejected(status)

    with pytest.raises(Exception) as caught:
        # No waiting between attempts: a 429 is retried twice and this test is
        # about what comes out of the end, not about the backoff.
        backend._retry(refused, max_retries=0)

    assert bool(permanent_failure(caught.value)) is settled


def test_a_rejected_key_is_named_in_the_reason_the_health_line_shows():
    backend = GroqBackend()
    backend.retire(permanent_failure(rejected(401)))
    assert "key was rejected" in backend.retired_reason
    assert not backend.is_available()
