"""Pydantic request/response schemas shared across the API."""

from __future__ import annotations

import json
import re

from pydantic import BaseModel, Field, field_validator

from backend.services.arabic_text import shown_root


# Trust-boundary caps: user text flows into LLM prompts and NLP engines, 
# unbounded input is a token-cost / latency attack surface. Reject loud (422).
class AnalyzeRequest(BaseModel):
    sentence: str = Field(min_length=1, max_length=2000)


class MorphologyRequest(BaseModel):
    word: str = Field(min_length=1, max_length=100)
    # Which verb form to conjugate. The word alone cannot say which Form I baab
    # a verb takes, so the reader picks; blank means the default.
    form: str | None = Field(default=None, max_length=20)


class ConjugationRequest(BaseModel):
    """Rebuild the table for a different باب. The root is all the rules need."""
    root: str = Field(min_length=1, max_length=100)
    form: str = Field(min_length=1, max_length=20)


class MeaningRequest(BaseModel):
    """The AI enrichment, asked for on its own so it never holds up the table."""
    word: str = Field(min_length=1, max_length=100)


class PracticeRequest(BaseModel):
    sentence: str = Field(min_length=1, max_length=2000)


class Source(BaseModel):
    """Where a result came from and how far it can be trusted. Attached to every
    answer so the UI never shows a claim without saying who made it."""
    key: str
    label: str
    confidence: str   # verified | derived | translated | guessed, see lib/confidence.js
    detail: str


# Every role name the word grid knows how to colour. The role itself is written
# in Arabic for the reader; this is the stable name beside it, the same idea as
# a tarkeeb node's `tone`. The frontend owns the actual colours (`role.*` in
# theme.json), this list only says which roles exist.
ROLE_KEYS = frozenset({
    "fil",      # the verb
    "fail",     # doer; and the pronoun standing in for one
    "mubtada",  # subject of a nominal sentence, and the ism of inna
    "khabar",   # what is said about it
    "mafool",   # object
    "sifah",    # na't / adjective following its noun
    "haal",     # circumstantial
    "mudaf",    # first of a genitive pair
    "harf",     # particle, and whatever it governs
})


class WordAnalysis(BaseModel):
    word: str
    root: str | None = None
    type: str | None = None
    role: str | None = None
    # The stable name of that role, for the one job the Arabic prose above cannot
    # do: telling the grid which colour to draw it in. Unset means "not settled",
    # which stays uncoloured rather than being given a plausible colour.
    role_key: str | None = None
    case: str | None = None
    sign: str | None = None
    reason: str | None = None
    notes: str | None = None

    @classmethod
    def from_raw(cls, w: dict) -> "WordAnalysis":
        """Build one from a word dict that may not be trustworthy.

        The rule engine's dicts are already the right shape, but the AI's are a
        model's answer to a prompt and can carry anything, or be missing fields.
        Both paths come through here so neither can put a role name on screen
        that the grid would draw in a colour meaning a different role.
        """
        key = w.get("role_key")
        # A particle has no root in nahw, whatever the AI wrote for it, and a
        # root that is a code rather than letters is no root at all. Judged by
        # the word's own type: role_key "harf" also covers the noun a
        # preposition governs, which does have a root.
        root = "" if w.get("type") == "harf" else shown_root(w.get("root"))
        return cls(
            word=w.get("word", ""),
            root=root or None,
            type=w.get("type"),
            role=w.get("role"),
            role_key=key if key in ROLE_KEYS else None,
            case=w.get("case"),
            sign=w.get("sign"),
            reason=w.get("reason"),
            notes=w.get("notes"),
        )


class AnalyzeResponse(BaseModel):
    sentence: str
    words: list[WordAnalysis]
    summary: str | None = None
    source: Source | None = None
    # The same reading drawn as brackets: which words join, and what the unit
    # does. Unset when the parser could join nothing, so the cards stand alone.
    tree: "TarkeebTree | None" = None


