"""Names each word's i'raab role from the links the parser drew.

The parser says which word hangs off which and how (subject, object, idafa
and so on), but it says it in CATiB's short tags and it never sees the harakat,
because it is fed the letters alone. This module turns those links into the
words a nahw book uses. Two things decide a name: the link, and the vowels the
reader typed, which are the only evidence for case and for a passive verb.

Nothing here reaches the network or a model. Given the same tokens it always
answers the same, which is why the roles it writes may be shown as derived.

Scored by `backend/scripts/score_iraab.py`; the numbers are quoted once, in this
package's `__init__.py`.
"""
from __future__ import annotations

from backend.services import verb_reader
from backend.services.arabic_text import bare_letters, strip_diacritics
from backend.services.nahw_book import book_path, case_of, family_cards, in_family, is_mabni, is_one, named_roles, role_table
from backend.services.syntax import facts, walker
from backend.services.harakat import (
    CASE_NAME, PRESENT_PREFIX, SUKUN, drops_weak, five_verb_nun, letters, own_letters, paused, typed_case)

# Every role this module can name, with its card colour key and bracket tone
# (data/nahw_rules/roles.json); a role missing there is left uncoloured.
ROLES = role_table()
NAMED = named_roles()


def _entry(role: str | None) -> tuple:
    # a recorded role is fully vowelled (نَائِبُ فَاعِلٍ); it is the same role
    return ROLES.get(strip_diacritics(role or ""), (None, None))


def role_key(role: str | None) -> str | None:
    """The stable name the word grid colours a card by."""
    return _entry(role)[0]


def roles_keyed(*keys: str) -> tuple[str, ...]:
    """Every role the card colours by one of these keys (`fail` is فاعل and نائب فاعل)."""
    return tuple(role for role in ROLES if role_key(role) in keys)


FOLLOWERS = roles_keyed("tabi", "sifah")


def tone(role: str | None) -> str | None:
    """The colour the bracket diagram draws this role in."""
    return _entry(role)[1]


def base_tokens(words: list[str], tokens: list[dict]) -> list[dict]:
    """The parser's tokens that are the words the reader typed, clitics aside.
    Fewer or more than `words` means the split does not line up."""
    bases = [t for t in tokens if t.get("token_type") == "baseword"]
    if len(bases) != len(words):
        # a reader who writes بِ or وَ apart types as many words as the parser splits
        bases = [t for t in tokens if not t["form"].startswith("+")]
    return bases


