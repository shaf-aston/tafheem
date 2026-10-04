"""One word's whole Sarf answer, in the order the steps depend on each other.

The tagger gives the root and part of speech. The dictionary is asked for the
meaning first: Wiktionary writes its commonest sense first, for a reader, where
the tagger's gloss is a parser label. The باب comes from a dictionary that
states it (verb_forms.babs_of) before conjugation.resolve_form rebuilds it from
the letters. The table is then rule-only, so it never waits on an AI; /meaning
is a separate request.
"""
from __future__ import annotations

from backend.models.schemas import (
    ConjugationResponse,
    ConjugationTable,
    MorphologyResponse,
    Source,
    VerbVerdict,
)
from backend.services import conjugation, dictionary_service, morphology, provenance, verb_forms


def table_for(radicals: str, form: str) -> ConjugationResponse:
    """The table for these letters in this باب, or the reason there isn't one.

    The full analysis and the form switch both end here, so the reason a root
    has no table is worded once.
    """
    try:
        table, note = ConjugationTable(**conjugation.conjugate(radicals, form)), None
    except ValueError as exc:
        table, note, form = None, str(exc), None
    return ConjugationResponse(
        form=form,
        wazn=conjugation.scale_name(form) if form else None,
        table=table,
        table_note=note,
        source=Source(**provenance.of("rules")) if table else None,
    )


def analyze(word: str, form: str | None) -> MorphologyResponse:
    """Root, meaning, باب, وزن and table for a word; `form` overrides the باب."""
    tag = morphology.analyze_word(word)
    root = tag.get("root") or None

    meaning = dictionary_service.meaning_of(word)
    meaning_key = "wiktionary" if meaning else "rules"
    if not meaning:
        meaning = morphology.clean_gloss(tag.get("gloss") or "") or None

    radicals = conjugation.radicals_of(root or word)
    verdict = verb_forms.babs_of(word)
    form, table_note = conjugation.resolve_form(
        word, radicals, tag.get("pos") in morphology.NOUNISH, form, verdict["form_key"],
    )
    made = table_for(radicals, form) if form else ConjugationResponse()

    return MorphologyResponse(
        word=word,
        root=root,
        wazn=made.wazn,
        # Worked out, not guessed; /meaning's AI may still supply one for letters we cannot judge.
        verb_class=conjugation.root_type(radicals) if len(radicals) in {3, 4} else None,
        meaning=meaning,
        table=made.table,
        notes=tag.get("features") or None,
        form=made.form,
        # Only the أبواب this root's letters can take, so switching باب never lands on an empty one.
        form_options=conjugation.forms(len(radicals)),
        table_note=made.table_note or table_note,
        source=made.source,
        meaning_source=Source(**provenance.of(meaning_key)) if meaning else None,
        verb=VerbVerdict.of(verdict),
    )