class ConjugationColumn(BaseModel):
    """One tense or mood, read down the table."""
    id: str
    label: str
    arabic: str


class ConjugationRow(BaseModel):
    """One of the fourteen persons, read across the table."""
    person: str
    cells: dict[str, str]   # column id -> the word


class SarfSlot(BaseModel):
    """One entry of the صرف صغير, the one-line summary of a باب."""
    label: str
    arabic: str


class ConjugationTable(BaseModel):
    columns: list[ConjugationColumn]
    rows: list[ConjugationRow]
    summary: list[SarfSlot]
    notes: list[str] = []


class MorphologyResponse(BaseModel):
    word: str
    root: str | None = None
    wazn: str | None = None
    verb_class: str | None = None
    meaning: str | None = None
    table: ConjugationTable | None = None
    notes: str | None = None
    form: str | None = None                 # which form the table above is for
    form_options: dict[str, str] = Field(default_factory=dict)
    table_note: str | None = None           # why there is no conjugation table
    source: Source | None = None          # where the table came from
    meaning_source: Source | None = None  # the meaning may come from elsewhere
    verb: VerbVerdict | None = None       # which باب, when the word is a verb


class ConjugationResponse(BaseModel):
    """Only what a new باب changes. The root and the meaning are the word's."""
    form: str | None = None
    wazn: str | None = None
    table: ConjugationTable | None = None
    table_note: str | None = None
    source: Source | None = None


class MeaningResponse(BaseModel):
    """Comes back after the table already has, or not at all if no AI is reachable."""
    meaning: str | None = None
    meaning_source: Source | None = None
    verb_class: str | None = None


class WordSegment(BaseModel):
    """One piece of a word, a prefix, the word itself, an ending."""
    arabic: str
    grammar: list[str] = Field(default_factory=list)


class QuranWord(BaseModel):
    position: str
    arabic: str
    pos: str | None = None
    root: str | None = None
    lemma: str | None = None
    grammar: list[str] = Field(default_factory=list)   # plain-English grammar
    segments: list[WordSegment] = Field(default_factory=list)
    meaning: str | None = None   # word-by-word English
    uthmani: str | None = None   # printed spelling, waqf marks included


class QuranAyah(BaseModel):
    surah: int
    ayah: int
    arabic_text: str
    words: list[QuranWord]
    end_mark: str | None = None   # the ring-and-number that closes the printed ayah
    source: Source | None = None


class TarkeebNode(BaseModel):
    """One bracket of the tree.

    It says what a piece **does** (`role`) or what a unit **is** (`label`), and
    has no field for a part of speech, so "it is a noun", which answers a
    different question entirely, cannot be returned from here.

    `word` is set on a leaf and is an index into the ayah's words. `parts` are
    the joins inside a single written word (لِلَّهِ is jarr + majroor). `gap` marks
    a join the rules could not make, which the diagram draws as an open bracket.
    """
    role: str | None = None
    label: str | None = None
    tone: str | None = None
    word: int | None = None
    gap: bool = False
    # A ghair-`aamil` particle, و / ف that opens a new clause, or a bare
    # connective like ثم, governs nothing. It still gets its own name and
    # colour, so this is how the diagram tells it apart from a real gap
    # without having to compare against a colour string.
    ghair_aamil: bool = False
    # True when the wording is the Treebank's own, not one the app checked.
    raw_wording: bool = False
    # A short, plain-language note for the hover/click detail on a role that
    # needs one. Most roles need none, so this stays unset for them.
    detail: str | None = None
    # The exact Arabic of a connector glued onto the front of this word (فَ /
    # وَ), so the diagram can slice it into its own column on request instead
    # of always drawing it fused with the word it precedes.
    prefix_arabic: str | None = None
    parts: list["TarkeebNode"] = Field(default_factory=list)
    children: list["TarkeebNode"] = Field(default_factory=list)


class Unwritten(BaseModel):
    """How a word that is understood but not written is shown, and what to call it."""
    mark: str
    note: str


