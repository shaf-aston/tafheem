"""The one step that corrects the parser's tokens, in place, before anything reads them.
Each repair is its own module; `PASSES` runs them in order (the list, with each one's job, is
docs/glossary/nahw-flow.md, kept equal to it by a test). `naming` and everything after only read.

A split that does not line up with the typed words keeps only the book's links."""
from __future__ import annotations

from backend.services.nahw.syntax import particles
from backend.services.nahw.syntax.mask import book_links
from backend.services.nahw.syntax.facts import Sentence, base_tokens
from backend.services.nahw.syntax.repair.answer import untied_command
from backend.services.nahw.syntax.repair.asked import asked_anna, asked_before_verb, counted_by_min, asked_of_kana, asked_man, man_before_verb
from backend.services.nahw.syntax.repair.called import called, called_annexes
from backend.services.nahw.syntax.repair.clause import amma_clause, doer_then_khabar, negated_conjunct, oath_clause, said_again
from backend.services.nahw.syntax.repair.dua import counted_times, dua_clause
from backend.services.nahw.syntax.repair.hal import elative_describes, hal_clause, naat_beside_its_noun, no_khabar_on_full_verb
from backend.services.nahw.syntax.repair.khabar import after_pointer, jar_off_particle, masdar_khabar, jar_on_its_khabar, before_la, hung_on_pronoun, majrur_of_jar, naat_after_its_noun, known_pair_in_order, naat_not_subject, la_over_its_khabar, zarf_is_no_subject, khabar_said_first, described_doer, elative_specified, hasr_khabar, name_not_told_by_ma, object_of_noun, relative_khabar, khabar_after_silah, second_khabar, sentence_khabar, tawkeed_before_khabar, told_of_jar
from backend.services.nahw.syntax.repair.nasab import nasab
from backend.services.nahw.syntax.repair.number import compound_number
from backend.services.nahw.syntax.repair.subject_clash import added_to_verb, pronoun_on_its_verb, excepted_after_doer, first_object_owed, name_told_to, repeated_doer, doer_after_object, doer_first, late_doer, outer_doer, kana_subject, kafa_doer, kana_fronted_khabar, kana_nasb_khabar, inna_object, inna_second_khabar, object_past_verb, relative_owed, verb_under_fronted_object, object_after_tanween, subject_clash, zanna_pair, praise_specified
from backend.services.nahw.syntax.repair.typed import adverb_only, described_after_tanween, described_known, emphasis_lam_opener, jarr_after_mudaf, number_after_one, nunless_mudaf, since_jarr, typed_words


# Each repair takes the one Sentence: its tokens, the typed words (`s.bases`) and the lookups, kept in step as it moves
# links (`Sentence.relink`, `Sentence.relabel`).
PASSES = (
    typed_words,
    adverb_only,
    compound_number,
    since_jarr,
    jarr_after_mudaf,
    number_after_one,
    nunless_mudaf,
    emphasis_lam_opener,
    asked_man,
    man_before_verb,
    asked_anna,
    counted_by_min,  # first: the verb it puts back on كم is the one asked_before_verb places
    asked_before_verb,
    asked_of_kana,
    pronoun_on_its_verb,
    added_to_verb,
    excepted_after_doer,
    first_object_owed,
    subject_clash,
    described_known,  # after: the object subject_clash moved onto the verb is a noun it describes
    name_told_to,
    repeated_doer,
    kana_subject,
    kafa_doer,
    kana_fronted_khabar,
    kana_nasb_khabar,
    inna_object,
    inna_second_khabar,
    zanna_pair,
    praise_specified,
    doer_first,
    doer_after_object,
    late_doer,
    outer_doer,
    verb_under_fronted_object,
    object_after_tanween,
    described_after_tanween,
    object_past_verb,
    relative_owed,
    called,
    called_annexes,
    dua_clause,
    counted_times,
    object_of_noun,
    elative_specified,
    after_pointer,
    relative_khabar,
    khabar_after_silah,
    name_not_told_by_ma,
    majrur_of_jar,
    hung_on_pronoun,
    told_of_jar,
    zarf_is_no_subject,
    khabar_said_first,
    second_khabar,
    known_pair_in_order,
    naat_after_its_noun,
    naat_not_subject,
    before_la,
    la_over_its_khabar,
    jar_off_particle,
    masdar_khabar,
    jar_on_its_khabar,
    tawkeed_before_khabar,
    sentence_khabar,
    hasr_khabar,
    described_doer,
    hal_clause,
    oath_clause,
    amma_clause,
    negated_conjunct,
    said_again,
    doer_then_khabar,
    no_khabar_on_full_verb,
    naat_beside_its_noun,
    elative_describes,
    nasab,
    untied_command,
    particles.stamp,
    particles.emphasis_lam_frees_its_word,
    particles.hasr_frees_its_words,
    particles.negation_settles_its_words,
    particles.wonder_settles_its_words,
    particles.asks_settles_its_words,
    particles.idhan_settles_its_words,
)


def correct(words: list[str], tokens: list[dict]) -> None:
    parsed = {t["id"]: (t["head"], t["rel"]) for t in tokens}  # a tree: every word reaches the root (decode)
    book_links(tokens)
    s = Sentence(tokens)
    untangle(s, parsed)
    if len(bases := base_tokens(words, tokens)) == len(words):
        for word, base in zip(words, bases):
            base["typed"] = word
        s.bases = bases
        for repair in PASSES:
            s.refresh()  # a pass may change more than links (a retag): the next reads the tokens as it left them
            repair(s)
            untangle(s, parsed)  # the next pass walks up the links, and a walk round a loop never ends


def untangle(s: Sentence, parsed: dict[int, tuple[int, str]]) -> None:
    """Each repair moves one link; two of them may close a loop (a word under a word under
    itself), which no sentence has: every word hangs on a word that reaches the root. A word
    left in a loop takes back the parser's own link, or hangs on the root when that loops too.
    Runs after every repair, so none reads a loop (وهو الله لا إله إلا هو froze in excepted_from)."""
    tokens = s.tokens
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
            s.relink(token, *parsed.get(token["id"], (0, token["rel"])))
            if looped(token):
                s.relink(token, 0, token["rel"])
