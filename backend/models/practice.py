"""Request and reply types for routers/practice.py."""

from __future__ import annotations

from pydantic import BaseModel, Field

from backend.config import get_settings
from backend.models.common import Source


class PracticeRequest(BaseModel):
    sentence: str = Field(min_length=1, max_length=get_settings().max_sentence_chars)


class PracticeQuestion(BaseModel):
    question: str
    answer: str
    hint: str | None = None


class PracticeResponse(BaseModel):
    sentence: str
    questions: list[PracticeQuestion]
    source: Source | None = None


class CheckedSentence(BaseModel):
    ar: str
    en: str
    words: list[str]  # the learnt words the AI was given


class KeptQuestion(PracticeQuestion):
    """A generated question as it was filed in progress.db."""
    sentence: str
    source: str
    at: str


class KeptQuestions(BaseModel):
    questions: list[KeptQuestion]
