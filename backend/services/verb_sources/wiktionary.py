"""Wiktionary as a verb-form source, its ar-verb head templates.

Contract every source in this package keeps (README.md here): every verb
form filed under the typed word's letters, or [] when none is recorded.
"""
from __future__ import annotations

from backend.services import dictionary_service


def verb_forms_of(word: str) -> list[dict]:
    return dictionary_service.verb_forms_of(word)
