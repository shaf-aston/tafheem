"""One parsed sentence with its lookups built once, and the few questions that need it
but belong to no single axis: the verb above a word, the noun before it, what a jarr takes."""
from __future__ import annotations

from backend.services.nahw_book import is_one
from backend.services.syntax.facts.word import is_prefix, is_suffix, is_called_noun, is_light, is_preposition, is_verb, read_as, same_case, typed_or_parsed_case


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

    def _hijazi(self) -> tuple[dict, dict, dict] | None:
        """(ما, its ism, its khabar) of ما الحجازية, which works like ليس (Tasheel 1.9 n6
        p23): a verbless sentence opening ما, a noun, then an indefinite noun in nasb."""
        words = [t for t in self.tokens if not is_suffix(t)]
        while words and is_prefix(words[0]):
            words.pop(0)  # وَما زيدٌ قائمًا: a وَ or فَ written onto it opens nothing else
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
        if (is_one(lemma, "inna") and not is_light(word)) or read_as(word, "la_jins"):
            return "inna"
        if is_one(lemma, "kana", "like_laysa"):
            # ما alone works as ليس only as ما الحجازية; any other ما (ما اسمك) governs nothing
            return "kana" if self.hijazi and word is self.hijazi[0] else None
        # the other families are verbs: the noun عِلْمُهُ shares a lemma with عَلِمَ and governs nothing
        if not is_verb(word):
            return None
        if is_one(lemma, "kana") \
                or (is_one(lemma, "kana", "needs_negation") and self._has_particle(word, "negation")) \
                or (is_one(lemma, "kana", "needs_ma") and self._has_particle(word, "kana", "like_laysa")):
            return "kana"
        if is_one(lemma, "kaada") and self._completed_by_present_verb(word):
            return "kaada"
        return "zanna" if is_one(lemma, "zanna") and self._two_objects(word) else None

    def _two_objects(self, verb: dict) -> bool:
        """ظن الولدُ الأمرَ سهلًا: an object and a second word in nasb after it, or an أنّ
        clause standing for both (علمت أنّ الحق منتصر). تعلّمَ القرآنَ has one, and is a plain verb."""
        kids = self.kids(verb)
        first = next((k for k in kids if k["rel"] == "OBJ" and k["pos"] != "PRT"), None)
        if any(k["pos"] == "PRT" and is_one(k["lemma"], "inna") for k in kids):
            return True
        return bool(first) and any(k["id"] > first["id"] and k["rel"] in ("OBJ", "MOD") and k["pos"] in ("NOM", "PROP")
                                   and typed_or_parsed_case(k) in (None, "a") for k in kids)

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
    if head and token["rel"] in ("SBJ", "TPC") and read_as(head, "la_jins"):
        return "u"
    return typed_or_parsed_case(token)


def told_of_lone_mubtada(token: dict, head: dict, s: Sentence) -> bool:
    """الدينُ النصيحةُ: a verbless sentence resting on one noun with nothing else said of
    it, so the plain noun in its case after it is its khabar; a describing word
    (الطبيبُ الماهرُ) stays its صفة (Tasheel 1.4 p6)."""
    return s.verbless and head["rel"] == "---" and head["pos"] in ("NOM", "PROP") \
        and same_case(token, head) and token.get("stt") == "d" and token.get("ud") != "ADJ" \
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
            return t if t["pos"] in ("NOM", "PROP") and not is_verb(t) else None
    return None


def jarr_takes(token: dict, s: Sentence) -> bool:
    """A preposition works only on the noun straight after it (Tasheel 1.7 p18): a second
    noun the parser hung on it (لله الحمدُ) is not its majrur."""
    head = s.head(token)
    if not (token["rel"] == "OBJ" and head and not is_called_noun(head) and is_preposition(head)):
        return False  # إلا، و: a particle that is no preposition takes no majrur
    if is_one(head["lemma"], "jarr", "oath_only") and not head.get("reading") and any(
            t["pos"] in ("NOM", "PROP", "VRB", "VRB-PASS") and t["id"] < head["id"] for t in s.tokens):
        return False  # the و of an oath opens its clause; after a word it joins
    return not any(t["pos"] in ("NOM", "PROP") and head["id"] < t["id"] < token["id"] for t in s.tokens)
