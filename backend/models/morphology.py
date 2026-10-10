"""Request and reply types for routers/morphology.py."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.models.common import Source


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
    term: str     # the slot's Arabic name, as a column's `arabic`
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


class VerbReading(BaseModel):
    """One باب a named source states for this verb, and which source(s) said so."""
    label: str
    sources: list[Source] = Field(default_factory=list)


class VerbVerdict(BaseModel):
    """Every باب a dictionary states for this verb, never a guess. Empty
    readings means no source recorded one. See services/verb_forms.py."""
    form_key: str | None = None
    readings: list[VerbReading] = Field(default_factory=list)

    @classmethod
    def of(cls, verdict: dict) -> "VerbVerdict":
        """The card's shape from verb_forms.babs_of's answer, source keys made badges."""
        from backend.services import provenance
        return cls(
            form_key=verdict["form_key"],
            readings=[
                VerbReading(
                    label=r["label"],
                    sources=[Source(**provenance.of(k)) for k in r["source_keys"]],
                )
                for r in verdict["readings"]
            ],
        )
