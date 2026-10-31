"""One parsed sentence with its lookups built once, and the few questions that need it
but belong to no single axis: the verb above a word, the noun before it, what a jarr takes."""
from __future__ import annotations

from backend.services.text.arabic_text import bare_letters
from backend.services.nahw.book import doer_written_in, extra_ba_on, frames, is_extra_ba, is_mabni, is_one, is_subject_pronoun
from backend.services.text.arabic_text import strip_diacritics
from backend.services.nahw.syntax.facts.word import SUBJECTS, is_passive, listed, NOUN_LINKS, is_prefix, is_suffix, is_called_noun, is_light, is_preposition, is_verb, read_as, same_case, typed_or_parsed_case, noun_tagged, is_participle, describes, is_name, present_verb_tagged, subject_link, attached_pronoun, holds_doer, own_doer


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


def khabar_behind_ba(ba: dict, noun: dict) -> bool:
    """مَا اللَّهُ بِغَافِلٍ، لَسْتُ بِغَافِلٍ: a زائدة باء written onto the khabar of ما or ليس (Ibn Aqil on
    وبعد ما وليس جرّ البا الخبر); a word with ال after the باء, unless a participle, is a plain
    jar-majrur (ما زيدٌ بالبيت), while an annexed one is the khabar still (أَلَسْتُ بِرَبِّكُمْ)."""
    return is_prefix(ba) and is_extra_ba(ba["form"]) and noun_tagged(noun) \
        and (noun.get("stt") != "d" or is_participle(noun))


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
        A verb before it (قَالَ مَا اسْمُكَ) leaves the asked clause verbless; one after it does not.
        One in jarr is no mubtada (لِمَنْ هذا الكتابُ: the جار ومجرور is the fronted khabar)."""
        words = [t for t in self.tokens if not is_suffix(t)]
        return next(((asked, told) for asked, told in zip(words, words[1:])
                     if not any(is_verb(t) for t in words[words.index(asked):]) and not puts_in_jarr(asked, self)
                     and read_as(asked, "istifham") and is_one(asked["lemma"], "istifham", "heads")
                     and told["pos"] == "NOM" and not is_preposition(told)), None)  # ما ذاهبٌ المسلمون: ما negates

    def _hijazi(self) -> tuple[dict, dict, dict] | None:
        """(ما, its ism, its khabar) of ما الحجازية, which works like ليس (Tasheel 1.9 n6
        p23): a verbless sentence opening ما, a noun, then an indefinite noun in nasb."""
        words = [t for t in self.tokens if not is_suffix(t)]
        while words and is_prefix(words[0]):
            words.pop(0)  # وَما زيدٌ قائمًا: a وَ or فَ written onto it opens nothing else
        # its ism is marfu': ما أحسنَ زيدًا is the ما of wonder; the fatha of a built أنتَ is no nasb
        if not (self.verbless and len(words) >= 3 and words[0]["lemma"] == "ما" and noun_tagged(words[1])
                and (is_mabni(words[1].get("pos_camel", "")) or typed_or_parsed_case(words[1]) != "a")):
            return None
        # a noun straight after a مضاف is its مضاف إليه, never the khabar: ما عِقَابُ إِبْرَاهِيمَ asks
        khabar = next((t for before, t in zip(words[1:], words[2:]) if noun_tagged(t) and t.get("stt") == "i"
                       and before.get("stt") != "c" and typed_or_parsed_case(t) == "a"), None)
        # مَا اللَّهُ بِغَافِلٍ: its khabar may stand behind a زائدة باء, jarr in its letters (data:
        # closed_words extra_ba `on`); a word with ال after the باء is a plain jar-majrur (ما زيدٌ بالبيت)
        if not khabar and extra_ba_on(words[0]["lemma"]) and len(words) >= 4 and khabar_behind_ba(words[2], words[3]):
            khabar = words[3]
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
    (الطبيبُ الماهرُ، الطالبُ المجتهدُ: one tagged a noun too) stays its صفة when it agrees with it (`describes`; Tasheel 1.4 p6). Made definite by its مضاف إليه
    (الطهورُ شطرُ الإيمانِ) it is a khabar too: a plain noun names a thing, it does not describe one, and one of
    a participle's shape no less (زيدٌ صاحبُ المالِ): the two parts alike definite, the first is the mubtada
    (Ibn Aqil V1 p232: زيد أخوك). So is a name, definite by itself whatever its tanween (أخوك زيدٌ)."""
    plain_mudaf = token.get("stt") == "c" and token.get("pos_camel") == "noun"
    return s.verbless and head["rel"] == "---" and noun_tagged(head) \
        and same_case(token, head) and (token.get("stt") == "d" or plain_mudaf or is_name(token)) and token.get("ud") != "ADJ" and not (token.get("stt") == "d" and describes(token, head)) \
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


