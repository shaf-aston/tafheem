"""The one reading of a small word with several (لا، إلا، ألا، إذا), decided once per sentence.

A word on more than one list (لا is a joining word, the لا of genus, a negation and a
prohibition) used to be read by whichever list a caller asked first, so the card, the
picture and the case rules could each read it apart. Here the book's tests decide it
once (data/nahw_rules/particle_tree.json, walked like the naming tree) and the answer is
stamped on the token as `reading`; facts, naming, the picture and the card all read that.
Pure: tokens in, readings stamped.
"""
from __future__ import annotations

from functools import lru_cache
from typing import Callable

from backend.services.arabic_text import strip_diacritics
from backend.services.harakat import (
    PRESENT_PREFIX, SHADDA, SUKUN, fits_shape, five_verb_nun, has_tanween, letters, own_letters, stilled, typed_case)
from backend.services.morphology import has_comparative
from backend.services.nahw_book import book_file, book_map, book_words, frames, is_mabni, is_one
from backend.services.syntax import facts, walker


def _attached(token: dict) -> bool:
    return token["form"].startswith("+")


def _next(token: dict, s: facts.Sentence) -> dict | None:
    """The word after it, past a pronoun written onto it."""
    return next((t for t in s.tokens if t["id"] > token["id"] and not _attached(t)), None)


def _lemma(token: dict) -> str:
    """The word's lemma, spelled as the reader typed it: إِذًا (a tanween) is the spelling of
    إذن, which the time word إذا never takes (data: nasb_mudari `tanween_spells`)."""
    lemma = strip_diacritics(token["lemma"]).strip("+")
    spelled = book_map("nasb_mudari", "tanween_spells").get(lemma)
    return spelled if spelled and has_tanween(token.get("typed") or "") else lemma


def _word(token: dict, s: facts.Sentence) -> str:
    lemma = _lemma(token)
    return lemma if lemma in _words() else "other"


def _what_follows(token: dict, s: facts.Sentence) -> str:
    """A verb in jazm (its last letter stilled or the nun of the five verbs gone), any other
    verb, an indefinite noun (no ال, no name, no pronoun on it: رجلَ، عدوى), a definite one,
    a particle, or nothing."""
    after = _next(token, s)
    if after is None:
        return "none"
    typed = after.get("typed") or ""
    if facts.is_verb(after):
        stuck_on, weak = after.get("stuck_on", 0), after.get("weak_last")
        return "verb_jazm" if stilled(typed, after["base"], stuck_on, weak) or five_verb_nun(typed, stuck_on, weak) == "dropped" else "verb"
    if after["pos"] == "PRT":
        return "particle"
    bare = strip_diacritics(typed or after["form"])
    pronoun = any(t["head"] == after["id"] and _attached(t) for t in s.tokens)
    # a name is definite unless CAMeL itself read it indefinite (ضِرَارَ of لا ضرارَ, tagged a name)
    named = after["pos"] == "PROP" and after.get("stt") != "i"
    definite = bare.startswith("ال") or named or after.get("stt") == "d" or pronoun
    return "noun" if definite else "indefinite_noun"


def _negated(token: dict, s: facts.Sentence) -> str:
    return "yes" if s.negated_before(token) else "no"


def _joins(token: dict, s: facts.Sentence) -> str:
    """The noun after it wears the case of the noun before it: جاء زيدٌ لا عمرٌو, ما جاء
    الطلابُ إلا زيدٌ. Nothing to share a case with (ما جاء إلا زيدٌ) or a case apart
    (لا إلهَ إلا اللهُ) says no."""
    before, after = facts.previous_noun(token, s), _next(token, s)
    if not (before and after and after["pos"] in ("NOM", "PROP")):
        return "no"
    behind = s.by_id.get(before["id"] - 1)
    if behind and behind["pos"] == "PRT" and is_one(behind["lemma"], "negation") and not facts.read_as(behind, "la_jins"):
        return "no"  # ما أنت إلا بشر: the noun after the negation is the مبتدأ, what follows إلا its khabar
    mine = facts.typed_or_parsed_case(after)
    return "yes" if mine and mine == facts.place_case(before, s) else "no"


def _tool_next(token: dict, s: facts.Sentence) -> str:
    """The word after it is خلا, عدا or حاشا (ما عدا زيدًا): the ما that turns them into a masdar."""
    after = _next(token, s)
    return "yes" if after and is_one(strip_diacritics(after["form"]), "istithna_verbs") else "no"