class TarkeebTree(BaseModel):
    # Unset for a sentence someone typed, which belongs to no ayah
    surah: int | None = None
    ayah: int | None = None
    words: list[str]
    tree: TarkeebNode | None = None
    # The share of words the rules placed in a named unit. The rest are gaps, and
    # this number is what keeps that visible instead of implied.
    coverage: float = 0.0
    unwritten: Unwritten | None = None
    source: Source | None = None


class TarkeebExample(BaseModel):
    """One sentence a book worked out, and the tree it drew for it."""
    id: str
    ref: str            # where in the book it is, so a reader can go and check
    topic: str          # the grammar topic it teaches, how the page is browsed
    sentence: str
    translation: str
    words: list[str]
    tree: TarkeebNode


class TarkeebTopic(BaseModel):
    """A grammar topic examples are browsed by. Shared by every book."""
    key: str
    en: str
    ar: str


class TarkeebExampleBook(BaseModel):
    key: str
    title: str
    detail: str
    examples: list[TarkeebExample]
    source: Source | None = None


class TarkeebExamples(BaseModel):
    """Every worked example the app carries: the shared topics, and the books.

    Topics sit beside the books, not inside them, because they are how the page
    is browsed, one chip gathers the same topic from every book.
    """
    topics: list[TarkeebTopic]
    books: list[TarkeebExampleBook]


class TamreenTag(BaseModel):
    """A grammar point the exercises are filed under. Shared by every exercise."""
    key: str
    ar: str
    en: str
    meaning: str


class TamreenPart(BaseModel):
    """One thing an example asks: choose, explain, translate, count the mistakes."""
    letter: str
    question: str
    options: list[str] | None = None
    rows: list[str] | None = None     # a grid asks the same options of several words
    answer: list[str] | dict[str, list[str]] | str
    by: str                           # "teacher" or "claude": who gave the answer
    labels: dict[str, str] | None = None  # what a placeholder ("A", "?3") points at in the picture
    picture: str | None = None        # a part with its own picture, e.g. a tarkeeb tree
    doubt: str | None = None          # a reviewer's reason to distrust the marking, kept in view


class TamreenRule(BaseModel):
    """A statement to complete, with the options the teacher marked right."""
    id: str
    question: str
    options: list[str]
    answer: list[str]
    picture: str | None = None
    tags: list[str]


class TamreenExample(BaseModel):
    """A picture question: the sentence as read off the picture, and its parts."""
    id: str
    section: str
    picture: str
    instruction: str
    sentence: str
    marked: list[dict] = []           # which words were underlined, and how
    doubt: str | None = None          # what the readers could not settle from the picture
    parts: list[TamreenPart]
    tags: list[str]


class TamreenExercise(BaseModel):
    key: str
    title: str
    form: str
    harvested: str
    rules: list[TamreenRule]
    examples: list[TamreenExample]


class TamreenLibrary(BaseModel):
    """The tags beside the exercises, and a count per tag so a gap is a number."""
    tags: list[TamreenTag]
    exercises: list[TamreenExercise]
    coverage: dict[str, int]


class NoteRole(BaseModel):
    """A kind of piece a note marks inside its own text, and so a kind a test can hide."""
    key: str
    ar: str
    en: str
    hint: str


class NoteBlock(BaseModel):
    """One piece of a topic's notes, in the order the page has it.

    One model for every kind rather than six, because a block is read as a
    whole: a table is a caption plus rows, a rule is the Arabic plus its
    English, and the kind says which of these the reader will find.
    """
    id: str
    kind: str                         # heading | rule | list | example | table | picture
    page: int                         # which of the teacher's pages it was read from
    ar: str | None = None
    en: str | None = None
    items: list[str] | None = None    # a list block's lines
    caption: str | None = None
    caption_en: str | None = None
    columns: list[str] | None = None
    rows: list[list[str]] | None = None
    answer_col: int | None = None     # which column a test asks for, given the others
    note_ar: str | None = None        # the small print under a table
    note_en: str | None = None
    labels: list[dict] | None = None  # an example's words and what each is called


