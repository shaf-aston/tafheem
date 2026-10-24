"""The one step that corrects the parser's tokens, in place, before anything reads them.
Each repair is its own module, run in the order below; `naming` and everything after only read.

    book links → typed words → مَنْ that asks → subject clash → كان's raf' khabar → ظنّ's two objects → praise's تمييز → doer after the object → verb under its fronted object → object after tanween → verb under يا → praying noun → times counted → object of a plain noun → indefinite after a definite opener → second khabar → noun before لا → و هو + verb → ابن between names → untied command answering a condition → particle readings

A split that does not line up with the typed words keeps only the book's links."""
from __future__ import annotations

from backend.services.nahw.syntax import particles
from backend.services.nahw.syntax.mask import book_links
from backend.services.nahw.syntax.facts import base_tokens
from backend.services.nahw.syntax.repair.answer import untied_command
from backend.services.nahw.syntax.repair.asked import asked_man
from backend.services.nahw.syntax.repair.called import called
from backend.services.nahw.syntax.repair.dua import counted_times, dua_clause
from backend.services.nahw.syntax.repair.hal import hal_clause
from backend.services.nahw.syntax.repair.khabar import after_pointer, before_la, described_doer, hasr_khabar, object_of_noun, second_khabar
from backend.services.nahw.syntax.repair.nasab import nasab
from backend.services.nahw.syntax.repair.subject_clash import doer_after_object, kana_subject, verb_under_fronted_object, object_after_tanween, subject_clash, zanna_pair, praise_specified
from backend.services.nahw.syntax.repair.typed import since_jarr, typed_words


def correct(words: list[str], tokens: list[dict]) -> None:
    book_links(tokens)
    if len(bases := base_tokens(words, tokens)) == len(words):
        typed_words(words, bases, tokens)
        since_jarr(tokens)
        asked_man(bases, tokens)
        subject_clash(tokens)
        kana_subject(tokens)
        zanna_pair(tokens)
        praise_specified(tokens)
        doer_after_object(tokens)
        verb_under_fronted_object(tokens)
        object_after_tanween(tokens)
        called(tokens)
        dua_clause(tokens)
        counted_times(tokens)
        object_of_noun(tokens)
        after_pointer(tokens)
        second_khabar(tokens)
        before_la(tokens)
        hasr_khabar(tokens)
        described_doer(tokens)
        hal_clause(bases, tokens)
        nasab(bases, tokens)
        untied_command(tokens)
        particles.stamp(tokens)
