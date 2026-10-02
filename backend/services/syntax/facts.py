"""The questions (axes) the naming tree splits a word on.

An axis is a small pure test of one token and what hangs round it that answers
with exactly one value from a closed list; the tree (data/nahw_rules/naming_tree.json)
names the axis each branch splits on, walker.py reads the answers.

`is_verb` lives here, not in naming, so the walker (which naming calls) can
import the axes without a loop. Pure: tokens in, names out.
"""
from __future__ import annotations

from typing import Callable

from backend.services.arabic_text import bare_letters, strip_diacritics
from backend.services.nahw_book import book_map, book_words, is_one, is_plain_noun
from backend.services.syntax.vowels import (
    CAMEL_CASE, SHADDA, SUKUN, has_tanween, past_passive_shape, typed_case, typed_passive)

PRESENT_PREFIX = set("أنيت")
# a root letter is what is left once the letters that come and go are removed
WEAK = set("اويىءأإآئؤة")


def is_verb(token: dict) -> bool:
    if has_tanween(token.get("typed")):
        return False  # a verb never carries tanween, whatever the parser tagged it
    if token["pos"].startswith("VRB"):  # VRB-PASS is a verb too
        return True
    # the word is unknown to the morphology, but the reader typed a passive verb or a
    # hollow command (بِعْ, which CAMeL takes for a name)
    typed = token.get("typed") or ""
    # naming marks a typed command shape (asp c): بِعِ البيتَ، اعْبُدُوا. Not Form IV's أَفْعِلْ,
    # which a name shares (أَحْمَدْ); CAMeL's own reading settles that one
    if token.get("asp") == "c" and strip_diacritics(typed)[:1] != "أ":
        return token.get("pos_camel") in ("noun", "noun_prop")  # نَمْ is not the noun نَمّ
    return token.get("pos_camel") == "noun_prop" and (
        (strip_diacritics(typed)[:1] in PRESENT_PREFIX and typed_passive(typed, True))
        or past_passive_shape(typed))


def is_light(token: dict) -> bool:
    """The light لكنْ (or إنْ، أنْ) the reader typed: a sukun on the end and no shadda. It
    only joins (or is the light particle); the inna sister wears the shadda (Tasheel 1.8 p20)."""
    typed = token.get("typed") or ""
    return typed.endswith(SUKUN) and SHADDA not in typed


def is_passive(token: dict) -> bool:
    if token.get("vox") == "p":
        return True
    typed = token.get("typed")
    present = token.get("asp") == "i" or not (token["pos"].startswith("VRB") or past_passive_shape(typed))
    return typed_passive(typed, present)


