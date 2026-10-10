"""Hadith tab types: collections and search, narrators, weak points, family view."""

from __future__ import annotations

from pydantic import BaseModel

from backend.models.common import Correction, Source


class HadithCollection(BaseModel):
    """One collection the module can browse or search, e.g. Sahih al-Bukhari."""
    id: str
    name: str
    short: str = ""
    # Every hadith in it is graded sahih, so none carries a grade of its own.
    sahih: bool = False


class HadithGrade(BaseModel):
    """One scholar's verdict on one hadith, e.g. Al-Albani: Hasan Sahih."""
    by: str
    grade: str


class HadithBook(BaseModel):
    """One book (chapter) inside a collection, and how many hadiths it holds."""
    number: int
    name: str
    count: int


class HadithEntry(BaseModel):
    """One hadith's own words. `cite` is where it is checked, sunnah.com's page.
    `cut` is [teller_at, body_at], offsets into `arabic` (services/hadith/chain); None where the end of the chain is not plain."""
    collection: str
    book: int
    number: int
    part: str = ""
    arabic: str
    english: str = ""
    grades: list[HadithGrade] = []
    cite: str = ""
    cut: list[int] | None = None


class HadithBookResponse(BaseModel):
    collection: HadithCollection
    book: HadithBook
    hadiths: list[HadithEntry]
    source: Source


class HadithChapter(HadithBook):
    """A book the hits fall in, offered as a way to narrow a loose question."""
    collection: str


class HadithReference(BaseModel):
    """A search that named one hadith ("muslim 8"): the number asked and the number shown, which differ when the collection skips it."""
    collection: str
    asked: str
    shown: str


class HadithSearchResponse(BaseModel):
    query: str
    collections: list[str] = []
    hits: list[HadithEntry] = []
    corrected: list[Correction] = []
    # Typed words no hadith holds and nothing is near enough to stand in for.
    unmatched: list[str] = []
    # No hadith holds every word; the hits are the closest by words and meaning.
    partial: bool = False
    chapters: list[HadithChapter] = []
    reference: HadithReference | None = None
    # False when the database has not been built yet (see services/hadith),
    # same shape as DaleelResponse.ready: the panel tells the two apart rather
    # than showing "nothing matches" for a search that could not run.
    ready: bool = True
    source: Source


class NarratorSummary(BaseModel):
    """A narrator of a chain in a line: his name and how sunnah.com grades him (rank 1 is the highest, None when ungraded)."""
    id: int
    name_ar: str = ""
    name_en: str = ""
    grade_ar: str = ""
    grade_rank: int | None = None


class RijalVerdict(BaseModel):
    scholar: str
    quote: str


class RijalText(BaseModel):
    """A classical book's entry on him, as sunnah.com prints it."""
    book: str
    body: str


class RijalFact(BaseModel):
    """One labelled fact as sunnah.com prints it, in English and in Arabic."""
    label_en: str
    en: str
    label_ar: str
    ar: str


class RijalBook(BaseModel):
    """A book that carries his hadith, named in both languages."""
    en: str
    ar: str


class UsulRule(BaseModel):
    say: str
    quote: str
    book: str
    page: str = ""


class UsulFact(BaseModel):
    """One line on a narrator's page: `text` in English, `ar` the Arabic it names, `quote` the book's words, `rule` the
    rule the line rests on, and the book and page."""
    text: str
    ar: str = ""
    quote: str = ""
    rule: UsulRule | None = None
    book: str
    page: str = ""


class UsulFacts(BaseModel):
    reliability: list[UsulFact] = []
    habits: list[UsulFact] = []
    life: list[UsulFact] = []
    books: list[UsulFact] = []
    source: Source | None = None


class Narrator(NarratorSummary):
    """One narrator's sheet. Teachers and students keep their names even where we hold no page of theirs."""
    kunya_ar: str = ""
    grade_en: str = ""
    generation_ar: str = ""
    years: str = ""
    lineage_ar: str = ""
    nisba_ar: str = ""
    city_ar: str = ""
    profession_ar: str = ""
    school_ar: str = ""
    books: list[RijalBook] = []
    facts: list[RijalFact] = []
    hadith_total: int | None = None
    verdicts: list[RijalVerdict] = []
    teachers: list[NarratorSummary] = []
    students: list[NarratorSummary] = []
    texts: list[RijalText] = []
    # What the narrator books say of him; empty while usul.db is not built.
    usul: UsulFacts = UsulFacts()
    source: Source


class RijalHadithRef(BaseModel):
    collection: str
    book: int
    number: int
    part: str = ""


class WeakNote(BaseModel):
    """A weak narrator named in a hadith: `at` is where his name starts in the hadith's Arabic, `grade` his wording as the data has it."""
    at: int
    id: int
    level: int
    kind: str
    grade: str


class WeakLift(BaseModel):
    """What a source says about support lifting a weakness, quoted. lifts is false where the source says it does not."""
    en: str
    lifts: bool = True
    quote: str
    source: str