def _raf(token: dict, s: facts.Sentence) -> str:
    """The noun after it is typed in raf' (damma or tanween with damma): the noun of لا of the
    genus is never raf', so this لا is a plain negation and the noun is a مبتدأ."""
    after = _next(token, s)
    return "yes" if after and facts.typed_case_of(after) == "u" else "no"


def _told(token: dict, s: facts.Sentence) -> str:
    """What stands straight after the noun that follows: a noun (its khabar) or anything else."""
    noun = _next(token, s)
    told = _next(noun, s) if noun else None
    return "noun" if told and told["pos"] in ("NOM", "PROP") and not facts.is_verb(told) else "other"


def _opens(token: dict, s: facts.Sentence) -> str:
    """The noun after it opens a sentence of its own: a definite noun in raf' with an
    indefinite one in raf' after it that does not describe it, its khabar (واللهُ أكبرُ)."""
    noun = _next(token, s)
    told = _next(noun, s) if noun else None
    if not (noun and told and noun["pos"] in ("NOM", "PROP") and told["pos"] in ("NOM", "PROP")) or facts.is_verb(told):
        return "no"
    definite = noun.get("stt") == "d" or noun["pos"] == "PROP"
    return "yes" if definite and facts.typed_or_parsed_case(noun) == "u" \
        and facts.typed_or_parsed_case(told) == "u" and told.get("stt") != "d" else "no"


def _pronoun_of(verb: dict, s: facts.Sentence) -> dict | None:
    """The pronoun written onto the verb (أدراك، أجملها)."""
    return next((t for t in s.tokens if t["id"] == verb["id"] + 1 and _attached(t)), None)


def _asked_after(token: dict, s: facts.Sentence) -> bool:
    """A question word stands straight after it (data: istifham `words`); a preposition does not
    count (مِنْ لَيْلَةٍ)."""
    after = _next(token, s)
    return bool(after) and not facts.is_preposition(after) and is_one(strip_diacritics(after["form"]), "istifham")


def _after_object(noun: dict, s: facts.Sentence) -> dict | None:
    """The indefinite noun in nasb straight after an object."""
    more = _next(noun, s)
    return more if more and more["pos"] in ("NOM", "PROP") and more.get("stt") == "i" and not facts.is_verb(more) \
        and facts.typed_or_parsed_case(more) == "a" else None


def _wonder_parts(token: dict, s: facts.Sentence) -> tuple[dict, dict] | None:
    """ما أجمل السماء: (the verb, its object) when ما is followed by a verb of the wonder shape
    (data: wonder `shapes`, read from the letters) and a noun that is not raf', or a pronoun on the
    verb (ما أجملها), its one object that closes the clause (Tasheel 1.4.2 p8). A typed case is held to
    nasb; plain text only has the analyser's, so a noun it reads raf' (ما أكرم زيدٌ) makes the verb an
    ordinary one. A second indefinite nasb noun (ما أعطى الرجل كتابًا) is no wonder, nor is a question
    word after the pronoun (ما أدراك ما يوم الدين: that clause is its second object), nor a verb whose
    root gives no comparative أفعل (ما أنزل الله: a negation), the wonder being built only where the
    comparative is."""
    verb = _next(token, s)
    pronoun = _pronoun_of(verb, s) if verb else None
    noun = pronoun or (_next(verb, s) if verb else None)
    if not (verb and noun and verb["pos"] != "PRT" and noun["pos"] in ("NOM", "PROP") and not facts.is_verb(noun)):
        return None
    if pronoun:
        if _asked_after(pronoun, s):
            return None
    else:
        typed = facts.typed_case_of(noun)
        case = facts.typed_or_parsed_case(noun)
        if case == "u" or (typed == "i" and not facts.shows_nasb_by_kasra(noun)):
            return None
    own = own_letters(verb.get("typed") or "", 0, verb.get("stuck_on", 0))  # the pronoun's letters are not the shape's
    if not any(fits_shape(own, shape, verb.get("root") or "") for shape in book_words("wonder", "shapes")) \
            or not has_comparative(verb["form"]):
        return None
    # after a noun object a second indefinite nasb noun is no wonder (ما أعطى الرجل كتابًا); after a
    # pronoun it is a second object only of a verb that takes two (ما أعطاها كتابًا), else the
    # tamyeez (ما أجملها ليلةً)
    lemma = strip_diacritics(verb["lemma"])
    second = _after_object(noun, s) and (not pronoun or is_one(lemma, "two_objects_give") or is_one(lemma, "zanna"))
    return None if second else (verb, noun)


