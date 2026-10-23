"""One parsed sentence with its lookups built once, and the few questions that need it
but belong to no single axis: the verb above a word, the noun before it, what a jarr takes."""
from __future__ import annotations

from backend.services.arabic_text import bare_letters
from backend.services.nahw_book import doer_written_in, frames, is_one
from backend.services.arabic_text import strip_diacritics
from backend.services.syntax.facts.word import SUBJECTS, is_passive, listed, NOUN_LINKS, is_prefix, is_suffix, is_called_noun, is_light, is_preposition, is_verb, read_as, same_case, typed_or_parsed_case, noun_tagged, is_participle, present_verb_tagged, subject_link


def praised_noun(token: dict, s: "Sentence") -> bool:
    """نِعْمَ الْخُلُقُ الْوَفَاءُ، بِئْسَ الْخُلُقُ الْكَذِبُ: a verb of praise or blame (closed_words
    praise_blame) has one doer, the noun with ال straight after it; the raf' noun after that is
    the one praised or blamed (المخصوص), the مبتدأ of a sentence of its own, whether the parser
    hung it on the verb as a second subject or on the doer as its modifier. The follows axis
    and the slot both ask this, so neither calls it a صفة or a second doer."""
    head = s.head(token)
    if not head or typed_or_parsed_case(token) != "u" or not noun_tagged(token):
        return False
    verb = head if is_verb(head) else s.head(head)
    if not verb or not is_verb(verb) or not is_one(verb["lemma"], "praise_blame"):
        return False
    if doer_written_in(verb["lemma"], "praise_blame"):
        return head is verb and token["rel"] in NOUN_LINKS
    # the doer by what it shows, not the parser's label for it (it hangs the noun as SBJ or OBJ)
    # or the تمييز that explains a doer hidden in the verb (نِعْمَ رَجُلًا زَيْدٌ)
    doer = next((k for k in s.kids(verb) if k["id"] < token["id"] and noun_tagged(k) and (k["rel"] == "TMZ" or (
                 k["rel"] in NOUN_LINKS and typed_or_parsed_case(k) == "u"))), None)
    return bool(doer and (token["rel"] in NOUN_LINKS or (token["rel"] == "MOD" and head is doer)))


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
        self.governed_by: dict[int, int] = {}  # token id -> the id of the word that governs it
        self.hijazi = self._hijazi()
        self.described_doer = self._described_doer()
        self.asked_pair = self._asked_pair()

    def _described_doer(self) -> tuple[dict, dict, dict] | None:
        """(the negation or question particle, the وصف, its doer) of the مبتدأ وصف: a singular describing word straight after a
        negation or a question word, then a raf' noun, is the mubtada and that noun its فاعل,
        which stands in for the khabar (Alfiyya: وأوّلٌ مبتدأ والثاني فاعلٌ اغنى؛ ما ذاهبٌ
        المسلمون، أقائمٌ الزيدان). Dual or plural and agreeing (أقائمون الزيدون), the noun is the
        mubtada and the وصف its khabar (إن في سوى الإفراد طِبقًا استقر), left to the other rules."""
        words = [t for t in self.tokens if not is_suffix(t)]
        return next(((lead, wasf, doer) for lead, wasf, doer in zip(words, words[1:], words[2:])
                     if (is_one(lead["lemma"], "negation") or is_one(lead["lemma"], "istifham"))
                     and not any(is_verb(t) for t in words[words.index(lead):])
                     and is_participle(wasf) and wasf.get("stt") == "i" and wasf.get("num") in ("s", None)
                     and typed_or_parsed_case(wasf) in ("u", None)
                     and doer["pos"] in ("NOM", "PROP") and not is_preposition(doer)
                     and typed_or_parsed_case(doer) in ("u", None)), None)

    def _asked_pair(self) -> tuple[dict, dict] | None:
        """(the question noun, the noun after it) when a question noun that is no ظرف or hal
        (closed_words istifham heads) opens a verbless clause on a noun: the question noun
        is the mubtada and that noun its khabar (مَا هِيَ، مَنْ أَبُوكَ، الْقَارِعَةُ مَا الْقَارِعَةُ).
        A verb before it (قَالَ مَا اسْمُكَ) leaves the asked clause verbless; one after it does not."""
        words = [t for t in self.tokens if not is_suffix(t)]
        return next(((asked, told) for asked, told in zip(words, words[1:])
                     if not any(is_verb(t) for t in words[words.index(asked):])
                     and read_as(asked, "istifham") and is_one(asked["lemma"], "istifham", "heads")
                     and told["pos"] == "NOM" and not is_preposition(told)), None)  # ما ذاهبٌ المسلمون: ما negates

    def _hijazi(self) -> tuple[dict, dict, dict] | None:
        """(ما, its ism, its khabar) of ما الحجازية, which works like ليس (Tasheel 1.9 n6
        p23): a verbless sentence opening ما, a noun, then an indefinite noun in nasb."""
        words = [t for t in self.tokens if not is_suffix(t)]
        while words and is_prefix(words[0]):
            words.pop(0)  # وَما زيدٌ قائمًا: a وَ or فَ written onto it opens nothing else
        # its ism is marfu': ما أحسنَ زيدًا is the ما of wonder
        if not (self.verbless and len(words) >= 3 and words[0]["lemma"] == "ما"
                and noun_tagged(words[1]) and typed_or_parsed_case(words[1]) != "a"):
            return None
        khabar = next((t for t in words[2:] if noun_tagged(t) and t.get("stt") == "i"
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
                if any(present_verb_tagged(k) for k in self.kids(kid)):
                    return True
            elif present_verb_tagged(kid):
                return True
        return False

    def _family_of(self, word: dict) -> str | None:
        lemma = word["lemma"]
        if (is_one(lemma, "inna") and not is_light(word)) or read_as(word, "la_jins"):
            return "inna"
        if is_one(lemma, "kana", "like_laysa"):
            # ما alone works as ليس only as ما الحجازية; any other ما (ما اسمك) governs nothing
            return "kana" if self.hijazi and word is self.hijazi[0] else None
        # the other families are verbs: the noun عِلْمُهُ shares a lemma with عَلِمَ and governs nothing
        if not is_verb(word):
            return None
        if (is_one(lemma, "kana")
                or (is_one(lemma, "kana", "needs_negation") and self._has_particle(word, "negation"))
                or (is_one(lemma, "kana", "needs_ma") and self._has_particle(word, "kana", "like_laysa"))) \
                and not self._stands_alone(word):
            return "kana"
        if is_one(lemma, "kaada") and self._completed_by_present_verb(word):
            return "kaada"
        return "zanna" if is_one(lemma, "zanna") and self._two_objects(word) else None

    def _stands_alone(self, verb: dict) -> bool:
        """وَإِنْ كَانَ ذُو عُسْرَةٍ، أَصْبَحْنَا: with no خبر, كان and its sisters are تامة and take a
        فاعل like any verb (Ibn Aqil on كان التامة); كان في الدار رجل: the خبر may come first, a phrase.
        ليس is never تامة: it has no meaning of being without its خبر."""
        return not is_one(verb["lemma"], "kana", "always_defective") \
            and all(k["rel"] in SUBJECTS or k["pos"] == "PRT" and k["rel"] == "MOD" for k in self.kids(verb))

    def _two_objects(self, verb: dict) -> bool:
        """ظن الولدُ الأمرَ سهلًا: an object and a second word in nasb after it, or an أنّ
        clause standing for both (علمت أنّ الحق منتصر). تعلّمَ القرآنَ has one, and is a plain verb."""
        kids = self.kids(verb)
        first = next((k for k in kids if k["rel"] == "OBJ" and k["pos"] != "PRT"), None)
        if any(k["pos"] == "PRT" and is_one(k["lemma"], "inna") for k in kids):
            return True
        return bool(first) and any(k["id"] > first["id"] and k["rel"] in ("OBJ", "MOD") and noun_tagged(k)
                                   and typed_or_parsed_case(k) in (None, "a") for k in kids)

    def noun_before(self, particle: dict) -> bool:
        """The particle follows a noun it can join to, which an oath و does not: the noun it
        hangs on, or the noun straight before it (دخل المعلمُ فالطلابُ, ف hung on the verb)."""
        return any(before and before["id"] < particle["id"] and noun_tagged(before)
                   and not is_verb(before)
                   for before in (self.head(particle), self.by_id.get(particle["id"] - 1)))

    def negated_before(self, word: dict) -> bool:
        return any(t["pos"] == "PRT" and t["id"] < word["id"] and is_one(t["lemma"], "negation")
                   for t in self.tokens)

    def asked_of(self, token: dict) -> bool:
        """The word hangs off the question word, so it is what is asked about: the mubtada,
        whatever the parser drew it as."""
        head = self.head(token)
        return bool(head and "interrog" in head.get("pos_camel", "") and self.asks
                    and not is_one(head["lemma"], "istifham", "inflected"))  # أيُّ الأعمالِ: its مضاف إليه


def puts_in_jarr(token: dict, s: "Sentence") -> bool:
    """Something puts the word in jarr: a مضاف before it, or a preposition hung over it
    or written onto it (بِ، لِ)."""
    head = s.head(token)
    return token["rel"] == "IDF" or bool(head and is_preposition(head)) or any(is_preposition(k) for k in s.kids(token))


def place_case(token: dict, s: "Sentence") -> str | None:
    """The case a word stands in: the noun of لا النافية للجنس is built on fatha, but لا with its
    noun stands where a mubtada would, in raf' (لا إلهَ إلا اللهُ: اللهُ is its بدل)."""
    head = s.head(token)
    if head and subject_link(token) and read_as(head, "la_jins"):
        return "u"
    return typed_or_parsed_case(token)


def told_of_lone_mubtada(token: dict, head: dict, s: Sentence) -> bool:
    """الدينُ النصيحةُ: a verbless sentence resting on one noun with nothing else said of
    it, so the plain noun in its case after it is its khabar; a describing word
    (الطبيبُ الماهرُ) stays its صفة (Tasheel 1.4 p6). Made definite by its مضاف إليه
    (الطهورُ شطرُ الإيمانِ) it is a khabar too: a plain noun names a thing, it does not describe one."""
    plain_mudaf = token.get("stt") == "c" and token.get("pos_camel") == "noun" and not is_participle(token)
    return s.verbless and head["rel"] == "---" and noun_tagged(head) \
        and same_case(token, head) and (token.get("stt") == "d" or plain_mudaf) and token.get("ud") != "ADJ" \
        and [t for t in s.tokens if t["rel"] == "---"] == [head] \
        and all(k is token or k["rel"] == "IDF" for k in s.kids(head))


def verb_above(token: dict, s: Sentence) -> dict | None:
    """The verb the word hangs on, or the one its noun head hangs on (a hal, tamyeez or
    absolute object modifies the noun under a verb)."""
    head = s.head(token)
    if head and is_verb(head):
        return head
    up = s.head(head) if head else None
    return up if up and is_verb(up) else None


def next_word(token: dict, s: Sentence) -> dict | None:
    """The word after it, past a pronoun written onto it."""
    return next((t for t in s.tokens if t["id"] > token["id"] and not is_suffix(t)), None)


def previous_noun(token: dict, s: Sentence) -> dict | None:
    """The noun straight before this word, past any pronoun joined to that noun (أخو+ك)."""
    for t in sorted((t for t in s.tokens if t["id"] < token["id"]), key=lambda t: -t["id"]):
        if not is_suffix(t):
            return t if noun_tagged(t) and not is_verb(t) else None
    return None


def excepted_after_la(token: dict, s: Sentence) -> tuple[dict, dict, dict] | None:
    """(اسم لا, إلا, its entry) when the word is the name straight after لا, its noun, then إلا,
    and that noun is one roles.json `exception_after_la` lists (لا إله إلا الله); no word between
    them, so no khabar is written."""
    words = [t for t in s.tokens if t["id"] <= token["id"] and not is_suffix(t)]
    if len(words) < 4 or words[-1] is not token:
        return None
    la, noun, illa = words[-4:-1]
    listed = frames()["exception_after_la"]["by_noun"]
    entry = next((listed[k] for k in listed if bare_letters(k) == bare_letters(noun["form"])), None)
    if not (entry and read_as(la, "la_jins") and read_as(illa, "istithna")):
        return None
    return noun, illa, entry


def ma_kind(token: dict, s: Sentence) -> str | None:
    """What a ما with a verb hung on it after it is, by its عائد (مغني اللبيب، ما المصدرية):
    the relative's صلة holds a pronoun going back to it, ما المصدرية's never does. So "relative"
    while the verb has a place one could sit in: a هـ on it (أعجبني ما كتبتَه), a hidden هو for
    its doer (ما نفعك), an object it may take and lacks (أكلتُ ما طبختَ, the default when both
    readings stand). "masdar" when every place is taken by another word: its object written
    (أكره ما يهمل الطلابُ دروسَهم), a passive's نائب فاعل written (بما تُرِكَ العملُ), or a verb
    that takes no object (intransitive_verbs) with its doer written (سرّني ما قمتَ). None: no verb."""
    if strip_diacritics(token["form"]) != "ما":
        return None
    verb = next((t for t in s.kids(token) if t["id"] > token["id"] and is_verb(t)), None)
    if not verb:
        return None
    kids = s.kids(verb)
    pronouns = [t for t in kids if is_suffix(t) and t.get("pos_camel") == "pron"]
    if any(strip_diacritics(t["form"]).strip("+") == "ه" for t in pronouns):  # the هـ that goes back to ما
        return "relative"
    named = [t for t in kids if t["rel"] in ("SBJ", "OBJ") and not is_suffix(t) and not is_verb(t)]
    if is_passive(verb):
        return "masdar" if named else "relative"
    if not any(t["rel"] == "SBJ" for t in kids) and (verb.get("per"), verb.get("gen"), verb.get("num")) == ("3", "m", "s"):
        return "relative"
    if any(t["rel"] == "OBJ" for t in kids) or listed(verb, "intransitive_verbs"):
        return "masdar"
    return "relative"


def jarr_takes(token: dict, s: Sentence) -> bool:
    """A preposition works only on the noun straight after it (Tasheel 1.7 p18): a second
    noun the parser hung on it (لله الحمدُ) is not its majrur."""
    head = s.head(token)
    if not (token["rel"] == "OBJ" and head and not is_called_noun(head) and is_preposition(head)):
        return False  # إلا، و: a particle that is no preposition takes no majrur
    if is_one(head["lemma"], "jarr", "oath_only") and not head.get("reading") and any(
            t["pos"] in ("NOM", "PROP", "VRB", "VRB-PASS") and t["id"] < head["id"] for t in s.tokens):
        return False  # the و of an oath opens its clause; after a word it joins
    return not any(noun_tagged(t) and head["id"] < t["id"] < token["id"] for t in s.tokens)
