"""One parsed sentence with its lookups built once, and the few questions that need it
but belong to no single axis: the verb above a word, the noun before it, what a jarr takes."""
from __future__ import annotations

from backend.services.text.arabic_text import bare_letters
from backend.services.nahw.book import ADVERB_FAMILIES, doer_written_in, extra_ba_on, frames, is_built_word, is_definite_kind, is_extra_ba, is_mabni, is_one, is_subject_pronoun, only_adverb, says, takes_object
from backend.services.text.arabic_text import strip_diacritics
from backend.services.nahw.syntax.facts.word import SUBJECTS, case_unseen, is_passive, listed, NOUN_LINKS, is_prefix, is_suffix, is_called_noun, is_light, is_preposition, is_verb, read_as, same_case, typed_or_parsed_case, noun_tagged, is_participle, describes, is_built, works_as_verb, typed_bare, typed_case_of, indefinite_nasb, purpose, is_name, present_verb_tagged, subject_link, attached_pronoun, holds_doer, may_be_nasb


def praised_noun(token: dict, s: "Sentence") -> bool:
    """نِعْمَ الْخُلُقُ الْوَفَاءُ، بِئْسَ الْخُلُقُ الْكَذِبُ: a verb of praise or blame (closed_words
    praise_blame) has one doer, the noun with ال straight after it; the raf' noun after that is
    the one praised or blamed (المخصوص), the مبتدأ of a sentence of its own, whether the parser
    hung it on the verb as a second subject or on the doer as its modifier. The follows axis
    and the slot both ask this, so neither calls it a صفة or a second doer."""
    head = s.head(token)
    if not head or typed_case_of(token) not in (None, "u") or not noun_tagged(token):
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


def extra_min_place(min_: dict, s: "Sentence") -> str | None:
    """مِن الزائدة (closed_words extra_min): after a negation or هل, مِن before an indefinite noun holding a place of its own.
    The place, a roles.json id: `mubtada` with no verb over it (ما لكم من إلهٍ), `fail` on كان and its sisters or a verb of coming
    with no doer said (ما كان له من وليٍّ، ما جاءنا من بشيرٍ), `mafool_bih` on one taking an object whose doer is said (ما اتخذ الله من ولدٍ، هل ترى من فطورٍ).
    None for a plain مِن: hung on a noun (شيءٌ من طعامٍ), before a known noun, or where the doer may be the verb's
    hidden pronoun and the مِن starts a place (لم يخرج من بيتٍ)."""
    if not (is_preposition(min_) and is_one(min_["lemma"], "extra_min")):
        return None
    noun, head = extra_min_noun(min_, s), s.head(min_)
    # the negation (ليس too) or هل is said in the مِن's own clause: no other verb, relative or إلا between (لا أعرف ما في الدار من متاعٍ)
    over = [t for t in s.tokens if t["id"] < min_["id"] and (is_one(t["lemma"], "extra_min", "asks") or (t["pos"] == "PRT" or is_verb(t))
            and is_one(t["lemma"], "negation") and not read_as(t, "inna") and not opens_condition(t, s)) and not any(t["id"] < b["id"] < min_["id"] and (
            is_verb(b) and b is not head or "pron_rel" in b.get("pos_camel", "") or is_one(b["lemma"], "istithna")) for b in s.tokens)]
    # its noun is an indefinite one that takes a case: never a built word or adverb (لم يأت من قبلُ، من هناك)
    if not noun or is_known(noun, s) or is_built(noun) or is_built_zarf(noun) or noun.get("pos_camel", "").startswith("adv") or not over:
        return None
    if not head or not is_verb(head):
        # a ظرف holds the khabar put first (ما عندي من مالٍ); any other noun the مِن is hung on is told of by it
        return None if head and noun_tagged(head) and not is_zarf(head, s) else "mubtada"
    kids = [k for k in s.kids(head) if k is not min_]
    # a doer said, or one hidden that goes back to the مبتدأ the verb tells of (زيدٌ لم يكن من قريةٍ), unless a
    # pronoun on the verb is the one going back (زيدٌ ما جاءه من أحدٍ)
    told = s.head(head)
    doer = any(k["rel"] == "SBJ" and noun_tagged(k) for k in kids) or head.get("per") in ("1", "2") or bool(
        told and told["head"] == 0 and told["id"] < head["id"] and noun_tagged(told) and not any(attached_pronoun(k) for k in kids))
    # كان and its sisters say their اسم there (ما كان له من وليٍّ، ليس لي من مالٍ), and a verb of coming its doer,
    # with an object or none (ما جاءنا من بشيرٍ، وما تسقط من ورقةٍ); the family names the place
    if not doer and (s.family(head) == "kana" or is_one(head["lemma"], "extra_min", "comes")):
        return "fail"
    if any(k["rel"] == "OBJ" for k in kids):
        return None
    # a verb of coming or taking from has مِن as its own, where from (ما نزل من سماءٍ مطرٌ، ما أخذت من صديقٍ)
    own = is_one(head["lemma"], "extra_min", "comes") or is_one(head["lemma"], "extra_min", "from")
    return "mafool_bih" if doer and takes_object(head["lemma"]) and not own else None