def roles(words: list[str], tokens: list[dict]) -> list[dict]:
    """One {role, case, aspect, book} per typed word, in the order they were typed;
    `book` is the proof line, the tree's branches that named it.

    The parser splits بِ and ـه off as their own tokens; the words a reader types
    are the base words, so only those are named and the vowels are carried over.
    The case is decided here, once: the vowel the reader typed, else the case the
    role itself takes (رأيتُ أخي shows none, yet a مفعول به is منصوب).
    """
    bases = base_tokens(words, tokens)
    if len(bases) != len(words):
        return [{"role": None, "case": None} for _ in words]  # the split does not line up
    for i, (word, token) in enumerate(zip(words, bases)):
        token["typed"] = word
        # letters at the end that belong to an attached pronoun, not to the word
        token["stuck_on"] = sum(len(bare_letters(t["form"].strip("+"))) for t in tokens
                                if t["head"] == token["id"] and t["form"].startswith("+"))
        # اُكْتُبْ، أَكْرِمْ: the typed command is the tense, whatever reading the parser had;
        # a verb's reading (فَاقْبَلْهَا) is also tried on its own letters, the ف and ها aside;
        # a noun's never is, or the يَدِ of وَيَدِهِ would be a command
        after = words[i + 1] if i + 1 < len(words) else ""
        verb = token["pos"].startswith("VRB")
        if verb or token.get("pos_camel") in ("noun", "noun_prop"):
            governed = i > 0 and any(is_one(bases[i - 1]["base"], family, "before_a_present_verb")
                                     for family in ("jazm", "nasb_mudari"))
            root = token.get("root", "")
            joined = max(0, len(letters(word)) - token["stuck_on"] - len(token["base"]))
            own = own_letters(word, joined, token["stuck_on"]) if verb else word
            cell = next((found for form in dict.fromkeys((word, paused(word, after), own))
                         if (found := verb_reader.command(form, governed, root))), None)
            if cell:
                # the person is sarf's: the reading may have taken اقبل for "I accept"
                token.update(asp="c", per=cell.person, gen=cell.gender, num=cell.number)
        token["mudaf"] = any(t["head"] == token["id"] and t["rel"] == "IDF" for t in tokens)
    found_answers, governed_by = facts.of_sentence(tokens)
    answers = {t["id"]: a for t, a in zip(tokens, found_answers)}
    # the book's tree has no leaf for some answers: that word stays unnamed
    walked = [walker.walk(answers[token["id"]]) for token in bases]
    named = [found.role if found else None for found in walked]
    # بِـ، ـها: an attached piece is named by the same tree as a typed word
    base_ids = {token["id"] for token in bases}
    attached = {t["id"]: found.role if (found := walker.walk(answers[t["id"]])) else None
                for t in tokens if t["id"] not in base_ids}
    role_by_id = {token["id"]: role for token, role in zip(bases, named)} | attached
    # a particle with a مجرور under it is a حرف جر: the one name, for card and picture
    for t in tokens:
        if t["pos"] == "PRT" and any(role_by_id.get(kid["id"]) == NAMED.majroor
                                     for kid in tokens if kid["head"] == t["id"]):
            role_by_id[t["id"]] = NAMED.harf_jarr
    named = [role_by_id[token["id"]] for token in bases]
    cases = [_ending(role, token, bases[i - 1] if i else None, words[i + 1] if i + 1 < len(words) else "")
             for i, (role, token) in enumerate(zip(named, bases))]
    _followers_take_their_case(named, cases, bases, tokens)
    # what each word shows: the governor and follower the tree gave it, and its case
    shown = [{answers[token["id"]]["governor"], answers[token["id"]]["follows"], case}
             for token, case in zip(bases, cases)]
    # a piece written onto a تابع joins it, it does not govern it: وَإِيمَانٌ shows عطف first
    joined = [{answers[token["id"]]["follows"]} if answers[token["id"]]["follows"] else said
              for token, said in zip(bases, shown)]
    word_of = _typed_word_of(bases, tokens)
    # the parser's tense goes with a فعل, so a card CAMeL took for a noun (ضُرِبَ) still says ماضٍ
    return [{"role": role, "case": case,
             "aspect": token.get("asp") if role == NAMED.fil else None,
             "family": _family(token, bases, shown) if role in (NAMED.fil, NAMED.harf, NAMED.harf_jarr) else None,
             "book": book_path(found.path, found.book) if found else None,
             "attached": [{"id": t["id"], "role": role_by_id[t["id"]], "before": t["form"].endswith("+"), "form": t["form"].strip("+"),
                           "family": _family(t, bases, joined, below=True) if role_by_id[t["id"]] in (NAMED.harf, NAMED.harf_jarr) else None}
                          for t in tokens if t["id"] in attached and word_of.get(t["id"]) == i],
             **_governed(i, role, token, bases, tokens, governed_by, word_of)}
            for i, (role, case, token, found) in enumerate(zip(named, cases, bases, walked))]


def _typed_word_of(bases: list[dict], tokens: list[dict]) -> dict[int, int]:
    """Token id -> the typed word it sits in: a clitic (بِـ، ـه) belongs to the base word
    it is written onto, a proclitic to the one after it, an enclitic to the one before."""
    base_ids = {t["id"]: i for i, t in enumerate(bases)}
    at, word, pending = {}, 0, []
    for t in tokens:
        if t["id"] in base_ids:
            word = base_ids[t["id"]]
            at.update(dict.fromkeys(pending, word))
            pending = []
        elif t["form"].endswith("+"):
            pending.append(t["id"])
            continue
        at[t["id"]] = word
    at.update(dict.fromkeys(pending, word))
    return at


def _governed(i: int, role: str | None, token: dict, bases: list[dict], tokens: list[dict],
              governed_by: dict[int, int], word_of: dict[int, int]) -> dict:
    """The typed word this one takes its case from: `follows` for a تابع (the word it copies),
    else `governor` (its عامل); each only when it is another typed word."""
    if role in FOLLOWERS and (head := _followed(token, bases, tokens)) is not None:
        return {"follows": head} if head != i else {}
    governor = word_of.get(governed_by.get(token["id"]))
    return {"governor": governor} if governor is not None and governor != i else {}