class NoteTopic(BaseModel):
    """One topic of the teacher's notes, whole. `tamreen` names the exercises that test it."""
    id: str
    title: str
    arabic: str
    tamreen: list[str] = []
    pages: int                        # how many of the teacher's pages sit behind it
    blocks: list[NoteBlock]


class NoteLibrary(BaseModel):
    """Every topic, the roles a test can hide, and where the notes came from."""
    roles: list[NoteRole]
    topics: list[NoteTopic]
    source: Source


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
    """One hadith's own words, Arabic and English, as sunnah.com has them."""
    arabic: str
    english: str = ""


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


class RootForm(BaseModel):
    lemma: str
    pos: str
    uses: int


class RootOccurrence(BaseModel):
    surah: int
    ayah: int
    arabic: str
    grammar: list[str] = Field(default_factory=list)


class RootResponse(BaseModel):
    """Everything the Qur'an does with one root, the link between the tabs."""
    root: str
    total: int
    forms: list[RootForm] = Field(default_factory=list)
    occurrences: list[RootOccurrence] = Field(default_factory=list)
    source: Source | None = None


class SurahAyah(BaseModel):
    """One ayah as the reader sees it. `words` is filled only when the full
    grammar was asked for, reading a surah does not need it, and it is roughly
    fifty times the payload."""
    ayah: int
    arabic: str
    english: str = ""
    words: list[QuranWord] | None = None
    # The page of the 604-page Madani mushaf this ayah begins on. None where the
    # layout has never been built, which is what tells a reader to fall back to
    # sizing a page by word count rather than printing a page number that is a
    # guess. See services/quran_layout.py.
    page: int | None = None


class QuranSurah(BaseModel):
    surah: int
    name_en: str = ""
    name_ar: str = ""
    ayah_count: int
    ayahs: list[SurahAyah]
    source: Source | None = None


class SurahGlosses(BaseModel):
    """A whole surah's word-by-word English, for showing a word's meaning on hover.

    Words in reading order per ayah, not keyed by number, because the reader
    lines them up against the ayah's own words in the same order. An ayah whose
    gloss count does not match its printed words is left out entirely rather
    than shipped to be mis-aligned: the reader then shows that ayah plain.

    Separate from QuranSurah, and small enough to be: al-Baqarah, the longest,
    is 121KB. Folding it into the reading response would put it on every caller
    of that route, including ones that never draw a word.
    """
    surah: int
    ayahs: dict[int, list[str]]


class Edition(BaseModel):
    """One book of text hung on the ayahs: a tafsir, a translation.

    Described once, for the picker and for the reference list, so that the
    passage shape below does not have to repeat a book's licence on every ayah
    the reader opens.
    """
    id: str
    kind: str
    language: str
    name: str
    short: str
    author: str
    licence: str
    origin: str
    passages: int
    ayahs: int
    source: Source | None = None


class Passage(BaseModel):
    """What one book says about one ayah.

    `covers` is every ayah this same passage was written about. A tafsir often
    takes a run of ayahs together, and a reader shown commentary on ten of them
    is entitled to know that rather than to think it was written about one.
    """
    edition: str
    kind: str
    language: str
    name: str
    author: str
    surah: int
    ayah: int
    # How this passage is cited: the ayah it opens on, "78:1". Stable, and the
    # same string the library stores it under.
    passage: str
    text: str
    covers: list[int]
    source: Source | None = None


class SurahEdition(BaseModel):
    """One book's text for a whole surah, keyed by ayah number.

    A dictionary rather than a list because the caller draws one surah's ayahs
    and looks each one up; ayahs the book says nothing about are simply absent,
    which is what lets a line be drawn only where there is one.
    """
    surah: int
    edition: str
    ayahs: dict[int, str]