def opens_condition(token: dict, s: "Sentence") -> bool:
    """إنْ the شرط (إن جاءك رجلٌ فأكرمه): a verb right after it and no إلا later, which marks the negating إنْ (إن يتبعون إلا الظن)."""
    after = s.by_id.get(token["id"] + 1)
    return is_one(token["lemma"], "jazm", "conditional_particles") and bool(after) and is_verb(after) \
        and not any(t["id"] > token["id"] and is_one(t["lemma"], "istithna") for t in s.tokens)


def extra_min_noun(min_: dict, s: "Sentence") -> dict | None:
    """The noun a مِن draws, a word of its own (not a pronoun joined to it)."""
    return next((k for k in s.kids(min_) if k["rel"] == "OBJ" and noun_tagged(k) and not is_suffix(k)), None)


def extra_min_of(noun: dict, s: "Sentence") -> dict | None:
    """The زائدة مِن the noun comes after, which stands (with it) in the noun's place: ما جاءنا من بشيرٍ."""
    min_ = s.head(noun)
    return min_ if min_ and noun["rel"] == "OBJ" and extra_min_place(min_, s) else None


def extra_min_case(noun: dict, s: "Sentence") -> str | None:
    """The case the noun after a زائدة مِن stands in by its place (raf' as a مبتدأ or فاعل, nasb as an object), beside
    the jarr it shows; its تابع may wear either (Mughni, مِن الزائدة: هل من خالقٍ غيرُ الله, غيرُ on the place)."""
    min_ = s.head(noun)
    place = extra_min_place(min_, s) if min_ and noun["rel"] == "OBJ" else None
    return ("a" if place == "mafool_bih" else "u") if place else None


