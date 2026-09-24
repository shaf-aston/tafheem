"""Tarkeeb, how the words of an ayah assemble into one another.

Tarkeeb is not i'raab. I'raab is the ending on one word; tarkeeb is the bracket
tree: which words join into a unit, what that unit is, and what the unit then
does in the sentence. So the answer here is a nested tree, never a flat list.

The corpus records morphology only. Nothing in it says which word governs which,
so every join below is *derived* by rule, not read off a page. A join the rules
cannot make is not guessed: it comes back as an unresolved node, which the
diagram draws as a visible gap.

A node names what a piece **does** (`role`) or what a unit **is** (`label`). It
has no field for a part of speech, so "it's a noun" cannot be written here.

The joins run smallest-first, and the order matters:

  1. na't: an adjective binds to the noun before it, before that noun can be
               taken as a mudaf, so بسم الله الرحمن reads اسم + (الله الرحمن).
  2. idafa: a bare noun followed by a genitive noun.
  3. jarr: a preposition takes the whole unit after it, idafa included.
  4. sentence, the frames over whatever units are left. A verb, a governing
               word (إِنَّ, كَانَ, كَادَ and their sisters), a pronoun or
               demonstrative after و, a negative or a connective, and a word
               with a resumptive prefix each open a clause that runs to the
               next; no search crosses into another clause. A governing word decides the case of its
               ism and khabar; a clause that opens on a noun is nominal, and
               the verb clause after it may be its khabar.

A word that shows a case is read by it. A word that shows none, typed Arabic
without harakat, takes a role only from the place nahw gives it.

Every Arabic word and every corpus tag comes from data/nahw_rules/tarkeeb.json.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.services import quran_corpus
from backend.services.arabic_text import DIACRITICS_RE

RULES_FILE = Path(__file__).parent.parent / "data" / "nahw_rules" / "tarkeeb.json"


@lru_cache(maxsize=1)
def _rules() -> dict:
    return json.loads(RULES_FILE.read_text(encoding="utf-8"))


def _term(key: str) -> dict:
    """One grammatical term: the Arabic the diagram prints and the colour it uses."""
    term = _rules()["terms"][key]
    out = {"ar": term["ar"], "tone": term["tone"]}
    if "detail" in term:
        out["detail"] = term["detail"]
    return out


def relation_wording(relation: str | None) -> tuple[str, bool]:
    """What to call a treebank relation, and whether any of it is still unchecked wording.

    Three cases, in order: the app has a wording for the whole name; the name is
    "خبر / اسم" plus the word that governs it, so the frame is the app's and the
    governing word is spelled the app's way when it is one a book names; or
    nothing is known, and the treebank's own wording is used and said to be so,
    its wording beats no wording, but it must not read as a finished term.

    The recorded treebank and the rules below both name a governed word through
    this, so اِسْمُ إِنَّ is spelled one way whichever path drew it.
    """
    settings = _rules()["treebank"]
    if not relation:
        return "", False
    if known := settings["relation_terms"].get(relation):
        return known, False

    head, _, rest = relation.partition(" ")
    frame = settings["relation_frames"].get(head)
    if frame and rest:
        governor = settings["governors"].get(rest)
        return f"{frame} {governor or rest}", governor is None
    return relation, True


def relation_tone(relation: str | None) -> str:
    """A relation's colour: the first listed name it contains, else the default."""
    for needle, tone in _rules()["treebank"]["relation_tones"]:
        if relation and needle in relation:
            return tone
    return "default"


def _named(name: str) -> dict:
    """A role's wording, colour and note, from a term key or a treebank relation."""
    if name in _rules()["terms"]:
        term = _term(name)
        out = {"role": term["ar"], "tone": term["tone"]}
        if "detail" in term:
            out["detail"] = term["detail"]
        return out
    wording, raw = relation_wording(name)
    out = {"role": wording, "tone": relation_tone(name)}
    if raw:
        out["detail"] = _rules()["treebank"]["raw_note"]
    return out


# ── What a rule is allowed to know about a word ──────────────────────────────

