"""Axis `slot`: the word's place in its clause: subject, predicate, object, hal, tamyeez, zarf
and the rest, under a verb (verb_place) or in a verbless sentence (nominal_place)."""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics
from backend.services.nahw_book import book_map, is_mabni, is_one, is_plain_noun
from backend.services.syntax.facts.word import is_suffix, listed, indefinite_nasb, is_deputy, is_masdar, is_object_pronoun, is_participle, is_passive, is_preposition, is_state_word, is_verb, read_as, same_root, shows_jarr, state_or_specification, told_of_subject, typed_case_of, typed_or_parsed_case, unlike
from backend.services.syntax.facts.sentence import Sentence, jarr_takes, told_of_lone_mubtada, verb_above
from backend.services.syntax.facts.follows import with_waw


def takes_tamyeez(token: dict, s: Sentence) -> bool:
    """A tamyeez stands after a number or a measure, or after a verb of tamyeez al-nisba."""
    head = s.head(token)
    if head and is_one(head["lemma"], "tamyeez_verbs"):
        return True
    return any(listed(t, "tamyeez_head") for t in s.tokens if t["id"] < token["id"])


def completes_kaada(token: dict, s: Sentence) -> bool:
    """The present verb that finishes a كاد-type verb; its clause is that verb's khabar."""
    head = s.head(token)
    return bool(head and is_verb(token) and s.family(head) == "kaada")


def is_zarf(token: dict, s: Sentence) -> bool:
    """A listed time or place word, or كل/بعض added to one (كلَّ يومٍ)."""
    if token["pos"] == "PRT":
        return False
    if listed(token, "zarf_zaman") or listed(token, "zarf_makan"):
        return True
    return listed(token, "zarf_zaman", "carriers") and any(
        k["rel"] == "IDF" and (listed(k, "zarf_zaman") or listed(k, "zarf_makan")) for k in s.kids(token))


def zarf_of_khabar(token: dict, s: Sentence) -> bool:
    """الأستاذُ عندَ البابِ: in a verbless sentence a place or time word with its mudaf ilayh
    is the khabar's maf'ul fihi (the khabar itself is understood, Tasheel 1.4.4 p13)."""
    return (s.verbless and is_zarf(token, s) and "interrog" not in token.get("pos_camel", "")
            and token["rel"] in ("---", "MOD", "PRD")
            and typed_or_parsed_case(token) in (None, "a") and any(k["rel"] == "IDF" for k in s.kids(token)))


def place_time(token: dict, s: Sentence) -> bool:
    """A listed time or place word that is a verb's مفعول فيه (Tasheel 3.2 p67): it
    modifies the verb with no vowel or fatha (the parser may draw that as idafa), or it
    stands before its verb with the verb hanging off it (مَتَى سافر)."""
    if not is_zarf(token, s):
        return False
    head = s.head(token)
    # مسافرٌ غدًا: a participle works like its verb
    if head and (is_verb(head) or (is_participle(head) and token["rel"] == "MOD")):
        return token["rel"] in ("MOD", "IDF") and typed_case_of(token) in (None, "a")
    return typed_or_parsed_case(token) in (None, "a") and any(
        is_verb(k) and k["id"] > token["id"] for k in s.kids(token))


def _object_of_participle(token: dict, head: dict, s: Sentence) -> bool:
    """A word hung on a participle that is its object: linked as one in nasb, or in the
    nasb the reader typed where the link cannot hold it, since a مضاف إليه is never منصوب
    (فاهمٌ الدرسَ) and a نعت has its noun's case (ضاربٌ بكرًا). An indefinite state word
    stays a حال (قادمٌ مسرعًا), and the participle's own root a مفعول مطلق. A diptote's fatha
    is its jarr, so it stays the مضاف إليه (طَرِيقَ جَهَنَّمَ)."""
    rel, typed = token["rel"], typed_case_of(token)
    if rel == "OBJ":
        return typed_or_parsed_case(token) == "a"
    return typed == "a" and ((rel == "IDF" and not shows_jarr(token)) or (
        rel == "MOD" and typed_or_parsed_case(head) != "a" and not is_state_word(token)
        and not same_root(token, head)))


