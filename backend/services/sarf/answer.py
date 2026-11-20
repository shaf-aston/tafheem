"""One word's whole Sarf answer, in the order the steps depend on each other.

The tagger gives the root and part of speech. The dictionary is asked for the
meaning first: Wiktionary writes its commonest sense first, for a reader, where
the tagger's gloss is a parser label. The باب comes from a dictionary that
states it (verb_forms.babs_of) before conjugation.resolve_form rebuilds it from
the letters. The table is then rule-only, so it never waits on an AI; /meaning
is a separate request.
"""
from __future__ import annotations


from backend.models.morphology import (

    ConjugationResponse,

    ConjugationTable,

    MorphologyResponse,

    VerbVerdict,

)
from backend.services.sarf import conjugation
from backend.services.dictionary import service as dictionary_service
from backend.services.sarf import morphology
from backend.services.core import provenance
from backend.services.dictionary import roots
from backend.services.sarf import verb_forms


def table_for(radicals: str, form: str, guessed: bool | None = None) -> ConjugationResponse:
    """The table for these letters in this باب, or the reason there isn't one.

    The full analysis and the form switch both end here, so the reason a root
    has no table is worded once. A hollow root whose weak letter is a guess (`guessed`; asked of the letters alone,
    roots.weak_letter_named, when the caller has no word) takes the letter the باب asked tells (بوع on ضَرَبَ: يَبِيعُ);
    a known letter is kept, and a باب that refuses it says why.
    """
    try:
        guessed = not roots.weak_letter_named(radicals) if guessed is None else guessed
        letters = conjugation.letters_for(radicals, form, guessed)
        table, note = ConjugationTable(**conjugation.conjugate(letters, form)), None
    except ValueError as exc:
        table, note, form = None, str(exc), None
    return ConjugationResponse(
        form=form,
        wazn=conjugation.scale_name(form) if form else None,
        table=table,
        table_note=note,
        source=provenance.of("rules") if table else None,
    )


def analyze(word: str, form: str | None) -> MorphologyResponse:
    """Root, meaning, باب, وزن and table for a word; `form` overrides the باب."""
    tag = morphology.analyze_word(word)
    # The one place every tab asks (the typed vowels choosing: فَفِرُّوا is فرر), then the reading's own; a command's
    # own first, its letters its jussive's less the present letter (قِفْ is وقف, never قفف; verb_reader.command).
    root = (tag.get("aspect") == "c" and tag.get("root")) or roots.root_of(word) or tag.get("root") or None

    meaning = dictionary_service.meaning_of(word)
    meaning_key = "wiktionary" if meaning else "rules"
    if not meaning:
        # the word's own piece of CAMeL's gloss: the whole of وَكَتَبَ's is and+write+he, read as "and"
        meaning = morphology.clean_gloss(tag.get("stemgloss") or tag.get("gloss") or "") or None

    radicals = conjugation.radicals_of(root or word)
    verdict = verb_forms.babs_of(word)
    guessed = not roots.weak_letter_named(radicals, word)
    form, table_note = conjugation.resolve_form(
        word, radicals, tag.get("pos") in morphology.NOUNISH, form, verdict["form_key"], guessed,
    )
    made = table_for(radicals, form, guessed) if form else ConjugationResponse()

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
        form_options=conjugation.forms_for(radicals, either_weak=guessed),
        table_note=made.table_note or table_note,
        source=made.source,
        meaning_source=provenance.of(meaning_key) if meaning else None,
        verb=VerbVerdict.of(verdict),
    )