class AyahEditions(BaseModel):
    """Every book that has something on one ayah, in the library's own order."""
    surah: int
    ayah: int
    passages: list[Passage]


class QuranSearchResult(BaseModel):
    surah: int
    ayah: int
    arabic_text: str
    # Which of the two searches found it: the hand-tagged corpus on this
    # machine, or Quran.com over the network. One list can hold either.
    source: Source | None = None


class Synonym(BaseModel):
    """Another word for one sense, and what that word itself means.

    The meaning is looked up as the entry goes out, not stored: it is the first
    definition of that word's own entry. Empty where the dictionary has no entry
    for it, a phrase or a name, and the app says so rather than guessing.
    """
    word: str
    meaning: str = ""


class VerbForm(BaseModel):
    """One verb built off this entry's spelling, as a named source states it."""
    form: str
    past: str
    babs: list[str] = Field(default_factory=list)


class DictionaryEntry(BaseModel):
    arabic: str
    root: str | None = None
    transliteration: str | None = None
    definitions: list[str] = Field(default_factory=list)
    # Other words meaning the same, one list per definition and in the same
    # order, synonyms[2] belongs to definitions[2]. A separate list rather than
    # a field on each definition, so an entry built before synonyms existed is
    # still a valid entry with none.
    synonyms: list[list[Synonym]] = Field(default_factory=list)
    verbs: list[VerbForm] = Field(default_factory=list)


class VerbReading(BaseModel):
    """One باب a named source states for this verb, and which source(s) said so."""
    label: str
    sources: list[Source] = Field(default_factory=list)


class VerbVerdict(BaseModel):
    """Every باب a dictionary states for this verb, never a guess. Empty
    readings means no source recorded one. See services/verb_forms.py."""
    form_key: str | None = None
    readings: list[VerbReading] = Field(default_factory=list)


class DictionaryResponse(BaseModel):
    query: str
    lang: str
    results: list[DictionaryEntry]
    source: Source | None = None


class RootMeaning(BaseModel):
    core_meaning: str
    sarf_pattern: str = ""
    variances: list[str] = Field(default_factory=list)
    # The rest of the entry, the examples, the Qur'an verses and their
    # references, the poetry. Prose, never split into pieces: Ibn Faris marks
    # where one sense ends in only a minority of entries.
    body: str = ""
    # A plain English gloss of the origin sense. Read off a page image by a
    # machine, unlike everything above it, so it carries its own weaker badge on
    # the card and must never be presented as the book's own words.
    english: str = ""


class RootMeaningResponse(BaseModel):
    """A root's classical origin sense, and, when there isn't one, which kind of
    nothing it is. "The book isn't installed" and "the book has no entry for this
    root" are different sentences and are never allowed to look the same."""

    root: str          # the exact letters searched, so a mismatch is visible
    status: str        # missing | broken | ready, see services/root_meaning.py
    # The spelling the book itself files this entry under, sent only when it is
    # not the one searched. Typing بدا reaches the entry printed بدأ, and without
    # saying so the reader takes an answer about one root as an answer about the
    # letters they typed.
    book_root: str | None = None
    meaning: RootMeaning | None = None
    source: Source | None = None
    # A second badge, for the one field that came from somewhere weaker. Sent
    # only when there is English to badge, so the card never shows a credit for
    # something it is not displaying.
    english_source: Source | None = None


class LexiconEntry(BaseModel):
    """One dictionary's whole entry for a root, as that dictionary wrote it."""

    book: str          # lisan | taj | maqayis | lane
    title: str         # the book's own name, in its own language
    english: str       # what that name means, for a reader who cannot read it
    author: str
    died: int | None = None   # the year the author died, AH for the Arabic books
    language: str      # ar | en, which decides how the entry is set on the page
    # The spelling this book files the root under, sent only when it differs from
    # the letters searched, so "filed under أمر" can be said rather than leaving
    # the reader to wonder why the letters changed.
    filed_under: str | None = None
    text: str
    source: Source


