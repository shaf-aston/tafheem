"""A typed sentence's i'raab, by the book's rules alone (no AI, no network).

1. CAMeL reads each word (morphology).
2. An ayah the Quranic Treebank recorded is read from that record (tarkeeb_store);
   anything else goes to the parser and the book's tree (syntax), which alone name
   each word's job and its case. A word the tree leaves unnamed stays a gap.
3. Each card is built once (cards): what the word is (rule_engine), the tree's name
   on it, then its sign. The summary is the picture's top label, so the cards, the
   line above them and the picture all come from one reading.

The Analyse page and the practice questions both read sentences through here.
"""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics, words
from backend.services import morphology, provenance, quran_corpus, rule_engine, signs, syntax, tarkeeb_store, tree_columns
from backend.services.harakat import CASE_NAME, typed_case
from backend.services.nahw_book import case_of, family_cards, is_object_stem, reason, teacher_rules
from backend.services.syntax import teacher
from backend.services.syntax.tree import names_a_sentence as names_a_sentence
from backend.services.syntax.naming import NAMED, role_key


def analyze(sentence: str, recorded: bool = True) -> dict:
    """{words, summary, source, tree} for one sentence; `tree` is None when nothing joins.
    `recorded=False` skips the treebank and always works the sentence out. The summary is the picture's own top label, so the line above the cards and the
    picture can never name the sentence apart; with no picture, or a phrase (محمد بن عبد الله), there is none."""
    picks = morphology.pick(words(sentence), syntax.disambiguator())  # the one reading, cards and parser alike
    tags = morphology.analyze_sentence(sentence, picks)
    record = tarkeeb_store.for_sentence(sentence) if recorded else None
    parsed = record or syntax.read(sentence, picks)
    tree = _drawn(record) if record else parsed["tree"]
    return {
        "words": cards(tags, parsed["roles"]),
        "summary": label if tree and names_a_sentence(label := tree["tree"].get("label")) else None,
        "source": provenance.of("treebank" if record else "nahw"),
        "tree": tree,
    }


def ayah_tree(surah: int, ayah: int) -> dict:
    """An ayah the treebank has no record of, read as a typed sentence is: one engine,
    one set of rules, so an ayah and the same words typed are named alike."""
    text = dict(quran_corpus.ayah_texts(surah)).get(ayah)
    if not text:
        return {"words": [], "tree": None, "coverage": 0.0}
    drawn = syntax.read(text, morphology.pick(words(text), syntax.disambiguator()))["tree"]
    return drawn or {"words": words(text), "tree": None, "coverage": 0.0}


def _drawn(recorded: dict) -> dict:
    """The recorded tree, in the shape the page draws a typed sentence's in."""
    keep = ("surah", "ayah", "words", "tree", "coverage", "unwritten")
    return {**tree_columns.cut({key: recorded[key] for key in keep}), "source": provenance.of("treebank")}


def cards(tags: list[dict], roles: list[dict]) -> list[dict]:
    """One card per word, built once: what the word is (rule_engine), the job the book's
    tree names on it, then its sign from the final case (signs.settle). A word the tree
    left unnamed keeps the no-role dash; a name the teacher took back shows why."""
    entries = rule_engine.cards(tags)
    if len(roles) == len(entries):
        for entry, found, after in zip(entries, roles, roles[1:] + [{}]):
            if _my_ya(entry, found, after):
                entry["camel"] = {**entry["camel"], "enclitic": "1s_poss"}
            if found.get("gap"):
                entry.update(role=rule_engine.UNNAMED, role_key=None, case=found["case"], sign=None, gap=True,
                             reason=found["gap"]["ar"], notes=found["gap"]["en"])
            elif found["role"]:
                _named(entry, found, after.get("role") == NAMED.mudaf_ilayh)
            elif found["case"] and entry["type"] not in ("fi'l", "harf", "damir", "punc"):
                entry["case"] = found["case"]  # no name yet: the vowel the reader typed, not CAMeL's guess
    words = signs.settle(entries)
    if len(roles) != len(words):
        return words
    for word, found in zip(words, roles):
        if word.get("role") in found.get("pair", {}):  # لا رجلَ: its governor names the pair, after the sign is settled
            word["role"] = found["pair"][word["role"]]
            word["reason"] = reason(word["role"])
    for word in words:  # غير، سوى: the excepted noun is the tool itself, and says so, not إلا's rule
        if teacher.tool_reason(word):
            word["reason"] = teacher.tool_reason(word)
    for word, found in zip(words, roles):
        if found.get("also") and word.get("reason"):
            word["reason"] = f"{word['reason']}، {found['also']}"
    _pieces_said(words, roles)
    return rule_engine.mark_condition(words, roles)