class Sentence:
    """One parsed sentence with its lookups built once; every axis asks it and none rebuilds them."""

    def __init__(self, tokens: list[dict]):
        self.tokens = tokens
        self.by_id = {t["id"]: t for t in tokens}
        self._kids: dict[int, list[dict]] = {}
        for t in tokens:
            self._kids.setdefault(t["head"], []).append(t)
        self.verbless = not any(is_verb(t) for t in tokens)
        # a verbless sentence with a question word in it (كيف حالك); a question particle
        # (هل، أ) only asks and leaves the rest a plain sentence
        self.asks = self.verbless and any(
            "interrog" in t.get("pos_camel", "") and t["pos"] != "PRT" for t in tokens)
        self._family: dict[int, str | None] = {}
        self.hijazi = self._hijazi()

    def _hijazi(self) -> tuple[dict, dict, dict] | None:
        """(ما, its ism, its khabar) of ما الحجازية, which works like ليس (Tasheel 1.9 n6
        p23): a verbless sentence opening ما, a noun, then an indefinite noun in nasb."""
        words = [t for t in self.tokens if not t["form"].startswith("+")]
        # its ism is marfu': ما أحسنَ زيدًا is the ما of wonder
        if not (self.verbless and len(words) >= 3 and words[0]["lemma"] == "ما"
                and words[1]["pos"] in ("NOM", "PROP") and typed_or_parsed_case(words[1]) != "a"):
            return None
        khabar = next((t for t in words[2:] if t["pos"] in ("NOM", "PROP") and t.get("stt") == "i"
                       and typed_or_parsed_case(t) == "a"), None)
        return (words[0], words[1], khabar) if khabar else None

    def head(self, token: dict) -> dict | None:
        return self.by_id.get(token["head"])

    def kids(self, token: dict) -> list[dict]:
        return self._kids.get(token["id"], [])

    def family(self, word: dict) -> str | None:
        """Which family a governing word belongs to: inna, kana, kaada or zanna."""
        if word["id"] not in self._family:
            self._family[word["id"]] = self._family_of(word)
        return self._family[word["id"]]

    def _has_particle(self, verb: dict, family: str, part: str = "words") -> bool:
        return any(k["pos"] == "PRT" and is_one(k["lemma"], family, part) for k in self.kids(verb))

    def _completed_by_present_verb(self, verb: dict) -> bool:
        """كاد يموت, أوشك أن ينتهي: a present verb, bare or behind أن, finishes the clause."""
        for kid in self.kids(verb):
            if kid["pos"] == "PRT" and is_one(kid["lemma"], "nasb_mudari"):
                if any(k["pos"].startswith("VRB") and k.get("asp") == "i" for k in self.kids(kid)):
                    return True
            elif kid["pos"].startswith("VRB") and kid.get("asp") == "i":
                return True
        return False

    def _family_of(self, word: dict) -> str | None:
        lemma = word["lemma"]
        if (is_one(lemma, "inna") and not is_light(word)) or is_one(lemma, "la_jins"):
            return "inna"
        if is_one(lemma, "kana") or is_one(lemma, "kana", "like_laysa") \
                or (is_one(lemma, "kana", "needs_negation") and self._has_particle(word, "negation")) \
                or (is_one(lemma, "kana", "needs_ma") and self._has_particle(word, "kana", "like_laysa")):
            return "kana"
        if is_one(lemma, "kaada") and self._completed_by_present_verb(word):
            return "kaada"
        return "zanna" if is_one(lemma, "zanna") else None

    def noun_before(self, particle: dict) -> bool:
        """The particle follows a noun it can join to, which an oath و does not: the noun it
        hangs on, or the noun straight before it (دخل المعلمُ فالطلابُ, ف hung on the verb)."""
        return any(before and before["id"] < particle["id"] and before["pos"] in ("NOM", "PROP")
                   and not is_verb(before)
                   for before in (self.head(particle), self.by_id.get(particle["id"] - 1)))

    def negated_before(self, word: dict) -> bool:
        return any(t["pos"] == "PRT" and t["id"] < word["id"] and is_one(t["lemma"], "negation")
                   for t in self.tokens)

    def asked_of(self, token: dict) -> bool:
        """The word hangs off the question word, so it is what is asked about: the mubtada,
        whatever the parser drew it as."""
        head = self.head(token)
        return bool(head and "interrog" in head.get("pos_camel", "") and self.asks)


def typed_or_parsed_case(token: dict) -> str | None:
    """What the reader typed first, the parser's guess second."""
    return (typed_case(token.get("typed"), token.get("stuck_on", 0))
            or CAMEL_CASE.get(token.get("cas")))


def same_case(token: dict, head: dict) -> bool:
    """The word and the noun it hangs on wear one case."""
    mine = typed_or_parsed_case(token)
    return bool(mine) and mine == typed_or_parsed_case(head) and not is_verb(head)


def agrees(token: dict, head: dict) -> bool:
    """A na't matches its noun in case and in "the": a word in idafa counts as
    definite, so an indefinite word after a definite or construct noun does not agree."""
    return same_case(token, head) and not (token.get("stt") == "i" and head.get("stt") in ("d", "c"))


def is_state_word(token: dict) -> bool:
    """What a hal is made of: a participle, or any word beginning مـ."""
    return is_participle(token) or bare_letters(token.get("typed") or "")[:1] == "م"


def state_or_specification(token: dict, head: dict) -> str:
    """An indefinite nasb word is a hal if it is a participle, else a tamyeez, which never
    comes before its head (Tasheel 3.2 p67)."""
    if is_state_word(token):
        return "state"
    return "specification" if token["id"] > head["id"] else "none"


def is_deputy(token: dict, doers: list[dict]) -> bool:
    """Under a passive verb the first of its nouns (a subject before an object, then by
    position) stands in for the doer; only a later one is an object."""
    first = min(doers, key=lambda t: (t["rel"] == "OBJ", t["id"]))
    return token is first