class LexiconsResponse(BaseModel):
    """What the classical dictionaries say about one root.

    Empty entries with status ready means the books were read and none of them
    covers this root. That is a fact about the root; "missing" is a fact about
    this machine. The two must never be shown as the same sentence.
    """

    root: str
    status: str        # missing | broken | ready, see services/lexicons.py
    entries: list[LexiconEntry] = []


class RootEntryEnglishResponse(BaseModel):
    """A whole Maqayees entry retold in English, asked for one root at a time.

    Deliberately not part of RootMeaningResponse. The entry above it is the
    book's own words; this is a machine reading them, it costs a call to make,
    and it is only ever fetched because a reader asked for it. Keeping it a
    separate answer keeps those two apart on the wire as well as on the page."""

    root: str
    english: str
    # True when the entry was longer than the model was given. The card says so:
    # a retelling that stops early must not look like the whole entry.
    truncated: bool = False
    source: Source


class EntryLine(BaseModel):
    """One line of the entry with its English, paired on the wire.

    Paired here, not on the screen: only the backend splits the Arabic, so the
    two sides cannot drift and put a translation under the wrong line."""

    arabic: str
    english: str


class RootEntryLinesResponse(BaseModel):
    """The rest of a Maqayees entry, one English line under each Arabic line.

    Only ever sent with as many English lines as Arabic ones: an answer that
    could not be lined up is refused by the backend, and the card falls back to
    the prose reading it already has."""

    root: str
    lines: list[EntryLine]
    # True when the entry was longer than the model was given: the lines cover
    # its opening, and the card says so.
    truncated: bool = False
    source: Source


class PracticeQuestion(BaseModel):
    question: str
    answer: str
    hint: str | None = None


class PracticeResponse(BaseModel):
    sentence: str
    questions: list[PracticeQuestion]
    source: Source | None = None


class DaleelHit(BaseModel):
    """One quotation, exactly as its book has it.

    There is deliberately no field for a summary, an explanation or an answer.
    Daleel shows where something is written and stops; a field for a verdict
    would be a field somebody eventually fills in."""

    locator: str
    """How a person would cite it: "2:255", "§1.4.4". Never blank."""
    arabic: str
    english: str = ""
    match: str
    """exact | partial | root | loose. The screen labels a loose match as one
    rather than letting a probable typo-fix pass for a clean find."""
    source: Source
    book: str = ""
    """Which book of that source. Fourteen classical works share one badge, so
    the badge alone no longer says where a quotation is from."""


class DaleelBook(BaseModel):
    """One book a reader can narrow the search to."""

    name: str
    """What the book calls itself. Also its id: the index stores this string,
    so there is no second name to keep in step with this one."""
    source: str
    """The source it is credited to, so the list can be grouped the way the
    results are."""
    category: str = ""
    """The shelf it sits on: Qur'an, Fiqh, Grammar. Read from sources.json, so
    a new shelf is a line of data rather than a change here."""
    english: str = ""
    """Its name in English letters, for a reader who cannot type Arabic. Empty
    when the book's own name is already English, and empty rather than invented
    when nobody has written one; never used as an id."""


class DaleelResponse(BaseModel):
    query: str
    hits: list[DaleelHit]
    books: list[str] = []
    """The books this search was narrowed to, echoed back. Names the reader
    asked for that no book has are dropped, so this is what was actually
    searched rather than what was requested."""
    # False when the index has not been built yet, so the panel can say that
    # instead of showing an empty list, which would read as "not in any book".
    ready: bool = True


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


class Heard(BaseModel):
    """What a recording turned out to be.

    Empty words with no ayahs is the ordinary answer to silence, not a failure.
    How sure the ear is of each word is a separate question, answered by
    POST /api/listen/check (see Sureness below) rather than carried here, so a
    slow score never holds back the words a reciter is already reading by.
    """
    text: str
    ayahs: list[HeardAyah] = []


