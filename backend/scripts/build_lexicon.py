"""Build backend/data/lexicon.db, every word the quiz can ask about, in one table.

    python backend/scripts/build_lexicon.py

Why one table
-------------
The quiz's words used to sit in three files with three shapes. The everyday list
knew each word's topic but not whether it was a noun; the corpus files knew that
but had no topic; and the corpus cut was written once per surah and again once
per juz, so 3,657 words filled 38,000 rows. A wrong option is only tempting when
it shares the answer's topic or is the same type of word, so no file could
supply more than half of what makes a question fair.

One row per word here, every column filled. Which list a word came from stops
being which file it sits in and becomes a tag on its row, so a word can belong
to two lists at once and still be one word.

What counts as one word
-----------------------
The vocalised spelling. عالَم (worlds) and عالِم (All-Knower) are two words that
stop being different the moment the vowels come off, so bare letters cannot be
the identity, 268 spellings in the Qur'an alone share their letters with
another. A word that arrives twice under two spellings of one meaning, سَلَام
from the book and سَلام from the corpus, is one word: those merge on
(bare letters, meaning key), the only pair that means "same word, written
differently".

Where a word type comes from
----------------------------
Never guessed. Each list already declares it: the book names a type on every
group, the everyday list on every category, and the corpus tags every word by
hand. backend/data/word_kinds.json overrules all three for the handful they get
wrong. Anything still unknown is left NULL and printed by name, a gap is shown
as a gap, and such a word is still asked, matched on topic alone.

Derived, never authored
-----------------------
Every fact here comes from a file that is still the source of truth: corpus.db
and meanings.db for the Qur'an, vocabulary.json and quranic-words.json for the
two hand-written lists. Rebuild whenever they change. A correction therefore
goes in word_kinds.json, never into this database, or the next build loses it.
"""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
import tempfile
import zipfile
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.services.arabic_text import bare_letters  # noqa: E402

ROOT = Path(__file__).parent.parent.parent
DATA = ROOT / "backend" / "data"
QURAN = DATA / "quran"
LISTS = DATA  # the two hand-written word lists, beside the file that corrects them
OUT = DATA / "lexicon.db"

CONFIG = json.loads((DATA / "quiz_words.config.json").read_text("utf-8"))
STOPWORDS = set(CONFIG["stopwords"])
LEAD_FRAGMENTS = set(CONFIG["lead-fragments"])
PRONOUNS = set(CONFIG["pronouns"])
MAX_GLOSS_WORDS = CONFIG["max-gloss-words"]
ANKI_DECKS = [DATA / name for name in CONFIG["anki-decks"]]
GOVERNED = {bare_letters(particle) for particle in CONFIG["governed-particles"]}

WORD = re.compile(r"[a-z]+")
BRACKETED = re.compile(r"\([^)]*\)|\[[^\]]*\]")
# The stem of a word is the part that carries meaning. A word with two of them is
# a fused pair the corpus writes as one; it belongs to neither lemma, so it goes.
CONTENT = ("N", "V")
# The corpus names a name: PN sits in the segment's features. It is the only
# honest way to find them, the English gloss cannot be trusted for it, because
# the word-by-word capitalises "Most Merciful" and "Day" the same as "Hunain".
NAME = "PN"
DESCRIBING = "ADJ"
WORD_TYPES = ("noun", "verb", "adjective")
# Wiktionary's own names for the three, used only to argue with what the lists
# declare. Everything else it knows (adverb, particle, name…) is not one of them.
POS_TYPE = {"noun": "noun", "verb": "verb", "adj": "adjective"}

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE word (
  id             INTEGER PRIMARY KEY,
  ar             TEXT NOT NULL,   -- the vocalised spelling; what is shown
  bare           TEXT NOT NULL,   -- the same letters without the vowels
  en             TEXT NOT NULL,
  -- The same word's meaning in Urdu, empty where nobody wrote one. Only the
  -- Qur'anic words have it: it comes from Quran.com's word-by-word, and the
  -- everyday lists have no Urdu source at all. Empty stays empty rather than
  -- being filled in from the English, which would be a translation nobody made.
  ur             TEXT NOT NULL DEFAULT '',
  meaning_key    TEXT NOT NULL,   -- lowercased meaning; two options never share one
  word_type      TEXT CHECK (word_type IN ('noun','verb','adjective')),  -- NULL = not known
  root           TEXT NOT NULL DEFAULT '',
  times_in_quran INTEGER NOT NULL DEFAULT 0,
  attached       INTEGER NOT NULL DEFAULT 0,  -- never stands alone; its English is borrowed
  source         TEXT NOT NULL
);
-- Two spellings of one meaning are one word; one spelling is one word. Both
-- indexes hold only because the build merges on exactly those two keys, so a
-- broken merge fails here loudly instead of shipping a duplicate option.
CREATE UNIQUE INDEX word_spelling ON word (ar);
CREATE UNIQUE INDEX word_meaning  ON word (bare, meaning_key);

