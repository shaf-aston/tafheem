"""Axis `follows`: is the word a تابع (naat, atf, tawkeed, badal) of a word before it."""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics
from backend.services.harakat import has_tanween
from backend.services.nahw_book import is_one
from backend.services.syntax.facts.word import _listed, agrees, indefinite_nasb, is_called_noun, is_light, is_participle, is_verb, read_as, shown_cases, told_of_subject, typed_case_of, typed_or_parsed_case
from backend.services.syntax.facts.sentence import Sentence, place_case, previous_noun, told_of_lone_mubtada, verb_above
from backend.services.syntax.facts.kind import _joins_clauses, calling_head


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
    # the pronoun stuck on a noun is its مضاف إليه whatever link the parser drew (عِلْمُهُ)
    names = token["pos"] == "PROP" or any(k.get("pos_camel") == "pron" and k["form"].startswith("+")
                                          for k in s.kids(token))
    mine = typed_or_parsed_case(token)
    if not (names and before.get("stt") in ("d", "c") and mine and mine == typed_or_parsed_case(before)):
        return False
    # جاء الرجلُ أبوه عالمٌ: an indefinite noun in its case after it is its khabar, so the
    # noun opens a sentence of its own (a حال) and stands for nothing
    after = next((t for t in s.tokens if t["id"] > token["id"] and not t["form"].startswith("+")), None)
    if after and after["pos"] in ("NOM", "PROP") and after.get("stt") == "i" and typed_or_parsed_case(after) == mine:
        return False
    verb = verb_above(before, s)
    return not (verb and (is_one(verb["lemma"], "zanna") or is_one(verb["lemma"], "two_objects_give")))


def with_waw(token: dict, s: Sentence) -> bool:
    """سرتُ والشاطئَ: after واو المعية (و meaning "with") a noun the reader put in nasb is the
    مفعول معه when nothing before the و is in nasb for it to join (Tasheel 3.8.5 p76); a
    معطوف would wear the case of what it joins."""
    head = s.head(token)
    if not (head and head["pos"] == "PRT" and head["lemma"].strip("+") == "و"
            and typed_case_of(token) == "a" and verb_above(head, s) is not None):
        return False
    # the noun straight before, and every noun on the verb before the و: جَعَلْنَا الْبَيْتَ مَثَابَةً
    # ... وَأَمْنًا joins مثابة; a ـات kasra is nasb too (خَلَقَ السَّمَاوَاتِ وَالْأَرْضَ)
    verb = verb_above(head, s)
    joinable = [previous_noun(head, s)] + [k for k in s.kids(verb) if k["id"] < head["id"]
                                           and k["pos"] in ("NOM", "PROP") and not is_verb(k)]
    return not any(k and "a" in shown_cases(k) for k in joinable)


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
    # ما جاء أحدٌ إلا زيدٌ: after إلا in a negated complete sentence the excepted noun in the
    # case of the noun before إلا is its بدل (Tasheel 3.2 p67)
    excepting = s.by_id.get(token["id"] - 1)
    if excepting and excepting["pos"] == "PRT" and read_as(excepting, "istithna") \
            and s.negated_before(excepting):
        before = previous_noun(excepting, s)
        if before and typed_or_parsed_case(token) and typed_or_parsed_case(token) == place_case(before, s):
            return "badal"
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
    if (head["pos"] == "PRT" or _joins_clauses(head, s)) and read_as(head, "atf") \
            and (not is_one(head["lemma"], "inna") or is_light(head)) and s.noun_before(head):
        return "atf"
    # الخليفة عمر: a bare name right after a noun with ال is that noun's badal
    if token["pos"] == "PROP" and token["rel"] == "MOD" and head["id"] == token["id"] - 1 \
            and head["pos"] == "NOM" and head["form"].startswith("ال") and not is_verb(head) \
            and not has_tanween(token.get("typed")):
        return "badal"
    with_pronoun = any(k.get("pos_camel") == "pron" for k in s.kids(token))
    tawkeed_word = _listed(token, "tawkeed", "with_pronoun" if with_pronoun else "without_pronoun")
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
    if _listed(token, "mawsul") and head.get("stt") == "d" and head["id"] == token["id"] - 1 and not owed:
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
    if mine and shown_cases(token) & shown_cases(head):
        # كوبًا لبنًا: after a measure a plain noun is its tamyeez; only a describing word is a na't
        measure = _listed(head, "tamyeez_head") and not is_participle(token)
        return "naat" if agrees(token, head) and not measure else "none"
    # لا رجلَ حاضرٌ (khabar) and a hal or tamyeez in nasb are not followers
    if told_of_subject(token, head) or indefinite_nasb(token):
        return "none"
    return "naat" if token.get("ud") == "ADJ" else "none"
