"""Axis `slot`: the word's place in its clause: subject, predicate, object, hal, tamyeez, zarf
and the rest, under a verb (verb_place) or in a verbless sentence (nominal_place)."""
from __future__ import annotations

from backend.services.text.arabic_text import strip_diacritics
from backend.services.nahw.book import book_map, extra_ba_on, is_extra_ba, is_built_word, is_mabni, is_one, is_plain_noun, named_roles, takes_object
from backend.services.nahw.syntax.facts.word import is_elative, is_name, is_suffix, works_as_verb, listed, indefinite_nasb, is_deputy, is_masdar, is_object_pronoun, is_participle, is_passive, is_preposition, is_state_word, is_verb, read_as, same_root, shows_jarr, state_or_specification, told_of_subject, typed_case_of, typed_or_parsed_case, unlike, attached_pronoun, noun_tagged, subject_link, holds_doer, own_doer, NOUN_LINKS, SUBJECTS
from backend.services.nahw.syntax.facts.sentence import Sentence, busied, jarr_takes, praised_noun, quoted_head, told_of_lone_mubtada, verb_above
from backend.services.nahw.syntax.facts.follows import verb_joined_by_waw

NAMED = named_roles()


def takes_tamyeez(token: dict, s: Sentence) -> bool:
    """A tamyeez stands after a number or a measure, or after a verb of tamyeez al-nisba or an
    elative, which tells in what way one thing passes another (أَثْقَلُ وَزْنًا), or after a verb of
    praise or blame, whose hidden doer it explains (نِعْمَ رَجُلًا زَيْدٌ)."""
    head = s.head(token)
    if head and (is_one(head["lemma"], "tamyeez_verbs") or is_one(head["lemma"], "praise_blame") or is_elative(head)):
        return True
    return any(listed(t, "tamyeez_head") for t in s.tokens if t["id"] < token["id"])


def _doer_by_extra_ba(token: dict, verb: dict) -> bool:
    """كَفَى بِاللَّهِ: the doer comes after a زائدة باء, hung on the verb as the book's rule says."""
    rule = extra_ba_on(verb["lemma"])
    return bool(rule and rule["role"] == NAMED.fail and token["rel"] == rule["rel"] and is_extra_ba(token["form"]))


def completes_kaada(token: dict, s: Sentence) -> bool:
    """The present verb that finishes a كاد-type verb; its clause is that verb's khabar."""
    head = s.head(token)
    return bool(head and is_verb(token) and s.family(head) == "kaada")


def is_zarf(token: dict, s: Sentence) -> bool:
    """A listed time or place word, or كل/بعض or a number added to one (كلَّ يومٍ، عشرَ سنينَ)."""
    if token["pos"] == "PRT":
        return False
    if listed(token, "zarf_zaman") or listed(token, "zarf_makan"):
        return True
    return (listed(token, "zarf_zaman", "carriers") or listed(token, "adad_mudaf")) and any(
        k["rel"] == "IDF" and (listed(k, "zarf_zaman") or listed(k, "zarf_makan")) for k in s.kids(token))


def is_built_zarf(token: dict) -> bool:
    """أمسِ، حيثُ، الآن: a time or place word built on one ending (closed_words `built`)."""
    return token["pos"] != "PRT" and is_built_word(token["lemma"])


def zarf_of_khabar(token: dict, s: Sentence) -> bool:
    """الأستاذُ عندَ البابِ: in a verbless sentence a place or time word with its mudaf ilayh
    is the khabar's maf'ul fihi (the khabar itself is understood, Tasheel 1.4.4 p13)."""
    # المرءُ مع مَن أحبّ: a verb inside the مضاف إليه's صلة still leaves the sentence verbless at its root
    rests = token["rel"] == "---" and any(k["rel"] in SUBJECTS for k in s.kids(token))
    return ((s.verbless or rests) and is_zarf(token, s) and "interrog" not in token.get("pos_camel", "")
            and token["rel"] in ("---", "MOD", "PRD")
            and typed_or_parsed_case(token) in (None, "a") and any(k["rel"] == "IDF" for k in s.kids(token)))