class Sentence:
    """One parsed sentence with its lookups built once; every axis asks it and none rebuilds them."""

    def __init__(self, tokens: list[dict]):
        self.tokens = tokens
        self.refresh()

    def refresh(self) -> None:
        """Read the tokens again, every lookup: for a change of more than links (a retag)."""
        tokens = self.tokens
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
                     # أُمُّهُ: a word the parser reads a plain noun is no particle, though its letters spell أَمْ
                     if (is_one(lead["lemma"], "negation") or is_one(lead["lemma"], "istifham")) and lead.get("pos_camel") != "noun"
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
        One in jarr is no mubtada (لِمَنْ هذا الكتابُ: the جار ومجرور is the fronted khabar). The indefinite
        nasb noun after كم is its tamyeez, not what is told of it (كَمْ وَلَدًا فِي الْحَدِيقَةِ)."""
        words = [t for t in self.tokens if not is_suffix(t)]
        # مَنِ الَّذِي يَضْمَنُ: the verb in a relative's صلة is no verb of the clause
        return next(((asked, told) for asked, told in zip(words, words[1:])
                     if not any(is_verb(t) for t in words[words.index(asked):] if t["id"] not in self.below(told) or not listed(told, "mawsul"))
                     and not puts_in_jarr(asked, self)
                     and read_as(asked, "istifham") and is_one(asked["lemma"], "istifham", "heads")
                     and told["pos"] == "NOM" and not is_preposition(told)
                     and not (listed(asked, "tamyeez_head") and indefinite_nasb(told))), None)  # ما ذاهبٌ المسلمون: ما negates

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

    def relink(self, token: dict, head: int, rel: str) -> None:
        """Hang the token on the word with id `head` as `rel`, and keep the lookups that follow the links in step.
        The kid lists are replaced, never edited, so a loop already walking one finishes on the links it started with."""
        self._kids[token["head"]] = [k for k in self._kids.get(token["head"], []) if k is not token]
        token["head"], token["rel"] = head, rel
        kids = self._kids.get(head, [])
        self._kids[head] = [*(k for k in kids if k["id"] < token["id"]), token, *(k for k in kids if k["id"] > token["id"])]
        self._family.clear()
        self.asked_pair = self._asked_pair()

    def climb(self, token: dict | None, stop) -> dict | None:
        """The first word at or above `token` that `stop` accepts. None when the climb runs past the root;
        a word already met (links that loop) ends it there, as no word above it would be new."""
        seen = set()
        while token and not stop(token) and token["id"] not in seen:
            seen.add(token["id"])
            token = self.head(token)
        return token

    def kids(self, token: dict) -> list[dict]:
        return self._kids.get(token["id"], [])

    def below(self, token: dict) -> set[int]:
        """The ids of every word hung under the token, at any depth."""
        found, queue = set(), [token]
        while queue:
            for kid in self.kids(queue.pop()):
                if kid["id"] not in found:
                    found.add(kid["id"])
                    queue.append(kid)
        return found

    def family(self, word: dict) -> str | None:
        """Which family a governing word belongs to: inna, kana, kaada or zanna."""
        if word["id"] not in self._family:
            self._family[word["id"]] = self._family_of(word)
        return self._family[word["id"]]

    def _has_particle(self, verb: dict, family: str, part: str = "words") -> bool:
        return any(k["pos"] == "PRT" and is_one(k["lemma"], family, part) for k in self.kids(verb))

    def _ma_before(self, verb: dict) -> bool:
        """دام governs only right after its ما (ما دمت حيا), whichever of the two the parser hung on the other."""
        before = self.by_id.get(verb["id"] - 1)
        return bool(before) and before["pos"] == "PRT" and is_one(before["lemma"], "kana", "like_laysa") \
            and (before["head"] == verb["id"] or verb["head"] == before["id"])

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
        if (is_one(lemma, "inna") and not is_light(word) and not self.one_word_after(word)) or read_as(word, "la_jins"):
            return "inna"
        if is_one(lemma, "kana", "like_laysa"):
            # ما alone works as ليس only as ما الحجازية; any other ما (ما اسمك) governs nothing
            return "kana" if self.hijazi and word is self.hijazi[0] else None
        # the other families are verbs: the noun عِلْمُهُ shares a lemma with عَلِمَ and governs nothing
        if not is_verb(word):
            return None
        if (is_one(lemma, "kana")
                or (is_one(lemma, "kana", "needs_negation") and self._has_particle(word, "negation"))
                or (is_one(lemma, "kana", "needs_ma") and self._ma_before(word))) \
                and not self._stands_alone(word):
            return "kana"
        # جَعَلَ زَيْدٌ يَكْتُبُ: a verb of starting governs a noun and a present verb; جَعَلَ مِنْ بَعْدِ قُوَّةٍ ضَعْفًا يَخْلُقُ: one with
        # an object of its own is the plain verb (جعل: made), and the present verb after it begins afresh
        if is_one(lemma, "kaada") and self._completed_by_present_verb(word) and not any(
                k["rel"] == "OBJ" and noun_tagged(k) and typed_or_parsed_case(k) != "u" for k in self.kids(word)):
            return "kaada"
        return "zanna" if is_one(lemma, "zanna") and self._two_objects(word) else None

    def _stands_alone(self, verb: dict) -> bool:
        """وَإِنْ كَانَ ذُو عُسْرَةٍ، أَصْبَحْنَا: with no خبر, كان and its sisters are تامة and take a
        فاعل like any verb (Ibn Aqil on كان التامة); كان في الدار رجل: the خبر may come first, a phrase.
        ليس is never تامة: it has no meaning of being without its خبر. فَمَنْ كَانَتْ هِجْرَتُهُ إِلَى دُنْيَا: a jar the
        parser hung on a known اسم describes nothing (a known noun takes no صفة), so it is the خبر (repair.kana_subject); a وَ joining a second اسم is none (مَا دَامَتِ السَّمَاوَاتُ وَالْأَرْضُ)."""
        kids = self.kids(verb)
        return not is_one(verb["lemma"], "kana", "always_defective") \
            and all(k["rel"] in SUBJECTS or k["pos"] == "PRT" and k["rel"] == "MOD" for k in kids) \
            and not any(k["rel"] in SUBJECTS and is_known(k, self) and any(
                j["rel"] == "MOD" and j["id"] > k["id"] and is_preposition(j)
                for j in self.kids(k)) for k in kids)

    def _two_objects(self, verb: dict) -> bool:
        """ظن الولدُ الأمرَ سهلًا: an object and a second word in nasb after it, or an أنّ
        clause standing for both (علمت أنّ الحق منتصر). تعلّمَ القرآنَ has one, and is a plain verb."""
        kids = self.kids(verb)
        first = next((k for k in kids if k["rel"] == "OBJ" and k["pos"] != "PRT"), None)
        if any(k["pos"] == "PRT" and is_one(k["lemma"], "inna") for k in kids):
            return True
        # رَأَيْتُ صَدِيقَكَ مُسْرِعًا: a verb with an everyday one-object sense (closed_words zanna `one_object`,
        # رأى of the eye) is read in it, so the word in nasb after its object is that object's حال
        if is_one(verb["lemma"], "zanna", "one_object"):
            return False
        # لَا تَتْرُكْ الدَّرْسَ خَوْفًا مِنَ التَّعَبِ: the second is what the first is said to be (أصلهما مبتدأ وخبر), so a masdar of
        # the heart giving the reason (its مفعول لأجله) is no second object, and the verb is the plain one of one object;
        # جَعَلَ مِنْ بَعْدِ ضَعْفٍ قُوَّةً ثُمَّ: nor a joining word the parser tags a noun
        return bool(first) and any(k["id"] > first["id"] and k["rel"] in ("OBJ", "MOD") and noun_tagged(k) and not read_as(k, "atf")
                                   and may_be_nasb(k) and not purpose(k, verb) for k in kids)

    def noun_before(self, particle: dict) -> bool:
        """The particle follows a noun it can join to, which an oath و does not: the noun it
        hangs on, or the noun straight before it (دخل المعلمُ فالطلابُ, ف hung on the verb)."""
        return any(before and before["id"] < particle["id"] and noun_tagged(before)
                   and not is_verb(before)
                   for before in (self.head(particle), self.by_id.get(particle["id"] - 1)))

    def one_word_after(self, particle: dict) -> bool:
        """ما جاء زيد لكن عمرو: a single word ends the sentence after the particle, so an inna sister has no خبر
        to be given: typed bare, the light لكن (Tasheel 1.8 p20) that joins that word is meant. Only a sister the
        books list as joining (closed_words atf)."""
        return (typed_bare(particle) and is_one(particle["lemma"], "atf")
                and sum(1 for t in self.tokens if t["id"] > particle["id"] and not is_suffix(t)) == 1)

    def negated_before(self, word: dict) -> bool:
        # إِنَّ لِلَّهِ تِسْعَةً ... إِلَّا وَاحِدًا: an إن the particle tree reads as إنّ denies nothing, so إلا excepts
        return any(t["pos"] == "PRT" and t["id"] < word["id"] and is_one(t["lemma"], "negation") and not read_as(t, "inna")
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
        and (is_built(head) or same_case(token, head)) and (token.get("stt") == "d" or plain_mudaf or is_name(token)) and token.get("ud") != "ADJ" and not (token.get("stt") == "d" and describes(token, head)) \
        and [t for t in s.tokens if t["rel"] == "---"] == [head] \
        and all(k is token or k["rel"] == "IDF" or _in_silah(k, head, token) for k in s.kids(head))


def _in_silah(kid: dict, relative: dict, told: dict) -> bool:
    """A word between a relative and what is told of it is its صلة, one noun with it
    (الموصول وصلته كالكلمة الواحدة): اَلَّتِي فِي الْبَيْتِ أُمِّي, في البيت is no second thing said."""
    return listed(relative, "mawsul") and relative["id"] < kid["id"] < told["id"]


def at_work(word: dict, s: Sentence) -> str | None:
    """works_as_verb, for a word working on the noun after it: a verb always; an indefinite participle only
    leaning on something, a khabar, a صفة, a حال, or a question or negation before it (Ibn Aqil V3 p106:
    وولي استفهاما او حرف ندا او نفيا او جا صفة او مسندا), and one with ال whatever its place. One that is
    itself a verb's doer or object leans on nothing: قابلتُ مسافرةً صبورةً, so صبورة is its صفة, never its object."""
    if not (kind := works_as_verb(word)) or is_verb(word):
        return kind
    above = s.head(word)
    leans = word.get("stt") == "d" or not (above and is_verb(above) and word["rel"] in NOUN_LINKS)
    return kind if leans else None


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
               or ((is_preposition(k) or (k["rel"] == "OBJ" and typed_or_parsed_case(k) != "u")) and reaches_pronoun(k, s))
               for k in s.kids(verb))


