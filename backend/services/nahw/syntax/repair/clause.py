"""Repair 7: clauses a particle opens or a speaker leaves short, that the parser reads as a plain sentence: an oath over a relative or a noun, أمّا and its answer, a noun joined after وَلَا, a khabar after the doer."""
from __future__ import annotations

from backend.services.nahw.book import is_one
from backend.services.nahw.syntax.facts import Sentence, is_known, is_preposition, is_suffix, is_verb, noun_tagged, stays_adverb, typed_case_of


def oath_clause(tokens: list[dict]) -> None:
    """وَالَّذِي نَفْسِي بِيَدِهِ لَا تَدْخُلُونَ الْجَنَّةَ، وَاللَّهِ مَا أَنْعَمَ اللَّهُ عَلَيَّ: the و that opens a sentence is
    the oath (closed_words jarr `oath_only`); the relative or the noun in jarr after it is the sworn-by, its majrur, and
    what follows a relative is its صلة, a nominal one (نفسي بيده: the khabar a jar-majrur said after its mubtada). The sentence
    is an oath only when the main clause is its answer (closed_words jarr `oath_answer`: the lam,
    لا, ما, قد, إن; Ibn Aqil vol 4 p42): without one the و resumes (وَالَّذِينَ هُمْ عَنِ اللَّغْوِ مُعْرِضُونَ)."""
    s = Sentence(tokens)
    root = next((t for t in tokens if t["head"] == 0), None)
    # فَوَالَّذِي: a فاء ties the oath to what came before (Ibn Aqil vol 4 p42), so the و is the next piece
    lead = int(bool(tokens) and tokens[0]["pos"] == "PRT" and tokens[0]["lemma"].strip("+") == "ف")
    first, relative = (tokens + [None, None, None])[lead:lead + 2]
    if not (root and first and relative and first["pos"] == "PRT" and is_one(first["lemma"], "jarr", "oath_only")
            and root["id"] > relative["id"]):
        return
    sworn_relative = is_one(relative["lemma"], "mawsul") and not is_one(relative["lemma"], "jazm", "conditional_nouns")
    if not (sworn_relative or noun_tagged(relative) and typed_case_of(relative) == "i"):
        return
    # the answer is a particle under the main clause, or the clause's own head (فَوَالَّذِي لَا إِلَهَ غَيْرُهُ إِنَّ أَحَدَكُمْ)
    if not (is_one(root["lemma"], "jarr", "oath_answer") or any(
            k["pos"] == "PRT" and k["id"] < root["id"] and is_one(k["lemma"], "jarr", "oath_answer") for k in s.kids(root))):
        return
    first["head"], first["rel"] = root["id"], "MOD"
    relative["head"], relative["rel"] = first["id"], "OBJ"
    if not sworn_relative:
        return
    named = next((k for k in s.kids(relative) if noun_tagged(k) and not is_verb(k) and k["id"] > relative["id"]), None)
    jar = next((k for k in s.kids(relative) if is_preposition(k) and named and k["id"] > named["id"]), None)
    if named and jar:  # the khabar a jar-majrur, the noun before it its mubtada
        named["head"], named["rel"] = jar["id"], "SBJ"
        jar["head"], jar["rel"] = relative["id"], "MOD"


def amma_clause(tokens: list[dict]) -> None:
    """فَأَمَّا الَّذِي يَرَى النَّاسُ أَنَّهَا النَّارُ فَمَاءٌ بَارِدٌ، وَأَمَّا مَنْ كَانَ مِنْ أَهْلِ الشَّقَاءِ
    فَيُيَسَّرُ: the one word after أما is the mubtada, its صلة and the rest under it, and what comes
    after the فاء is its khabar, said of it (closed_words ghair_amila_other `detail`; Awdah
    al-Masalik vol 4 p231-232). The parser hangs the noun on أما as its object, or lets a verb
    take it as doer (كان من), so it is hung on the answer as that answer's subject, and the verb
    it was doer of becomes its صلة."""
    s = Sentence(tokens)
    root = next((t for t in tokens if t["head"] == 0), None)
    for amma in tokens:
        noun = s.by_id.get(amma["id"] + 1)
        if not (root and noun and amma["pos"] == "PRT" and is_one(amma["lemma"], "ghair_amila_other", "detail")
                and noun_tagged(noun) and not is_verb(noun) and not stays_adverb(noun) and root["id"] > noun["id"]):
            continue
        if not any(t["pos"] == "PRT" and t["lemma"].strip("+") == "ف" and t["head"] == root["id"] and t["id"] > noun["id"] for t in tokens):
            continue
        told = s.head(noun)
        if told and is_verb(told) and told["head"] == amma["id"]:
            told["head"], told["rel"] = noun["id"], "MOD"
        noun["head"], noun["rel"] = root["id"], "SBJ"


def negated_conjunct(tokens: list[dict]) -> None:
    """مَا جَاءَنِي زَيْدٌ وَلَا عَمْرٌو، لَيْسَ الْمِسْكِينُ ... وَلَا اللُّقْمَةُ: the و joins, and the لا after it only
    makes the negation certain (Mughni V1 p316: فالعاطف الواو ولا توكيد للنفي), so the noun after
    the pair is joined to the noun before the و, not the subject of the لا. The parser hangs the
    لا on the و and the noun on the لا; the noun goes under the و, the لا beside it. A known noun
    only: لا before an unknown one is the لا of genus (وَلَا رَجُلَ)."""
    s = Sentence(tokens)
    for waw in tokens:
        la, noun, before = s.by_id.get(waw["id"] + 1), s.by_id.get(waw["id"] + 2), s.head(waw)
        if (waw["pos"] == "PRT" and waw["lemma"].strip("+") == "و" and before and noun_tagged(before) and la and noun
                and is_one(la["lemma"], "negation") and la["head"] == waw["id"] and noun["head"] == la["id"]
                and noun["rel"] == "SBJ" and noun_tagged(noun) and not is_verb(noun) and is_known(noun, s)):
            noun["head"], noun["rel"] = waw["id"], "OBJ"
            la["head"], la["rel"] = noun["id"], "MOD"



def doer_then_khabar(tokens: list[dict]) -> None:
    """خَصْلَتَيْنِ يُحِبُّهُمَا اللَّهُ الْحِلْمُ وَالْأَنَاةُ: a verb has one doer (Tasheel 2.4.1), so a second raf' noun
    after it, with a pronoun already written onto the verb for it to name (هما), is no second doer
    but the khabar of a مبتدأ left out, هما الحلم والأناة (Ibn Aqil V1 p243: وحذف ما يعلم جائز). Not one
    that carries a pronoun back to the doer (أعجبني المعلم علمه: a بدل الاشتمال).
    The parser hangs both as the verb's subject; the second hangs on the verb as its khabar."""
    s = Sentence(tokens)
    for verb in tokens:
        kids = s.kids(verb)
        doers = [k for k in kids if k["rel"] == "SBJ" and noun_tagged(k) and not is_verb(k) and not is_suffix(k)]
        if is_verb(verb) and len(doers) == 2 and any(is_suffix(k) and k["rel"] == "OBJ" for k in kids) \
                and doers[0]["id"] < doers[1]["id"] and typed_case_of(doers[1]) == "u" \
                and not any(is_suffix(k) for k in s.kids(doers[1])):
            doers[1]["rel"] = "PRD"
