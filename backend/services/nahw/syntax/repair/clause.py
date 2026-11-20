"""Repair 7: clauses a particle opens or a speaker leaves short, that the parser reads as a plain sentence: an oath over a relative or a noun, أمّا and its answer, a noun joined after وَلَا, a noun said again after و, a khabar after the doer."""
from __future__ import annotations

from backend.services.nahw.book import is_one
from backend.services.text.arabic_text import strip_diacritics
from backend.services.nahw.syntax.facts import Sentence, is_known, is_sworn_relative, is_preposition, is_suffix, is_verb, noun_tagged, stays_adverb, sworn_by, typed_case_of


def oath_clause(s: Sentence) -> None:
    """وَالَّذِي نَفْسِي بِيَدِهِ لَا تَدْخُلُونَ الْجَنَّةَ، وَاللَّهِ مَا أَنْعَمَ اللَّهُ عَلَيَّ: the و that opens a sentence is
    the oath (closed_words jarr `oath_only`); the relative or the noun in jarr after it is the sworn-by, its majrur, and
    what follows a relative is its صلة, a nominal one (نفسي بيده: the khabar a jar-majrur said after its mubtada). The sentence
    is an oath only when the main clause is its answer (closed_words jarr `oath_answer`: the lam,
    لا, ما, قد, إن; Ibn Aqil vol 4 p42): without one the و resumes (وَالَّذِينَ هُمْ عَنِ اللَّغْوِ مُعْرِضُونَ)."""
    tokens = s.tokens
    root = next((t for t in tokens if t["head"] == 0), None)
    relative = sworn_by(s)
    if not (root and relative and root["id"] > relative["id"]):
        return
    first = tokens[tokens.index(relative) - 1]
    sworn_relative = is_sworn_relative(relative)
    # the answer is a particle under the main clause, or the clause's own head (فَوَالَّذِي لَا إِلَهَ غَيْرُهُ إِنَّ أَحَدَكُمْ)
    if not (is_one(root["lemma"], "jarr", "oath_answer") or any(
            k["pos"] == "PRT" and k["id"] < root["id"] and is_one(k["lemma"], "jarr", "oath_answer") for k in s.kids(root))):
        return
    s.relink(first, root["id"], "MOD")
    s.relink(relative, first["id"], "OBJ")
    if not sworn_relative:
        return
    named = next((k for k in s.kids(relative) if noun_tagged(k) and not is_verb(k) and k["id"] > relative["id"]), None)
    jar = next((k for k in s.kids(relative) if is_preposition(k) and named and k["id"] > named["id"]), None)
    if named and jar:  # the khabar a jar-majrur, the noun before it its mubtada
        s.relink(named, jar["id"], "SBJ")
        s.relink(jar, relative["id"], "MOD")


def amma_clause(s: Sentence) -> None:
    """فَأَمَّا الَّذِي يَرَى النَّاسُ أَنَّهَا النَّارُ فَمَاءٌ بَارِدٌ، وَأَمَّا مَنْ كَانَ مِنْ أَهْلِ الشَّقَاءِ
    فَيُيَسَّرُ: the one word after أما is the mubtada, its صلة and the rest under it, and what comes
    after the فاء is its khabar, said of it (closed_words ghair_amila_other `detail`; Awdah
    al-Masalik vol 4 p231-232). The parser hangs the noun on أما as its object, or lets a verb
    take it as doer (كان من), so it is hung on the answer as that answer's subject, and the verb
    it was doer of becomes its صلة."""
    tokens = s.tokens
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
            s.relink(told, noun["id"], "MOD")
        s.relink(noun, root["id"], "SBJ")


def negated_conjunct(s: Sentence) -> None:
    """مَا جَاءَنِي زَيْدٌ وَلَا عَمْرٌو، لَيْسَ الْمِسْكِينُ ... وَلَا اللُّقْمَةُ: the و joins, and the لا after it only
    makes the negation certain (Mughni V1 p316: فالعاطف الواو ولا توكيد للنفي), so the noun after
    the pair is joined to the noun before the و, not the subject of the لا. The parser hangs the
    لا on the و and the noun on the لا; the noun goes under the و, the لا beside it. A known noun
    only: لا before an unknown one is the لا of genus (وَلَا رَجُلَ)."""
    tokens = s.tokens
    for waw in tokens:
        la, noun, before = s.by_id.get(waw["id"] + 1), s.by_id.get(waw["id"] + 2), s.head(waw)
        if (waw["pos"] == "PRT" and waw["lemma"].strip("+") == "و" and before and noun_tagged(before) and la and noun
                and strip_diacritics(la["lemma"]) == "لا" and la["head"] == waw["id"] and noun["head"] == la["id"]
                and noun["rel"] == "SBJ" and noun_tagged(noun) and not is_verb(noun) and is_known(noun, s)):
            s.relink(noun, waw["id"], "OBJ")
            s.relink(la, noun["id"], "MOD")