-- Every membership, on two axes. 'set' is which list the word belongs to;
-- 'group' is a named part of a set, stored with the set's own prefix because
-- the names collide, 'body' is both an everyday topic and a book group.
CREATE TABLE word_tag (
  word_id INTEGER NOT NULL REFERENCES word(id),
  axis    TEXT NOT NULL CHECK (axis IN ('set','group')),
  value   TEXT NOT NULL,
  PRIMARY KEY (word_id, axis, value)
);
CREATE INDEX word_tag_lookup ON word_tag (axis, value);

-- Where a word occurs in the Qur'an. Surah cuts and juz cuts are both worked
-- out from this, so neither is stored twice.
CREATE TABLE word_place (
  word_id INTEGER NOT NULL REFERENCES word(id),
  surah   INTEGER NOT NULL,
  ayah    INTEGER NOT NULL,
  PRIMARY KEY (word_id, surah, ayah)
);
"""


@dataclass
class Word:
    """One word, however many lists it turns out to belong to."""

    ar: str
    en: str
    meaningKey: str  # noqa: N815, the name the word lists and the browser use
    source: str
    ur: str = ""  # the Urdu meaning, where a source wrote one; "" is a real answer
    wordType: str | None = None  # noqa: N815
    root: str = ""
    timesInQuran: int = 0  # noqa: N815
    attached: bool = False
    sets: set[str] = field(default_factory=set)
    groups: set[str] = field(default_factory=set)
    places: set[tuple[int, int]] = field(default_factory=set)

    @property
    def bare(self) -> str:
        # A bracketed aside is a note about the word, not part of how it is
        # spelt: اِعْتَدَى (على) is spelt اعتدى. Counting the note as letters gave
        # it an identity no other list could ever match, which is how 24 words
        # the Qur'anic sets already teach walked past the check that drops them.
        return " ".join(bare_letters(BRACKETED.sub(" ", self.ar)).split())


class Lexicon:
    """The words gathered so far, and the two keys that decide "same word".

    The hand-written lists are read first, so when a word arrives twice the
    English a person wrote is the one kept and the corpus only adds to it.
    """

    def __init__(self) -> None:
        self.words: list[Word] = []
        self._by_spelling: dict[str, Word] = {}
        self._by_meaning: dict[tuple[str, str], Word] = {}
        self.merged = 0

    def add(self, word: Word) -> None:
        kept = self._by_spelling.get(word.ar) or self._by_meaning.get((word.bare, word.meaningKey))
        if kept is None:
            self.words.append(word)
            self._by_spelling[word.ar] = word
            self._by_meaning[(word.bare, word.meaningKey)] = word
            return

        self.merged += 1
        kept.sets |= word.sets
        kept.groups |= word.groups
        kept.places |= word.places
        kept.wordType = kept.wordType or word.wordType
        # The hand-written lists have no Urdu, so whichever copy of this word came
        # from the corpus is the only one that can supply it.
        kept.ur = kept.ur or word.ur
        kept.root = kept.root or word.root
        kept.timesInQuran = max(kept.timesInQuran, word.timesInQuran)
        # "attached" means the word never stands alone. One list finding it
        # standing alone settles it for both.
        kept.attached = kept.attached and word.attached


# ── the two hand-written lists ────────────────────────────────────────────────


def list_words(path: Path, set_id: str, groups_key: str, source: str) -> list[Word]:
    """One hand-written word list, typed by its own grouping.

    Both lists group their words and say what each group holds, the book names
    the baab for its verbs and the topic for its nouns, the everyday list names
    a topic per category. That declaration is the author's, so it is read rather
    than worked out.
    """
    payload = json.loads(path.read_text("utf-8"))
    declared = {group["id"]: group.get("wordType") for group in payload[groups_key]}
    if missing := {w["category"] for w in payload["words"]} - set(declared):
        raise SystemExit(f"{path.name}: no group declared for {sorted(missing)}")

    return [
        Word(
            ar=entry["ar"],
            en=entry["en"],
            meaningKey=entry["meaningKey"],
            source=source,
            wordType=declared[entry["category"]],
            timesInQuran=entry.get("timesInQuran", 0),
            sets={set_id},
            groups={f"{set_id}:{entry['category']}"},
        )
        for entry in payload["words"]
    ]


# ── an Anki deck ──────────────────────────────────────────────────────────────

# The card types that hold one word each. Everything else in a deck is a
# sentence, a fill-in-the-blank or a two-sided card that might be any of those,
# and none of them answer "what does this word mean?".
#
# The same "Arabic verbs"/"Arabic nouns" card name is used by more than one
# deck with different field names for the word and its meaning, one writes
# them as Arabic/English, another as Front/Back; so each entry lists every
# field-name pair it might be under, and the first pair the deck's own model
# actually has is the one read. Nothing here is a guess about one file; it is
# every name a deck author has in fact used for "the word" and "its meaning".
ANKI_CARDS = {
    "Optimal Arabic Verb Card": {"word_type": "verb", "fields": [("الماضي", "ترجمة")]},
    "Optimal Arabic Noun Card": {"word_type": "noun", "fields": [("المفرد", "الترجمة")]},
    "Arabic verbs": {"word_type": "verb", "fields": [("Arabic", "English"), ("Front", "Back")]},
    "Arabic nouns": {"word_type": "noun", "fields": [("Arabic", "English"), ("Front", "Back")]},
}
HTML_TAG = re.compile(r"<[^>]+>")
ARABIC_LETTER = re.compile(r"[ء-ي]")
ASIDE = re.compile(r"\s*\(([^)]*)\)")
# The deck writes alternatives three ways, and sometimes two of them in one
# gloss: "to follow, to pursue/to investigate". They all mean "or".
SEPARATOR = re.compile(r"\s*[/;]\s*")
# Two ways a deck has named its own book and chapter, tried in this order:
# Bayna_Yadayk::Book3::Ch.8::p2::Nouns, and Arabiyyah_Bayna_Yadayk_3::Chapter_01
#, the second sometimes with a ::Listening_Texts:: branch in between (still
# that chapter's own vocabulary, one word and its meaning per card, not the
# passage itself), and a book's own end-of-book word list tagged
# ::Appendix_1-16 rather than a chapter number.
REFERENCE = re.compile(r"Book\s*(\d+)::Ch\.\s*(\d+)")
REFERENCE_ALT = re.compile(
    r"Bayna_Yadayk_(\d+)::(?:Listening_Texts::)?(?:Chapter|Appendix)_([\w-]+)"
)


def anki_text(raw: str) -> str:
    """One field, as a person would read it: no markup, no runs of whitespace.

    A tag is replaced by a space rather than by nothing, so that "one<br>two"
    stays two words, which then leaves a gap in front of any punctuation that
    followed the tag, and "offspring ; descendant" is not how anyone writes it.
    """
    return tidy(HTML_TAG.sub(" ", raw).replace("&nbsp;", " "))


def tidy(text: str) -> str:
    """One meaning, punctuated one way.

    Three characters are used for "or" across the deck, a comma, a slash, a
    semicolon, so all three are written as the comma. Taking a bracket out can
    leave a space in front of the punctuation that followed it, and a separator
    at either end with nothing on the other side of it.
    """
    text = SEPARATOR.sub(", ", " ".join(text.split()))
    return re.sub(r"\s+([;,.!?])", r"\1", text).strip(" ,;-")


FORM_SEP = re.compile(r"\s*\\\s*")


def anki_lemma(raw: str) -> str:
    """The word a card teaches, without the preposition it governs.

    اِعْتَدَى (على) is a note to the reader that this verb takes على, useful on a
    flashcard, and not part of the spelling. An aside that is not one of the
    particles named in the config stays: كَادَ (يكاد) beside كَادَ (يكيد) are two
    different verbs sharing a past tense, and the aside is the only thing
    telling them apart on screen.

    Some decks write every principal part in one field, "تَحَدَّى \\ يَتَحَدَّى \\
    تَحَدَّ \\ تَحَدٍّ" is past, present, imperative, verbal noun of one verb, and
    "حَقٌّ \\ حُقُوقٌ" is a noun's singular and plural. Only the first is the word
    to learn; the rest are conjugation, not a second word.
    """
    # Two cards were typed as "(أَغْنَى (عَنْ": a bracket in front of the word,
    # opening nothing, and the real aside left unclosed at the end. Both are
    # mended before the rule below reads them, on the same argument anki_gloss
    # already makes, an unclosed aside is still an aside.
    text = FORM_SEP.split(anki_text(raw), 1)[0].lstrip("( ")
    text += ")" * max(0, text.count("(") - text.count(")"))
    return ASIDE.sub(
        lambda aside: "" if bare_letters(aside[1]) in GOVERNED else aside[0],
        text,
    ).strip()


def anki_gloss(raw: str) -> str:
    """The meaning a card teaches, without the notes its author left himself.

    These cards carry asides in brackets, "noble, honoured (not كريم or نبيل)",
    "to bless (with على)", which warn a reader off a near-synonym or name the
    preposition. Useful on a flashcard, wrong in a quiz option twice over: the
    aside is about a different word than the one being asked, and it puts Arabic
    inside the English, which an Arabic-to-English question gives itself away
    on before anything is read. 287 of these meanings carry Arabic that way.

    Only the brackets go. The meaning itself is left whole, however long; a
    full "to carry out, to execute, to implement" is safe beside three other
    options that also open "to", which is what pickDistractors now arranges.
    """
    text = anki_text(raw)
    # One card opens a bracket and never closes it, "road, way, street, lane
    # (not طريق, سبيل,", and an unclosed aside is still an aside, so it is cut
    # at the bracket rather than costing the word its perfectly good meaning.
    if text.count("(") > text.count(")"):
        text = text[: text.rindex("(")]
    # Tidied again after the brackets go, because taking one out of the middle
    # is what leaves "to follow , to pursue" and a trailing "to bite/".
    return tidy(clean_gloss(text))


def anki_note(note: dict, spec: dict, tags: str, where: str) -> Word | None:
    """One card as a word, or None when the card cannot be quizzed.

    Pure: the note's fields already split out, a word or nothing back, no file
    and no deck. This is every rule about what a card has to say before it may
    join the quiz, in one place where each can be read and checked.

    `where` names the deck only so a card that breaks a rule can say which file
    it came from; nothing is read from it.
    """
    ar_field, en_field = spec["pair"]
    ar, en = anki_lemma(note[ar_field]), anki_gloss(note[en_field])
    # A meaning that was nothing but an aside comes back empty, and a word with
    # Arabic still in its English after the brackets are gone is one this deck
    # wrote as a note rather than as a meaning. Neither can be quizzed.
    if not ar or not en or ARABIC_LETTER.search(en):
        return None

    if not (
        chapter := REFERENCE.search(note.get("reference", ""))
        or REFERENCE.search(tags)
        or REFERENCE_ALT.search(tags)
    ):
        # Every set's words are grouped, and the quiz leans on that to pick a
        # tempting wrong option. A word with nowhere to belong would join
        # silently and quietly weaken every question it appears in.
        raise SystemExit(f"{where}: {ar} names no book and chapter")

    return Word(
        ar=ar,
        en=en,
        # Two cards glossed the same way are the same meaning, which is what
        # stops both being offered as options in one question.
        meaningKey=en.lower(),
        source=spec["source"],
        wordType=spec["word_type"],
        # Not every deck declares a root, only kept when the field is there and
        # says something, so a missing one stays "" rather than becoming a fact.
        root=bare_letters(anki_text(note["Root"])) if note.get("Root") else "",
        sets={spec["set_id"]},
        # The chapter is kept because it is the only grouping the deck states.
        # No picker reads it yet; it is here so one can, without a rebuild. Six
        # cards leave the reference field empty and carry the same chapter in
        # their tags, so both are read.
        groups={f"{spec['set_id']}:book{chapter[1]}-ch{chapter[2]}"},
    )


def anki_words(path: Path, set_id: str, source: str) -> list[Word]:
    """The vocabulary cards of an Anki deck, as words.

    An .apkg is a zip holding a SQLite collection, so no Anki install is needed
    to read one. Each note stores its fields as one string with 0x1f between
    them, in the order its own note type declares; which is why the note types
    are read first rather than the columns being counted.

    The card says which type of word it is by being a verb card or a noun card,
    so nothing here is guessed. A verb is filed under its past tense, the form
    the deck itself leads with and the one a dictionary lists.
    """
    with zipfile.ZipFile(path) as archive:
        collection = Path(tempfile.gettempdir()) / f"{path.stem}.anki21"
        collection.write_bytes(archive.read("collection.anki21"))

    deck = sqlite3.connect(collection)
    fields_of = {
        int(mid): (model["name"], [f["name"] for f in model["flds"]])
        for mid, model in json.loads(
            deck.execute("SELECT models FROM col").fetchone()[0]
        ).items()
    }

    words, unquizzable = [], []
    for mid, tags, raw in deck.execute("SELECT mid, tags, flds FROM notes"):
        card, names = fields_of[mid]
        if card not in ANKI_CARDS:
            continue
        pair = next((pair for pair in ANKI_CARDS[card]["fields"] if pair[0] in names), None)
        if pair is None:
            raise SystemExit(f"{path.name}: {card} has none of the expected field names ({names})")

        note = dict(zip(names, raw.split("\x1f")))
        spec = {**ANKI_CARDS[card], "pair": pair, "set_id": set_id, "source": source}
        if word := anki_note(note, spec, tags, path.name):
            words.append(word)
        elif ar := anki_lemma(note[pair[0]]):
            # Counted, not silently dropped: a deck that suddenly stops
            # importing says so in this number rather than in a short quiz.
            unquizzable.append((ar, anki_text(note[pair[1]])))
    deck.close()
    collection.unlink(missing_ok=True)
    if unquizzable:
        print(f"  {len(unquizzable)} whose English is a note, not a meaning; left out:")
        for ar, en in unquizzable[:5]:
            print(f"    {ar}  {en[:70]}")
        if len(unquizzable) > 5:
            print(f"    …and {len(unquizzable) - 5} more")
    return words


# ── the Qur'an ────────────────────────────────────────────────────────────────


def clean_gloss(text: str) -> str:
    """Strip the bracketed helper text a word-by-word gloss carries.

    Both shapes of bracket: "(is) Allah" and "[the] cows", and the ones written
    inside a word, "darkness[es]" is darkness. A gloss that was nothing but a
    bracket comes back empty and is dropped further down.
    """
    return " ".join(BRACKETED.sub(" ", text).split())


def gloss_flaws(gloss: str, word_type: str) -> int:
    """How far this gloss is from a dictionary meaning, 0 is clean.

    A gloss is written for the word in its place, so it drags its neighbours in:
    "and not he delayed" is لَبِثَ standing after a وَ, "on the bank" is the bank
    with an عَلَى on its front, and "their fingers" is fingers with a pronoun
    stuck to its back. All are unlearnable as answers and free to dismiss as
    wrong options, so the count is used twice below; to pick which reading of a
    lemma to quote, and to drop a lemma that has no clean reading anywhere.

    A verb is judged more gently: "He guides" is how English writes a conjugated
    verb, not a leak.
    """
    if words := gloss.lower().split():
        return (
            int(words[0] in LEAD_FRAGMENTS)
            + int(len(words) > MAX_GLOSS_WORDS)
            + int(word_type != "verb" and bool(PRONOUNS & set(WORD.findall(gloss.lower()))))
        )
    else:
        return 3  # an empty gloss, the cleaning took the whole thing away


def is_quizzable(lemma: str, gloss: str) -> bool:
    """Is this word worth a four-option meaning question?

    Particles and pronouns are not: "and" has no meaning you could pick out of a
    list of four. Names are refused before this, by the corpus's own PN tag.
    """
    if len(bare_letters(lemma)) < CONFIG["min-arabic-chars"]:
        return False
    return any(word not in STOPWORDS for word in gloss.lower().split())


def type_of(pos: str, features: str) -> str:
    """Which of the three types this word is, read off the corpus's own tags.

    The corpus already knows verb from noun from adjective, so nothing here is
    guessed.
    """
    if pos == "V":
        return "verb"
    return "adjective" if DESCRIBING in features.split("|") else "noun"


def words_with_lemmas(
    corpus: sqlite3.Connection,
) -> dict[tuple[int, int, int], tuple[str, int, bool, str, str]]:
    """Every word of the Qur'an that has one content stem, and what is known of
    it: its lemma, how many pieces the word is in, whether it is a name here,
    which type of word it is, and its root.

    The piece count is what makes a gloss trustworthy: 1 means the word stands
    alone in the ayah, with no "and", no "the", no attached pronoun; so the
    English beside it is the English of the word itself.
    """
    pieces: dict[tuple[int, int, int], list[tuple[str, str, str, str]]] = defaultdict(list)
    for surah, ayah, word, pos, lemma, features, root in corpus.execute(
        "SELECT surah, ayah, word, pos, lemma, features, root FROM segment"
        " ORDER BY surah, ayah, word, segment"
    ):
        pieces[(surah, ayah, word)].append((pos, lemma, features or "", root or ""))

    found = {}
    for place, parts in pieces.items():
        stems = [part for part in parts if part[1] and part[0] in CONTENT]
        if len(stems) == 1:
            pos, lemma, features, root = stems[0]
            found[place] = (
                lemma,
                len(parts),
                NAME in features.split("|"),
                type_of(pos, features),
                root,
            )
    return found


def corpus_words(corpus: sqlite3.Connection, meanings: sqlite3.Connection) -> list[Word]:
    """Every Qur'anic lemma worth asking about, glossed from its cleanest place.

    A word-by-word gloss describes the word IN ITS PLACE, prefixes and all, so
    each lemma is quoted from the one occurrence where it stands with the fewest
    pieces attached. Two thirds stand completely bare somewhere; the rest never
    do and are marked `attached` so the quiz can say so rather than pass a
    joined-up gloss off as a dictionary meaning.
    """
    lemmas = words_with_lemmas(corpus)
    rows = list(meanings.execute("SELECT surah, ayah, word, en, ur FROM meaning"))
    glosses = {(surah, ayah, word): clean_gloss(english) for surah, ayah, word, english, _ in rows}
    # The Urdu of the very same occurrence, so both meanings describe the same
    # reading of the word. Which occurrence is cleanest is decided on the English
    # below, because that is the side the flaw rules were written for; the Urdu
    # follows the place that choice lands on rather than being judged again.
    urdu = {(surah, ayah, word): clean_gloss(text) for surah, ayah, word, _, text in rows if text}

    # Each lemma's own cleanest reading is where its English comes from: not a
    # name if the word is ever used as an ordinary word, then the gloss that
    # reads as a meaning rather than a clause, then fewest pieces attached, then
    # earliest in the Qur'an to break a tie. مَدِينَة is a city before it is
    # Madinah; حُنَيْن is only ever the valley, so it has no ordinary reading to
    # fall back on and drops out below.
    best: dict[str, tuple[bool, int, int, tuple[int, int, int]]] = {}
    facts: dict[str, tuple[str, str]] = {}
    where: dict[str, set[tuple[int, int]]] = defaultdict(set)
    seen: dict[str, int] = defaultdict(int)
    for place, (lemma, pieces, is_name, word_type, root) in lemmas.items():
        if place not in glosses:
            continue
        seen[lemma] += 1
        where[lemma].add(place[:2])
        reading = (is_name, gloss_flaws(glosses[place], word_type), pieces, place)
        if lemma not in best or reading < best[lemma]:
            best[lemma] = reading
            facts[lemma] = (word_type, root)

    words, names, fragments = [], 0, 0
    for lemma, (is_name, flaws, pieces, place) in best.items():
        gloss = glosses[place]
        if is_name:
            # Every reading of this word in the Qur'an is a name. Knowing who
            # Fir'awn was is Islamic knowledge, not Arabic vocabulary, and as a
            # wrong option a name is dismissed without reading the question.
            names += 1
            continue
        if flaws:
            # No reading of this word anywhere in the Qur'an gives a meaning that
            # stands on its own, every one is a clause or starts mid-sentence.
            # Asked, it cannot be learnt; offered, it is dismissed.
            fragments += 1
            continue
        if not is_quizzable(lemma, gloss):
            continue
        word_type, root = facts[lemma]
        words.append(
            Word(
                ar=lemma,
                en=gloss,
                ur=urdu.get(place, ""),
                meaningKey=gloss.lower(),
                source="corpus",
                wordType=word_type,
                root=root,
                timesInQuran=seen[lemma],
                attached=pieces > 1,
                sets={"quran"},
                places=where[lemma],
            )
        )

    print(f"  Qur'an: {len(words)} words, out of {len(best)} lemmas the corpus names")
    print(f"    {names} dropped as names, {fragments} as clauses")
    return words


# ── writing ───────────────────────────────────────────────────────────────────


def only_new_words(lexicon: Lexicon, arriving: list[Word]) -> tuple[list[Word], dict[str, int]]:
    """The arriving words that are not already somewhere in the table.

    Everything else in this build merges: a word in two lists becomes one row
    carrying both labels. This set does not. It is everyday vocabulary, and a
    word already in the Qur'anic sets is one you are already being asked, so
    letting it in again would ask it twice under two names rather than teach
    anything new. It is dropped, and counted so the build can say how many.

    It must ask the same question the merge asks, on both of the merge's keys,
    or a word slips through this test and is then merged anyway, landing its
    everyday tag on a row that is already Qur'anic, which is the one outcome
    this exists to prevent. So a word is known if it shares an exact spelling
    with a row, OR its letters and meaning, OR its letters and type: the first
    two are Lexicon.add's own keys, the third catches this deck vowelling a
    word its own way. أَوَّل arrived under all three at once.
    """
    def keys_of(word: Word) -> tuple[object, ...]:
        # Noun and adjective count as one type here, and only here. Arabic does
        # not draw that line sharply, طَيِّب is "good" as either, and this build
        # already re-labels whole groups of the book from one to the other, so
        # رَبّ the adjective and رَبٌّ the noun are the same word to someone
        # deciding what to study, even though the quiz keeps them apart when it
        # picks wrong options. The verb boundary is the real one: مَال (wealth)
        # and مَالَ (to lean) share their letters and are two words.
        naming = word.wordType == "verb"
        return (word.ar, (word.bare, word.meaningKey), (word.bare, naming))

    known: dict[object, str] = {}
    for word in lexicon.words:
        label = "+".join(sorted(word.sets))
        for key in keys_of(word):
            known.setdefault(key, label)

    kept, dropped = [], defaultdict(int)
    for word in arriving:
        keys = keys_of(word)
        seen = next((known[k] for k in keys if k in known), None)
        if seen is not None:
            dropped[f"already in {seen}"] += 1
            continue
        for key in keys_of(word):
            known.setdefault(key, "this deck")
        kept.append(word)
    return kept, dict(sorted(dropped.items()))


def content_digest(db: sqlite3.Connection) -> str:
    """A fingerprint of what the table holds.

    The browser reads files exported from this table, not the table itself, so
    rebuilding it and forgetting to export leaves the quiz on yesterday's words
    with nothing on screen to say so. The export carries this digest, and a test
    compares the two, which is the whole point of it. It is a digest of the
    content rather than a build time so that rebuilding the same sources twice
    gives the same answer, and only a real change moves it.
    """
    fingerprint = hashlib.sha256()
    for query in (
        "SELECT ar, en, meaning_key, word_type, times_in_quran, attached FROM word ORDER BY id",
        "SELECT word_id, axis, value FROM word_tag ORDER BY word_id, axis, value",
        "SELECT word_id, surah, ayah FROM word_place ORDER BY word_id, surah, ayah",
    ):
        for row in db.execute(query):
            fingerprint.update(repr(row).encode())
    return fingerprint.hexdigest()[:16]


def write(lexicon: Lexicon, sets: list[dict]) -> None:
    OUT.unlink(missing_ok=True)
    db = sqlite3.connect(OUT)
    db.executescript(SCHEMA)
    for word in lexicon.words:
        cursor = db.execute(
            "INSERT INTO word"
            " (ar, bare, en, ur, meaning_key, word_type, root, times_in_quran, attached, source)"
            " VALUES (?,?,?,?,?,?,?,?,?,?)",
            (word.ar, word.bare, word.en, word.ur, word.meaningKey, word.wordType, word.root,
             word.timesInQuran, int(word.attached), word.source),
        )
        word_id = cursor.lastrowid
        db.executemany(
            "INSERT INTO word_tag (word_id, axis, value) VALUES (?,?,?)",
            [(word_id, "set", s) for s in sorted(word.sets)]
            + [(word_id, "group", g) for g in sorted(word.groups)],
        )
        db.executemany(
            "INSERT INTO word_place (word_id, surah, ayah) VALUES (?,?,?)",
            [(word_id, surah, ayah) for surah, ayah in sorted(word.places)],
        )
    db.executemany(
        "INSERT INTO meta (key, value) VALUES (?,?)",
        [
            ("schema_version", "1"),
            ("sets", json.dumps(sets, ensure_ascii=False)),
            ("content", content_digest(db)),
        ],
    )
    db.commit()
    db.close()


def main() -> None:
    print("Reading the two word lists…")
    everyday = json.loads((LISTS / "vocabulary.json").read_text("utf-8"))
    book = json.loads((LISTS / "quranic-words.json").read_text("utf-8"))

    lexicon = Lexicon()
    # Hand-written lists first: when the same word also turns up in the Qur'an,
    # the English a person wrote is the one kept.
    for word in list_words(LISTS / "vocabulary.json", "everyday", "categories", "vocabulary"):
        lexicon.add(word)
    for word in list_words(LISTS / "quranic-words.json", "book", "groups", "80% of Qur'anic Words"):
        lexicon.add(word)
    hand_written = list(lexicon.words)

    print("Reading the hand-tagged corpus…")
    for word in corpus_words(
        sqlite3.connect(QURAN / "corpus.db"), sqlite3.connect(QURAN / "meanings.db")
    ):
        lexicon.add(word)

    # Last, and only what is new. Read after the Qur'an so the drop rule can see
    # every Qur'anic word: these decks teach everyday Arabic, and a word already
    # waiting in the Qur'anic sets should not also be asked as everyday. Read in
    # order, each deck seeing what the ones before it already added, so the same
    # word taught twice, once in the old merged deck, once in a newer per-book
    # one, becomes one row rather than being asked twice under two names.
    for deck in ANKI_DECKS:
        print(f"Reading {deck.name}…")
        arriving = anki_words(deck, "everyday", "Al-'Arabiyyah Bayna Yadayk")
        fresh, skipped = only_new_words(lexicon, arriving)
        for word in fresh:
            lexicon.add(word)
        print(f"  {len(arriving)} vocabulary cards, {len(fresh)} of them new")
        for reason, count in skipped.items():
            print(f"    {count:>5} {reason}")

    # A word a person has checked beats every list's declaration.
    overrides = json.loads((DATA / "word_kinds.json").read_text("utf-8"))["kinds"]
    by_spelling = {word.ar: word for word in lexicon.words}
    if unknown := sorted(set(overrides) - set(by_spelling)):
        raise SystemExit(f"word_kinds.json names words that are not in any list: {unknown}")
    for spelling, word_type in overrides.items():
        if word_type not in WORD_TYPES:
            raise SystemExit(f"word_kinds.json gives {spelling} an unknown type: {word_type}")
        by_spelling[spelling].wordType = word_type

    # What the picker needs to name each set on screen. Kept with the words
    # because it belongs to the list it describes.
    sets = [
        {"id": "everyday", "label": "Everyday", "dialect": everyday["dialect"]},
        {"id": "book", "label": "80% book", "source": book["source"], "groups": book["groups"]},
        {
            "id": "quran",
            "label": "Whole Qur'an",
            "source": {
                "title": "Quranic Arabic Corpus morphology (lemmas)",
                "english": "Quran.com word-by-word",
            },
        },
    ]
    write(lexicon, sets)

    # ── what the build could not settle, said out loud ────────────────────────
    tally: dict[str | None, int] = defaultdict(int)
    for word in lexicon.words:
        tally[word.wordType] += 1
    print(f"\n{len(lexicon.words)} words ({lexicon.merged} arrived twice and merged)")
    print(f"  types: {dict(sorted(tally.items(), key=lambda kv: str(kv[0])))}")

    if untyped := [w for w in lexicon.words if w.wordType is None]:
        print(f"  {len(untyped)} with no type, asked, but matched on topic alone:")
        for word in untyped:
            print(f"    {word.ar}  {word.en}  ({', '.join(sorted(word.sets))})")

    # Wiktionary never decides a type here, it only argues with one. A word whose
    # entry cannot be a noun, verb or adjective at all is where a list's group is
    # most likely wrong.
    pos: dict[str, set[str]] = defaultdict(set)
    for entry in json.loads((DATA / "arabic_dictionary.json").read_text("utf-8")):
        pos[bare_letters(entry["arabic"])] |= {POS_TYPE[p] for p in entry["pos"] if p in POS_TYPE}
    if disputed := [
        word
        for word in hand_written
        if word.wordType
        and pos.get(word.bare)
        and word.wordType not in pos[word.bare]
    ]:
        print(f"  {len(disputed)} the dictionary disagrees with, check their group:")
        for word in disputed:
            print(f"    {word.ar}  {word.en}  list says {word.wordType},"
                  f" dictionary says {'/'.join(sorted(pos[word.bare]))}")

    print(f"\nWrote {OUT} ({OUT.stat().st_size / 1_000_000:.1f} MB)")
    # The quiz reads the export, not this table, so the build is only half done.
    print("Now run: python backend/scripts/export_quiz_words.py")


if __name__ == "__main__":
    main()
