"""Request and reply types for routers/timelines.py."""

from __future__ import annotations

from pydantic import BaseModel

from backend.models.common import Source


class TimelineRef(BaseModel):
    """Where an event is told. Exactly one of quran, hadith or book is set.

    quran is "S", "S:A" or "S:A-B", checked against the Qur'an's own ayah counts.
    hadith is a collection key with its number, and `checked` names where that
    number was read, since no hadith collection is installed here to check it.
    """
    quran: str | None = None
    hadith: str | None = None
    number: int | None = None
    # sunnah.com's own letter where one reference number covers several
    # narrations and the event means one of them: "Sahih Muslim 157c".
    part: str | None = None
    checked: str | None = None        # where the number was looked up, e.g. "sunnah.com"
    book: str | None = None
    page: str | None = None           # a book's own page, filled into its cite link


class TimelineDate(BaseModel):
    """An estimate of when, in the words of the one reference that states it."""
    says: str
    ref: TimelineRef


class TimelineStep(BaseModel):
    """One step inside an event, and the moments inside that step.

    An event's own shape less the two things the line itself owns: a step has no
    `at`, because it is placed by the order it is written in rather than by a
    date, and no `until`, because it cannot stretch across rows it is not on.
    Everything else is optional: a step that adds nothing to its parent's
    references simply carries none.
    """
    id: str
    title: str
    arabic: str = ""
    when: str = ""
    place: str | None = None
    summary: str
    flags: list[str] = []
    refs: list[TimelineRef] = []
    # A side detail away from the main story: the reader shows it folded.
    aside: bool = False
    # A key of library paths: read side by side with neighbours on other paths.
    path: str | None = None
    steps: list["TimelineStep"] = []


class TimelineEvent(BaseModel):
    """One moment on a section's line. Equal `at` means the events happen together;
    `until` names the event a stretch lasts until."""
    id: str
    title: str
    arabic: str
    when: str
    dates: list[TimelineDate] = []  # estimates of when, each beside its source
    at: float
    hijri: str | None = None        # "5 AH" or "13 BH", beside the common-era year
    until: str | None = None
    place: str | None = None
    period: str | None = None       # makkan | madinan: a stretch of revelation
    names: list[str] = []           # the Arabic wording that ties a report to this event
    summary: str
    flags: list[str]
    refs: list[TimelineRef]
    steps: list[TimelineStep] = []  # the smaller events inside this one, in order
    asbab: int = 0                  # how many asbab al-nuzul reports it holds


class TimelineSection(BaseModel):
    id: str
    order: int
    name: str
    arabic: str
    science: str
    kind: str                         # dated | undated | unseen
    sub: str
    map: str | None = None            # a key of map.views
    events: list[TimelineEvent]


class TimelineHadith(BaseModel):
    """One hadith's own words, Arabic and English, as sunnah.com has them. `cut` is HadithEntry's."""
    arabic: str
    english: str = ""
    cut: list[int] | None = None


class TimelineLibrary(BaseModel):
    """Every section, beside the vocabulary its events point at, sent whole."""
    sciences: list[dict]
    paths: dict[str, str]
    flags: dict[str, str]
    collections: dict[str, dict]
    places: dict[str, dict]
    map: dict
    # The words of every hadith the sections cite, keyed "muslim:2902". Empty
    # until scripts/fetch_timeline_hadith.py has been run.
    hadith: dict[str, TimelineHadith] = {}
    sections: list[TimelineSection]
    source: Source


class TimelineReport(BaseModel):
    """One asbab al-nuzul report, as the list shows it before it is opened."""
    ref: str                        # "8:9"
    surah: int
    surah_name: str
    ayah: int
    how: str                        # named | period: how it came to this event
    opening: str
    arabic_opening: str


class TimelineAsbab(BaseModel):
    section: str
    event: str
    reports: list[TimelineReport]
    # How many reports in the book matched no single ayah, so are in none of
    # these lists. Shown, not hidden: see services/timelines._unplaced.
    unplaced: int
    # The two books these reports live in, so the tab reads them by the ids the
    # manifest gives rather than holding a third copy of the names.
    books: dict[str, str]
    source: Source
