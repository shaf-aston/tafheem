"""Sarf (morphology) analysis endpoint: root, pattern, conjugation table.

Strategy:
  1. Run local morphology (CAMeL / Qalsadi), gives root, part of speech, features.
  2. Look up the word's own dictionary entry for a bab a named source already
     states (verb_forms.babs_of); only when that is silent does the tab fall
     back to rebuilding each Form I past tense from the root and seeing which one the
     reader actually typed. Deterministic, and it is what stops the tab
     conjugating اِسْتَقْبَلَ as if it were قَبَلَ.
  3. Conjugate from the rule tables in data/sarf/patterns.json, always local,
     always the same answer, never dependent on an AI being reachable.
  4. The meaning comes from the local dictionary, the first sense Wiktionary
     lists, falling back to the tagger's gloss. Local either way, so the table
     and its meaning arrive together.
  5. The AI is never waited on here. A network call to an AI backend can take
     seconds, and none of the above needs it; so this route answers from local
     data alone, and /meaning is a second, separate request the frontend fires
     once the table is already on screen.
"""
from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException

from backend.models.schemas import (
    ConjugationRequest,
    ConjugationResponse,
    ConjugationTable,
    MeaningRequest,
    MeaningResponse,
    MorphologyRequest,
    MorphologyResponse,
    Source,
    VerbReading,
    VerbVerdict,
)
from backend.services import ai as ai_service
from backend.services import conjugation, dictionary_service, morphology, provenance, verb_forms
from backend.utils import call_service, normalize_text, require_arabic

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/morphology", tags=["morphology"])

def _table(radicals: str, form: str) -> tuple[ConjugationTable | None, str | None, str | None]:
    """The table for these letters in this باب, or the reason there isn't one.

    Both routes end here, the full analysis once it has worked out the باب, and
    the form switch, which changes nothing else; so the reason a root has no
    table is worded once.
    """
    try:
        return ConjugationTable(**conjugation.conjugate(radicals, form)), None, form
    except ValueError as exc:
        return None, str(exc), None



@router.post("", response_model=MorphologyResponse)
async def analyze_morphology(request: MorphologyRequest) -> MorphologyResponse:
    word = normalize_text(request.word, "Word")
    require_arabic(word, "Word")
    # A form has to be one we actually hold. Rejected here rather than carried
    # down and echoed back inside the "why there is no table" message.
    if request.form and request.form not in conjugation.forms():
        raise HTTPException(422, "Unknown verb form.")

    # ── Step 1: Local morphology ──────────────────────────────────────────────
    tag = await asyncio.to_thread(morphology.analyze_word, word)

    root = tag.get("root") or None
    notes = tag.get("features") or None

    # The dictionary before the tagger. Wiktionary writes the commonest sense
    # first and writes it for a reader; the tagger's gloss is a lexicon label
    # ("understand;comprehend") written for a parser. The Define button beside
    # the meaning is for the reader who wants the whole entry, so what stands in
    # the card should be the first line of the entry that button opens.
    meaning = await asyncio.to_thread(dictionary_service.meaning_of, word)
    meaning_key = "wiktionary" if meaning else "rules"
    if not meaning:
        meaning = morphology.clean_gloss(tag.get("gloss") or "") or None

    # ── Step 2: Which باب, and can this word have a table at all ─────────────
    # The reasoning is the service's; the router only says what the tagger thought
    # the word was and hands the answer on.
    radicals = conjugation.radicals_of(root or word)
    verdict = verb_forms.babs_of(word)
    form, table_note = conjugation.resolve_form(
        word, radicals, tag.get("pos") in morphology.NOUNISH, request.form, verdict["form_key"],
    )

    # ── Step 3: Conjugate from the rule tables ────────────────────────────────
    # Always local and always the same answer, so the table never depends on an
    # AI being reachable. The meaning is fetched separately, by /meaning.
    table: ConjugationTable | None = None
    if form:
        table, note, form = _table(radicals, form)
        table_note = note or table_note

    # The pattern is the chosen form's own template written in the scale letters,
    # so it always agrees with the table beside it. The tagger's own `pattern`
    # field was digits, `ٱِسْتَ1ْ2َ3َ`, and never belonged on screen.
    wazn = conjugation.scale_name(form) if form else None
    # Which family the root belongs to is worked out, not guessed. When the
    # letters are not a root we can judge locally, /meaning's AI call may still
    # supply one, the frontend merges it in once it arrives.
    vclass = conjugation.root_type(radicals) if len(radicals) in {3, 4} else None

    return MorphologyResponse(
        word=word,
        root=root,
        wazn=wazn,
        verb_class=vclass,
        meaning=meaning,
        table=table,
        notes=notes,
        form=form,
        # Only the أبواب this root's letters can take, so switching باب can never
        # land on one that has no table to show.
        form_options=conjugation.forms(len(radicals)),
        table_note=table_note,
        # The table is a rule table and is always the same.
        source=Source(**provenance.of("rules")) if table else None,
        meaning_source=Source(**provenance.of(meaning_key)) if meaning else None,
        verb=VerbVerdict(
            form_key=verdict["form_key"],
            readings=[
                VerbReading(
                    label=reading["label"],
                    sources=[Source(**provenance.of(k)) for k in reading["source_keys"]],
                )
                for reading in verdict["readings"]
            ],
        ),
    )


@router.post("/meaning", response_model=MeaningResponse)
async def analyze_meaning(request: MeaningRequest) -> MeaningResponse:
    """The AI enrichment for a word, asked for on its own.

    A network call to an AI backend can take seconds. The main route above never
    waits on this, the table is already on screen by the time the frontend
    fires this request, so the wait is felt only by the one field that needs it.
    """
    word = normalize_text(request.word, "Word")
    require_arabic(word, "Word")

    if not await asyncio.to_thread(ai_service.is_ai_available):
        return MeaningResponse()

    tag = await asyncio.to_thread(morphology.analyze_word, word)
    tags_str = morphology.tags_as_string([tag])
    # Optional enrichment: a failure here is never worth an error screen over a
    # table the reader already has, so it degrades to "no meaning" instead.
    try:
        ai_result = await call_service(
            ai_service.analyze_sarf,
            word,
            tags_str,
            operation="Sarf AI analysis",
            timeout_msg="AI service timed out.",
        )
    except HTTPException as exc:
        logger.warning("Sarf AI failed for '%s': %s", word, exc.detail)
        return MeaningResponse()

    meaning = ai_result.get("meaning") or None
    return MeaningResponse(
        meaning=meaning,
        meaning_source=Source(**provenance.of("ai")) if meaning else None,
        verb_class=ai_result.get("verb_class"),
    )


@router.post("/conjugate", response_model=ConjugationResponse)
async def conjugate_form(request: ConjugationRequest) -> ConjugationResponse:
    """The same root in a different باب, rule tables only.

    Changing the باب changes the table and the وزن beside it. The root and the
    meaning belong to the word, and the page already has them, so this route
    never wakes the tagger or an AI for them: it is the rule engine and
    nothing else, and it answers in about a millisecond.
    """
    root = normalize_text(request.root, "Root")
    require_arabic(root, "Root")
    if request.form not in conjugation.forms():
        raise HTTPException(422, "Unknown verb form.")

    table, table_note, form = _table(conjugation.radicals_of(root), request.form)
    return ConjugationResponse(
        form=form,
        wazn=conjugation.scale_name(form) if form else None,
        table=table,
        table_note=table_note,
        source=Source(**provenance.of("rules")) if table else None,
    )