class WeakLevel(BaseModel):
    """One of Ibn Hajar's twelve levels. lift is keyed by kind of weakness, empty where no source speaks."""
    level: int
    ar: str
    en: str
    kind: str
    weak: bool
    source: str
    lift: dict[str, WeakLift] = {}


class WeakLink(BaseModel):
    """A link of a chain a source puts in doubt: `student` says `word` before `teacher`, whose name starts at `at`.

    kind is tadlis, tadlis_unclear or not_heard; sub is the sort of statement for not_heard. level is the Ta'rif level
    of a tadlis teller. quote, scholar, source and page are a scholar's statement (not_heard only)."""
    at: int
    student: int
    teacher: int
    kind: str
    sub: str = ""
    word: str
    level: int = 0
    quote: str = ""
    scholar: str = ""
    source: str = ""
    page: str = ""


class WeakRule(BaseModel):
    """A rule a link note rests on, quoted from its book with the page."""
    label: str = ""
    say: str
    quote: str = ""
    source: str = ""
    page: str = ""


class WeakLinkRules(BaseModel):
    """kinds: by link kind (and by sub for a scholar's statement); levels: by the teller's Ta'rif level."""
    kinds: dict[str, WeakRule] = {}
    levels: dict[str, WeakRule] = {}


class Ruling(BaseModel):
    """What a classical ruling book says of a hadith, quoted: `quote` is the scholar's own sentence (empty for a chapter
    heading alone, which `chapter` then holds), `quote_label` what to call it where the book's remark needs
    saying, `asked` the question an 'Ilal answer answers, `page` where the book prints it. Matched by text and chain, so possible."""
    kind: str
    label: str
    quote_label: str = ""
    scholar: str = ""
    quote: str = ""
    asked: str = ""
    chapter: str = ""
    source: str
    page: str = ""


class UsulTerm(BaseModel):
    """One sort of ruling: `say` is its plain meaning, `count` how many of our hadith carry one."""
    kind: str
    label: str
    say: str
    count: int


class UsulTermHadith(BaseModel):
    """A page of the hadith carrying one sort of ruling; total counts them all."""
    kind: str
    total: int
    items: list[RijalHadithRef] = []


class RijalChains(BaseModel):
    """Where each narrator is named in a book's Arabic: hadith number and letter ("1620a") to [start, end, narrator id] slices.

    notes, links, link_rules and scale are the weak points on those chains, rulings what scholars said of each hadith;
    all are empty while usul.db is not built."""
    collection: str
    book: int
    chains: dict[str, list[list[int]]] = {}
    kin: dict[str, int] = {}   # hadith number to its lettered narrations across the collection, where more than one
    notes: dict[str, list[WeakNote]] = {}
    links: dict[str, list[WeakLink]] = {}
    rulings: dict[str, list[Ruling]] = {}
    link_rules: WeakLinkRules | None = None
    scale: list[WeakLevel] = []
    # False when rijal.db has not been built, same as HadithSearchResponse.ready.
    ready: bool = True
    source: Source


class FamilyNarrator(BaseModel):
    id: int
    name: str


class FamilyMark(BaseModel):
    """The word at index `at` of the matn split on whitespace: "only" in this telling, or a "dots" difference from `other`."""
    at: int
    kind: str
    other: str = ""


class FamilyPart(BaseModel):
    """One narration of a number against the viewed one: its own narrators, where it meets that chain, what it borrows."""
    part: str
    book: int
    own: list[FamilyNarrator]
    meet: FamilyNarrator | None = None
    borrowed: list[FamilyNarrator] = []
    said: str = ""
    # The telling's matn as the build split it into words, and the words only this telling has; only where some are marked.
    words: list[str] = []
    marks: list[FamilyMark] = []


class FamilyPlace(BaseModel):
    """One place of the chains (the Companion first): how many narrators stand there; `alone` words it where one carries every narration."""
    label: str
    count: int
    alone: str = ""


class FamilyPlaces(BaseModel):
    """The narrators at each place of the chains one book gives under one number. A count of this book's narrations, not a name for the hadith."""
    heading: str
    note: str
    places: list[FamilyPlace]


class FamilyWordsView(BaseModel):
    """What the words view is called and what its marks mean (usul.json `family.words`)."""
    label: str
    legend: str


class RijalFamily(BaseModel):
    viewed: str
    parts: list[FamilyPart]
    places: FamilyPlaces | None = None
    words: FamilyWordsView | None = None   # set only when some telling has marked words


class NarratorListItem(NarratorSummary):
    generation_ar: str = ""
    years: str = ""
    city_ar: str = ""
    hadith_count: int = 0


class RijalGeneration(BaseModel):
    key: str
    label: str


class NarratorList(BaseModel):
    """One page of the narrators named in our hadith, the most narrated first; total counts the whole filter."""
    items: list[NarratorListItem] = []
    total: int = 0
    generations: list[RijalGeneration] = []


class RijalSearch(BaseModel):
    query: str
    narrators: list[NarratorSummary] = []
    ready: bool = True
    source: Source