def verb_above(token: dict, s: Sentence) -> dict | None:
    """The verb the word hangs on, or the one its noun head hangs on (a hal, tamyeez or
    absolute object modifies the noun under a verb)."""
    head = s.head(token)
    if head and is_verb(head):
        return head
    up = s.head(head) if head else None
    return up if up and is_verb(up) else None


def calling_head(token: dict, s: Sentence) -> str | None:
    """nida or istithna when the word is called or excepted: it hangs on the listed
    particle (the excepting one only when no negation came before it), or it is a listed
    excepting noun (غير، سوى) under a verb."""
    head = s.head(token)
    if head and head["pos"] == "PRT":
        if is_one(head["lemma"], "nida") and "interrog" not in head.get("pos_camel", ""):
            return "nida"
        if is_one(head["lemma"], "istithna") and not s.negated_before(head):
            return "istithna"
    # غير، سوى after a complete clause: hung on its verb, or on a definite noun under it
    # (an indefinite one takes غير as its صفة: رجلٌ غيرُ كريم)
    if head and is_one(token["lemma"], "istithna", "nouns") and not s.negated_before(token) \
            and (is_verb(head) or (head.get("stt") == "d" and verb_above(token, s))):
        return "istithna"
    return None


def _joins_clauses(token: dict, s: Sentence) -> bool:
    """ثم is a noun to the parser, but a listed joining word between two nouns, or bare
    before a verb, is the particle (the place-word ثَمَّ wears its shadda)."""
    if not is_one(token["lemma"], "atf"):
        return False
    if s.noun_before(token) and any(k["rel"] == "OBJ" for k in s.kids(token)):
        return True
    typed = token.get("typed") or ""
    follower = s.by_id.get(token["id"] + 1)
    return bool(typed and typed == strip_diacritics(typed) and follower and is_verb(follower))


def is_called_noun(token: dict) -> bool:
    """أيها، أيتها: the noun يا calls, though the parser tags it a particle."""
    return _listed(token, "nida", "called_nouns")


def previous_noun(token: dict, s: Sentence) -> dict | None:
    """The noun straight before this word, past any pronoun joined to that noun (أخو+ك)."""
    for t in sorted((t for t in s.tokens if t["id"] < token["id"]), key=lambda t: -t["id"]):
        if not t["form"].startswith("+"):
            return t if t["pos"] in ("NOM", "PROP") and not is_verb(t) else None
    return None


def stands_for(token: dict, s: Sentence) -> bool:
    """The بدل (Tasheel 3.10.4 p95), straight after a definite noun in the same case: a name
    that names it again (جاء أخوك زيدٌ), or a noun with a pronoun back to it, a part or a
    quality of it (أكلت الرغيفَ ثلثَه، نفعني المعلمُ علمُه). A صفة is neither a name nor
    carries that pronoun. Only in a sentence with a verb: after a bare mubtada a definite
    noun is its khabar (اللهُ ربُّنا); nor after a verb of two objects, whose second object
    stands there (أعطيت الولدَ كتابَه)."""
    before = previous_noun(token, s)
    if s.verbless or not before or token["rel"] == "IDF":
        return False
    names = token["pos"] == "PROP" or any(k.get("pos_camel") == "pron" and k["rel"] == "IDF" for k in s.kids(token))
    mine = typed_or_parsed_case(token)
    if not (names and before.get("stt") in ("d", "c") and mine and mine == typed_or_parsed_case(before)):
        return False
    verb = verb_above(before, s)
    return not (verb and (is_one(verb["lemma"], "zanna") or is_one(verb["lemma"], "two_objects_give")))


def with_waw(token: dict, s: Sentence) -> bool:
    """سرتُ والشاطئَ: after واو المعية (و meaning "with") a noun the reader put in nasb is the
    مفعول معه when nothing before the و is in nasb for it to join (Tasheel 3.8.5 p76); a
    معطوف would wear the case of what it joins."""
    head = s.head(token)
    if not (head and head["pos"] == "PRT" and head["lemma"].strip("+") == "و"
            and typed_case(token.get("typed"), token.get("stuck_on", 0)) == "a" and verb_above(head, s) is not None):
        return False
    joined = previous_noun(head, s)
    return joined is None or typed_or_parsed_case(joined) != "a"