def place_time(token: dict, s: Sentence) -> bool:
    """A listed time or place word that is a verb's مفعول فيه (Tasheel 3.2 p67): it
    modifies the verb with no vowel or fatha (the parser may draw that as idafa), or it
    stands before its verb with the verb hanging off it (مَتَى سافر)."""
    if not is_zarf(token, s):
        return False
    head = s.head(token)
    if is_built_zarf(token) and head and is_verb(head) and token["rel"] in ("MOD", "IDF"):
        return True  # سافر أمسِ: its kasra is built in, so it says nothing of its case
    # مسافرٌ غدًا: a participle works like its verb
    # كُلَّمَا جَاءَ زَيْدٌ أَكْرَمْتُهُ: its own verb hung on it, whatever link it has to the verb above
    opens_verb = typed_or_parsed_case(token) in (None, "a") and any(
        is_verb(k) and k["id"] > token["id"] for k in s.kids(token))
    if head and works_as_verb(head) and (is_verb(head) or token["rel"] == "MOD"):
        return token["rel"] in ("MOD", "IDF") and typed_case_of(token) in (None, "a") or opens_verb
    return opens_verb


def _object_of_participle(token: dict, head: dict) -> bool:
    """A word hung on a participle that is its object: linked as one in nasb, or in the
    nasb the reader typed where the link cannot hold it, since a مضاف إليه is never منصوب
    (فاهمٌ الدرسَ) and a نعت has its noun's case (ضاربٌ بكرًا) and is a describing word
    (آمِرًا أحدًا: both in nasb, yet أحد describes nothing); with ال on both in the same nasb it
    follows as a نعت (إِنَّ الْمُهَنْدِسَ الْعَجُوزَ). An indefinite state word
    stays a حال (قادمٌ مسرعًا), and the participle's own root a مفعول مطلق. A diptote's fatha
    is its jarr, so it stays the مضاف إليه (طَرِيقَ جَهَنَّمَ). An elative takes none (Ashmuni V2 p312:
    أجمعوا على أنه لا ينصب المفعول به): its nasb noun is its تمييز (أَكْبَرُ مِنْكَ سِنًّا)."""
    if is_elative(head):
        return False
    rel, typed = token["rel"], typed_case_of(token)
    if rel == "OBJ":
        return typed_or_parsed_case(token) == "a"
    return typed == "a" and ((rel == "IDF" and not shows_jarr(token)) or (
        rel == "MOD" and (typed_or_parsed_case(head) != "a" or token.get("pos_camel") != "adj")
        and not (typed_or_parsed_case(head) == "a" and token.get("stt") == head.get("stt") == "d")
        and not is_state_word(token) and not same_root(token, head)))


def _doer_of_describer(token: dict, head: dict, s: Sentence) -> bool:
    """جاء رجلٌ كريمٌ أبوه، المسجدُ مفتوحٌ بابُه: a raf' noun straight after a participle or
    adjective, carrying a pronoun back to the noun described, is what that describer tells of:
    its فاعل, or its نائب فاعل after a passive participle (النعت السببي, Tasheel 3.10.1).
    The parser may hang it as the describer's مضاف إليه (الْبُسْتَانُ وَاسِعٌ أَشْجَارُهُ); a damma
    typed on it rules that out, since a مضاف إليه is never مرفوع."""
    return ((subject_link(token) or (token["rel"] == "IDF" and typed_case_of(token) == "u"))
            and token["id"] == head["id"] + 1
            and typed_or_parsed_case(token) == "u"
            and any(attached_pronoun(k) for k in s.kids(token)))


def stands_for_masdar(token: dict, verb: dict, s: Sentence) -> bool:
    """ضربتُه ثلاثَ مراتٍ، أحببتُه كلَّ الحبِّ: a word added to the verb's own masdar, or to the
    count of its doing, takes the masdar's place as its مفعول مطلق (النائب عن المصدر, Tasheel 3.2 p67):
    the number of times, كل or بعض. Added to any other noun it is the object (أكلتُ كلَّ الطعامِ)."""
    return any(k["rel"] == "IDF" and (listed(k, "times_counted") or (is_masdar(k) and same_root(k, verb)))
               for k in s.kids(token))