def said_again(s: Sentence) -> None:
    """الْيَدُ الْعُلْيَا خَيْرٌ مِنَ الْيَدِ السُّفْلَى وَالْيَدُ الْعُلْيَا الْمُنْفِقَةُ وَالسُّفْلَى السَّائِلَةُ: a noun after a و
    that says again in full what the sentence already named, a noun with its صفة (اليد العليا) or a صفة standing for
    the noun it described (السفلى), speaks of that thing anew (التقسيم): it opens its own sentence, a مبتدأ (Ajrumiyya,
    المبتدأ والخبر; page unchecked), and the word in raf' after it is its خبر, what is newly said of it. In another case
    it is joined (رَأَيْتُ الْيَدَ السُّفْلَى وَالسُّفْلَى السَّائِلَةَ), and a noun alone said again (جَاءَ الرَّجُلُ الطَّوِيلُ
    وَالرَّجُلُ الْقَصِيرُ) is a second thing, joined, its صفة its own. So is a noun with a word of otherness after it
    (وَالطَّالِبُ الْمُجْتَهِدُ الْآخَرُ): another thing, not the first said again, the word its صفة wherever the parser hung it.
    Nor is a noun with a raf' word after the phrase (الرَّجُلُ الصَّالِحُ وَالرَّجُلُ الصَّالِحُ الْغَنِيُّ سَوَاءٌ): that word is the
    خبر the two share, so the noun is joined to the first.
    The parser hangs the noun on the و as a joined word and the new word on it as one more صفة; the new word goes
    under the و, the noun under it as its مبتدأ."""
    for waw in s.tokens:
        noun = s.by_id.get(waw["id"] + 1)
        if not (waw["pos"] == "PRT" and waw["lemma"].strip("+") == "و" and noun):
            continue
        earlier = [t for t in s.tokens if t["id"] < waw["id"] and noun_tagged(t)]
        said = {t["lemma"] for t in earlier}
        described_by = {t["lemma"] for t in earlier if t["rel"] == "MOD" and (owner := s.head(t)) and noun_tagged(owner)}
        # the noun's own words after it, and the one the parser may have made the noun's head (its خبر)
        phrase = [noun]
        while (nxt := s.by_id.get(phrase[-1]["id"] + 1)) and (nxt["head"] == noun["id"] or noun["head"] == nxt["id"]):
            phrase.append(nxt)
        *again, new = phrase
        if again and is_one(new["lemma"], "otherness"):
            s.relink(noun, waw["id"], "OBJ")
            s.relink(new, noun["id"], "MOD")
            continue
        # only a sentence that opens with a noun is divided so: after a verb (جَاءَ الرَّجُلُ
        # الطَّوِيلُ وَالرَّجُلُ الطَّوِيلُ نَفْسُهُ) the noun said again is joined to its doer, its words its صفات
        shared = (after := s.by_id.get(new["id"] + 1)) and noun_tagged(after) and typed_case_of(after) in ("u", None)
        if (len(again) > 1 or again and noun["lemma"] in described_by) and all(t["lemma"] in said for t in again) \
                and typed_case_of(new) == "u" and noun_tagged(s.tokens[0]) and not shared:
            s.relink(new, waw["id"], "OBJ")
            s.relink(noun, new["id"], "SBJ")


def doer_then_khabar(s: Sentence) -> None:
    """خَصْلَتَيْنِ يُحِبُّهُمَا اللَّهُ الْحِلْمُ وَالْأَنَاةُ: a verb has one doer (Tasheel 2.4.1), so a second raf' noun
    after it, with a pronoun already written onto the verb for it to name (هما), is no second doer
    but the khabar of a مبتدأ left out, هما الحلم والأناة (Ibn Aqil V1 p243: وحذف ما يعلم جائز). Not one
    that carries a pronoun back to the doer (أعجبني المعلم علمه: a بدل الاشتمال).
    The parser hangs both as the verb's subject; the second hangs on the verb as its khabar."""
    tokens = s.tokens
    for verb in tokens:
        kids = s.kids(verb)
        doers = [k for k in kids if k["rel"] == "SBJ" and noun_tagged(k) and not is_verb(k) and not is_suffix(k)]
        if is_verb(verb) and len(doers) == 2 and any(is_suffix(k) and k["rel"] == "OBJ" for k in kids) \
                and doers[0]["id"] < doers[1]["id"] and typed_case_of(doers[1]) == "u" \
                and not any(is_suffix(k) for k in s.kids(doers[1])):
            doers[1]["rel"] = "PRD"