def jarr_takes(token: dict, s: Sentence) -> bool:
    """A preposition works only on the noun straight after it (Tasheel 1.7 p18): a second
    noun the parser hung on it (لله الحمدُ) is not its majrur."""
    head = s.head(token)
    if not (token["rel"] == "OBJ" and head and head["pos"] == "PRT" and not is_called_noun(head)):
        return False
    return not any(t["pos"] in ("NOM", "PROP") and head["id"] < t["id"] < token["id"] for t in s.tokens)


def _kind(token: dict, s: Sentence) -> str:
    """Particle, verb or noun. A word a calling or excepting particle takes is a noun,
    whatever the parser tagged it, so that test comes before the verb test."""
    if is_called_noun(token):
        return "ism"
    if token["pos"] == "PRT" or _joins_clauses(token, s) or (s.hijazi and token is s.hijazi[0]):
        return "harf"
    if calling_head(token, s):
        return "ism"
    return "fil" if is_verb(token) else "ism"


def _follows(token: dict, s: Sentence) -> str:
    """Which follower (tabi') the word is, or none: a follower takes its case from the
    word it follows, every other noun from a governor (Tasheel 3.10 p88).

    A word is a follower only on the evidence of both its link and what it hangs on;
    an indefinite word after a definite or construct noun is a khabar or hal, so it
    answers none and the rest of the naming decides it. Tested in this order because
    each earlier follower has a mark of its own (a pointer child, a joining particle, a
    bare name after a noun with ال, a listed تأكيد word) that a plain na't lacks."""
    if s.asked_of(token) or calling_head(token, s) or with_waw(token, s):
        return "none"  # غيرُ خالدٍ after a complete clause is the مستثنى, not a صفة
    head = s.head(token)
    # هذا البستانُ: the noun with ال a pointer points at, hung on it or (as some parses
    # have it) under it; a pointer is mabni, so its own vowel says nothing of the case
    pointer = next((c for c in (*s.kids(token), head) if c and "dem" in c.get("pos_camel", "")
                    and c["id"] == token["id"] - 1), None)
    if pointer and token.get("stt") == "d":
        return "naat"
    # يا أيها الناسُ: the noun with ال after أيها is its صفة
    if head and is_called_noun(head) and token.get("stt") == "d":
        return "naat"
    # جاء زيدٌ زيدٌ: the same noun said twice is التوكيد اللفظي (Tasheel 3.10.3 p94)
    before = s.by_id.get(token["id"] - 1)
    if before and not is_verb(before) and before["pos"] != "PRT" \
            and strip_diacritics(before.get("typed") or "-") == strip_diacritics(token.get("typed") or ""):
        return "tawkeed"
    if not head:
        return "none"
    # لكنّ is also an inna sister; it joins only when no clause of its own follows, or as the light لكنْ
    if (head["pos"] == "PRT" or _joins_clauses(head, s)) and is_one(head["lemma"], "atf") \
            and (not is_one(head["lemma"], "inna") or is_light(head)) and s.noun_before(head):
        return "atf"
    # الخليفة عمر: a bare name right after a noun with ال is that noun's badal
    if token["pos"] == "PROP" and token["rel"] == "MOD" and head["id"] == token["id"] - 1 \
            and head["pos"] == "NOM" and head["form"].startswith("ال") and not is_verb(head) \
            and not has_tanween(token.get("typed")):
        return "badal"
    with_pronoun = any(k.get("pos_camel") == "pron" for k in s.kids(token))
    if not _listed(token, "tawkeed", "with_pronoun" if with_pronoun else "without_pronoun") \
            and stands_for(token, s):
        return "badal"
    if _listed(token, "tawkeed", "with_pronoun" if with_pronoun else "without_pronoun") \
            and head["id"] < token["id"] and not is_verb(head) and head["pos"] != "PRT":
        return "tawkeed"
    if token["rel"] != "MOD" or is_verb(head):
        return "none"
    mine, theirs = typed_or_parsed_case(token), typed_or_parsed_case(head)
    if mine and mine == theirs:
        return "naat" if agrees(token, head) else "none"
    # لا رجلَ حاضرٌ (khabar) and a hal or tamyeez in nasb are not followers
    if mine and theirs and head["rel"] in ("SBJ", "TPC") and mine != "a":
        return "none"
    if mine == "a" and token.get("stt") != "d":
        return "none"
    return "naat" if token.get("ud") == "ADJ" else "none"


