"""Registry of every source verb_forms.babs_of() can ask which باب a verb takes.

See README.md in this folder for the contract every adapter here keeps, and
the steps to add one.
"""
from __future__ import annotations

from backend.services.verb_sources import lane, wiktionary

SOURCES = {
    "lane": lane.verb_forms_of,
    "wiktionary": wiktionary.verb_forms_of,
}
