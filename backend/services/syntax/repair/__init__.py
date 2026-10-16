"""The one step that corrects the parser's tokens, in place, before anything reads them.
Each repair is its own module, run in the order below; `naming` and everything after only read.

    book links → typed words → مَنْ that asks → subject clash → verb under يا → praying noun → times counted → second khabar → noun before لا → و هو + verb → ابن between names → particle readings

A split that does not line up with the typed words keeps only the book's links."""
from __future__ import annotations

from backend.services.syntax import particles
from backend.services.syntax.mask import book_links
from backend.services.syntax.naming import base_tokens
from backend.services.syntax.repair.asked import asked_man
from backend.services.syntax.repair.called import called
from backend.services.syntax.repair.dua import counted_times, dua_clause
from backend.services.syntax.repair.hal import hal_clause
from backend.services.syntax.repair.khabar import before_la, second_khabar
from backend.services.syntax.repair.nasab import nasab
from backend.services.syntax.repair.subject_clash import subject_clash
from backend.services.syntax.repair.typed import typed_words


def correct(words: list[str], tokens: list[dict]) -> None:
    book_links(tokens)
    if len(bases := base_tokens(words, tokens)) == len(words):
        typed_words(words, bases, tokens)
        asked_man(bases, tokens)
        subject_clash(tokens)
        called(tokens)
        dua_clause(tokens)
        counted_times(tokens)
        second_khabar(tokens)
        before_la(tokens)
        hal_clause(bases, tokens)
        nasab(bases, tokens)
        particles.stamp(tokens)