def _read(word: dict) -> dict:
    """The handful of tag facts the joins consult, and nothing else.

    A word arrives as its segments, a prefix, a stem, an ending. Some facts sit
    on the stem (its case), some on any segment (the definite article is its own
    prefix), so the two are kept apart rather than merged into one bag.
    """
    tag = _rules()["feature"]
    pos = _rules()["pos"]
    governing = _rules()["governing"]
    person = _rules()["person"]
    subject_words = _rules()["subject_words"]
    stem = set(word["features"].split("|")) - {""}
    segments = [(s["pos"], set(s["features"].split("|")) - {""}) for s in word["segments"]]

    def attached(kind: str, marker: str) -> bool:
        return any(marker in tags and tag[kind] in tags for _, tags in segments)

    def person_of(tags: set[str]) -> str | None:
        return next((t for t in tags if re.fullmatch(person["pattern"], t)), None)

    is_verb = word["pos"] == pos["verb"]
    is_noun = word["pos"] == pos["noun"] and not (stem & set(_rules()["not_a_noun"]))
    endings = [person_of(tags) for _, tags in segments
               if tag["suffix"] in tags and tag["pronoun"] in tags]
    own_person = person_of(stem)
    family = next((t.removeprefix(governing["family_tag"]) for t in stem
                   if t.startswith(governing["family_tag"])), None)
    # إِنَّمَا: the attached ما stops إِنَّ governing anything.
    if any(governing["preventive"] in tags for _, tags in segments):
        family = None
    # Named by its dictionary form: كُنتُمْ is still كَانَ.
    bare = DIACRITICS_RE.sub("", word.get("lemma") or word["arabic"])
    mabni = (word["pos"] == pos["noun"] and bool(stem & set(subject_words["mabni"]))
             and bare != subject_words["object_pronoun"])
    return {
        "verb": is_verb,
        "noun": is_noun,
        "proper": tag["proper_noun"] in stem,
        # رَبِّى: the my-ending hides the case, so no tag is taken as showing it.
        "case": None if set(endings) & set(person["implied_case"]) else next(
            (c for c in ("nominative", "accusative", "genitive") if tag[c] in stem), None),
        "adjective": tag["adjective"] in stem,
        "indefinite": tag["indefinite"] in stem,
        # Definite by the article, or by being a name; both block a na't from
        # binding to an indefinite noun, and both stop a word being a mudaf.
        "definite": attached("prefix", tag["definite_article"]) or tag["proper_noun"] in stem,
        # A preposition written as a word of its own (فِي), not glued on (لِ).
        "preposition_word": word["pos"] == pos["particle"] and tag["preposition"] in stem,
        "jarr_prefix": attached("prefix", tag["preposition"]),
        "atf_prefix": attached("prefix", tag["conjunction"]),
        # واو / فاء اِسْتِئْنَافِيَّة, a resumptive that opens a new sentence rather
        # than joining two things. Grammatically distinct from atf, but equally
        # a ghair-عامل: it governs nothing either.
        "rem_prefix": attached("prefix", tag["resumptive"]),
        "pronoun_suffix": attached("suffix", tag["pronoun"]),
        # A connective with no stem of its own, ثُمَّ, أَوْ; is not glued onto
        # anything; the whole word IS the join, unlike فَ in فَسَوَّىٰهُنَّ.
        "atf_word": word["pos"] == pos["particle"] and tag["conjunction"] in stem,
        "rem_word": word["pos"] == pos["particle"] and tag["resumptive"] in stem,
        "atf_text": _connector_text(word, tag["conjunction"]),
        "rem_text": _connector_text(word, tag["resumptive"]),
        # The corpus tags a subject ending and an object ending alike; the first
        # ending is the verb's own subject when it agrees with the verb, ءَامَنُوا.
        # A he or she verb hides its subject, so there it is the object, ضَرَبَهُ.
        "endings": len(endings),
        "subject_ending": (is_verb and own_person is not None
                           and own_person not in person["hidden_subject"]
                           and endings[:1] == [own_person]),
        # Only a he, she or they verb takes a noun as its subject.
        "named_subject": is_verb and (own_person or "").startswith(person["named_subject"]),
        "passive": tag["passive"] in stem,
        # إِذْ, فَوْقَ: a time or place word is never a subject, object or khabar.
        "adverb": tag["time"] in stem or tag["place"] in stem,
        "family": family,
        "negative": governing["negative"] in stem,
        "governor": bare,
        # هُوَ, هَٰذَا, ٱلَّذِى: no case to read, but able to head a sentence.
        "mabni": mabni,
        # وَهُمْ opens a sentence by its own prefix; هُمْ after لَا by its place.
        "subject_pronoun": mabni and bool(stem & set(subject_words["opens_sentence"])),
        "khabar_mabni": mabni and bool(stem & set(subject_words["khabar_mabni"])),
        "sentence_prefix": any(attached("prefix", marker)
                               for marker in subject_words["sentence_prefixes"]),
        # يَٰٓأَيُّهَا ٱلنَّاسُ: a called noun is no one's subject.
        "vocative": attached("prefix", tag["vocative"]),
    }


