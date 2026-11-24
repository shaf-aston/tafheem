"""A word's case, decided in one place: what each typed word ends on.

    resolve()    every word's case: its own ending, then a condition's jazm, then what followers take
    mood()       a present verb's case, its governor first
    idle_card()  the card of a governor some Arabs leave idle (أن، لم)

naming asks `resolve` once; `signs` only prints what it decided.
"""
from __future__ import annotations

from collections.abc import Sequence

from backend.services.nahw.book import (
    book_merges, book_spelling, case_of, family_cards, is_mabni, is_one, named_roles, unseen_case)
from backend.services.nahw.syntax import condition, facts
from backend.services.nahw.syntax.followers import take_their_ending
from backend.services.text.harakat import (
    CASE_NAME, KASRA, SUKUN, build_nun, doubled_last, five_verb_nun, letters, merged_nun, paused)

NAMED = named_roles()


def resolve(named: list, bases: list[dict], tokens: list[dict], s: facts.Sentence, words: list[str],
            moods: list, before: list, after: list) -> tuple[list, list[dict]]:
    """Each word's case and the conditions found: a condition is read from the cases (which verbs show jazm),
    then puts its own verbs in jazm, then followers take the case of what they follow."""
    cases = [_ending(role, token, _governor(bases, i), words[i + 1] if i + 1 < len(words) else "",
                     facts.puts_in_jarr(token, s), moods[i], before[i])
             for i, (role, token) in enumerate(zip(named, bases))]
    conditions = condition.find(bases, named, cases, before, after)
    for c in conditions:
        _jazm_by_condition(c, named, cases)
    take_their_ending(named, cases, bases, tokens)
    return cases, conditions


def _jazm_by_condition(c: dict, named: list, cases: list) -> None:
    """إن تدرس تنجح typed bare: a جازم opener puts both its verbs in jazm (يجزم فعلين), so a present
    verb showing no ending of its own is in jazm, not the raf' a verb nothing governs is in."""
    for part in ("verb", "answer"):
        if c["frame"]["case"] and c[part] is not None and named[c[part]] == NAMED.fil and cases[c[part]] is None:
            cases[c[part]] = "jazm"


def _governor(bases: list[dict], i: int) -> dict | None:
    """The word before word i that may govern it. A لا straight after a nasb particle is
    the plain negation, which governs nothing: أَنْ لَا تَطُوفِي، لِكَيْ لَا يَعْلَمَ are
    in nasb by the particle before it, not in jazm by a لا of prohibition; so too a و لا after its verb."""
    before = bases[i - 1] if i else None
    if not (before and i > 1 and is_one(before["base"], "negation")):
        return before
    if is_one(bases[i - 2]["base"], "nasb_mudari", "before_a_present_verb"):
        return bases[i - 2]
    return facts.stressed_nasb(bases, i) or before  # لَنْ يَرُدَّ وَلَا يَمُدَّ


