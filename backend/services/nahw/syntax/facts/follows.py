"""Axis `follows`: is the word a تابع (naat, atf, tawkeed, badal) of a word before it."""
from __future__ import annotations

from backend.services.text.arabic_text import strip_diacritics
from backend.services.text.harakat import has_tanween
from backend.services.nahw.book import is_one, is_subject_pronoun
from backend.services.nahw.syntax.facts.word import case_shown, case_unseen, is_nasab, listed, agrees, indefinite_nasb, is_called_noun, is_light, is_participle, is_verb, same_case, read_as, takes_two_objects, shown_cases, told_of_subject, typed_case_of, typed_or_parsed_case, attached_pronoun, noun_tagged, works_as_verb
from backend.services.nahw.syntax.facts.sentence import Sentence, next_word, place_case, praised_noun, previous_noun, quoted_head, told_of_lone_mubtada, verb_above
from backend.services.nahw.syntax.facts.kind import joins_clauses, calling_head


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
    # the pronoun stuck on a noun is its مضاف إليه whatever link the parser drew (عِلْمُهُ); a name
    # after a name names a second one (ضرب موسى عيسى: the doer, then the done to)
    names = token["pos"] == "PROP" and not token.get("guessed") and before["pos"] != "PROP" \
        or any(attached_pronoun(k) for k in s.kids(token))
    # a مضاف with nothing added to it yet (أَبُو مُوسَى) takes this word so
    if before.get("stt") == "c" and not any(k["rel"] == "IDF" for k in s.kids(before)):
        return False
    mine = typed_or_parsed_case(token)
    # a name is definite though it wears tanween (أعجبني زيدٌ علمُه)
    definite = before.get("stt") in ("d", "c") or before["pos"] == "PROP"
    if not (names and definite and same_case(token, before)):
        return False
    # جاء الرجلُ أبوه عالمٌ: an indefinite noun in its case after it is its khabar, so the
    # noun opens a sentence of its own (a حال) and stands for nothing
    after = next_word(token, s)
    if after and mine and noun_tagged(after) and after.get("stt") == "i" and typed_or_parsed_case(after) == mine:
        return False
    verb = verb_above(before, s)
    return not (verb and takes_two_objects(verb))


def verb_joined_by_waw(token: dict, s: Sentence) -> dict | None:
    """سرتُ والشاطئَ: after واو المعية (و meaning "with") a noun the reader put in nasb is the
    مفعول معه when nothing before the و is in nasb for it to join (Tasheel 3.8.5 p76); a
    معطوف would wear the case of what it joins. The verb before the و, which works on it, or None."""
    head = s.head(token)
    if not (head and head["pos"] == "PRT"):
        # سافرتُ والصديقَ: the parser may hang the noun on the verb beside its و; the و written onto it is the same
        head = next((t for t in s.tokens if t["id"] == token["id"] - 1 and t.get("form", "").endswith("+")), None)
    # جاء الولدُ وهُوَ يبكي: هُوَ's fatha is built in, no nasb; the و opens a hal clause
    case = typed_case_of(token)
    if not (head and head["pos"] == "PRT" and head["lemma"].strip("+") == "و" and not is_subject_pronoun(token)
            and case in ("a", None) and (verb := verb_above(head, s)) is not None and verb["id"] < head["id"]):
        return None  # وما أدراك: the verb comes after the و, so it is no "with" after a clause
    # the noun straight before, and every noun on the verb before the و: جَعَلْنَا الْبَيْتَ مَثَابَةً
    # ... وَأَمْنًا joins مثابة; a ـات kasra is nasb too (خَلَقَ السَّمَاوَاتِ وَالْأَرْضَ)
    joinable = [k for k in [previous_noun(head, s)] + [k for k in s.kids(verb) if k["id"] < head["id"]
                                                       and noun_tagged(k) and not is_verb(k)] if k]
    if case is None:
        # سافرت والصديق typed bare, سرت والفتى its case unseen: with only the verb's own pronoun to join, the joining is weak and
        # the nasb chosen (Ibn Aqil V2 p204: والنصب مختار لدى ضعف النسق); a noun to join takes it (قام زيد وعمرو)
        return None if joinable else verb
    return None if any("a" in shown_cases(k) for k in joinable) else verb


