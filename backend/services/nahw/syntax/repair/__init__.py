"""The one step that corrects the parser's tokens, in place, before anything reads them.
Each repair is its own module, run in the order below; `naming` and everything after only read.

    book links → typed words → منذ before a noun → jarr after a مضاف → لام الابتداء → مَنْ that asks → مَنْ before its verb → a noun added to a verb → subject clash → a name told to → a doer said again → كان's raf' khabar → إنّ's nasb object → ظنّ's two objects → praise's تمييز → the doer first where no case shows → doer after the object → verb under its fronted object → object after tanween → object past verb → verb under يا → praying noun → times counted → object of a plain noun → an elative's تمييز → indefinite after a definite opener → noun told of by a jar → second khabar → noun before لا → حصر khabar → described doer → و هو + verb → ابن between names → untied command answering a condition → particle readings → no loop left

A split that does not line up with the typed words keeps only the book's links."""
from __future__ import annotations

from backend.services.nahw.syntax import particles
from backend.services.nahw.syntax.mask import book_links
from backend.services.nahw.syntax.facts import base_tokens
from backend.services.nahw.syntax.repair.answer import untied_command
from backend.services.nahw.syntax.repair.asked import asked_man, man_before_verb
from backend.services.nahw.syntax.repair.called import called
from backend.services.nahw.syntax.repair.dua import counted_times, dua_clause
from backend.services.nahw.syntax.repair.hal import hal_clause
from backend.services.nahw.syntax.repair.khabar import after_pointer, before_la, described_doer, elative_specified, hasr_khabar, object_of_noun, second_khabar, told_of_jar
from backend.services.nahw.syntax.repair.nasab import nasab
from backend.services.nahw.syntax.repair.subject_clash import added_to_verb, name_told_to, repeated_doer, doer_after_object, doer_first, kana_subject, inna_object, object_past_verb, verb_under_fronted_object, object_after_tanween, subject_clash, zanna_pair, praise_specified
from backend.services.nahw.syntax.repair.typed import emphasis_lam_opener, jarr_after_mudaf, since_jarr, typed_words


def correct(words: list[str], tokens: list[dict]) -> None:
    parsed = {t["id"]: (t["head"], t["rel"]) for t in tokens}  # a tree: every word reaches the root (decode)
    book_links(tokens)
    if len(bases := base_tokens(words, tokens)) == len(words):
        typed_words(words, bases, tokens)
        since_jarr(tokens)
        jarr_after_mudaf(tokens)
        emphasis_lam_opener(tokens)
        asked_man(bases, tokens)
        man_before_verb(bases, tokens)
        added_to_verb(tokens)
        subject_clash(tokens)
        name_told_to(tokens)
        repeated_doer(tokens)
        kana_subject(tokens)
        inna_object(tokens)
        zanna_pair(tokens)
        praise_specified(tokens)
        doer_first(tokens)
        doer_after_object(tokens)
        verb_under_fronted_object(tokens)
        object_after_tanween(tokens)
        object_past_verb(tokens)
        called(tokens)
        dua_clause(tokens)
        counted_times(tokens)
        object_of_noun(tokens)
        elative_specified(tokens)
        after_pointer(tokens)
        told_of_jar(tokens)
        second_khabar(tokens)
        before_la(tokens)
        hasr_khabar(tokens)
        described_doer(tokens)
        hal_clause(bases, tokens)
        nasab(bases, tokens)
        untied_command(tokens)
        particles.stamp(tokens)
    untangle(tokens, parsed)


def untangle(tokens: list[dict], parsed: dict[int, tuple[int, str]]) -> None:
    """Each repair moves one link; two of them may close a loop (a word under a word under
    itself), which no sentence has: every word hangs on a word that reaches the root. A word
    left in a loop takes back the parser's own link, or hangs on the root when that loops too."""
    by_id = {t["id"]: t for t in tokens}

    def looped(token: dict) -> bool:
        seen, up = set(), token["head"]
        while up in by_id and up not in seen:
            if up == token["id"]:
                return True
            seen.add(up)
            up = by_id[up]["head"]
        return False

    for token in tokens:
        if looped(token):
            token["head"], token["rel"] = parsed.get(token["id"], (0, token["rel"]))
            if looped(token):
                token["head"] = 0