def _ending(role: str | None, token: dict, before: dict | None, after: str, jarred: bool,
            lam: str | None = None, front: Sequence[str] = ()) -> str | None:
    """What to print under the word: a case for a noun or a present verb, else mabni.
    A noun's case is the vowel typed on it, else its role's own. A kasra on ـات is nasb when
    its role takes nasb, or it has no role and nothing puts it in jarr, shown by the kasra (رأيت المعلماتِ)."""
    if role == NAMED.fil:
        return "mabni" if is_mabni("verb", token.get("asp", "na"), token["base"]) or build_nun(token["typed"], token.get("stuck_on", 0), token.get("lemma", "")) else mood(paused(token["typed"], after), token, before, lam, front)
    if role in (NAMED.harf, NAMED.harf_jarr):
        return "mabni"
    if role == NAMED.munada and facts.my_ya_dropped(token):
        return "nasb"  # يَا قَوْمِ: مضاف to the ياء المتكلم gone, its kasra no case
    # يَا وَلَدُ، يا أيها: a single called noun is built on the damma (in the place of nasb), as is اللهمّ
    if role == NAMED.munada and (facts.typed_case_of(token) == "u" or facts.is_called_noun(token)
                                 or facts.is_called_alone(token)):
        return "mabni"
    # a question word, a demonstrative, a relative or a pronoun never changes its
    # ending, so the vowel on it is part of the word and not a case
    if facts.is_built(token) or facts.is_object_pronoun(token) or facts.is_built_zarf(token):
        return "mabni"
    # وَإِذْ قَالَ: a noun's case never ends on a sukun but at a pause, so one typed mid-sentence is built;
    # a name is never built, so a sukun on one is the reader pausing (أَحْمَدْ جَاءَ). A sukun on a last و or ي
    # is that letter's own (اثْنَيْ عَشَرَ، كِتَابَيْ الطَّالِبِ: the dual's ya), the letter the case shows by, no build
    marked = letters(token["typed"])
    if (after and not token.get("stuck_on") and marked and SUKUN in marked[-1][1] and marked[-1][0] not in "وي"
            and token.get("pos_camel") != "noun_prop"):
        return "mabni"
    if facts.shows_nasb_by_kasra(token) and (case_of(role, token["mudaf"]) == "a" if role else not jarred):
        return "nasb"
    if facts.shows_jarr(token) and (case_of(role, token["mudaf"]) == "i" if role else jarred):
        return "jarr"  # إِلَى إِبْرَاهِيمَ: a diptote's fatha is its jarr
    return CASE_NAME.get(facts.typed_case_of(token) or case_of(role or "", token["mudaf"]) or unseen_case(role))


def idle_card(word: str) -> dict | None:
    """The card of a governor some Arabs leave idle (closed_words.json card `idle_as`: أن، لم), by its book spelling."""
    return next((card for family, card in family_cards() if word in card.get("idle_as", {}) and is_one(word, family)), None)