def _wonder(token: dict, s: facts.Sentence) -> str:
    return "yes" if _wonder_parts(token, s) else "no"


def _informing(token: dict, s: facts.Sentence) -> dict | None:
    """وما أدراك ما يوم الدين: the verb after it when it is a verb of informing with its first
    object written on it and a question word after that, the clause which is its second object."""
    verb = _next(token, s)
    pronoun = _pronoun_of(verb, s) if verb else None
    lemma = strip_diacritics(verb["lemma"]) if verb else ""
    return verb if pronoun and (is_one(lemma, "two_objects_give") or is_one(lemma, "zanna")) \
        and _asked_after(pronoun, s) else None


def _asks_nominal(token: dict, s: facts.Sentence) -> bool:
    """ما اسمك، من أنت: a noun, pronoun or pointer in raf' (its مبتدأ; a ظرف is one only if typed so:
    ما يومُ الدين) and nothing else of a clause: no verb after it, no preposition or restricting إلا
    (ما أنت بعالمٍ, ما أنت إلا بشر), no khabar of its own for the noun (ما زيدٌ قائمٌ), not ما الحجازية."""
    after = _next(token, s)
    if token["pos"] == "PRT" or s.hijazi or not after or after["pos"] not in ("NOM", "PROP") or facts.is_verb(after) \
            or (facts.is_zarf(after, s) and facts.typed_case_of(after) != "u") \
            or not (is_mabni(after) or facts.typed_case_of(after) in (None, "u")):
        return False
    later = [t for t in s.tokens if t["id"] > token["id"] and not _attached(t)]
    return not any(facts.is_verb(t) or facts.is_preposition(t) or (t["pos"] == "PRT" and is_one(t["lemma"], "hasr"))
                   for t in later) and _opens(token, s) == "no"


def _asks(token: dict, s: facts.Sentence) -> str:
    return "yes" if _informing(token, s) or _asks_nominal(token, s) else "no"


def _opens_clause(token: dict, s: facts.Sentence) -> bool:
    """Nothing before it asks for it: a verb straight before takes it as its object (قرأتُ ما كتبَ),
    and so does a preposition (لا يعلمُ ما في الغيبِ), unless the verb is one of saying, whose quoted
    speech it opens (قالوا ما أنتم إلا بشرٌ; data: roles.json said_clause)."""
    before = next((t for t in reversed(s.tokens) if t["id"] < token["id"] and not _attached(t)), None)
    saying = frames()["said_clause"]["verbs"]
    return not (before and (facts.is_preposition(before)
                            or (facts.is_verb(before) and strip_diacritics(before["lemma"]) not in saying)))


def _restricted(token: dict, s: facts.Sentence) -> str:
    """The ما opens its clause and an إلا of restriction comes later in it: the ما is the negation."""
    return "yes" if _opens_clause(token, s) and any(
        t["id"] > token["id"] and not _attached(t) and is_one(t["lemma"], "hasr") for t in s.tokens) else "no"


def _starts(token: dict, s: facts.Sentence) -> str:
    """It opens its clause: nothing before it, or a و or ف written onto it (data: nasb_mudari
    `idhan_after`), as in فَإِذًا after the sentence it answers; زيدٌ إذن يَنجحُ is not."""
    before = next((t for t in reversed(s.tokens) if t["id"] < token["id"]), None)
    return "yes" if before is None or (
        _attached_before(before) and before["form"].strip("+") in book_words("nasb_mudari", "idhan_after")) else "no"


def _attached_before(token: dict) -> bool:
    """A letter written onto the word after it (ف+, و+)."""
    return token["form"].endswith("+")


def _verb_after(token: dict, s: facts.Sentence) -> dict | None:
    """The verb that follows it directly, a negating لا or an oath (و and the noun sworn by)
    allowed between (data: nasb_mudari `idhan_between`, `idhan_oath`)."""
    rest = [t for t in s.tokens if t["id"] > token["id"] and not _attached(t)]
    at = 0
    while at < len(rest):
        word = rest[at]
        if facts.is_verb(word):
            return word
        if is_one(word["lemma"], "nasb_mudari", "idhan_between") and word["pos"] == "PRT":
            at += 1
        elif is_one(word["lemma"], "nasb_mudari", "idhan_oath") and at + 1 < len(rest) \
                and facts.typed_case_of(rest[at + 1]) == "i":
            at += 2
        else:
            return None
    return None