def _connector_text(word: dict, marker: str) -> str | None:
    """The exact Arabic of a glued prefix carrying `marker`, و or ف, never
    the word it is stuck to, so the diagram can peel the two apart on
    request instead of guessing where one ends and the other begins."""
    tag = _rules()["feature"]
    for segment in word["segments"]:
        tags = set(segment["features"].split("|")) - {""}
        if tag["prefix"] in tags and marker in tags:
            return segment["arabic"]
    return None


# ── Working units ────────────────────────────────────────────────────────────
# A unit is one span of the ayah plus the node that draws it. `head` is the word
# whose case and definiteness stand for the whole unit, the mudaf of an idafa,
# the man'ut of a na't, so a later rule asks one word, not the whole span.

def _leaf(index: int, fact: dict) -> dict:
    """One written word, with the joins that happen inside it already named.

    A prefix and an ending are part of the word, not neighbours of it, so they
    are settled here: لِلَّهِ is jarr + majroor before any word-to-word rule runs.
    """
    node: dict[str, Any] = {"word": index, "role": None, "tone": None}
    # ثُمَّ, أَوْ and the like govern nothing and have no stem of their own for
    # any join to reach, they are named here, once, and skip every join and
    # claim below rather than falling through to an unworked-out gap.
    if fact["atf_word"] or fact["rem_word"]:
        term = _term("harf_atf" if fact["atf_word"] else "harf_istinaf")
        node["role"], node["tone"], node["ghair_aamil"] = term["ar"], term["tone"], True
        if "detail" in term:
            node["detail"] = term["detail"]
        return node
    before, after = [], []
    if fact["atf_prefix"] or fact["rem_prefix"]:
        before.append("harf_atf" if fact["atf_prefix"] else "harf_istinaf")
        node["prefix_arabic"] = fact["atf_text"] if fact["atf_prefix"] else fact["rem_text"]
    if fact["jarr_prefix"]:
        before.append("jarr")
        node["inner"] = "majroor"
    if fact["pronoun_suffix"]:
        if fact["verb"]:
            # كُنتُمْ: a governing verb's own subject is its ism, not a فاعل.
            subject, obj = ((_governed(fact, "ism"), _governed(fact, "khabar"))
                            if fact["family"] else (_subject(fact), "mafool"))
            subjects = [subject] if fact["subject_ending"] else []
            after += subjects + [obj] * (fact["endings"] - len(subjects))
        elif fact["family"]:
            # إِنَّهُمْ: the ism is the governing word's own ending.
            after.append(_governed(fact, "ism"))
        elif fact["preposition_word"]:
            node["inner"] = "jarr"
            after.append("majroor")
        elif fact["noun"]:
            node["inner"] = "mudaf"
            after.append("mudaf_ilayhi")
    if before or after:
        node["before"], node["after"] = before, after
    return node


def _unit(lo: int, hi: int, head: int, node: dict, jarr: bool = False) -> dict:
    return {"lo": lo, "hi": hi, "head": head, "node": node, "jarr": jarr}