def purpose(token: dict, verb: dict) -> bool:
    """قام الطلاب احترامًا: a masdar of the heart (a feeling or intent, reason_masdars) not of its verb's root,
    in nasb and indefinite or a مضاف, gives the reason for the verb: its مفعول لأجله
    (Tasheel 3.8.3 p73). Any other masdar there is a حال (جاء ركضًا)."""
    return (listed(token, "reason_masdars") and not same_root(token, verb)
            and typed_or_parsed_case(token) in (None, "a") and token.get("stt") in ("i", "c"))


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
    if is_object_pronoun(token):
        return "object"  # إيّاك نعبد، ما عبدنا إلا إيّاه: the detached pronoun of nasb is only an object
    if with_waw(token, s):
        return "accompaniment"
    head = s.head(token)
    rel = token["rel"]
    typed = typed_case_of(token)
    # زيدٌ ضاربٌ بكرًا: a word like the verb (شبه الفعل) takes its object as the verb does
    # (notes, المفعول به p0: a فعل or a شبه الفعل governs it)
    if head and not is_verb(head) and is_participle(head) and _object_of_participle(token, head, s):
        return "object"
    if head and is_verb(head):
        before = token["id"] < head["id"]
        siblings = [t for t in s.kids(head) if t is not token]
        if before and is_object_pronoun(token):
            return "object"  # إيّاك نعبد: the object put first
        asked = book_map("istifham", "before_verb").get(strip_diacritics(token["form"]))
        if asked and before and not any(t["rel"] == "OBJ" for t in siblings):
            return asked  # ماذا قرأت، كيف جئت: the question noun fills the place it asks about
        if before and rel in ("SBJ", "TPC") and typed == "a" and not is_mabni(token.get("pos_camel", "")):
            return "object"  # القرآنَ قرأ الطالبُ: the reader's own fatha marks the fronted object (a built word's is no case: أنتَ)
        if before and rel in ("SBJ", "TPC"):
            return "none"  # a doer never comes first (نحن نكتب): the noun opens the sentence
        if head.get("asp") == "c" and rel in ("SBJ", "TPC", "OBJ", "---") and typed != "u":
            return "object"  # قل الحق: a command's doer is always the hidden أنت (Tasheel 2.4.1 p30)
        if (not before and typed in (None, "a") and token.get("stt") in ("i", "c") and is_masdar(token)
                and same_root(token, head)):
            return "absolute"  # يُطَهِّرَكُمْ تَطْهِيرًا: the verb's own masdar
        after_first = rel == "OBJ" and typed in (None, "a") and any(t["rel"] == "OBJ" and t["id"] < token["id"] for t in siblings)
        # لا يُؤْتُونَ النَّاسَ نَقِيرًا: a verb of two objects keeps its second OBJ, so no state or tamyeez
        if after_first and (s.family(head) == "zanna" or is_one(head["lemma"], "two_objects_give")):
            return "second_object"
        if not before and rel in ("OBJ", "MOD", "TMZ") and purpose(token, head):
            return "purpose"
        if rel in ("OBJ", "MOD", "TMZ") and typed in (None, "a") and not before \
                and token.get("stt") == "i" and any(t["rel"] in ("SBJ", "TPC", "OBJ") for t in siblings):
            if is_one(head["lemma"], "tamyeez_verbs") and not is_participle(token):
                return "specification"
            if is_participle(token):
                return "state"
        if after_first:
            return "second_object"  # ظن الولد الأمر سهلا, أعطى الولد الكتاب
        if (rel in ("SBJ", "TPC", "OBJ") or (rel == "IDF" and typed != "i")
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
                nouns = [t for t in (*siblings, token) if t["rel"] in ("SBJ", "TPC", "OBJ")]
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
            return "subject" if leads else "predicate"  # كيف حالك: the question word is the khabar, brought to the front
        if leads and token["pos"] == "NOM" and typed_or_parsed_case(token) == "u" and rel != "IDF":
            return "predicate"
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
        pointer = next((c for c in kids if "dem" in c.get("pos_camel", "") and c["id"] < token["id"]), None)
        # only a noun with ال is the pointer's مشار إليه: هذا بيتٌ and هذا أبي are sentences
        if pointer and token.get("stt") != "d" and s.verbless:
            return "predicate"
        # زيدٌ أبوه عالمٌ، زيدٌ أكلَ الطعامَ: the sentence rests on the noun, its khabar (or the
        # verb whose clause is the khabar) hung after it; after a pointer (هذا رجلٌ يعملُ) the
        # noun is the khabar and the verb its صفة
        if not pointer and any(c["rel"] == "PRD" or (is_verb(c) and c["id"] > token["id"]) for c in kids):
            return "subject"
        if token["pos"] in ("NOM", "PROP") and s.verbless:
            loose = [t for t in s.tokens if t["rel"] == "---" and t["pos"] in ("NOM", "PROP")]
            if loose != [token]:
                return "subject" if not loose or token is loose[0] else "predicate"
            # محمدُ بنُ عبدِ اللهِ، الطبيبُ الماهرُ: a noun with only its صفة and مضاف إليه
            # under it is a phrase, no sentence: nothing is told of it, so it is no mubtada
            # المعلماتُ في الفصلِ: a raf' noun with a jar-majrur after it is told of by it, its khabar
            told = any(_nominal_place(k, s) == "predicate" or (is_preposition(k) and k["id"] > token["id"]
                                                              and typed_or_parsed_case(token) == "u"
                                                              and not (before and strip_diacritics(before["form"]) == "يا"))
                       for k in kids if not is_suffix(k))
            return "subject" if told else "none"
    if rel == "MOD" and head:
        if told_of_lone_mubtada(token, head, s):
            return "predicate"
        if unlike(token, head):
            return "state" if typed_or_parsed_case(token) == "a" else "predicate"
        if told_of_subject(token, head):
            return "predicate"
        if indefinite_nasb(token):
            return state_or_specification(token, head)
    return "none"


def _slot(token: dict, s: Sentence) -> str:
    """Which place the word fills, from its link, position, typed case, definiteness and
    siblings alone; never from what governs it, so one reading serves every family and
    the tree's branch for that family says which places it names. A place a verb gives
    (verb_place) comes first, then the nominal sentence's (_nominal_place)."""
    place = verb_place(token, s)
    return place if place != "none" else _nominal_place(token, s)