def _is_present(verb: dict) -> bool:
    """A present verb by the parser, or by its shape when the parser took it for a past one
    (أُكْرِمَكَ): a present prefix with a damma, or followed by a letter at rest (أَذْهَبَ)."""
    if verb.get("asp") == "i":
        return True
    marked = letters(verb.get("typed") or "")
    return verb["base"][:1] in PRESENT_PREFIX and len(marked) > 2 and (
        "ُ" in marked[0][1] or SUKUN in marked[1][1])


def _shows(token: dict, s: facts.Sentence) -> str:
    """The mood the present verb after it shows: nasb (a fatha, or the nun of the five verbs
    dropped), raf' (a damma, or the nun kept), else other; none where no such verb follows."""
    verb = _verb_after(token, s)
    if verb is None or not _is_present(verb):
        return "none"
    nun = five_verb_nun(verb.get("typed") or "", verb.get("stuck_on", 0), verb.get("weak_last"))
    shown = typed_case(verb.get("typed") or "", verb.get("stuck_on", 0))
    return "nasb" if nun == "dropped" or shown == "a" else "raf" if nun == "kept" or shown == "u" else "other"


AXES: dict[str, tuple[tuple[str, ...], Callable[[dict, facts.Sentence], str]]] = {
    "next": (("verb_jazm", "verb", "indefinite_noun", "noun", "particle", "none"), _what_follows),
    "negated": (("yes", "no"), _negated),
    "joins": (("yes", "no"), _joins),
    "opens": (("yes", "no"), _opens),
    "raf": (("yes", "no"), _raf),
    "tool_next": (("yes", "no"), _tool_next),
    "told": (("noun", "other"), _told),
    "wonder": (("yes", "no"), _wonder),
    "asks": (("yes", "no"), _asks),
    "restricted": (("yes", "no"), _restricted),
    "starts": (("yes", "no"), _starts),
    "shows": (("nasb", "raf", "other", "none"), _shows),
}


@lru_cache(maxsize=1)
def _tree() -> dict:
    tree = book_file("particle_tree.json")["tree"]
    words = tuple(child["is"] for child in tree["children"]) + ("other",)
    walker.validate(tree, {"word": (words, _word), **AXES}, book_file("closed_words.json")["families"])
    return tree


@lru_cache(maxsize=1)
def _words() -> frozenset[str]:
    return frozenset(child["is"] for child in _tree()["children"])


@lru_cache(maxsize=None)
def _judged(word: str) -> frozenset[str]:
    """The families the tree decides for this word: every role at a leaf of its branch."""
    def roles(node: dict) -> set[str]:
        return {node["role"]} if "role" in node else set().union(*map(roles, node.get("children", [])))
    return frozenset(roles(next(c for c in _tree()["children"] if c["is"] == word)))


def _merged(tokens: list[dict], s: facts.Sentence) -> None:
    """أَلَّا (shadda on the lam) is أنْ with its nun merged into لا (data: nasb_mudari `merges`):
    the word is the nasb particle, and the لا the parser split off it a plain negation.
    Only before a present verb (أنّ + لا before a noun is not this)."""
    for word, merged in book_map("nasb_mudari", "merges").items():
        for token, tail in zip(tokens, tokens[1:]):
            if strip_diacritics(token["lemma"]) == word and SHADDA in (token.get("typed") or "") and _attached(tail) \
                    and (after := _next(tail, s)) and facts.is_verb(after) and after.get("asp") == "i":
                token["reading"] = {"family": "nasb_mudari", "named": merged["named"], "kind": "harf", "book": None}
                tail["reading"] = {"family": merged["tail"], "named": None, "kind": "harf", "book": None}


def _hasr_frees_its_words(tokens: list[dict]) -> None:
    """لا تعبدوا إلا الله: the إلا of restriction excepts nothing, so the word the parser hung on
    it belongs to the verb above it, as in ما ضربتُ إلا زيدًا (Tasheel 3.8.7 p85)."""
    by_id = {t["id"]: t for t in tokens}
    for particle in tokens:
        verb = by_id.get(particle["head"])
        if (particle.get("reading") or {}).get("family") == "hasr" and verb and facts.is_verb(verb):
            for kid in tokens:
                if kid["head"] == particle["id"]:
                    kid["head"] = verb["id"]