def mood(typed: str, token: dict, before: dict | None, lam: str | None = None, front: Sequence[str] = ()) -> str | None:
    """A present verb's case, the governor first (the book's عامل), in this order:
    the five verbs keeping their nun, raf'; a particle that settles it by itself (لم يكتب، لن يذهب), or one of the shapes
    only jazm or nasb leaves, a weak last letter gone (لم يَدْعُ، لا تَنْسَ) or the five verbs' nun gone, after a jazm or nasb
    particle (لا تَسُبُّوا); that nun gone, or a doubled verb's fatha, with a ف written onto the verb: فاء السببية, nasb by a
    hidden أن (وَلَا تَنَازَعُوا فَتَفْشَلُوا; Ibn Aqil on the Alfiyya, وبعد فا جواب نفي أو طلب, vol 4 p11-12). The text is
    trusted there: the nun goes after such a ف only in the answer of a request or a negation, so no check looks for one;
    the other reading, a ف joining the verb to a jussive (لَمْ يَذْهَبُوا فَيَنْدَمُوا), is a second tarkeeb, not given. Then the ending
    the reader typed, on the verb's own last letter (يُفَقِّهْهُ), a doubled verb's fatha by what stands before it, else the
    mood of a لام written onto it (facts.lam_mood), else None: nothing shows, and the verb it is joined to decides, else raf'.
    `typed` is the word as paused on (harakat.paused); `before` the base token before it."""
    particle, stuck_on = before["base"] if before else "", token.get("stuck_on", 0)
    nun = five_verb_nun(typed, stuck_on, token.get("weak_last"))
    nasbs = is_one(particle, "nasb_mudari", "before_a_present_verb")
    # لَمْ تُكَلِّمُونِّي: before ني the five verbs' kept nun may merge into the pronoun's (harakat.merged_nun), a nun no
    # governor took; a root's own ن there is a hollow verb's, one doer's (يَخُونِّي: خَانَ), so none of the five verbs
    nun = "kept" if merged_nun(typed, stuck_on) else nun
    # the five verbs keep their nun only in raf' (يَكْتُبُونَ، تَكْتُبِينَ), so a kept one leaves the particle before it no work: a
    # jazm particle some leave idle (لَمْ يُوفُونَ بِالْجَارِ, Ibn Aqil; page unchecked) or one that never governs a verb so (لا
    # النافية), and after a ف the verb is a noun clause's khabar, the answer (إِنْ تَجْتَهِدُوا فَتَنْجَحُونَ). A nasb particle is left
    # idle only by those who leave أن so (card `idle_as`; أَنْ تَقْرَآنِ، Ibn Aqil; page unchecked; or it is أنّ lightened: _idle),
    # and only where the nun cannot be the root's own: a nun with a fatha may end a root (يَخُونَ: خَانَ, one doer, in nasb), and
    # the analyser may take such a root for a weak one's plural (وَخَى), so a root ending ن، و or ي leaves the nun in doubt;
    # the pair's nun alone takes a kasra. No one leaves لن idle: لَنْ يَكْتُبَانِ stays nasb, the nun a slip
    marked = letters(typed)[: len(letters(typed)) - stuck_on]
    pair_nun = bool(marked) and marked[-1][0] == "ن" and KASRA in marked[-1][1]
    nun_may_be_roots = (token.get("root") or "")[-1:] in ("ن", "و", "ي")
    if facts.five_verbs(token) and nun == "kept" and (not nasbs or idle_card(book_spelling(particle)) is not None and (
            pair_nun or not nun_may_be_roots)):
        return "raf'"
    dropped_nun = nun == "dropped"
    read, named = facts.reading(before), facts.reading(before, "named")  # أَلَّا: the nasb أنْ with a لا merged in
    for family, case in (("jazm", "jazm"), ("nasb_mudari", "nasb")):
        if is_one(particle, family, "before_a_present_verb") or (dropped_nun and is_one(particle, family)) \
                or (read == family and named in {m["named"] for m in book_merges(family).values()}):
            return case
    # لَمْ يَرُدَّ: a doubled verb's jussive takes the fatha its nasb does (harakat.doubled_last), so that fatha shows neither
    # the nun of emphasis on one of the five verbs is neither (facts.five_emphasised): no فاء السببية's nasb takes it
    emphasised = facts.five_emphasised(typed, token)
    doubled = doubled_last(typed, stuck_on, fatha=True) and not emphasised
    if (dropped_nun or doubled) and front and front[-1] == "ف" and not emphasised:
        return "nasb"
    typed_mood = facts.typed_mood(typed, token)
    if typed_mood == "jazm":
        return "jazm"
    if lam and doubled_last(typed, stuck_on):
        return lam  # the لام says which, whatever vowel the doubled letter wears (لِيَمُدَّ يَدَهُ، لِيَرُدَّنِي، لِيَرُدُّ)
    if doubled:
        if is_one(particle, "jazm"):
            return "jazm"  # a لا: no negation puts a verb in nasb, so لَا تَمُدَّ يَدَكَ is its prohibition
        if front or is_one(particle, "atf"):
            return None  # joined on (وَيَرُدَّ، ثُمَّ يَرُدَّ): the verb it is joined to decides (followers)
        # straight after a verb or a noun, with no hidden أن before it, the fatha is its jussive's: the answer of a condition or a
        # request (إِنْ تَدْرُسُوا يُحِبَّكُمُ الْمُعَلِّمُ، ازْهَدْ فِي الدُّنْيَا يُحِبَّكَ اللَّهُ); after another particle, its nasb's (إِذَنْ أُحِبَّكَ)
        return "nasb" if is_one(particle, "nasb_mudari") or read == "nasb_mudari" else "jazm"  # إِذًا: إذن (particles.stamp)
    return typed_mood or lam  # None: nothing shows (followers.take_their_ending)
