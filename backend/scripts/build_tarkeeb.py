"""Build data/tarkeeb/tarkeeb.db, the Qur'an's tarkeeb, as scholars recorded it.

Where this comes from
---------------------
The Quranic Treebank (NoorBayan, MIT licence). For every word of all 6,236
ayahs it names the word's job in Arabic, فاعل, مضاف إليه, بدل; and points at
the word that governs it. That is the thing corpus.db does not have and the
rules in services/tarkeeb.py can only approximate.

The data is a .rar, so it is not downloaded here. Get it once::

    curl -LO https://raw.githubusercontent.com/NoorBayan/Quranic/main/corpus/Quranic.rar
    curl -LO https://raw.githubusercontent.com/NoorBayan/Quranic/main/corpus/RelLabels.csv
    7z x Quranic.rar
    venv/Scripts/python backend/scripts/build_tarkeeb.py Quranic.csv RelLabels.csv

How a particle is read
----------------------
The treebank often hangs the governed word off its particle, يَعْلَمُ off لَا,
and writes the particle's meaning (نفي) on that arrow. Read as the verb's own
job, that drew 1,331 verbs as "نفي", 931 as "شرط", and 5,000-odd particles a
sentence rests on as its مبتدأ. An arrow whose name is already inside its
particle head's own name (نفي in حرف نفي) is the particle's meaning; the word
under it opens a clause, and the particle is named by what it is, from
tarkeeb.json's particle_kinds. Arrows the name does not say (مجرور under
حرف جر, منادى under حرف نداء) stay the governed word's job.

What it has to do
-----------------
A treebank is a set of arrows: each word points at the word it hangs off. A
tarkeeb diagram is a set of brackets: each unit covers a run of neighbouring
words. The two are not the same, and one does not always become the other; an
arrow can reach over words that belong to something else, and no bracket can be
drawn round that. So every ayah is put through five checks and an ayah that
fails any of them is not written. It falls back to the rules at read time, and
the count of what fell through is printed at the end rather than buried.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.services import arabic_text, quran_corpus, tarkeeb, tarkeeb_store  # noqa: E402

DATABASE = Path(__file__).parent.parent / "data" / "tarkeeb" / "tarkeeb.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS tarkeeb (
    surah INTEGER NOT NULL,
    ayah  INTEGER NOT NULL,
    words TEXT NOT NULL,
    tree  TEXT NOT NULL,
    -- the written words folded for lookup (tarkeeb_store.letters), so an ayah
    -- typed into the Nahw analyser is drawn from this record, not re-derived
    letters TEXT NOT NULL,
    -- which columns of `words` were written; the rest are the book's own
    written TEXT NOT NULL,
    PRIMARY KEY (surah, ayah)
);
CREATE INDEX IF NOT EXISTS tarkeeb_letters ON tarkeeb (letters);
"""


# ── Reading the treebank ─────────────────────────────────────────────────────

def read_rows(path: Path) -> dict[tuple[int, int], list[list[dict]]]:
    """Every ayah as its sentences, each sentence as its rows, in written order."""
    csv.field_size_limit(10**7)
    sentences: dict[tuple[int, int, int], list[dict]] = defaultdict(list)
    with path.open(encoding="utf-16", newline="") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            key = (int(row["chapter_id"]), int(row["verse_id"]), int(row["sentence_id"]))
            sentences[key].append(row)

    ayahs: dict[tuple[int, int], list[list[dict]]] = defaultdict(list)
    for (surah, ayah, _), rows in sentences.items():
        ayahs[(surah, ayah)].append(rows)
    return ayahs


def known_relations(path: Path) -> set[str]:
    """The relation names the treebank documents. Anything else is a typo, not a term."""
    with path.open(encoding="utf-16", newline="") as handle:
        return {row["rel_ar"].strip() for row in csv.DictReader(handle, delimiter="\t")}


# ── One sentence, from arrows to brackets ────────────────────────────────────