def busied(verb: dict, s: Sentence) -> bool:
    """زَيْدًا ضَرَبْتُهُ، زَيْدًا مَرَرْتُ بِهِ: the verb works on a pronoun of its own, by itself or through a
    جار, or on a word the pronoun is added to (its سببي: زَيْدًا ضَرَبْتُ غُلَامَهُ، غُلَامَ صَاحِبِهِ، مَرَرْتُ بِغُلَامِهِ),
    so a noun in nasb put before it is not its object (الاشتغال, Ibn Aqil V2 p128: أو في سببيه وهو المضاف
    إلى ضمير الاسم السابق). The سببي must be in nasb or jarr by it: typed with its damma it is the doer (زَيْدًا ضَرَبَ
    غُلَامُهُ), and زيدًا stays the object put first. The pronoun is one of the one away, as that noun is (رَبَّنَا
    ظَلَمْنَا أَنْفُسَنَا: نا is the speakers', and ربنا is called)."""
    return any((_absent_pronoun(k) and not subject_link(k))
               or ((is_preposition(k) or (k["rel"] == "OBJ" and typed_or_parsed_case(k) != "u")) and _reaches_pronoun(k, s))
               for k in s.kids(verb))


def _reaches_pronoun(word: dict, s: Sentence) -> bool:
    """A pronoun hangs below the word through its مجرور or مضاف إليه, however deep (غلامِ صاحبِه)."""
    seen, below = set(), [word]
    while below:
        if (at := below.pop())["id"] in seen:
            continue
        seen.add(at["id"])
        for kid in s.kids(at):
            if kid["rel"] in ("OBJ", "IDF"):
                if _absent_pronoun(kid):
                    return True
                below.append(kid)
    return False


def _absent_pronoun(token: dict) -> bool:
    """+هُ، +هَا، +هُمْ: a pronoun written on that can stand for a noun said before it (closed_words damir_muttasil absent)."""
    return attached_pronoun(token) and is_one(token["form"], "damir_muttasil", "absent")


def next_word(token: dict, s: Sentence) -> dict | None:
    """The word after it, past a pronoun written onto it."""
    return next((t for t in s.tokens if t["id"] > token["id"] and not is_suffix(t)), None)


def previous_noun(token: dict, s: Sentence) -> dict | None:
    """The noun straight before this word, past any pronoun joined to that noun (أخو+ك)."""
    for t in sorted((t for t in s.tokens if t["id"] < token["id"]), key=lambda t: -t["id"]):
        if not is_suffix(t):
            return t if noun_tagged(t) and not is_verb(t) else None
    return None


def is_known(token: dict, s: Sentence) -> bool:
    """معرفة: a noun with ال, a name, a pronoun, or a مضاف to a known noun (جميعُهم، كتابُ اللهِ);
    a مضاف to an unknown one stays unknown (كتابُ رجلٍ)."""
    if token.get("stt") == "d" or token["pos"] == "PROP":
        return True
    added = next((k for k in s.kids(token) if k["rel"] == "IDF"), None) if token.get("stt") == "c" else None
    return bool(added) and is_known(added, s)


def excepted_from(illa: dict, s: Sentence) -> dict | None:
    """The مستثنى منه: the noun before إلا, out of any جار ومجرور or إضافة that only adds to a noun
    (ما جاء أحدٌ من الضيوف إلا زيدٌ: زيدٌ is excepted from أحد, not from الضيوف). A جار hung on a verb
    adds to no noun, so its majrur is the one excepted from (ما مررت بأحدٍ إلا زيدٍ)."""
    noun = previous_noun(illa, s)
    while noun and (up := s.head(noun)):
        holder = up if noun["rel"] == "IDF" else s.head(up) if noun["rel"] == "OBJ" and is_preposition(up) else None
        if not holder or not noun_tagged(holder) or is_verb(holder):
            break
        noun = holder
    return noun


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


def quoted_head(token: dict, s: Sentence) -> bool:
    """قال الضيفُ سلامٌ عليكم، قال زيدٌ الجوُّ جميلٌ: a verb has one doer (Tasheel 2.4.1), so a raf'
    word a verb of saying (roles.json said_clause) holds after its doer is no second one but heads
    the sentence it says, its مقول القول, named inside as that sentence would be on its own.
    قُلْ هُوَ اللَّهُ أَحَدٌ: a command's doer is the hidden أنت, so it holds one before any word.
    قال إبراهيمُ أنا أكسرُ: a detached pronoun of raf' is raf' by its own form, untyped or not.
    قُلْتُ أَنَا ذَاهِبٌ: a verb of the first or second person holds its doer in itself (its تاء)."""
    head = s.head(token)
    return (token["rel"] == "OBJ" and (typed_or_parsed_case(token) == "u" or is_subject_pronoun(token)) and head is not None and is_verb(head)
            and head["id"] < token["id"] and strip_diacritics(head["lemma"]) in frames()["said_clause"]["verbs"]
            and (own_doer(head) or holds_doer(head, (t for t in s.kids(head) if t is not token and t["id"] < token["id"]))))