def _follows(token: dict, s: Sentence) -> str:
    """Which follower (tabi') the word is, or none: a follower takes its case from the
    word it follows, every other noun from a governor (Tasheel 3.10 p88).

    A word is a follower only on the evidence of both its link and what it hangs on;
    an indefinite word after a definite or construct noun is a khabar or hal, so it
    answers none and the rest of the naming decides it. Tested in this order because
    each earlier follower has a mark of its own (a pointer child, a joining particle, a
    bare name after a noun with ال, a listed تأكيد word) that a plain na't lacks."""
    if s.asked_of(token) or calling_head(token, s) or verb_joined_by_waw(token, s) or praised_noun(token, s):
        return "none"  # غيرُ خالدٍ after a complete clause is the مستثنى, not a صفة; بِئْسَ الْخُلُقُ الْكَذِبُ: the one blamed
    # ما جاء أحدٌ إلا زيدٌ: after إلا in a negated complete sentence the excepted noun in the
    # case of the noun before إلا is its بدل (Tasheel 3.2 p67)
    excepting = s.by_id.get(token["id"] - 1)
    if excepting and excepting["pos"] == "PRT" and read_as(excepting, "istithna") \
            and s.negated_before(excepting):
        before = previous_noun(excepting, s)
        # no case shown (لا اله الا الله، لا إله إلا هو): the إتباع, the stronger reading (Tasheel 3.8.7)
        if before and (shown := case_shown(token)) in (None, place_case(before, s)):
            return "badal"
    head = s.head(token)
    # هذا البستانُ: the noun with ال a pointer points at, hung on it or (as some parses
    # have it) under it; a pointer is mabni, so its own vowel says nothing of the case
    pointer = next((c for c in (*s.kids(token), head) if c and "dem" in c.get("pos_camel", "")
                    and c["id"] == token["id"] - 1), None)
    if pointer and token.get("stt") == "d":
        return "naat"
    if is_nasab(token):
        return "naat"
    # يا أيها الناسُ، يا أيها الذين آمنوا، يا أيهذا: the noun with ال, relative or pointer after أيها is its صفة
    if head and is_called_noun(head) and (token.get("stt") == "d" or is_one(token.get("pos_camel", ""), "nida", "described_by")):
        return "naat"
    # جاء زيدٌ زيدٌ: the same noun said twice is التوكيد اللفظي (Tasheel 3.10.3 p94)
    before = s.by_id.get(token["id"] - 1)
    if before and not is_verb(before) and before["pos"] != "PRT" \
            and strip_diacritics(before.get("typed") or "-") == strip_diacritics(token.get("typed") or ""):
        return "tawkeed"
    # ذَهَبْتُ أَنَا: the verb holds its doer already (its تاء, or hidden), so the detached
    # pronoun of raf' straight after it repeats that doer: التوكيد اللفظي (Tasheel 3.10.3 p94).
    # Only one of its person: قُلْ هُوَ اللَّهُ أَحَدٌ, هو opens the sentence قل says, not أنت again; nor one
    # that is the subject of the raf' word heading that sentence: قُلْتُ أَنَا ذَاهِبٌ (facts.quoted_head)
    if before and is_verb(before) and is_subject_pronoun(token) and before.get("per") == token.get("per") \
            and not (head and token["rel"] == "SBJ" and quoted_head(head, s)):
        return "tawkeed"
    if not head:
        return "none"
    # دخل المديرُ وهو مبتسمٌ: a raf' pronoun straight after the و, hung on this word, is its
    # مبتدأ; the و brings a sentence (واو الحال), joining no noun (Tasheel 3.7)
    opener = s.by_id.get(head["id"] + 1)
    if opener and opener["id"] < token["id"] and opener["head"] == token["id"] and is_subject_pronoun(opener):
        return "none"
    # لكنّ is also an inna sister; it joins only when no clause of its own follows, or as the light لكنْ
    if (head["pos"] == "PRT" or joins_clauses(head, s)) and read_as(head, "atf") \
            and (not is_one(head["lemma"], "inna") or is_light(head)) and s.noun_before(head):
        return "atf"
    # الخليفة عمر: a bare name right after a noun with ال is that noun's badal
    if token["pos"] == "PROP" and token["rel"] == "MOD" and head["id"] == token["id"] - 1 \
            and head["pos"] == "NOM" and head["form"].startswith("ال") and not is_verb(head) \
            and not has_tanween(token.get("typed")):
        return "badal"
    # جاء الأميرُ خالدٌ: an indefinite word can be no صفة of a noun with ال; wearing that noun's
    # raf' or jarr (a nasb one is its حال) where a verb stands over it, it is its بدل
    if token["rel"] == "MOD" and head["id"] == token["id"] - 1 and head["form"].startswith("ال") \
            and has_tanween(token.get("typed")) and not is_verb(head) and verb_above(head, s) is not None \
            and (shown := typed_case_of(token)) in ("u", "i") and shown == typed_case_of(head):
        return "badal"
    with_pronoun = any(k.get("pos_camel") == "pron" for k in s.kids(token))
    tawkeed_word = listed(token, "tawkeed", "with_pronoun" if with_pronoun else "without_pronoun")
    if not tawkeed_word and stands_for(token, s):
        return "badal"
    if tawkeed_word and head["id"] < token["id"] and not is_verb(head) and head["pos"] != "PRT":
        return "tawkeed"
    # a صفة comes after the noun it describes: هَذَانِ hung on the قَلَمَانِ after it is the mubtada
    if token["rel"] != "MOD" or is_verb(head) or head["id"] > token["id"]:
        return "none"
    # زيدٌ أبوه كريمٌ: a word whose subject stands before it is told of that subject, a khabar
    if any(k["rel"] == "SBJ" and k["id"] < token["id"] for k in s.kids(token)):
        return "none"
    # الطالبُ الذي نجح: a relative straight after a noun with ال is its صفة, unless that
    # noun is the doer of a verb still without its object (كافأ المديرُ الذي نجح)
    verb = s.head(head)
    owed = bool(verb) and is_verb(verb) and typed_or_parsed_case(head) == "u"         and not any(k["rel"] == "OBJ" and k is not head for k in s.kids(verb))
    if listed(token, "mawsul") and head.get("stt") == "d" and head["id"] == token["id"] - 1 and not owed:
        return "naat"
    mine, theirs = typed_or_parsed_case(token), typed_or_parsed_case(head)
    # مدرسةُ البلدِ الكبيرةُ: a صفة of the مضاف comes after its مضاف إليه, in the مضاف's case
    mudaf = s.head(head) if head["rel"] == "IDF" else None
    if mine and mine != theirs and mudaf and not is_verb(mudaf) and mine == typed_or_parsed_case(mudaf) \
            and token.get("stt") == head.get("stt") == "d":
        return "naat"
    if mine and theirs and not shown_cases(token) & shown_cases(head) and token.get("stt") == head.get("stt") == "d":
        return "none"  # أعطى الغنيُّ الفقيرَ: with ال both show their case, and a na't wears its noun's
    if told_of_lone_mubtada(token, head, s):
        return "none"
    # مررت بزيدٍ هذا، فعله كبيرُهم هذا: a pointer stands for a describing word (المشار إليه), so it is
    # the صفة of a name or of a noun added to a known one; a noun with ال is less known than it,
    # and a صفة is never more known than its noun, so after one it is its بدل
    # (Ibn Ya'ish V2 p247, p249: امتنع وصف المعرف باللام بالمبهم)
    if "dem" in token.get("pos_camel", "") and noun_tagged(head):
        return "naat" if head["pos"] == "PROP" or head.get("stt") == "c" else "badal"
    # السُّفْلَى: a مقصور noun shows no case, so any its noun wears is its own
    if (mine or case_unseen(token)) and shown_cases(token) & shown_cases(head):
        # كوبًا لبنًا: after a measure a plain noun is its tamyeez; only a describing word is a na't
        # (شَعِيرًا has the فعيل shape, so the morphology's adjective tag tells, not the shape)
        measure = listed(head, "tamyeez_head") and token.get("pos_camel") != "adj"
        # آمِرًا أحدًا: after a participle at work a plain noun in nasb is its object (slot.py);
        # with ال on both it follows it (إِنَّ الْمُهَنْدِسَ الْعَجُوزَ)
        governed = (mine == "a" and works_as_verb(head) and not is_participle(token)
                    and not token.get("stt") == head.get("stt") == "d")
        return "naat" if agrees(token, head) and not measure and not governed else "none"
    # لا رجلَ حاضرٌ (khabar) and a hal or tamyeez in nasb are not followers
    if told_of_subject(token, head) or indefinite_nasb(token):
        return "none"
    return "naat" if token.get("ud") == "ADJ" else "none"