def reaches_pronoun(word: dict, s: Sentence) -> bool:
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


def describable_nouns(token: dict, s: Sentence) -> list[dict]:
    """The nouns a word after its describing words may belong to: the noun straight before, the noun each صفة already hung on it
    describes (التقرير السنوي الذي أصدرته: الذي describes التقرير, Tasheel 3.10.1: النعت يتبع المنعوت), and the مضاف a مضاف إليه is added to
    (أرشيف المكتبة الوطنية الذي أسس: the archive was founded, not the library); the parser's link says which of them."""
    nouns = []
    noun = previous_noun(token, s)
    while noun:
        nouns.append(noun)
        up = s.head(noun)
        if not (noun["rel"] in ("MOD", "IDF") and up and up["id"] < noun["id"] and noun_tagged(up) and not is_verb(up)):
            break
        noun = up
    return nouns


def is_known(token: dict, s: Sentence) -> bool:
    """معرفة, the one reading of "is this noun definite" (Tasheel V1 p21: مضمر وعلم ومشار به وموصول ومضاف وذو أداة): a noun
    with ال, a name, a pronoun, pointer or relative (CAMeL files many of these and every name indefinite, stt "i", so its
    stt is read only for ال; a name CAMeL only guessed, "backoff", is no evidence, it files any unknown word a name), or a
    مضاف to a known noun (جميعُهم، كتابُ اللهِ). A مضاف to an unknown one stays unknown
    (Ibn Aqil V3 p43: it narrows the first, makes it definite only when the second is: غلام امرأة، غلام زيد)."""
    if token.get("stt") == "d" or (is_name(token) and not token.get("guessed")) or is_definite_kind(token.get("pos_camel", "")):
        return True
    # a pronoun written onto a noun is its مضاف إليه, however the parser linked it (وَلِيُّ+كُمْ: OBJ)
    added = next((k for k in s.kids(token) if k["rel"] == "IDF" or attached_pronoun(k)), None) if token.get("stt") == "c" else None
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