def _wonder_settles_its_words(tokens: list[dict]) -> None:
    """ما أجمل السماء: a ما read as the wonder ما is the مبتدأ, the verb after it a built past verb
    (its hidden doer goes back to ما) and its clause the khabar, the noun its object. The parser
    tags and hangs these differently from one sentence to the next, so they are written over."""
    s = facts.Sentence(tokens)
    for ma in tokens:
        if (ma.get("reading") or {}).get("family") != "wonder" or not (parts := _wonder_parts(ma, s)):
            continue
        verb, noun = parts
        ma.update(pos="NOM", pos_camel="pron_rel")
        verb.update(pos="VRB", pos_camel="verb", asp="p", vox="a", per="3", gen="m", num="s",
                    reading={"family": "wonder", "named": None, "kind": "fil", "book": ma["reading"]["book"]})
        three = {ma["id"], verb["id"], noun["id"]}
        outer = next((t for t in (verb, ma, noun) if t["head"] not in three), None)
        ma["head"], ma["rel"] = (outer["head"], outer["rel"]) if outer else (0, "---")
        verb["head"], verb["rel"] = ma["id"], "---"
        noun["head"], noun["rel"] = verb["id"], "OBJ"
        if specified := _after_object(noun, s):
            specified["head"], specified["rel"] = verb["id"], "TMZ"  # ما أجملها ليلةً


def _asks_settles_its_words(tokens: list[dict]) -> None:
    """ما اسمك، وما أدراك: a ما or من read as the question word is a built noun. With a clause
    of its own after it (the verb of informing) it is that verb's مبتدأ; otherwise it is the
    khabar brought to the front and the noun after it its مبتدأ, hung on it. Standing after a verb,
    its clause is that verb's (قال ما اسمك). The parser tags and hangs these differently from one
    sentence to the next, so they are written over."""
    s = facts.Sentence(tokens)
    for ma in tokens:
        if (ma.get("reading") or {}).get("family") != "istifham":
            continue
        ma.update(pos="NOM", pos_camel="pron_interrog")
        if verb := _informing(ma, s):
            ma["head"], ma["rel"] = verb["id"], "SBJ"
            verb["head"], verb["rel"] = 0, "---"
            continue
        noun = _next(ma, s)
        noun["head"], noun["rel"] = ma["id"], "SBJ"
        before = next((t for t in reversed(tokens) if t["id"] < ma["id"] and not _attached(t)), None)
        ma["head"], ma["rel"] = (before["id"], "---") if before and facts.is_verb(before) else (0, "---")


def _idhan_settles_its_words(tokens: list[dict]) -> None:
    """إِذَنْ أُكْرِمَكَ: an إذن read as the particle stands over its verb, as لن does, and the verb
    is the present one it works on. The parser took it for a noun with a past verb under it,
    so both are written over."""
    s = facts.Sentence(tokens)
    for idhan in tokens:
        if not idhan.get("reading") or _word(idhan, s) != "إذن" or not (verb := _verb_after(idhan, s)):
            continue
        if verb["head"] == idhan["id"]:
            verb["head"], verb["rel"] = idhan["head"], idhan["rel"]
        idhan["head"], idhan["rel"] = verb["id"], "MOD"
        verb["asp"] = "i"


@lru_cache(maxsize=1)
def _retagged() -> frozenset[str]:
    """The words with a leaf that writes a new word class over the parser's (data: `retag`)."""
    def leaves(node: dict) -> list[dict]:
        return [node] if "role" in node else [leaf for child in node.get("children", []) for leaf in leaves(child)]
    return frozenset(child["is"] for child in _tree()["children"] if any("retag" in leaf for leaf in leaves(child)))


def stamp(tokens: list[dict]) -> None:
    """Stamp each listed word's reading on its token: {family, named, kind, book}, and the
    families the tree judges for it as `judged`. A word no leaf took (a و that opens no
    sentence) is read by its other lists as before, never as one of those families."""
    s = facts.Sentence(tokens)
    # a word class written over first (ما قبل إلا is a particle) is seen by the words read after it
    for token in sorted(tokens, key=lambda t: _word(t, s) not in _retagged()):
        token.pop("reading", None)
        token.pop("judged", None)
        if (word := _word(token, s)) == "other":
            continue
        token["judged"] = _judged(word)
        if word != strip_diacritics(token["lemma"]).strip("+"):
            token["lemma"] = word  # إِذًا is إذن, to every list
        values = {"word": word, **{axis: answer(token, s) for axis, (_, answer) in AXES.items()}}
        if found := walker.walk(values, _tree()):
            token["reading"] = {"family": found.role, "named": found.leaf.get("named"),
                                "kind": found.leaf.get("kind", "harf"), "book": found.book}
            token.update(found.leaf.get("retag", {}))
    _merged(tokens, s)
    _hasr_frees_its_words(tokens)
    _wonder_settles_its_words(tokens)
    _asks_settles_its_words(tokens)
    _idhan_settles_its_words(tokens)