def purpose(token: dict, verb: dict) -> bool:
    """قام الطلاب احترامًا: a masdar of the heart (a feeling or intent, reason_masdars) not of its verb's root,
    in nasb and indefinite or a مضاف, gives the reason for the verb: its مفعول لأجله
    (Tasheel 3.8.3 p73). Any other masdar there is a حال (جاء ركضًا)."""
    return (listed(token, "reason_masdars") and not same_root(token, verb)
            and typed_or_parsed_case(token) in (None, "a") and token.get("stt") in ("i", "c"))


def wants_object(verb: dict, kids: list[dict], s: Sentence) -> bool:
    """An active verb of no family that takes a noun as its object (book.takes_object) and has none of its
    own, before it, after it or written on it: a describing word in nasb is that object, standing for the
    noun it describes, left out (Ibn Aqil V3 p205: يجوز حذف المنعوت وإقامة النعت مقامه … أن اعمل سابغات أي
    دروعا سابغات). So the Qur'an's مَنْ عَمِلَ صَالِحًا، وَمَنْ يَقْتُلْ مُؤْمِنًا, and a name the dictionary reads as
    a describing word: أكرم محمد خالدا. A verb with its object keeps the hal (شرب زيد الماء باردا), as one that
    seldom takes a noun does (جاء زيد راكبا، فَتَقْعُدَ مَذْمُومًا) and a passive (قُتِلَ مَظْلُومًا)."""
    return (not is_passive(verb) and s.family(verb) is None and takes_object(verb["lemma"])
            and not any(k["rel"] == "OBJ" for k in kids))


def busied_before(token: dict, s: Sentence) -> bool:
    """زَيْدًا ضَرَبْتُهُ، زَيْدًا مَرَرْتُ بِهِ: the word comes before a verb busied with a pronoun of its own (facts.busied),
    so the verb that works on it is one like that verb, left out (الاشتغال, Ibn Aqil V2 p128: فالسابق انصبه بفعل
    أضمرا حتما موافق لما قد أظهرا). A participle doing its verb's work is busied the same (V2 p142: وسوِّ في ذا
    الباب وصفا ذا عمل بالفعل، زيدًا أنا ضاربُه الآن)."""
    head = s.head(token)
    return head is not None and works_as_verb(head) is not None and token["id"] < head["id"] and busied(head, s)