def _as(node: dict, name: str) -> None:
    """Give a node the role it plays in whatever now contains it.

    `name` is a term key, or a treebank relation such as اسم إن.
    """
    named = _named(name)
    node["role"] = named["role"]
    if "detail" in named:
        node["detail"] = named["detail"]
    if name == "unresolved":
        node["gap"] = True
    # رَبِّ الْعَالَمِينَ certainly is an idafa; only where it belongs is unknown. A
    # named unit therefore keeps its own colour, and only the open role greys out.
    if not (name == "unresolved" and node.get("label")):
        node["tone"] = named["tone"]


def _governed(fact: dict, slot: str) -> str:
    """The treebank's name for a governed word, اسم إن or خبر كان.

    A governor the treebank table does not list, a conjugated كَانَ, is named
    after its family, as nahw names كَانَ وَأَخَوَاتُهَا.
    """
    governing = _rules()["governing"]
    listed = fact["governor"] in _rules()["treebank"]["governors"]
    word = fact["governor"] if listed else governing["families"][fact["family"]]["word"]
    return f"{governing['frames'][slot]} {word}"


def _same_case(a: dict, b: dict) -> bool:
    """Both show the same case; or, typed without harakat, neither shows one
    and both are nouns, so only place and definiteness can join them."""
    if a["case"] or b["case"]:
        return a["case"] == b["case"]
    return a["noun"] and b["noun"]


def _joined(left: dict, right: dict, label: str, head: int) -> dict:
    """Two units become one, named by what the pair is."""
    term = _term(label)
    return _unit(
        left["lo"], right["hi"], head,
        {"label": term["ar"], "tone": term["tone"], "role": None,
         "children": [left["node"], right["node"]]},
        jarr=left["jarr"],
    )


# ── The joins ────────────────────────────────────────────────────────────────

def _join_naat(units: list[dict], facts: list[dict]) -> list[dict]:
    """An adjective describes the noun before it, and matches it in case and
    definiteness. Without both tests, a khabar (الْكِتَابُ مُفِيدٌ) would be read as
    a description, because it too is an adjective agreeing in case."""
    i = 0
    while i + 1 < len(units):
        noun, adj = facts[units[i]["head"]], facts[units[i + 1]["head"]]
        if (adj["adjective"] and _same_case(adj, noun)
                and adj["definite"] == noun["definite"]):
            _as(units[i + 1]["node"], "naat")
            # الرَّحْمَٰنِ الرَّحِيمِ both describe اللَّهِ, they are its two descriptions,
            # not one description of the other, so a run of them stays flat.
            if units[i]["node"].get("label") == _term("murakkab_tawsifi")["ar"]:
                units[i]["node"]["children"].append(units[i + 1]["node"])
                units[i]["hi"] = units[i + 1]["hi"]
                del units[i + 1]
                continue
            _as(units[i]["node"], "manoot")
            # Not incremented: a second description joins the pair just made.
            units[i:i + 2] = [_joined(units[i], units[i + 1], "murakkab_tawsifi", units[i]["head"])]
        else:
            i += 1
    return units


def _join_idafa(units: list[dict], facts: list[dict]) -> list[dict]:
    """A noun carrying neither the article nor tanween, followed by a genitive
    noun, is annexed to it. A name is not treated as a mudaf: لِلَّهِ رَبِّ has the
    shape of an idafa and is not one, and the corpus records nothing that tells
    the two apart, so it is left for the unresolved node rather than guessed."""
    i = 0
    while i + 1 < len(units):
        first, second = facts[units[i]["head"]], facts[units[i + 1]["head"]]
        if (first["noun"] and not first["proper"] and not first["definite"]
                and not first["indefinite"] and units[i]["lo"] == units[i]["hi"]
                and second["noun"] and second["case"] in ("genitive", None)):
            _as(units[i]["node"], "mudaf")
            _as(units[i + 1]["node"], "mudaf_ilayhi")
            units[i:i + 2] = [_joined(units[i], units[i + 1], "murakkab_idafi", units[i]["head"])]
        else:
            i += 1
    return units


