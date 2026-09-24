"""Which باب a verb takes, read from named dictionaries, never guessed.

`conjugation.identify()` cannot tell the six Form I babs apart, they all spell
the same past tense once vowels are off. Two books state it directly: Lane's
Lexicon and Wiktionary's ar-verb head template (parsed by `parse_head` below,
read through `verb_sources.SOURCES`). `babs_of()` is the one entry point: it
tries every source in babs.json's order and keeps every one that answers, so
a reading can cite both books when both name the same bab; a word neither
book records gets no reading at all, and the tab says so rather than falling
back to a guess. No I/O of its own: babs.json comes via conjugation.babs(),
sources come via verb_sources.SOURCES.

`record()` is the other half: the one place a build script turns a raw
(form, past, babs) triple into the shape this module and the dictionary
files agree on, so a script cannot write a form or bab code this module
would then have to guard against at read time.
"""
from __future__ import annotations

import logging
import re

from backend.services import conjugation, verb_sources

logger = logging.getLogger(__name__)

# Wiktionary spells the quadriliteral tail "q" (Iq), babs.json's form_keys "Q" (IQ).
_FORM_RE = re.compile(r"^[IVX]+q?$", re.IGNORECASE)


def parse_head(arg: str) -> tuple[str, list[str]] | None:
    """Read Wiktionary's ar-verb first template arg into (form, babs).

    Only the part before the first "." matters, everything after is a tag like
    .pass or .vn:... that this app does not use yet. Returns None for anything
    that does not start with a bare roman-numeral form, which means the
    template was not what this parser expects.
    """
    head = arg.split(".", 1)[0]
    form_part, _, vowel_part = head.partition("/")

    if not _FORM_RE.match(form_part):
        return None

    form = conjugation.babs()["form_keys"].get(form_part, form_part.upper())

    if not vowel_part:
        return form, []

    past_part, _, present_part = vowel_part.partition("~")
    if not present_part or "/" in present_part:
        # A second "/" here means an alternate-reading head (e.g. "a~a/u~u"),
        # not the form/vowel split this parser expects; reject rather than
        # fold the extra bit into the present-vowel list.
        return None

    pasts = past_part.split(",")
    presents = present_part.split(",")
    babs = [f"{p}~{q}" for p in pasts for q in presents]
    return form, babs


def record(form: str, past: str, babs: list[str]) -> dict | None:
    """One verb entry for a build script to write, or None if it is not one.

    Runs the same form_keys mapping parse_head applies to Wiktionary's own
    head template (Iq/IIq -> IQ/IIQ), so a script can hand this either a raw
    Wiktionary form or one already mapped; None when what is left is not a
    roman-numeral form at all. babs are kept only where babs.json's "babs"
    table names the code, same filter `babs_of()` applies at read time; a
    Form I that had babs stated but loses every one of them to that filter is
    not a verb entry worth recording, since a Form I nobody can cite a bab
    for tells a reader nothing a bare root does not already.
    """
    mapped = conjugation.babs()["form_keys"].get(form, form.upper())
    if not _FORM_RE.match(mapped):
        return None
    known = conjugation.babs()["babs"]
    kept = [code for code in babs if code in known]
    if mapped == "I" and babs and not kept:
        return None
    return {"form": mapped, "past": past, "babs": kept}


def babs_of(word: str, sources: dict | None = None) -> dict:
    """Every source's reading of this word's باب, merged into one verdict.

    `sources` defaults to `verb_sources.SOURCES`, read here rather than bound
    as a default argument, so a test can monkeypatch that public dict and see
    it without reloading this module. No early stop: a word both books
    record should show both, not whichever was tried first.
    """
    sources = verb_sources.SOURCES if sources is None else sources
    found = []
    for key in conjugation.babs()["sources"]:
        provider = sources.get(key)
        if provider is None:
            logger.debug("No provider wired for verb source '%s'", key)
            continue
        if verbs := provider(word):
            found.append((_pick(verbs, word), key))
    return _verdict(found)


def _pick(verbs: list[dict], word: str) -> list[dict]:
    """Every one of this source's verb forms that matches the word typed.

    Tries the full diacritized spelling first (only the joining-alif variant
    folded, same as bare() does): if any entry matches exactly, only exact
    matches come back, so a fully-vowelled بَخَعَ never also shows بَخِعَ's
    bab. Falls back to bare()-only matching for a reader who typed no vowels
    at all, which can return more than one entry, a root Lane states two
    pasts for (حَبَلَ a~u and حَبِلَ i~a) typed bare shows both babs. bare()
    matching is also what tells كتب (I) and كتّب (II) apart on the shaddah
    bare() keeps.
    """
    spelled = word.replace("ٱ", "ا").strip()
    if exact := [
        v for v in verbs if v["past"].replace("ٱ", "ا").strip() == spelled
    ]:
        return exact

    typed = conjugation.bare(word)
    return [v for v in verbs if conjugation.bare(v["past"]) == typed]


def _verdict(found: list[tuple[list[dict], str]]) -> dict:
    """Turn every source's picked verb forms into what the tab shows.

    One reading per distinct (past, bab): a Form I label names the bab's own
    pair of past and present ("كَتَبَ · باب نَصَرَ يَنْصُرُ"); every other
    form names itself ("كَتَّبَ · Form II") from patterns.json when it has a
    table, else just the roman numeral. Two sources naming the identical
    label merge into one reading citing both, in babs.json's source order
    (the order `found` already carries); naming different babs for the same
    word keeps them as separate readings, so the reader sees the disagreement
    rather than one book winning silently.

    form_key is the first reading's own form: a Form I bab's form_key, or the
    form code itself when conjugation.forms() holds a table for it, so the
    table conjugates whichever reading is shown first. A form with no table
    (Form IX, mudaaf) still gets a label but no form_key.

    A bab code babs.json does not name is skipped, same as the parser has
    always done. No verb at all, from any source, gives {"form_key": None,
    "readings": []}, the never-guess surface the tab reads as "not recorded".
    """
    rules = conjugation.babs()
    known_forms = conjugation.forms()
    order: list[str] = []
    by_label: dict[str, dict] = {}

    for verbs, key in found:
        for verb in verbs:
            form = verb["form"]
            past = verb["past"]
            if form == "I":
                entries = [rules["babs"][c] for c in verb.get("babs") or [] if c in rules["babs"]]
                candidates = [(f"{past} · باب {e['arabic']}", e["form_key"]) for e in entries]
            else:
                name = known_forms.get(form)
                label = f"{past} · {name}" if name else f"{past} · Form {form}"
                candidates = [(label, form if form in known_forms else None)]

            for label, form_key in candidates:
                entry = by_label.setdefault(label, {"form_key": form_key, "source_keys": []})
                if label not in order:
                    order.append(label)
                if key not in entry["source_keys"]:
                    entry["source_keys"].append(key)

    readings = [{"label": label, "source_keys": by_label[label]["source_keys"]} for label in order]
    form_key = by_label[order[0]]["form_key"] if order else None
    return {"form_key": form_key, "readings": readings}