def _words_of(rows: list[dict], settings: dict) -> tuple[list[dict], dict[int, int]]:
    """The sentence's words in order, and which word each token belongs to.

    A written word arrives as several rows, a prefix, the stem, an ending; and
    tarkeeb joins words, not pieces. An elided word has no spelling at all and
    still takes a column, because what a book is teaching there is exactly that
    something is missing.
    """
    words: list[dict] = []
    at: dict[tuple, int] = {}
    belongs: dict[int, int] = {}

    for row in rows:
        # Word 0 is the treebank's slot for what is not written: an elided khabar,
        # or the "you" inside an imperative. Each is its own column, keyed by its
        # token, keying by word 0 would fold two of them into one.
        unwritten = int(row["word_id"]) == 0
        key = ("unwritten", int(row["token_id"])) if unwritten else ("word", int(row["word_id"]))
        if key not in at:
            at[key] = len(words)
            # A written word starts empty and collects its pieces below. An
            # unwritten one is settled here: (*) has no spelling at all, while
            # (أَنْتَ) is the one the book supplies in brackets, and printing it
            # is the whole point.
            supplied = row["uthmani_token"]
            words.append({
                "text": (settings["unwritten_mark"] if supplied == "(*)" else supplied) if unwritten else "",
                "elided": unwritten,
            })
        index = at[key]
        belongs[int(row["token_id"])] = index
        if not unwritten:
            words[index]["text"] += row["uthmani_token"]

    # A و or ف that governs nothing is written as a token with no relation at
    # all. That is the fact worth keeping: it is not part of the word's own job,
    # and a reader may want to see it standing on its own.
    connectors = settings["connector_pos"]
    for row in rows:
        if row["rel_label_ar"] not in settings["not_a_relation"]:
            continue
        key = connectors.get(row["pos"])
        if key is None:
            continue
        word = words[belongs[int(row["token_id"])]]
        if "PREFIX" in row["features"]:
            word.setdefault("connector", {"text": row["uthmani_token"], "key": key})
        else:
            word.setdefault("connector_only", key)

    # A word's own job is the one its stem carries; a prefix like ٱل has none.
    kinds = settings["particle_kinds"]
    by_token = {int(row["token_id"]): row for row in rows}
    for row in rows:
        if row["rel_label_ar"] in settings["not_a_relation"]:
            continue
        word = words[belongs[int(row["token_id"])]]
        # Every piece that has a job, in written order: أَفَلَا is three.
        word.setdefault("pieces", []).append(row["pos_ar"])
        if "relation" in word:
            continue
        word["relation"] = row["rel_label_ar"]
        word["head"] = belongs.get(int(row["ref_token_id"]))
        word["constituent"] = row["constituent_label"]
        word["pos"] = row["pos"]
        if word["relation"] != settings["root"]:
            head = by_token.get(int(row["ref_token_id"]))
            word["states_head"] = _states_particle(word["relation"], head, kinds)

    for word in words:
        pieces = word.get("pieces", [])
        word["particle"] = bool(pieces) and all(piece in kinds for piece in pieces)
    return words, belongs


def _states_particle(relation: str, head: dict | None, kinds: dict) -> bool:
    """True when this arrow's name is its particle head's meaning, not this word's job.

    The treebank hangs يَعْلَمُ off لَا and writes نفي on the arrow: that is what
    لَا does, and it is already inside the particle's own name, حرف نفي. An arrow
    the name does not contain, مجرور under حرف جر, is the governed word's job.
    """
    if head is None or head["pos_ar"] not in kinds:
        return False
    said = arabic_text.bare_letters(relation)
    return bool(said) and said in arabic_text.bare_letters(head["pos_ar"])


def _sentence_label(word: dict | None, settings: dict) -> dict:
    """What kind of sentence rests on this word, verbal if the word is a verb.

    `word` is the first word under any particles the sentence opens with
    (أَفَلَا يَعْلَمُ rests on يَعْلَمُ), or None when a particle governs no clause.
    """
    kind = settings["sentence_labels"]["verb" if word and word.get("pos") == "V" else "other"]
    return tarkeeb._term(kind)


def _opening_role(word: dict, settings: dict) -> dict:
    """What the word a sentence (or a clause under a particle) rests on is doing in it.

    The treebank writes "root" here, which is a marker for its own machinery and
    says nothing to a reader. A particle is what it is, حَرْفُ اسْتِفْهَامٍ; otherwise
    the word a verbal sentence rests on is its verb, and the word a nominal one
    rests on is its mubtada.
    """
    if word.get("particle"):
        return _particle(word["pieces"][0], settings)
    return tarkeeb._term("fil" if word.get("pos") == "V" else "mubtada")


def _sentence_names(settings: dict) -> set[str]:
    """How a whole clause is labelled, whichever kind it is."""
    return {tarkeeb._term(key)["ar"] for key in settings["sentence_labels"].values()}


def _particle(kind: str, settings: dict) -> dict:
    """A particle named by what it is, in the app's spelling: a shared term where
    the rules name it too, so إِنَّ reads the same on every path."""
    named = settings["particle_kinds"][kind]
    if named in tarkeeb._rules()["terms"]:
        return tarkeeb._term(named)
    return {"ar": named, "tone": settings["particle_tone"]}