def _join_jarr(units: list[dict], facts: list[dict]) -> list[dict]:
    """A preposition governs the whole unit after it, an idafa included."""
    i = 0
    while i + 1 < len(units):
        particle = facts[units[i]["head"]]
        after = facts[units[i + 1]["head"]]
        if (particle["preposition_word"] and not particle["pronoun_suffix"]
                and units[i]["lo"] == units[i]["hi"]
                and (after["case"] == "genitive"
                     or (after["case"] is None and after["noun"])
                     or units[i + 1]["node"].get("children"))):
            _as(units[i]["node"], "jarr")
            _as(units[i + 1]["node"], "majroor")
            pair = _joined(units[i], units[i + 1], "jar_majroor", units[i + 1]["head"])
            pair["jarr"] = True
            units[i:i + 2] = [pair]
        else:
            i += 1
    # A glued-on preposition governs its own word, and through it whatever that
    # word was annexed to, so the flag is carried by the unit that contains it.
    for unit in units:
        if facts[unit["lo"]]["jarr_prefix"]:
            unit["jarr"] = True
    return units


# ── The sentence over what is left ───────────────────────────────────────────

def _sentence(units: list[dict], facts: list[dict]) -> str:
    """Name each remaining unit's job, and return what the whole sentence is.

    Only the frames are claimed. Where a jar-majroor attaches, to the verb, to a
    noun before it, is not recorded anywhere in the corpus, so it is named for
    what it is and never for what it hangs on.
    """
    taken: set[int] = set()
    # A standalone connective already named itself in _leaf. It governs
    # nothing and is nobody's فاعل or خبر, so it is marked taken before the
    # subject/verb search even starts rather than being offered as a candidate.
    for i, unit in enumerate(units):
        if unit["node"].get("ghair_aamil"):
            taken.add(i)

    def claim(start: int, stop: int, name: str, case: str | None = None,
              jarr: bool = False, verb: bool = False, first_only: bool = False,
              mabni: str | None = None, joined: bool = False,
              unlinked: bool = False) -> int | None:
        # A noun showing the case is taken wherever it stands in the clause; one
        # showing no case only in the first place in line, which is where nahw
        # puts it. A noun joined on by و shares the role of what it joins, so it
        # is passed over unless it opens the clause (`joined`). `mabni` names
        # which caseless words may also be taken: هُوَ, هَٰذَا, ٱلَّذِى. `unlinked`
        # refuses every noun: a khabar clause with nothing pointing back to its
        # mubtada has only a hidden subject.
        if unlinked:
            return None
        first = True
        for i in range(start, stop):
            unit, fact = units[i], facts[units[i]["head"]]
            if i in taken or (case and unit["jarr"]):
                continue
            if case and facts[unit["lo"]]["atf_prefix"] and not joined:
                continue
            if case:
                nominal = fact["noun"] or (mabni and fact[mabni])
                found = (nominal and not fact["adverb"] and not fact["vocative"]
                         and fact["case"] in ((case, None) if first else (case,)))
                first = False
            else:
                found = (jarr and unit["jarr"]) or (verb and fact["verb"])
            if found:
                _as(unit["node"], name)
                taken.add(i)
                return i
            if first_only:
                return None
        return None

    # A verb, a governing word, a standalone pronoun or demonstrative, and a
    # word with a resumptive prefix each open a clause running to the next.
    frames = {i for i, u in enumerate(units) if i not in taken
              and (facts[u["head"]]["family"] or facts[u["head"]]["verb"])}
    opens = {i for i, u in enumerate(units) if i not in taken and not u["jarr"]
             and _opens(units, facts, i)}
    starts = sorted(frames | opens | {0})
    kinds = []
    for n, (at, stop) in enumerate(zip(starts, starts[1:] + [len(units)])):
        following = [stop] if stop in frames else []
        if at in frames:
            kinds.append(_clause(units, facts, at, stop, claim, taken, following))
            continue
        mubtada = claim(at, stop, "mubtada", case="nominative", mabni="mabni", joined=True)
        if mubtada is not None:
            _claim_khabar(claim, mubtada + 1, stop, "khabar", "nominative", following,
                          facts[units[mubtada]["head"]]["mabni"])
            kinds.append("jumlah_ismiyyah")
    summary = kinds[0] if kinds else "unresolved"

    for i, unit in enumerate(units):
        if i in taken:
            continue
        # A jar-majroor is a real, named unit even when its attachment is not.
        _as(unit["node"], "jar_majroor" if unit["jarr"] else "unresolved")
    return summary