def _skeleton(word: str) -> list[str]:
    return [letter for letter in bare_letters(word) if letter not in WEAK]


def is_participle(token: dict) -> bool:
    """An active or passive participle, or an adjective: what a hal is made of.
    A word the morphology does not know (مسرعا) is judged by its مـ and its ending ـا."""
    typed = bare_letters(token.get("typed") or "")
    return (token.get("ud") == "ADJ" or token.get("pos_camel") == "adj"
            or token.get("pattern", "").removeprefix("ال").startswith(tuple(book_words("participle_patterns")))
            or (token.get("pos_camel") == "noun_prop" and typed[:1] == "م" and typed[-1:] == "ا"))


def takes_tamyeez(token: dict, s: Sentence) -> bool:
    """A tamyeez stands after a number or a measure, or after a verb of tamyeez al-nisba."""
    head = s.head(token)
    if head and is_one(head["lemma"], "tamyeez_verbs"):
        return True
    return any(is_one(t["lemma"], "tamyeez_head") or is_one(strip_diacritics(t["form"]), "tamyeez_head")
               for t in s.tokens if t["id"] < token["id"])


def completes_kaada(token: dict, s: Sentence) -> bool:
    """The present verb that finishes a كاد-type verb; its clause is that verb's khabar."""
    head = s.head(token)
    return bool(head and is_verb(token) and s.family(head) == "kaada")


def _listed(token: dict, family: str, part: str = "words") -> bool:
    """On a book list by its lemma or by the form as typed: the list holds صباحا
    and يوم, while the parser lemmatises the first to صباح."""
    return any(is_one(spelling, family, part) for spelling in (token["lemma"], strip_diacritics(token["form"])))


def _is_zarf(token: dict, s: Sentence) -> bool:
    """A listed time or place word, or كل/بعض added to one (كلَّ يومٍ)."""
    if token["pos"] == "PRT":
        return False
    if _listed(token, "zarf_zaman") or _listed(token, "zarf_makan"):
        return True
    return _listed(token, "zarf_zaman", "carriers") and any(
        k["rel"] == "IDF" and (_listed(k, "zarf_zaman") or _listed(k, "zarf_makan")) for k in s.kids(token))


def zarf_of_khabar(token: dict, s: Sentence) -> bool:
    """الأستاذُ عندَ البابِ: in a verbless sentence a place or time word with its mudaf ilayh
    is the khabar's maf'ul fihi (the khabar itself is understood, Tasheel 1.4.4 p13)."""
    return (s.verbless and _is_zarf(token, s) and "interrog" not in token.get("pos_camel", "")
            and token["rel"] in ("---", "MOD", "PRD")
            and typed_or_parsed_case(token) in (None, "a") and any(k["rel"] == "IDF" for k in s.kids(token)))


def _place_time(token: dict, s: Sentence) -> bool:
    """A listed time or place word that is a verb's مفعول فيه (Tasheel 3.2 p67): it
    modifies the verb with no vowel or fatha (the parser may draw that as idafa), or it
    stands before its verb with the verb hanging off it (مَتَى سافر)."""
    if not _is_zarf(token, s):
        return False
    head = s.head(token)
    if head and is_verb(head):
        return token["rel"] in ("MOD", "IDF") and typed_case(token.get("typed"), token.get("stuck_on", 0)) in (None, "a")
    return typed_or_parsed_case(token) in (None, "a") and any(
        is_verb(k) and k["id"] > token["id"] for k in s.kids(token))