def _pieces_said(cards: list[dict], roles: list[dict]) -> None:
    """A piece written onto the word that its family card says on the word's own card first
    (وَاللهُ: الواو حرف عطف، ويجوز أن تكون استئنافية), where the picture names it short."""
    said = dict(family_cards())
    for card, found in zip(cards, roles):
        for piece in found.get("attached", []):
            line = said.get((piece.get("reading") or {}).get("family"), {}).get("said")
            if line:
                card["reason"] = f"{line}، {card['reason']}"


def _my_ya(entry: dict, found: dict, after: dict) -> bool:
    """لِأَبِي: the parser split off "my" that CAMeL left on the word, so the kasra
    belongs to the ya and the six nouns' letter is no sign here. Not in أَبِي الطَّبِيبِ,
    where a noun in jarr after it can be its مضاف إليه and the ي the six nouns' sign."""
    idafa_next = after.get("role") == NAMED.mudaf_ilayh or (after.get("case") == "jarr" and not after.get("role"))
    return (any(not piece["before"] and piece["form"] == "ي" for piece in found.get("attached", []))
            and entry.get("camel", {}).get("enclitic") in (None, "", "0") and not idafa_next)


def _named(entry: dict, found: dict, annexed: bool) -> None:
    """One card takes the tree's name; the case is naming's (syntax.naming._ending)."""
    renamed = found["role"] != entry.get("role")
    # a recorded ayah names its words vowelled (فِعْلٌ، بَدَلٌ): the rules read the bare name
    plain = strip_diacritics(found["role"])
    if plain != found["role"]:
        if not found["case"] and plain != NAMED.fil and entry.get("type") in ("harf", "fi'l") \
                and not is_object_stem(entry["word"].lstrip("وَفَ")) \
                and (typed := typed_case(entry["word"])):
            found = {**found, "case": CASE_NAME[typed]}  # رَبِّ read by CAMeL as a particle: the kasra typed is its case
    entry.update(role=found["role"], book=found.get("book"), role_key=role_key(plain),
                 family=found.get("family"),  # كان، إنّ: named by what they govern (signs.settle)
                 named=found.get("named"),  # أَلَا: a reading's own name, where the family card's does not fit
                 governor=found.get("governor"), follows=found.get("follows"))
    if plain != NAMED.fil and entry.get("type") == "fi'l":  # نَعْبُدُ keeps CAMeL's tense and mood
        # لَسِحْرًا: CAMeL's verb is the parser's noun, so the verb's case goes with it
        entry.update(type="harf" if plain in (NAMED.harf, NAMED.harf_jarr) else "ism", case=None, aspect=None)
    elif entry.get("type") == "harf" and found["role"] and plain not in (NAMED.harf, NAMED.harf_jarr):
        entry["type"] = "ism"  # أينما: a particle's card named for a place is a built noun
    elif entry.get("type") in ("ism", "zarf") and found["role"] == NAMED.harf and found.get("named"):
        entry["type"] = "harf"  # ما عدا: CAMeL's relative is the particle the reading names
    if not found["case"] and entry.get("case") != "mabni" and (own := case_of(found["role"])):
        found = {**found, "case": CASE_NAME[own]}  # a recorded ayah's name brings its own case
    moved = found["case"] and found["case"] != entry.get("case")
    if found["role"] == NAMED.fil:
        # أَقِمْ: the root made it a command; the parser, seeing only a sukun, says jazm
        if entry.get("case") == "mabni" and found["case"] == "jazm":
            moved = False
        # a word CAMeL took for a noun (ضُرِبَ، كان) or a mood the particle before settled
        # (لن يذهب), or a command CAMeL read as past (فَاتَّبِعْنِي): the card is the verb's own, by naming's tense
        if entry.get("type") != "fi'l" or moved or found.get("aspect") not in (None, entry.get("aspect")):
            aspect = found.get("aspect") or ("i" if found["case"] != "mabni" else None)
            entry.update(type="fi'l", **rule_engine.verb_card(entry["camel"]["base"], aspect, found["case"]))
        return
    if renamed:
        entry["reason"] = reason(found["role"])  # the reason must explain the new name
    if not _stands_for_own(entry, found, annexed) and moved:
        entry["case"] = found["case"]  # signs.settle writes the sign for it
    if entry["case"] == "mabni" and entry.get("type") != "harf":
        entry["reason"] = reason(found["role"], mabni=True)  # الذي، هذا: in the place of a case


def _stands_for_own(entry: dict, found: dict, annexed: bool) -> bool:
    """The typed vowel is the sign of the role's own case for this kind of word (a sound plural's kasra in nasb, a diptote's fatha in jarr): mirrors
    facts.shows_jarr / shows_nasb_by_kasra on the card's reading, so the role's case stands."""
    own = case_of(found["role"])
    typed = next((letter for letter, name in CASE_NAME.items() if name == found["case"]), None)
    stands = teacher_rules()["signs"]["stands_for"].get(signs.kind_of(entry["camel"], annexed), {})
    if own and stands.get(typed) == own:
        entry["case"] = CASE_NAME[own]
        return True
    return False