def _opens(units: list[dict], facts: list[dict], i: int) -> bool:
    """Whether the unit at `i` starts a sentence of its own."""
    fact, first = facts[units[i]["head"]], facts[units[i]["lo"]]
    if first["sentence_prefix"]:
        return True
    if not fact["subject_pronoun"]:
        return False
    # وَهُمْ, and هُمْ after لَا or ثُمَّ; not أَلَيْسَ هَٰذَا or بَعْدِ ذَٰلِكَ.
    before = facts[units[i - 1]["head"]] if i else None
    return (first["atf_prefix"] or before is None
            or before["negative"] or bool(units[i - 1]["node"].get("ghair_aamil")))


def _subject(fact: dict) -> str:
    """A passive verb's subject is its نائب فاعل."""
    return "naib_fail" if fact["passive"] else "fail"


def _clause(units: list[dict], facts: list[dict], at: int, stop: int,
            claim, taken: set[int], following: list[int]) -> str:
    """One clause: the verb or governing word at `at`, up to `stop`.

    A clause already claimed as the khabar of the one before keeps that role,
    and its own words are still named inside it.
    """
    head = facts[units[at]["head"]]
    # A clause already taken is a khabar, and a khabar clause needs a pronoun
    # pointing back to its mubtada. Where no word carries one, that pronoun is
    # the hidden subject (إِنَّ رَبِّى يَقْذِفُ), so no noun is; where one does, a
    # noun may be (فَأُو۟لَٰٓئِكَ يَتُوبُ ٱللَّهُ عَلَيْهِمْ).
    khabar = at in taken
    unlinked = khabar and not any(
        facts[word]["pronoun_suffix"] for word in range(units[at]["lo"], units[stop - 1]["hi"] + 1))
    if head["family"]:
        return _governed_clause(units, facts, at, stop, head, claim, taken, following,
                                khabar, unlinked)
    if not khabar:
        _as(units[at]["node"], "fil")
        taken.add(at)
    # قُلْ, نَعْبُدُ keep a pronoun for their subject, and ءَامَنُوا carries its own.
    if head["named_subject"] and not head["subject_ending"]:
        claim(at + 1, stop, _subject(head), case="nominative", unlinked=unlinked)
    claim(at + 1, stop, "mafool", case="accusative")
    return "jumlah_filiyyah"


def _governed_clause(units: list[dict], facts: list[dict], at: int, stop: int,
                     head: dict, claim, taken: set[int], following: list[int],
                     khabar: bool, unlinked: bool) -> str:
    """إِنَّ, كَانَ, كَادَ and their sisters: the governing word decides the case
    of its ism and its khabar, so the case is looked for rather than read."""
    spec = _rules()["governing"]["families"][head["family"]]
    if not khabar:
        kind = "verb" if head["verb"] else "negation" if head["negative"] else "particle"
        _as(units[at]["node"], spec[kind])
        taken.add(at)
    # إِنَّهُمْ, كُنتُمْ: the ism is the governing word's own ending; أَكُونُ
    # keeps it as a pronoun.
    if head["verb"]:
        inside = head["subject_ending"] or not head["named_subject"]
    else:
        inside = head["pronoun_suffix"]
    ism_at = None if inside else claim(at + 1, stop, _governed(head, "ism"), case=spec["ism"],
                                       first_only=spec.get("ism_first", False), mabni="mabni",
                                       unlinked=unlinked and bool(head["verb"]))
    ism = inside or ism_at is not None
    name = _governed(head, "khabar")
    # Without its ism, or after a relative ism (إِنَّ الَّذِينَ كَفَرُوا), the verb
    # after it opens a relative clause, not the khabar, so it is not claimed.
    if ism_at is not None and facts[units[ism_at]["head"]]["mabni"]:
        following = []
    if spec["khabar"] == "verb":
        if ism and following:
            claim(following[0], following[0] + 1, name, verb=True)
    else:
        _claim_khabar(claim, at + 1, stop, name, spec["khabar"], following if ism else [],
                      inside or (ism_at is not None and facts[units[ism_at]["head"]]["mabni"]))
    return "jumlah_filiyyah" if head["verb"] else "jumlah_ismiyyah"