def verb_place(token: dict, s: Sentence) -> str:
    """The place a word fills under a verb (Tasheel 3.1 p60, 3.2 p67), `none` where the
    book names it elsewhere. Tested in this order because an earlier place shadows a
    later one of the same word: a listed time or place word is a مفعول فيه whatever its
    link; an indefinite word after a verb that already has its doer is not an argument
    but a tamyeez (after a tamyeez verb, not a participle) or a hal (a participle); a
    second OBJ after the first is the second object; only then is the argument itself
    told by the vowel the reader typed (damma subject, fatha object), else by the link;
    last, an indefinite word in nasb modifying a verb or the noun under it is an
    absolute object (same root), a hal or a tamyeez."""
    if place_time(token, s):
        return "place_time"
    if s.head(token) and listed(token, "verbless_masdars") and token.get("stt") == "i" and typed_or_parsed_case(token) in (None, "a"):
        return "absolute"  # مجتهداتٌ جِدًّا: a heard masdar whose verb is never said (جَدَّ جِدًّا); a lone one (شكرًا) gets its drawn verb (understood.verb)
    if is_object_pronoun(token):
        return "object"  # إيّاك نعبد، ما عبدنا إلا إيّاه: the detached pronoun of nasb is only an object
    if verb_joined_by_waw(token, s):
        return "accompaniment"
    head = s.head(token)
    rel = token["rel"]
    typed = typed_case_of(token)
    # زيدٌ ضاربٌ بكرًا: a word like the verb (شبه الفعل) takes its object as the verb does
    # (notes, المفعول به p0: a فعل or a شبه الفعل governs it)
    if head and not is_verb(head) and works_as_verb(head):
        if _object_of_participle(token, head):
            return "object"
        if _doer_of_describer(token, head, s) or (s.described_doer and [head, token] == list(s.described_doer[1:])):
            return "subject"  # its فاعل, standing in for the khabar
    if head and is_verb(head):
        if attached_pronoun(token) and rel == "SBJ":
            return "subject"  # قُومِي: the doer written onto the verb, ياء المخاطبة (Awdah V1 p85)
        before = token["id"] < head["id"]
        siblings = [t for t in s.kids(head) if t is not token]
        if before and is_object_pronoun(token):
            return "object"  # إيّاك نعبد: the object put first
        asked = book_map("istifham", "before_verb").get(strip_diacritics(token["form"]))
        if asked and before and not any(t["rel"] == "OBJ" and not is_verb(t) for t in siblings):  # قال after it is the reply, not its object
            return asked  # ماذا قرأت، كيف جئت: the question noun fills the place it asks about
        if before and typed == "a" and not is_mabni(token.get("pos_camel", "")) and (
                rel in SUBJECTS or (rel == "MOD" and is_plain_noun(token) and not is_participle(token)
                                    and (own_doer(head) or any(t["rel"] in SUBJECTS and t["id"] > token["id"] for t in siblings)))):
            # القرآنَ قرأ الطالبُ، زَيْدًا ضَرَبْتُ: the reader's own fatha marks the fronted object (a built word's is
            # no case: أنتَ) once the verb has its doer, after it or in it (Ibn Aqil V2 p129: فكنت تقول زيدا ضربت
            # فتنصب زيدا); a verb busied with its pronoun leaves it to one like it, left out (busied_before)
            return "object"
        if before and rel in SUBJECTS:
            return "none"  # a doer never comes first (نحن نكتب): the noun opens the sentence
        if quoted_head(token, s):
            return "none"  # its place is inside the sentence it heads (_nominal_place)
        if praised_noun(token, s):
            return "none"  # نِعْمَ الْخُلُقُ الْوَفَاءُ: the one praised is no second doer (_nominal_place: مبتدأ)
        if head.get("asp") == "c" and rel in (*NOUN_LINKS, "---") and typed != "u":
            return "object"  # قل الحق: a command's doer is always the hidden أنت (Tasheel 2.4.1 p30)
        if not before and typed != "u" and (listed(token, "times_counted") or stands_for_masdar(token, head, s)):
            return "absolute"  # ضربتُه مرتين، ثلاثَ مراتٍ، كلَّ الحبِّ: the count or the share stands in for the masdar
        # رَأَيْتُ كِلَا الصَّدِيقَيْنِ: a verb of the first or second person holds its doer (تُ، نا، تَ),
        # so the noun after it is its object, however the parser hung it or what case it guessed
        if (own_doer(head) and not before
                and rel in NOUN_LINKS and typed != "u"
                and not any(t["rel"] == "OBJ" and t["id"] < token["id"] for t in siblings)):
            return "object"
        if (not before and typed in (None, "a") and token.get("stt") in ("i", "c")
                and is_masdar(token, weak_or_doubled=False) and same_root(token, head)):
            return "absolute"  # يُطَهِّرَكُمْ تَطْهِيرًا: the verb's own masdar
        after_first = rel == "OBJ" and typed in (None, "a") and any(t["rel"] == "OBJ" and t["id"] < token["id"] for t in siblings)
        # لا يُؤْتُونَ النَّاسَ نَقِيرًا: a verb of two objects keeps its second OBJ, so no state or tamyeez
        if after_first and (s.family(head) == "zanna" or is_one(head["lemma"], "two_objects_give")):
            return "second_object"
        # مُنِحَ الطَّالِبُ هَدِيَّةً: a passive verb of giving raises its first object to نائب فاعل and keeps
        # the second منصوب, however the parser hung it (OBJ, MOD or TMZ). The deputy may be in the verb
        # (الطَّالِبُ أُعْطِيَ جَائِزَةً، أُعْطِيتُ): then a typed fatha is the second, never the deputy's raf'
        if (is_passive(head) and is_one(head["lemma"], "two_objects_give") and not before
                and rel in ("OBJ", "MOD", "TMZ") and typed in (None, "a")
                and (typed == "a" or any(t["rel"] in (*SUBJECTS, "OBJ") and t["id"] < token["id"] for t in siblings))):
            return "second_object"
        if not before and rel in ("OBJ", "MOD", "TMZ") and purpose(token, head):
            return "purpose"
        # زَيْدٌ أَكْرَمَ ضَيْفًا: a verb said of the مبتدأ the sentence rests on holds its doer, the
        # pronoun back to it its khabar must carry (رابط جملة الخبر, Ibn Aqil on the Alfiyya)
        told = s.head(head)
        if rel in ("OBJ", "MOD", "TMZ") and typed in (None, "a") and not before \
                and token.get("stt") == "i" and (told and told["rel"] == "---" or any(
                    t["rel"] in NOUN_LINKS or _doer_by_extra_ba(t, head)
                    or (t["id"] < token["id"] and verb_place(t, s) == "subject") for t in siblings)):
            if is_one(head["lemma"], "tamyeez_verbs") and not is_participle(token):
                return "specification"
            if is_participle(token) and wants_object(head, siblings, s):
                return "object"  # أكرم محمد خالدا، مَنْ عَمِلَ صَالِحًا: the describing word stands for its noun
            if is_participle(token):
                return "state"
            if rel != "TMZ" and is_plain_noun(token) and not same_root(token, head) and not is_one(head["lemma"], "intransitive_verbs"):
                return "object"  # نصر زيدٌ بكرًا: a plain noun is no hal, and a tamyeez only after a tamyeez verb (above)
        if after_first:
            return "second_object"  # ظن الولد الأمر سهلا, أعطى الولد الكتاب
        # صِلْ مَنْ قَطَعَكَ: a relative hung on the verb as a modifier is a noun no hal or tamyeez can be
        # (its صلة makes it definite); with the doer settled (a command's is the hidden أنت) it is the object.
        # A verb has no مضاف إليه, so a relative the parser hung as one (أَكْرِمْ مَنْ زَارَكَ) is the same
        if rel in ("MOD", "IDF") and listed(token, "mawsul") and not any(t["rel"] == "OBJ" for t in siblings) \
                and holds_doer(head, siblings):
            return "object"
        # نصر زيدٌ بكرًا: a noun the parser hung on the verb with no relation ("---" belongs to the
        # root alone) is still one of its arguments, told by its case like the rest; one with a subject
        # of its own heads a sentence instead (قال ما اسمُك: ما is the khabar of اسم)
        if (rel in NOUN_LINKS or (rel == "IDF" and typed != "i")
                or (rel == "---" and typed != "i" and not any(subject_link(k) for k in s.kids(token)))
                or (rel == "MOD" and typed == "u" and is_plain_noun(token))
                # بِعْ الكِتَابَ: hung on the verb as a modifier, but a definite word is never a
                # hal or tamyeez, so its fatha makes it the object (unless it is the verb's own masdar)
                or (rel == "MOD" and typed == "a" and token.get("stt") in ("d", "c") and is_plain_noun(token)
                    and not same_root(token, head))):
            if typed in ("u", "a"):  # damma stands for the doer (or its deputy), fatha is the done-to
                # طُوِّقَ طَوْقًا: under a passive verb the first object became the deputy, so
                # a fatha left is the second (أُعْطِيَ الولدُ الكتابَ)
                return "subject" if typed == "u" else "second_object" if is_passive(head) else "object"
            if is_passive(head):
                nouns = [t for t in (*siblings, token) if t["rel"] in NOUN_LINKS]
                return "subject" if rel != "OBJ" or is_deputy(token, nouns) else "object"
            # the parser reads letters only, so a nominative "object" with no subject is the subject
            return "object" if rel == "OBJ" and (
                typed_or_parsed_case(token) != "u" or any(t["rel"] == "SBJ" for t in siblings)) else "subject"
        if rel == "TMZ":
            return "specification"
    if rel == "MOD" and head:
        # an indefinite nasb word after a definite noun is that noun's hal, not the verb's
        if indefinite_nasb(token) and not unlike(token, head):
            verb = verb_above(token, s)
            if verb:
                if same_root(token, verb):
                    return "absolute"  # same root as its verb: فَرِحَ فَرَحًا
                if purpose(token, verb):
                    return "purpose"
                return state_or_specification(token, head)
    return "none"


