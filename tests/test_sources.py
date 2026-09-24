"""The source reference list, the thing the app shows when asked what it is built on.

The point of this list is that a reader can trust it. A source with no
description, a link that was guessed at, or a tab named that does not exist all
make it a list that looks complete and is not, which is worse than no list.
"""
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import provenance

client = TestClient(app)

# The tabs the frontend declares, in App.jsx. Written out here on purpose: a
# source pointing at a tab that does not exist would put a line at the foot of
# no page at all, and nothing else would notice.
TABS = {"nahw", "sarf", "quran", "mem", "dict", "quiz", "daleel", "timelines"}

# Only these are shown as levels; anything else falls back to the weakest one
# on screen, which would quietly downgrade a hand-checked source to a guess.
CONFIDENCES = {"verified", "derived", "translated", "guessed"}


def test_endpoint_returns_every_source():
    response = client.get("/api/sources")
    assert response.status_code == 200
    assert len(response.json()["sources"]) == len(provenance.all_sources())


def test_every_source_is_fully_described():
    for source in provenance.all_sources():
        assert source["label"].strip(), f"{source['key']} has no label"
        assert source["detail"].strip(), f"{source['key']} has no detail"
        # `where` is the plain sentence the reference list shows. Missing, the
        # list falls back to `detail`, which is written for a badge and assumes
        # the reader knows what a corpus is.
        assert source["where"].strip(), f"{source['key']} does not say where it lives"


def test_confidence_is_one_the_app_can_show():
    for source in provenance.all_sources():
        assert source["confidence"] in CONFIDENCES, source["key"]


def test_every_source_is_read_by_a_real_tab():
    for source in provenance.all_sources():
        assert source["used_in"], f"{source['key']} is read by no tab"
        unknown = set(source["used_in"]) - TABS
        assert not unknown, f"{source['key']} names tabs that do not exist: {unknown}"


def test_every_tab_has_at_least_one_source():
    """A tab with nothing declared prints "No sources are declared for this tab."

    That message is honest, but it means someone added a panel and forgot. It
    should fail here rather than be discovered at the bottom of a page.
    """
    declared = {tab for source in provenance.all_sources() for tab in source["used_in"]}
    assert TABS - declared == set()


def test_a_url_is_a_real_address_or_nothing():
    """Empty means "there is nothing public to point at", a printed book, a
    model on this machine. A half-written address would be shown as a link."""
    for source in provenance.all_sources():
        url = source["url"]
        assert url == "" or url.startswith("https://"), f"{source['key']}: {url!r}"


def test_badge_shape_is_unchanged():
    """The result badges read `of()`. Adding fields for the reference list must
    not change what a badge is handed."""
    assert set(provenance.of("corpus")) == {"key", "label", "confidence", "detail"}
