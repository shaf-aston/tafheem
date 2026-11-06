"""The one step that corrects the parser's tokens, in place, before anything reads them.
Each repair is its own module; `PASSES` runs them in order (the list, with each one's job, is
docs/glossary/nahw-flow.md, kept equal to it by a test). `naming` and everything after only read.

A split that does not line up with the typed words keeps only the book's links."""
from __future__ import annotations

from backend.services.nahw.syntax import particles
from backend.services.nahw.syntax.mask import book_links
from backend.services.nahw.syntax.facts import Sentence, base_tokens
from backend.services.nahw.syntax.repair.answer import untied_command
from backend.services.nahw.syntax.repair.asked import asked_anna, asked_before_verb, asked_of_kana, asked_man, man_before_verb
from backend.services.nahw.syntax.repair.called import called, called_annexes
from backend.services.nahw.syntax.repair.clause import amma_clause, doer_then_khabar, negated_conjunct, oath_clause
from backend.services.nahw.syntax.repair.dua import counted_times, dua_clause
from backend.services.nahw.syntax.repair.hal import elative_describes, hal_clause, naat_beside_its_noun, no_khabar_on_full_verb
from backend.services.nahw.syntax.repair.khabar import after_pointer, before_la, majrur_of_jar, naat_after_its_noun, la_over_its_khabar, zarf_is_no_subject, khabar_said_first, described_doer, elative_specified, hasr_khabar, object_of_noun, relative_khabar, second_khabar, told_of_jar
from backend.services.nahw.syntax.repair.nasab import nasab
from backend.services.nahw.syntax.repair.number import compound_number
from backend.services.nahw.syntax.repair.subject_clash import added_to_verb, excepted_after_doer, first_object_owed, name_told_to, repeated_doer, doer_after_object, doer_first, late_doer, outer_doer, kana_subject, kana_fronted_khabar, kana_nasb_khabar, inna_object, inna_second_khabar, object_past_verb, relative_owed, verb_under_fronted_object, object_after_tanween, subject_clash, zanna_pair, praise_specified
from backend.services.nahw.syntax.repair.typed import adverb_only, described_after_tanween, described_known, emphasis_lam_opener, jarr_after_mudaf, nunless_mudaf, since_jarr, typed_words


# Each repair and what it reads: the parser's "tokens", the typed words' "bases", "both", the "sentence" (links kept
# in step by `Sentence.relink`), or the "bases_sentence".
PASSES = (
    (typed_words, "both"),
    (adverb_only, "sentence"),
    (compound_number, "bases"),
    (since_jarr, "tokens"),
    (jarr_after_mudaf, "sentence"),
    (nunless_mudaf, "tokens"),
    (emphasis_lam_opener, "tokens"),
    (asked_man, "both"),
    (man_before_verb, "bases_sentence"),
    (asked_anna, "tokens"),
    (asked_before_verb, "sentence"),
    (asked_of_kana, "sentence"),
    (added_to_verb, "sentence"),
    (excepted_after_doer, "sentence"),
    (first_object_owed, "sentence"),
    (subject_clash, "sentence"),
    (described_known, "sentence"),  # after: the object subject_clash moved onto the verb is a noun it describes
    (name_told_to, "sentence"),
    (repeated_doer, "sentence"),
    (kana_subject, "sentence"),
    (kana_fronted_khabar, "sentence"),
    (kana_nasb_khabar, "sentence"),
    (inna_object, "sentence"),
    (inna_second_khabar, "sentence"),
    (zanna_pair, "sentence"),
    (praise_specified, "sentence"),
    (doer_first, "sentence"),
    (doer_after_object, "sentence"),
    (late_doer, "sentence"),
    (outer_doer, "sentence"),
    (verb_under_fronted_object, "sentence"),
    (object_after_tanween, "sentence"),
    (described_after_tanween, "sentence"),
    (object_past_verb, "sentence"),
    (relative_owed, "sentence"),
    (called, "sentence"),
    (called_annexes, "sentence"),
    (dua_clause, "sentence"),
    (counted_times, "sentence"),
    (object_of_noun, "sentence"),
    (elative_specified, "sentence"),
    (after_pointer, "sentence"),
    (relative_khabar, "sentence"),
    (majrur_of_jar, "sentence"),
    (told_of_jar, "sentence"),
    (zarf_is_no_subject, "sentence"),
    (khabar_said_first, "sentence"),
    (second_khabar, "sentence"),
    (naat_after_its_noun, "sentence"),
    (before_la, "sentence"),
    (la_over_its_khabar, "sentence"),
    (hasr_khabar, "sentence"),
    (described_doer, "sentence"),
    (hal_clause, "bases_sentence"),
    (oath_clause, "sentence"),
    (amma_clause, "sentence"),
    (negated_conjunct, "sentence"),
    (doer_then_khabar, "sentence"),
    (no_khabar_on_full_verb, "sentence"),
    (naat_beside_its_noun, "sentence"),
    (elative_describes, "sentence"),
    (nasab, "bases_sentence"),
    (untied_command, "tokens"),
    (particles.stamp, "tokens"),
)


def correct(words: list[str], tokens: list[dict]) -> None:
    parsed = {t["id"]: (t["head"], t["rel"]) for t in tokens}  # a tree: every word reaches the root (decode)
    book_links(tokens)
    if len(bases := base_tokens(words, tokens)) == len(words):
        for word, base in zip(words, bases):
            base["typed"] = word
        s = Sentence(tokens)
        reads = {"tokens": (tokens,), "bases": (bases,), "both": (bases, tokens), "sentence": (s,), "bases_sentence": (bases, s)}
        for repair, kind in PASSES:
            s.refresh()  # a pass may change more than links (a retag): the next reads the tokens as it left them
            repair(*reads[kind])
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