def _followed(token: dict, bases: list[dict], tokens: list[dict]) -> int | None:
    """The typed word a follower follows, reached through the و of a معطوف."""
    at = {t["id"]: i for i, t in enumerate(bases)}
    by_id = {t["id"]: t for t in tokens}
    head = by_id.get(token["head"])
    while head and (head["id"] not in at or head["pos"] == "PRT"):
        head = by_id.get(head["head"])
    return at[head["id"]] if head else None


def _followers_take_their_case(named: list, cases: list, bases: list[dict], tokens: list[dict]) -> None:
    """A صفة، معطوف، توكيد or بدل with no vowel typed wears the case of the word it
    follows (اليدُ العليا); in order, so a chain follows too."""
    for i, (role, token) in enumerate(zip(named, bases)):
        if cases[i] is not None or role not in FOLLOWERS:
            continue
        head = _followed(token, bases, tokens)
        if head is not None and cases[head] != "mabni":
            cases[i] = cases[head]


def _family(token: dict, bases: list[dict], shown: list[set], below: bool = False) -> str | None:
    """The family a particle or verb is named by (كان فعل ماضٍ ناقص، إنّ حرف مشبه بالفعل):
    one whose list holds it and whose effect shows on a word linked to it, the noun hung
    on إنّ or كان, or the verb لم hangs on. A listed word that governs nothing here (the
    لا of a plain negation) keeps its plain name. A piece written onto a word (وَ، بِـ)
    works only on the word `below` it: the وَ of وَإِيمَانٌ hangs on a مجرور's neighbour."""
    linked = set().union(*(said for other, said in zip(bases, shown)
                           if other["head"] == token["id"] or (not below and other["id"] == token["head"])))
    return next((family for family, card in family_cards()
                 if card["governs"] in linked and in_family(token["lemma"], family)), None)


def opens_with_verb(roles: list[str | None]) -> bool:
    """Verbal unless a مبتدأ (or the اسم of إنّ) comes before the first verb. A particle,
    a fronted adverb or a fronted object leaves it verbal (لم يكتب، متى سافر، القرآنَ قرأ):
    the book judges a sentence by the word it rests on, not the one put first."""
    for role in roles:
        if role == NAMED.fil:
            return True
        if role in (NAMED.mubtada, NAMED.ism_inna, NAMED.khabar):
            return False
    return False


def _ending(role: str | None, token: dict, before: dict | None, after: str) -> str | None:
    """What to print under the word: a case for a noun or a present verb, else mabni.
    A noun's case is the vowel typed on it, else its role's own."""
    if role == NAMED.fil:
        present = token["base"][:1] in PRESENT_PREFIX and token.get("asp") == "i"
        return _mood(paused(token["typed"], after), token, before) if present else "mabni"
    if role in (NAMED.harf, NAMED.harf_jarr):
        return "mabni"
    # يَا وَلَدُ، يا أيها: a single called noun is built on the damma (in the place of nasb)
    if role == NAMED.munada and (typed_case(token["typed"]) == "u" or facts.is_called_noun(token)):
        return "mabni"
    # a question word, a demonstrative, a relative or a pronoun never changes its
    # ending, so the vowel on it is part of the word and not a case
    if is_mabni(token):
        return "mabni"
    return CASE_NAME.get(facts.typed_case_of(token) or case_of(role or "", token["mudaf"]))


def _mood(typed: str, token: dict, before: dict | None) -> str:
    """A present verb's case, the governor first (the book's عامل): a particle that
    settles it by itself (لم يكتب، لن يذهب), or one of the shapes only jazm or nasb
    leaves, a weak last letter gone (لم يَدْعُ، لا تَنْسَ) or the five verbs' nun gone
    with a jazm or nasb particle before (لا تَسُبُّوا). Then the ending the reader typed,
    on the verb's own last letter (يُفَقِّهْهُ), else raf'. `typed` is the word as paused
    on (harakat.paused); `before` is the base token before it, its joined letters off."""
    particle = before["base"] if before else ""
    dropped_nun = five_verb_nun(typed) == "dropped"
    for family, case in (("jazm", "jazm"), ("nasb_mudari", "nasb")):
        if is_one(particle, family, "before_a_present_verb") or (dropped_nun and is_one(particle, family)):
            return case
    if drops_weak(token["base"], token.get("weak_last")):
        return "jazm"
    stuck_on = token.get("stuck_on", 0)
    own = letters(typed)[:len(letters(typed)) - stuck_on]
    if own and SUKUN in own[-1][1]:
        return "jazm"
    shown = typed_case(typed, stuck_on)
    return CASE_NAME[shown] if shown in ("u", "a") else "raf'"