def _tree_of(words: list[dict], settings: dict, tone_of) -> dict | None:
    """The bracket tree for one sentence, or None when no bracket can be drawn.

    A word becomes a bracket over itself and everything hanging off it. That is
    only a bracket if the words it reaches are exactly the neighbours between
    its first and its last, otherwise the arrows cross, and a diagram would
    have to draw a unit with a hole in it.
    """
    children: dict[int, list[int]] = defaultdict(list)
    roots: list[int] = []
    for index, word in enumerate(words):
        head = word.get("head")
        if word.get("relation") is None or head is None or head == index:
            roots.append(index)
        else:
            children[head].append(index)

    if not roots:
        return None

    reach: dict[int, tuple[int, int, int]] = {}

    def measure(index: int) -> tuple[int, int, int]:
        low = high = index
        count = 1
        for child in children[index]:
            a, b, n = measure(child)
            low, high, count = min(low, a), max(high, b), count + n
        reach[index] = (low, high, count)
        return reach[index]

    for root in roots:
        measure(root)
    if any(high - low + 1 != count for low, high, count in reach.values()):
        return None

    def resting(index: int) -> dict | None:
        """The word a sentence rests on once the particles opening it are passed:
        under أَ and لَا, it is يَعْلَمُ."""
        word = words[index]
        if not word.get("particle"):
            return word
        for child in sorted(children[index]):
            if words[child].get("states_head") and (found := resting(child)):
                return found
        return None

    def build(index: int) -> dict:
        word = words[index]
        relation = word.get("relation")
        # "root" is the treebank's marker for the word a sentence rests on, not
        # something a reader should ever see. What it means is that this is where
        # a sentence starts, so that is what gets written instead. A word whose
        # arrow only says what its particle head does starts a clause under that
        # particle, so it is named the same way.
        opens_clause = relation == settings["root"] or word.get("states_head", False)
        rests_on = resting(index) if opens_clause else None
        # a particle governing no clause at all opens no kind of sentence
        sentence = _sentence_label(rests_on, settings) if rests_on else None
        opening = _opening_role(word, settings) if opens_clause else None
        # Written the app's way where the app has a wording for it, and left in
        # the treebank's own words where it does not.
        said, raw = tarkeeb.relation_wording(relation)
        role = opening["ar"] if opens_clause else said
        tone = opening["tone"] if opens_clause else tone_of(relation)
        # Inside its own unit a particle is what it is (فِى is حَرْفُ جَرٍّ); the
        # unit it heads carries the job (the jar-majroor is مُتَعَلِّقٌ).
        kind = (word.get("pieces") or [""])[0]
        own = (_particle(kind, settings) if word.get("particle")
               else tarkeeb._term(settings["unit_heads"][kind])
               if children[index] and kind in settings["unit_heads"] else None)
        clause = settings["constituent_labels"].get(word.get("constituent"))
        if own is None and children[index] and clause in _sentence_names(settings):
            # هُوَ heading هُوَ ٱللَّهُ أَحَدٌ is its mubtada; the clause is the مفعول به
            own = _opening_role(word, settings)

        leaf = {"word": index, "role": own["ar"] if own else role,
                "tone": own["tone"] if own else tone}
        if own and "detail" in own:
            leaf["detail"] = own["detail"]
        if word.get("particle") and len(word["pieces"]) > 1:
            # أَفَلَا: question, extra فَ, negation, each named by what it is.
            leaf["parts"] = [{"role": part["ar"], "tone": part["tone"],
                              **({"detail": part["detail"]} if "detail" in part else {})}
                             for part in (_particle(piece, settings) for piece in word["pieces"])]
        if raw and not opens_clause and not own:
            # Said plainly rather than dressed up: this wording is the treebank's,
            # not the book's, and the page draws it as the weaker claim it is.
            leaf["raw_wording"] = True
            leaf["detail"] = settings["raw_note"]

        if lone := word.get("connector_only"):
            # ثُمَّ joins nothing to anything by governing it, so the treebank
            # gives it no relation. It still has a name, and a blank is worse.
            named = tarkeeb._term(lone)
            leaf.update(role=named["ar"], tone=named["tone"], ghair_aamil=True)
            if "detail" in named:
                leaf["detail"] = named["detail"]
        elif joined := word.get("connector"):
            # The two pieces of فَسَوَّىٰهُنَّ, named separately, so the diagram can
            # peel them apart on request instead of drawing one fused column.
            named = tarkeeb._term(joined["key"])
            piece = {"role": named["ar"], "tone": named["tone"], "ghair_aamil": True}
            if "detail" in named:
                piece["detail"] = named["detail"]
            leaf["prefix_arabic"] = joined["text"]
            leaf["parts"] = [piece, {"role": leaf["role"], "tone": leaf["tone"]}]

        if not children[index]:
            if sentence:
                leaf["label"] = sentence["ar"]
            return leaf

        # The governing word sits among its dependants in written order.
        pieces = sorted([index, *children[index]])
        if len(pieces) == 1:
            # Nothing to join, so no brace: a bracket round one word says nothing.
            if sentence:
                leaf["label"] = sentence["ar"]
            return leaf
        node = {
            "role": role,
            "tone": tone,
            "children": [leaf if piece == index else build(piece) for piece in pieces],
        }
        if sentence:
            node["label"] = sentence["ar"]
        elif name := settings["constituent_labels"].get(word.get("constituent")):
            node["label"] = name
        return node

    if len(roots) == 1:
        return build(roots[0])
    # A sentence can rest on more than one word, two clauses joined by a waw,
    # a vocative before its sentence. Each stands as its own branch rather than
    # being forced under a head the treebank never gave it.
    return {"role": "", "tone": "default",
            "children": [build(root) for root in sorted(roots)]}