def _claim_khabar(claim, start: int, stop: int, name: str, case: str,
                  following: list[int], after_pronoun: bool) -> None:
    """A khabar is a noun in its case or a jar-majroor, in the same clause;
    failing both, the clause that follows: لَفِي خُسْرٍ, إِنَّ اللَّهَ يُحِبُّ.

    A relative is the khabar only after a pronoun (هُوَ ٱلَّذِى); after a noun it
    describes that noun (ٱلْكِتَابُ ٱلَّذِى).
    """
    relative = "khabar_mabni" if after_pronoun else None
    if (claim(start, stop, name, case=case, mabni=relative) is None
            and claim(start, stop, name, jarr=True) is None and following):
        claim(following[0], following[0] + 1, name, verb=True)


# ── Output ───────────────────────────────────────────────────────────────────

# The two keys _leaf can put in a `before` list that are ghair-عامل rather
# than a real government relation, flagged on their own piece so the diagram
# can find the connector inside a compound word without comparing colours.
_GHAIR_AAMIL_KEYS = ("harf_atf", "harf_istinaf")


def _piece(name: str) -> dict:
    """One piece of a compound word's `parts`, from a term key or a relation."""
    piece = _named(name)
    if name in _GHAIR_AAMIL_KEYS:
        piece["ghair_aamil"] = True
    return piece


def _finish(node: dict) -> dict:
    """The working node, cleaned into the shape the diagram reads."""
    if node.get("role") is None and "label" not in node:
        _as(node, "unresolved")
    for child in node.get("children", ()):
        _finish(child)
    before, after = node.pop("before", None), node.pop("after", None)
    inner = node.pop("inner", None)
    if before or after:
        # The stem's job inside its own word is not always its job outside it:
        # in لِلَّهِ the word is the khabar while the stem is only the majroor.
        own = _piece(inner) if inner else {"role": node["role"], "tone": node["tone"]}
        node["parts"] = [_piece(k) for k in before] + [own] + [_piece(k) for k in after]
    return node


def tree_for(words: list[dict]) -> dict:
    """The tarkeeb of one ayah, as a tree the diagram can draw directly.

    `words` are the raw corpus tags of the ayah, from quran_corpus.tags_for_ayah.
    `coverage` is the share of words the rules placed in a named unit, the rest
    are drawn as gaps, and the number is what makes that honest rather than
    invisible.
    """
    if not words:
        return {"words": [], "tree": None, "coverage": 0.0}

    facts = [_read(word) for word in words]
    units = [_unit(i, i, i, _leaf(i, fact)) for i, fact in enumerate(facts)]
    for join in (_join_naat, _join_idafa, _join_jarr):
        units = join(units, facts)

    summary = _sentence(units, facts)
    placed = sum(u["hi"] - u["lo"] + 1 for u in units if not u["node"].get("gap"))
    root = _term(summary)
    tree = {
        "label": root["ar"], "tone": root["tone"],
        "children": [_finish(u["node"]) for u in units],
    }
    # The basmalah joins up completely and still has no frame, no verb, no
    # mubtada. Coverage counts words, so the top brace has to carry that gap
    # itself rather than let a full count imply the sentence was named.
    if summary == "unresolved":
        tree["gap"] = True
    return {
        "words": [word["arabic"] for word in words],
        "tree": tree,
        "coverage": round(placed / len(words), 2),
    }


def for_ayah(surah: int, ayah: int) -> dict:
    """The tarkeeb of one ayah of the Qur'an, straight from the corpus tags.

    Deriving a tree costs well under a millisecond, so there is nothing to cache
    and nothing to precompute, the answer is worked out per request.
    """
    return tree_for(quran_corpus.tags_for_ayah(surah, ayah))