def _verb_place(token: dict, s: Sentence) -> str:
    """The place a word fills under a verb (Tasheel 3.1 p60, 3.2 p67), `none` where the
    book names it elsewhere. Tested in this order because an earlier place shadows a
    later one of the same word: a listed time or place word is a مفعول فيه whatever its
    link; an indefinite word after a verb that already has its doer is not an argument
    but a tamyeez (after a tamyeez verb, not a participle) or a hal (a participle); a
    second OBJ after the first is the second object; only then is the argument itself
    told by the vowel the reader typed (damma subject, fatha object), else by the link;
    last, an indefinite word in nasb modifying a verb or the noun under it is an
    absolute object (same root), a hal or a tamyeez."""
    if _place_time(token, s):
        return "place_time"
    if with_waw(token, s):
        return "accompaniment"
    head = s.head(token)
    rel = token["rel"]
    typed = typed_case(token.get("typed"), token.get("stuck_on", 0))
    if head and is_verb(head):
        before = token["id"] < head["id"]
        siblings = [t for t in s.kids(head) if t is not token]
        asked = book_map("istifham", "before_verb").get(strip_diacritics(token["form"]))
        if asked and before and not any(t["rel"] == "OBJ" for t in siblings):
            return asked  # ماذا قرأت، كيف جئت: the question noun fills the place it asks about
        if before and rel in ("SBJ", "TPC") and typed == "a":
            return "object"  # القرآنَ قرأ الطالبُ: the reader's own fatha marks the fronted object
        if before and rel in ("SBJ", "TPC"):
            return "none"  # a doer never comes first (نحن نكتب): the noun opens the sentence
        if head.get("asp") == "c" and rel in ("SBJ", "TPC", "OBJ", "---") and typed != "u":
            return "object"  # قل الحق: a command's doer is always the hidden أنت (Tasheel 2.4.1 p30)
        if rel in ("OBJ", "MOD", "TMZ") and typed in (None, "a") and not before \
                and token.get("stt") == "i" and any(t["rel"] in ("SBJ", "TPC", "OBJ") for t in siblings):
            if is_one(head["lemma"], "tamyeez_verbs") and not is_participle(token):
                return "specification"
            if is_participle(token):
                return "state"
        if rel == "OBJ" and typed in (None, "a") and any(t["rel"] == "OBJ" and t["id"] < token["id"] for t in siblings):
            return "second_object"  # ظن الولد الأمر سهلا, أعطى الولد الكتاب
        if (rel in ("SBJ", "TPC", "OBJ") or (rel == "IDF" and typed != "i")
                or (rel == "MOD" and typed == "u" and is_plain_noun(token))
                # بِعْ الكِتَابَ: hung on the verb as a modifier, but a definite word is never a
                # hal or tamyeez, so its fatha makes it the object (unless it is the verb's own masdar)
                or (rel == "MOD" and typed == "a" and token.get("stt") in ("d", "c") and is_plain_noun(token)
                    and _skeleton(token["lemma"]) != _skeleton(head["lemma"]))):
            if typed in ("u", "a"):  # damma stands for the doer (or its deputy), fatha is the done-to
                return "subject" if typed == "u" else "object"
            if is_passive(head):
                nouns = [t for t in (*siblings, token) if t["rel"] in ("SBJ", "TPC", "OBJ")]
                return "subject" if rel != "OBJ" or is_deputy(token, nouns) else "object"
            # the parser reads letters only, so a nominative "object" with no subject is the subject
            return "object" if rel == "OBJ" and (
                typed_or_parsed_case(token) != "u" or any(t["rel"] == "SBJ" for t in siblings)) else "subject"
        if rel == "TMZ":
            return "specification"
    if rel == "MOD" and head:
        mine = typed_or_parsed_case(token)
        # an indefinite nasb word after a definite noun is that noun's hal, not the verb's
        if mine == "a" and token.get("stt") != "d" and not (same_case(token, head) and not agrees(token, head)):
            verb = verb_above(token, s)
            if verb:
                if _skeleton(token["lemma"]) == _skeleton(verb["lemma"]):
                    return "absolute"  # same root as its verb: فَرِحَ فَرَحًا
                return state_or_specification(token, head)
    return "none"