def _nominal_place(token: dict, s: Sentence) -> str:
    """The place of a word no verb governs: the nominal sentence, mubtada and khabar
    (Tasheel 1.4 p6), with the hal and tamyeez a noun can take. The parser's link is
    trusted last: the question word and the pointer say what the sentence is about
    before any link does, then the khabar link, the subject links, the word the
    sentence rests on, and last a modifier by its case."""
    rel = token["rel"]
    if s.hijazi and token in s.hijazi[1:]:
        return "subject" if token is s.hijazi[1] else "predicate"
    if s.described_doer and token is s.described_doer[1]:
        return "subject"  # ما ذاهبٌ المسلمون: the وصف is the mubtada, before ما is asked of it
    if s.asked_pair and token in s.asked_pair:
        return "subject" if token is s.asked_pair[0] else "predicate"
    if praised_noun(token, s):
        return "subject"  # بِئْسَ الْخُلُقُ الْكَذِبُ: the one blamed, a مبتدأ whose khabar is the sentence before it
    if zarf_of_khabar(token, s):
        return "place_time"
    # واللهُ أكبرُ: a و that opens a sentence (particles.stamp) leaves the noun after it its
    # mubtada, and the raf' noun hung on that its khabar
    before = s.by_id.get(token["id"] - 1)
    if before and read_as(before, "istinaf"):
        return "subject"
    opener = s.by_id.get(before["id"] - 1) if before else None
    if opener and read_as(opener, "istinaf") and typed_or_parsed_case(token) == "u":
        return "predicate"
    if (s.verbless and rel == "OBJ" and s.head(token) and s.head(token)["pos"] == "PRT" and not jarr_takes(token, s)
            and typed_or_parsed_case(token) == "u"):
        return "subject"  # لله الحمدُ: the noun after a fronted jar-majrur khabar is the مبتدأ
    if is_verb(token):  # a verb is only ever a khabar by its link; its clause is named from the tree above
        return "predicate" if rel == "PRD" else "none"
    head = s.head(token)
    camel = token.get("pos_camel", "")
    if s.asks:
        # أيُّ الأعمالِ أفضلُ: the question noun with a case of its own and a مضاف إليه is the
        # mubtada, the rest its khabar
        leads = any("interrog" in t.get("pos_camel", "") and is_one(t["lemma"], "istifham", "inflected")
                    and any(k["rel"] == "IDF" for k in s.kids(t)) for t in s.tokens)
        if "interrog" in camel:
            # مَنْ فِي البيتِ، مَنْ عندك: no noun is left to be the mubtada but a jar-majroor or ظرف, so the
            # question word is the mubtada and they its khabar
            told_of = [t for t in s.tokens if t is not token and t["pos"] == "NOM" and not jarr_takes(t, s)
                       and not is_zarf(t, s) and (t["rel"] != "IDF" or s.head(t) is token)]  # مَتَى السَّفَرُ: hung on it as idafa
            return "subject" if leads or not told_of else "predicate"  # كيف حالك: the question word is the khabar, brought to the front
        if leads and token["pos"] == "NOM" and typed_or_parsed_case(token) == "u" and rel != "IDF":
            return "predicate"
        if (token["pos"] == "NOM" and typed_or_parsed_case(token) == "u" and rel != "IDF") or s.asked_of(token):
            return "subject"
    if "dem" in camel and s.verbless and rel not in ("IDF", "OBJ"):
        return "subject"
    if rel == "PRD":
        fronted_jar = any(t["rel"] == "PRD" and t["pos"] == "PRT" and t["id"] < token["id"]
                          for t in (s.kids(head) if head else ()))
        # إِنَّ مِنَ الْبَيَانِ لَسِحْرًا: the jar-majrur the parser hung on the nasb noun stands
        # first as إنّ's khabar, so the noun after it is its اسم, brought back
        fronted_jar = fronted_jar or (head is not None and s.family(head) == "inna" and typed_or_parsed_case(token) == "a"
                                      and any(is_preposition(k) and k["id"] < token["id"] for k in s.kids(token)))
        return "subject" if fronted_jar else "predicate"
    if rel in SUBJECTS:
        return "subject"
    kids = s.kids(token)
    # وهو مبتسمٌ: the sentence a و brings rests on its khabar, as a whole one does on its own
    if rel == "OBJ" and head and head["pos"] == "PRT" and typed_or_parsed_case(token) == "u" \
            and any(subject_link(c) and c["id"] < token["id"] for c in kids):
        return "predicate"
    quoted = quoted_head(token, s)
    # قال زيدٌ اللهُ أكبرُ: a loose word hung on the head of a quote is in that quoted sentence too
    quoted_on = rel == "---" and head is not None and quoted_head(head, s)
    if rel == "---" or quoted:
        if any(subject_link(c) for c in kids):
            return "predicate"
        pointer = next((c for c in kids if "dem" in c.get("pos_camel", "") and c["id"] < token["id"]), None)
        # only a noun with ال is the pointer's مشار إليه: هذا بيتٌ and هذا أبي are sentences
        if pointer and token.get("stt") != "d" and s.verbless:
            return "predicate"
        # زيدٌ أبوه عالمٌ، زيدٌ أكلَ الطعامَ: the sentence rests on the noun, its khabar (or the
        # verb whose clause is the khabar) hung after it; after a pointer (هذا رجلٌ يعملُ) the
        # noun is the khabar and the verb its صفة
        if not pointer and any(c["rel"] == "PRD" or (is_verb(c) and c["id"] > token["id"]) for c in kids):
            return "subject"
        if noun_tagged(token) and (s.verbless or quoted or quoted_on):
            loose = sorted([t for t in s.tokens if t["rel"] == "---" and noun_tagged(t)] + [head] * quoted_on,
                           key=lambda t: t["id"])
            if loose != [token]:
                return "subject" if all(token["id"] <= t["id"] for t in loose) else "predicate"
            # محمدُ بنُ عبدِ اللهِ، الطبيبُ الماهرُ: a noun with only its صفة and مضاف إليه
            # under it is a phrase, no sentence: nothing is told of it, so it is no mubtada
            # المعلماتُ في الفصلِ: a raf' noun with a jar-majrur after it is told of by it, its khabar
            # زيدٌ عندك: a ظرف with its مضاف إليه tells of it too
            told = any(_nominal_place(k, s) == "predicate" or _jar_khabar(k, token, before) or zarf_of_khabar(k, s)
                       for k in kids if not is_suffix(k))
            return "subject" if told else "none"
    if rel == "MOD" and head:
        # اشتريت رطلين زيتًا: after a measure a plain noun in nasb is its tamyeez, though the two differ in number
        if listed(head, "tamyeez_head") and indefinite_nasb(token) and token.get("pos_camel") != "adj":
            return "specification"
        if told_of_lone_mubtada(token, head, s):
            return "predicate"
        # a name is definite by itself (رأيت أخاك زيدًا): its tanween makes it no hal; an unknown
        # word the analyser filed as a name is still one if it has a hal's shape (مسرعًا)
        if unlike(token, head) and (is_state_word(token) or not is_name(token)):
            return "state" if typed_or_parsed_case(token) == "a" else "predicate"
        if told_of_subject(token, head):
            return "predicate"
        if indefinite_nasb(token):
            return state_or_specification(token, head)
    return "none"


def _jar_khabar(kid: dict, token: dict, before: dict | None) -> bool:
    """A jar-majrur after a raf' noun is its khabar; not after a called noun (يا محمدُ في البيت ضيفٌ)."""
    return (is_preposition(kid) and kid["id"] > token["id"] and typed_or_parsed_case(token) == "u"
            and not (before and strip_diacritics(before["form"]) == "يا"))


def _slot(token: dict, s: Sentence) -> str:
    """Which place the word fills, from its link, position, typed case, definiteness and
    siblings alone; never from what governs it, so one reading serves every family and
    the tree's branch for that family says which places it names. A place a verb gives
    (verb_place) comes first, then the nominal sentence's (_nominal_place)."""
    place = verb_place(token, s)
    return place if place != "none" else _nominal_place(token, s)