def after_illa(token: dict, s: Sentence) -> bool:
    """The word written just before it is إلا of the exception (ما قام أحدٌ إلا زيدٌ)."""
    words = [t for t in s.tokens if t["id"] < token["id"] and not is_suffix(t)]
    return bool(words) and read_as(words[-1], "istithna")


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
    while the verb has a place one could sit in: a هـ on it or on its jar (أعجبني ما كتبتَه, سأنبئك بتأويل ما لم تستطع عليه صبرا), a hidden هو for
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
    # the verb's own pronouns, and those of the jar it holds (استطعتَ عليه)
    pronouns = [t for k in kids for t in ([k] if is_suffix(k) else s.kids(k) if is_preposition(k) else []) if is_suffix(t) and t.get("pos_camel") == "pron"]
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


def said_verb(token: dict, s: Sentence) -> bool:
    """قال المعلمُ لِيَكْتُبُوا دروسَهم: a verb a verb of saying (roles.json said_clause) holds after it opens
    the sentence it says, its مقول القول, as if nothing stood before it (facts.lam_mood: لام الأمر)."""
    head = s.head(token)
    return (token["rel"] == "OBJ" and is_verb(token) and head is not None and is_verb(head)
            and head["id"] < token["id"] and says(head["lemma"]))


def quoted_head(token: dict, s: Sentence) -> bool:
    """قال الضيفُ سلامٌ عليكم، قال زيدٌ الجوُّ جميلٌ: a verb has one doer (Tasheel 2.4.1), so a raf'
    word a verb of saying (roles.json said_clause) holds after its doer is no second one but heads
    the sentence it says, its مقول القول, named inside as that sentence would be on its own.
    قُلْ هُوَ اللَّهُ أَحَدٌ: a command's doer is the hidden أنت, so it holds one before any word.
    قال إبراهيمُ أنا أكسرُ: a detached pronoun of raf' is raf' by its own form, untyped or not.
    قُلْتُ أَنَا ذَاهِبٌ: a verb of the first or second person holds its doer in itself (its تاء)."""
    head = s.head(token)
    return (token["rel"] == "OBJ" and (typed_or_parsed_case(token) == "u" or is_subject_pronoun(token)) and head is not None and is_verb(head)
            and head["id"] < token["id"] and says(head["lemma"])
            and holds_doer(head, (t for t in s.kids(head) if t is not token and t["id"] < token["id"])))