def _governor(token: dict, s: Sentence) -> str:
    """What gives this word its case (Tasheel 3.3 p79). A word has one governor and the
    nearest wins: what is joined to it by form outranks what reaches it through a verb.
    Tested in this order: a word a question is about has none; a listed time or place
    word belongs to its verb; a particle that calls or excepts it, or that it is the
    object of (harf jarr), because a particle works only on the word straight after it;
    the noun it is the idafa of (a verb takes an idafa-linked word as its argument
    unless the reader typed kasra; a bare noun with kasra straight after a plain noun
    is idafa too, يا عبدَ اللهِ); the inna/kana/kaada/zanna family or plain verb it is an
    argument of (the verb's second object included); the number or measure a TMZ or OBJ
    under a noun specifies; a verb that reaches it by any other place (_verb_place);
    last, the family whose khabar it is: a modifier of that family's subject that fails
    to agree with it (a na't would agree), or that is not in nasb under a subject."""
    head = s.head(token)
    rel = token["rel"]
    typed = typed_case(token.get("typed"), token.get("stuck_on", 0))
    if s.asked_of(token):
        return "none"
    if s.hijazi and token in s.hijazi[1:]:
        return "kana"  # ما الحجازية: its ism and khabar, as ليس's
    if _place_time(token, s):
        return "verb"
    if calling := calling_head(token, s):
        return calling
    if with_waw(token, s):
        return "verb"  # the verb before واو المعية works on the noun after it
    if jarr_takes(token, s):
        return "harf_jarr"
    under_verb = bool(head) and is_verb(head)
    if rel == "IDF" and not (under_verb and typed != "i"):
        return "idafa"
    if rel == "---" and head and is_plain_noun(head) and head["id"] == token["id"] - 1 \
            and typed_or_parsed_case(token) == "i" and not any(c["rel"] in ("SBJ", "TPC") for c in s.kids(token)) \
            and not ("dem" in token.get("pos_camel", "") and s.verbless):
        return "idafa"
    # ظن الولد الأمر سهلا: a modifier after the first object is the verb's second
    second = (rel == "MOD" and under_verb and typed in (None, "a") and s.family(head) == "zanna"
              and any(k["rel"] == "OBJ" and k["id"] < token["id"] for k in s.kids(head)))
    # كان الطفلُ يلعب: the parser may hang كان's noun on it as a modifier
    named_by_kana = rel == "MOD" and under_verb and typed != "a" and s.family(head) == "kana" \
        and head["id"] == token["id"] - 1
    if head and (second or named_by_kana or rel in ("SBJ", "TPC", "OBJ", "PRD") or (rel == "IDF" and typed != "i")):
        family = s.family(head)
        if family:
            return family
    if rel in ("TMZ", "OBJ") and head and not under_verb and head["pos"] != "PRT":
        return "noun"  # عشرون كتابًا: a number or measure
    if _verb_place(token, s) != "none":
        return "verb"
    if rel == "MOD" and head and not is_verb(token):
        mine, theirs = typed_or_parsed_case(token), typed_or_parsed_case(head)
        if (same_case(token, head) and not agrees(token, head)) \
                or (mine and theirs and head["rel"] in ("SBJ", "TPC") and mine != "a"):
            above = s.head(head)
            family = s.family(above) if above else None
            if family in ("kana", "inna"):
                return family
    return "none"