# ── The five gates ───────────────────────────────────────────────────────────

def _leaves(node: dict, found: list[int]) -> list[int]:
    if node.get("children"):
        for child in node["children"]:
            _leaves(child, found)
    else:
        found.append(node["word"])
    return found


def gates(words: list[dict], tree: dict, corpus_words: list[str], vocabulary: set[str]) -> str | None:
    """Which gate this ayah fails, or None when it passes all five.

    Contiguity is checked in _tree_of, which returns nothing when it fails; the
    other four are checked here, against the ayah as this app already knows it.
    """
    if sorted(_leaves(tree, [])) != list(range(len(words))):
        return "coverage"

    if unknown := {
        word["relation"]
        for word in words
        if word.get("relation") not in (None, *vocabulary)
    }:
        return "vocabulary"

    written = [word["text"] for word in words if not word["elided"]]
    if len(written) != len(corpus_words):
        return "anchoring"
    # Folded to bare letters: the two sources spell the same word differently
    # (ٱللَّهِ against الله) and are still naming the same word.
    if any(arabic_text.bare_letters(a) != arabic_text.bare_letters(b)
           for a, b in zip(written, corpus_words)):
        return "anchoring"
    return None


# ── Build ────────────────────────────────────────────────────────────────────

def build(treebank: Path, labels: Path) -> None:
    rules = tarkeeb._rules()
    settings = rules["treebank"]

    vocabulary = known_relations(labels) | {settings["root"]}
    ayahs = read_rows(treebank)
    print(f"read {len(ayahs)} ayahs from {treebank.name}")

    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DATABASE)
    # every row is rewritten, so an older layout of the table goes with them
    db.execute("DROP TABLE IF EXISTS tarkeeb")
    db.executescript(SCHEMA)

    kept = 0
    rejected: Counter[str] = Counter()
    for (surah, ayah), sentences in sorted(ayahs.items()):
        corpus_words = [word["arabic"] for word in quran_corpus.tags_for_ayah(surah, ayah)]
        words: list[dict] = []
        branches: list[dict] = []
        failed = None

        for rows in sentences:
            piece, _ = _words_of(rows, settings)
            tree = _tree_of(piece, settings, tarkeeb.relation_tone)
            if tree is None:
                failed = "contiguity"
                break
            # Each sentence's word numbers restart; shift them into the ayah.
            _shift(tree, len(words))
            words += piece
            branches.append(tree)

        if failed is None:
            # An ayah of several sentences is one tree with each as a branch.
            tree = branches[0] if len(branches) == 1 else {
                "role": "", "tone": "default", "children": branches,
            }
            failed = gates(words, tree, corpus_words, vocabulary)

        if failed:
            rejected[failed] += 1
            continue

        written = [i for i, w in enumerate(words) if not w["elided"]]
        db.execute(
            "INSERT INTO tarkeeb (surah, ayah, words, tree, letters, written)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (surah, ayah,
             json.dumps([w["text"] for w in words], ensure_ascii=False),
             json.dumps(tree, ensure_ascii=False),
             tarkeeb_store.letters([words[i]["text"] for i in written]),
             json.dumps(written)),
        )
        kept += 1

    db.commit()
    db.close()

    total = len(ayahs)
    print(f"\nkept {kept} of {total} ayahs ({kept / total:.1%})")
    for gate, count in rejected.most_common():
        print(f"  rejected at {gate:<12} {count:5d} ({count / total:.1%})")
    print(f"\nwrote {DATABASE}")


def _shift(node: dict, by: int) -> None:
    if "word" in node:
        node["word"] += by
    for child in node.get("children", ()):
        _shift(child, by)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("usage: build_tarkeeb.py <Quranic.csv> <RelLabels.csv>")
    build(Path(sys.argv[1]), Path(sys.argv[2]))