def is_zarf(token: dict, s: Sentence) -> bool:
    """A listed time or place word, or كل/بعض or a number counting one (كلَّ يومٍ، عشرَ سنينَ، أَرْبَعِينَ لَيْلَةً): the number
    stands in for the ظرف it counts (Awdah al-Masalik V2 p231, باب المفعول فيه: أسماء العدد المميزة بهما، سرت عشرين يوما)."""
    if token["pos"] == "PRT":
        return False
    if any(listed(token, family) for family in ADVERB_FAMILIES):
        return True
    return (listed(token, "zarf_zaman", "carriers") or counts(token)) and any(
        k["rel"] in ("IDF", "TMZ") and any(listed(k, family) for family in ADVERB_FAMILIES) for k in s.kids(token))


def counts(token: dict) -> bool:
    """A number (3 to 10 and the hundred added to what they count; 11 to 99 followed by their تمييز, compound
    ones too), not a measure word (رطل)."""
    return (listed(token, "adad_mudaf") or listed(token, "compound_number")
            or (listed(token, "tamyeez_head") and not listed(token, "tamyeez_head", "measures")))


def zarf_in_nasb(token: dict, s: Sentence) -> bool:
    """بَيْنَ الطَّرَفَيْنِ، بَعْدَ الْفَتْحِ: a listed time or place word hung as a modifier, vowelled with a fatha or a case that
    shows nothing (ين), or bare where it is a place word added to a noun of its own (وقف التصعيد بين الطرفين, بعد الفتح,
    بيننا): no other word of the books' lists is spelled so, and a noun's نعت or مضاف إليه is not put in nasb, so it is the zarf
    (Tasheel 3.2 p67). Not a built word (أَيْنَ الْكِتَابُ: the khabar), one whose case is unseen (الْيَدُ الْعُلْيَا: a صفة), nor what a number counts
    (ثَلَاثِ سِنِينَ: the number's مضاف إليه)."""
    bare_place = typed_bare(token) and only_adverb(token["lemma"]) and listed(token, "zarf_makan")         and any(k["rel"] == "IDF" for k in s.kids(token))
    return (token["rel"] in ("MOD", "IDF") and may_be_nasb(token, typed_only=True) and (bare_place or not typed_bare(token))
            and not is_built(token) and not case_unseen(token) and is_zarf(token, s)
            and not (s.head(token) and listed(s.head(token), "adad_mudaf")))


def is_cut_off(token: dict) -> bool:
    """أَمَّا بَعْدُ، مِنْ قَبْلُ: قبل، بعد and the directions typed on the damma with nothing added to them are built
    (closed_words zarf_zaman `cut_off`; Ibn Aqil V3 p73)."""
    return (token["pos"] != "PRT" and typed_case_of(token) == "u" and not token.get("mudaf")
            and listed(token, "zarf_zaman", "cut_off"))


def stays_adverb(token: dict) -> bool:
    """قط، عوض (closed_words zarf_zaman `never_leaves`) and a قبل/بعد cut off: words that are never a doer, mubtada,
    khabar or اسم كان; with ال it is a plain noun (الْقِطُّ the cat)."""
    return token["pos"] != "PRT" and token.get("stt") != "d" and (listed(token, "zarf_zaman", "never_leaves") or is_cut_off(token))


def is_built_zarf(token: dict) -> bool:
    """أمسِ، حيثُ، الآن: a time or place word built on one ending (closed_words `built`), or one cut off from its مضاف إليه."""
    return token["pos"] != "PRT" and (is_built_word(token["lemma"]) or is_cut_off(token))