def _nominal_place(token: dict, s: Sentence) -> str:
    """The place of a word no verb governs: the nominal sentence, mubtada and khabar
    (Tasheel 1.4 p6), with the hal and tamyeez a noun can take. Tested in this order
    because the parser's link is trusted last: the question word and the pointer say
    what the sentence is about before any link does; then the khabar link; then the
    subject links; then a word the sentence rests on; then a modifier by its case.

    In a verbless sentence a question word is the khabar, brought to the front, and the
    nominative noun (or the one the question word governs) the mubtada; a pointer is
    the mubtada. A khabar (PRD) is the predicate, except that after a fronted
    jar-wa-majroor (إن في البيت رجلا) the noun is the subject. A SBJ or TPC is the
    subject; the word the sentence rests on, with its subject under it, the predicate,
    as is an indefinite noun after a pointer (هذا بيتٌ). A parser that leaves two loose
    halves gives the first the subject and the second the predicate. A modifier in the
    same case as a definite noun and indefinite is its khabar, or its hal in nasb; under
    a subject, in any case but nasb, a khabar; in nasb it is a hal or a tamyeez."""
    rel = token["rel"]
    if s.hijazi and token in s.hijazi[1:]:
        return "subject" if token is s.hijazi[1] else "predicate"
    if zarf_of_khabar(token, s):
        return "place_time"
    if (s.verbless and rel == "OBJ" and s.head(token) and s.head(token)["pos"] == "PRT" and not jarr_takes(token, s)
            and typed_or_parsed_case(token) == "u"):
        return "subject"  # لله الحمدُ: the noun after a fronted jar-majrur khabar is the مبتدأ
    if is_verb(token):  # a verb is only ever a khabar by its link; its clause is named from the tree above
        return "predicate" if rel == "PRD" else "none"
    head = s.head(token)
    camel = token.get("pos_camel", "")
    if s.asks:
        if "interrog" in camel:
            return "predicate"  # كيف حالك: the question word is the khabar, brought to the front
        if (token["pos"] == "NOM" and typed_or_parsed_case(token) == "u" and rel != "IDF") or s.asked_of(token):
            return "subject"
    if "dem" in camel and s.verbless and rel not in ("IDF", "OBJ"):
        return "subject"
    if rel == "PRD":
        fronted_jar = any(t["rel"] == "PRD" and t["pos"] == "PRT" and t["id"] < token["id"]
                          for t in (s.kids(head) if head else ()))
        return "subject" if fronted_jar else "predicate"
    if rel in ("SBJ", "TPC"):
        return "subject"
    kids = s.kids(token)
    if rel == "---":
        if any(c["rel"] in ("SBJ", "TPC") for c in kids):
            return "predicate"
        pointer = next((c for c in kids if "dem" in c.get("pos_camel", "")), None)
        if pointer and pointer["id"] < token["id"] and token.get("stt") == "i" and s.verbless:
            return "predicate"
        if token["pos"] == "NOM" and s.verbless:
            loose = [t for t in s.tokens if t["rel"] == "---" and t["pos"] == "NOM"]
            return "subject" if not loose or token is loose[0] else "predicate"
    if rel == "MOD" and head:
        mine, theirs = typed_or_parsed_case(token), typed_or_parsed_case(head)
        if same_case(token, head) and not agrees(token, head):
            return "state" if mine == "a" else "predicate"
        if mine and theirs and head["rel"] in ("SBJ", "TPC") and mine != "a":
            return "predicate"
        if mine == "a" and token.get("stt") != "d":
            return state_or_specification(token, head)
    return "none"


def _slot(token: dict, s: Sentence) -> str:
    """Which place the word fills, from its link, position, typed case, definiteness and
    siblings alone; never from what governs it, so one reading serves every family and
    the tree's branch for that family says which places it names. A place a verb gives
    (_verb_place) comes first, then the nominal sentence's (_nominal_place)."""
    place = _verb_place(token, s)
    return place if place != "none" else _nominal_place(token, s)


def _voice(token: dict, s: Sentence) -> str:
    """Whether the verb the word hangs on (itself or through its noun) is active or
    passive: under a passive verb the subject is the deputy of the doer. none where no
    verb is above the word."""
    verb = verb_above(token, s)
    return "none" if verb is None else "passive" if is_passive(verb) else "active"


# Each axis is one question the book asks of a word, with a closed list of answers
# and a function that gives exactly one. Axes never call one another: what they share
# is the plain helpers above. Siblings in the tree split on one axis and each takes
# one answer, so they cannot overlap.
AXES: dict[str, tuple[tuple[str, ...], Callable[[dict, Sentence], str]]] = {
    "kind": (("harf", "fil", "ism"), _kind),
    "follows": (("naat", "atf", "tawkeed", "badal", "none"), _follows),
    "governor": (("harf_jarr", "idafa", "verb", "noun", "inna", "kana", "kaada", "zanna", "nida", "istithna",
                  "none"), _governor),
    "slot": (("subject", "predicate", "object", "second_object", "absolute", "place_time", "accompaniment",
              "state", "specification", "none"), _slot),
    "voice": (("active", "passive", "none"), _voice),
}


def of_sentence(tokens: list[dict]) -> list[dict[str, str]]:
    """Every token's answer on every axis, in token order, with the sentence's lookups built once."""
    s = Sentence(tokens)
    answers = []
    for token in tokens:
        values = {}
        for axis, (allowed, answer) in AXES.items():
            values[axis] = answer(token, s)
            if values[axis] not in allowed:
                raise ValueError(f"axis {axis} answered {values[axis]!r}, not one of {allowed}")
        answers.append(values)
    return answers