class Sureness(BaseModel):
    """How sure the ear is of each word of the ayahs POST /api/listen/check named.

    Per "surah:ayah", one number per word, or null for a word the recording
    does not reach. Empty when the recording did not place on any of them.
    """
    sure: dict[str, list[float | None]] = {}


# ── Recite journal: what the page reports about itself ──────────────────────
# The same shape routers/listen.py uses for a reading id, so a page-reported
# event can be joined to the server-side lines for the same reading.
_ID_RE = re.compile(r"[A-Za-z0-9._:-]{1,64}")


class JournalPageEvent(BaseModel):
    """One thing the page itself saw: a mic gate closing, a reading it gave up
    waiting on. Server-side events are written straight to the journal through
    journal.note() and never pass through here."""
    at: str | int | float
    """When the page saw it, in whatever shape its own clock gave it."""
    kind: str = Field(min_length=1, max_length=40)
    session: str | None = Field(default=None, max_length=64)
    reading: str | None = Field(default=None, max_length=64)
    detail: dict | None = None

    @field_validator("kind")
    @classmethod
    def _kind_shape(cls, value: str) -> str:
        if not re.fullmatch(r"[a-z][a-z0-9._-]{0,39}", value):
            raise ValueError("kind must start with a lowercase letter and use only a-z 0-9 . _ -")
        return value

    @field_validator("session", "reading")
    @classmethod
    def _id_shape(cls, value: str | None) -> str | None:
        if value is not None and not _ID_RE.fullmatch(value):
            raise ValueError("must be 1-64 characters of letters, digits, . _ : -")
        return value


class JournalBatch(BaseModel):
    """What the page sends in one POST /api/journal. Event-count and byte-size
    limits are enforced by the router, from config, not here: they are
    runtime-tunable and a Pydantic Field constraint is fixed at import time."""
    events: list[JournalPageEvent]


# ── Progress: what a learner has answered ────────────────────────────────────
# Trust boundary as everywhere else in this file: the ids are a module's own
# short names, not prose, so they are capped tightly. `user` is deliberately
# absent, the server decides who is answering, never the page.
class AttemptIn(BaseModel):
    """One answer, as the page reports it."""
    module: str = Field(min_length=1, max_length=32)
    """Which panel asked: 'quiz' today, another tab later."""
    item: str = Field(min_length=1, max_length=200)
    """That panel's own stable id for the thing asked. The quiz sends meaningKey."""
    correct: bool
    ms: int | None = Field(default=None, ge=0, le=86_400_000)
    """How long the answer took. A day is already absurd; past that it is a bug
    or a clock change, and storing it would poison every average made from it."""
    context: dict | None = None
    """Small free-form note about the round it came from, kept for later
    questions nobody has asked yet ("am I worse on Arabic to English?"). Capped
    below, because an unbounded blob is a write endpoint's easiest abuse."""

    @field_validator("context")
    @classmethod
    def _small_enough(cls, value: dict | None) -> dict | None:
        if value is not None and len(json.dumps(value)) > 500:
            raise ValueError("context must serialise to 500 characters or fewer")
        return value


class AttemptSaved(BaseModel):
    saved: bool = True
    id: int


class FeedbackIn(BaseModel):
    """A note from the page about something that looks wrong."""
    module: str = Field(min_length=1, max_length=32)
    item: str | None = Field(default=None, max_length=200)
    """The question it is about, when there is one."""
    message: str = Field(min_length=1, max_length=2000)


class Forgotten(BaseModel):
    """How many answers a wipe removed."""

    deleted: int


class ItemStats(BaseModel):
    """One item's whole record. `avgMs` is None when nothing was timed honestly."""
    item: str
    attempts: int
    wrong: int
    avgMs: int | None = None
    inReview: bool = False


class ProgressSummary(BaseModel):
    module: str
    items: list[ItemStats] = []


class ReviewList(BaseModel):
    module: str
    items: list[str] = []
