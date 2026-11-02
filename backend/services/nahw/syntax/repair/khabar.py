"""Repair 5: khabars the parser hung elsewhere: a second adjective khabar, and a لا clause after its mubtada."""
from __future__ import annotations

from backend.services.text.arabic_text import strip_diacritics
from backend.services.nahw.book import is_one
from backend.services.nahw.syntax.facts import Sentence, noun_tagged, is_name, read_as, is_describing, is_elative, is_participle, is_preposition, is_verb, is_zarf, shows_jarr, typed_case_of, typed_or_parsed_case, subject_link, works_as_verb


def second_khabar(tokens: list[dict]) -> None:
    """إِنَّ اللَّهَ كَانَ عَلِيمًا حَكِيمًا، زيدٌ ذكيٌّ مجتهدٌ: a describing word describes a noun, not
    another describing word, so the second, in the first's case, is a khabar of its own
    (تعدد الخبر). A noun khabar keeps its صفة (زيدٌ طالبٌ مجتهدٌ)."""
    s = Sentence(tokens)
    for token in tokens:
        head = s.head(token)
        if (head and token["rel"] == "MOD" and head["rel"] == "PRD" and head["id"] == token["id"] - 1
                and is_participle(head) and is_participle(token) and token.get("stt") == head.get("stt") == "i"
                and typed_or_parsed_case(token) == typed_or_parsed_case(head)):
            token["head"], token["rel"] = head["head"], "PRD"


def naat_after_its_noun(tokens: list[dict]) -> None:
    """الخياطون حاذقون: a صفة stands after its موصوف, never before it, so in a verbless sentence a word
    with ال the parser hung on the indefinite word after it, which heads the sentence, is no na't of it:
    the known word is the mubtada and the indefinite word its khabar (the khabar is the new
    information, so it is the less known: Ajrumiyya, the mubtada is a known noun)."""
    s = Sentence(tokens)
    if not s.verbless:
        return
    for token in tokens:
        head = s.head(token)
        if (head and token["rel"] == "MOD" and head["id"] > token["id"] and head["head"] == 0
                and noun_tagged(token) and noun_tagged(head) and token.get("stt") == "d"
                and token["form"].startswith("ال") and head.get("stt") == "i"):
            token["head"], token["rel"] = 0, "---"
            head["head"], head["rel"] = token["id"], "PRD"


def hasr_khabar(tokens: list[dict]) -> None:
    """مَا جَزَاؤُهُ إِلَّا سَجْنُهُ، مَا مُحَمَّدٌ إِلَّا رَسُولٌ: after a negation, إلا excepts nothing; the
    word after it takes the place the sentence leaves for it (closed_words hasr, Tasheel 3.8.7 p85).
    A verbless clause with its mubtada said leaves the khabar, so a noun the parser hung on an إلا
    that hangs on that mubtada is its khabar, and the negation and إلا hang on it."""
    s = Sentence(tokens)
    for told in tokens:
        illa = s.head(told)
        if not (illa and illa["pos"] == "PRT" and is_one(illa["lemma"], "hasr") and illa["id"] < told["id"] and noun_tagged(told)):
            continue
        before = tokens[:tokens.index(illa)]
        # the parser may tag ما a noun, and hang إلا on the mubtada or on the negation
        negation = next((t for t in reversed(before) if is_one(t["lemma"], "negation") and not read_as(t, "la_jins")), None)
        if not negation or any(is_verb(t) for t in tokens[tokens.index(negation):tokens.index(told)]):
            continue  # ما جاء إلا زيدٌ: a verb in the clause takes the word after إلا
        held = s.head(illa)
        subject = held if held is not negation else next((k for k in s.kids(negation) if k in before and subject_link(k)), None)
        if subject and subject is not negation and noun_tagged(subject):
            # the khabar takes the clause's place (قالوا إن هذا إلا سحر: the said clause)
            told["head"], told["rel"] = negation["head"], negation["rel"]
            for word in (subject, illa, negation):
                word["head"], word["rel"] = told["id"], "SBJ" if word is subject else "MOD"
            return


def described_doer(tokens: list[dict]) -> None:
    """ما ذاهبٌ المسلمون، أذاهبٌ زيدٌ: the مبتدأ وصف (facts.Sentence.described_doer) heads its
    clause and the raf' noun after it is its doer, not its صفة: a نعت follows a noun, and the
    وصف here is no noun said of anything before it. The particle before it hangs on it."""
    if said := Sentence(tokens).described_doer:
        lead, wasf, doer = said
        doer["head"], doer["rel"] = wasf["id"], "SBJ"
        lead["head"], lead["rel"] = wasf["id"], "MOD"
        if wasf["head"] in (lead["id"], doer["id"]):
            wasf["head"], wasf["rel"] = 0, "---"


def before_la(tokens: list[dict]) -> None:
    """ذَلِكَ الْكِتَابُ لَا رَيْبَ فِيهِ: the noun of لا النافية للجنس stands after it, so a noun
    the parser hung on لا from before it is the mubtada, and the لا clause its khabar."""
    s = Sentence(tokens)
    for token in tokens:
        la = s.head(token)
        if (la and la["pos"] == "PRT" and strip_diacritics(la["form"]) == "لا" and token["id"] < la["id"]
                and subject_link(token) and la["head"] == 0):
            token["head"], token["rel"] = 0, "---"
            la["head"], la["rel"] = token["id"], "PRD"


def la_over_its_khabar(tokens: list[dict]) -> None:
    """لَا مُتْقِنًا صَنْعَتَهُ مَذْمُومٌ: لا النافية للجنس governs the pair after it (تنصب الاسم وترفع الخبر), so
    where the parser hung it under the word that is the khabar, or the noun straight after it as its
    khabar, لا heads the sentence, the noun after it is its اسم and the word it hung on its khabar."""
    s = Sentence(tokens)
    if not s.verbless:
        return
    for la in tokens:
        khabar, noun = s.head(la), s.by_id.get(la["id"] + 1)
        if (la["pos"] == "PRT" and strip_diacritics(la["form"]) == "لا" and la["rel"] == "MOD"
                and khabar and khabar["head"] == 0 and khabar["id"] > la["id"] + 1 and noun_tagged(khabar)
                and noun and noun_tagged(noun) and noun["head"] == la["id"] and noun["rel"] in ("SBJ", "PRD")):
            la["head"], la["rel"] = 0, "---"
            noun["rel"] = "SBJ"
            khabar["head"], khabar["rel"] = la["id"], "PRD"


def after_pointer(tokens: list[dict]) -> None:
    """هَاتَانِ قِلَادَتَانِ، زَيْدٌ ضَارِبٌ، وَمَا عِنْدَ اللَّهِ خَيْرٌ: the مبتدأ is as a rule the definite
    word (Ibn Aqil V1 p216: الأصل في المبتدأ أن يكون معرفة), and a نعت matches its noun in being definite
    (هذا الكتابُ، زيدٌ الكريمُ), so an indefinite noun or adjective the parser hung as the صفة of a
    definite word that opens the sentence (a pointer, a relative, a name, a word with ال), or a
    describing word it hung as its subject, is the khabar, that word its mubtada. A plain noun stays
    its subject: after ما it is the مبتدأ مؤخر of the negation (ما في الدار أحدٌ, particles `fronted`).
    A ظرف or جار ومجرور takes no subject, so one hung as the subject of the ظرف or majrur that is the
    opener's صلة (وَمَا عِنْدَ اللَّهِ خَيْرٌ وَأَبْقَى) is told of the opener. A pointer the parser hung on the
    indefinite noun after it is that noun's mubtada the same."""
    s = Sentence(tokens)
    for token in tokens:
        head = s.head(token)
        while token["rel"] == "SBJ" and head and head["head"] and _in_shibh_jumla(head, s):
            head = s.head(head)
        if (head and head["head"] == 0 and head["pos"] in ("NOM", "PROP") and not is_verb(head) and (token["rel"] == "MOD" or token["rel"] == "SBJ" and is_describing(token))
                and (head.get("pos_camel") in ("pron_dem", "pron_rel", "noun_prop") or head.get("stt") == "d")
                and token["id"] > head["id"] and token.get("pos_camel") in ("noun", "adj")
                and _indefinite(token, tokens) and typed_case_of(token) != "a"
                and not any(t is not token and t["head"] == head["id"] and t["rel"] in ("PRD", "SBJ") for t in tokens)):
            token["head"], token["rel"] = 0, "---"
            head["head"], head["rel"] = token["id"], "SBJ"
        # هَذِهِ حِجَارَةٌ: the parser may hang the pointer as the صفة of the indefinite noun after it, but a نعت
        # follows its noun, so the pointer is that noun's mubtada, as it hangs in هَذَا رَجُلٌ
        elif (token.get("pos_camel") == "pron_dem" and token["rel"] == "MOD" and head and head["head"] == 0
                and head["id"] > token["id"] and head.get("pos_camel") in ("noun", "adj")
                and _indefinite(head, tokens) and typed_case_of(head) != "a"):
            token["rel"] = "SBJ"


def told_of_jar(tokens: list[dict]) -> None:
    """لِزَيْدٍ هَذَا الْكِتَابُ، لِمَنْ هَذَا: a noun in jarr has no مبتدأ of its own, so a noun the parser
    hung as the subject of a preposition's majrur is told of by the whole جار ومجرور, the khabar
    said first, and hangs on the preposition as in لِزَيْدٍ كِتَابٌ. A وصف keeps its doer (لِلْقَائِمِ أَبُوهُ)."""
    s = Sentence(tokens)
    for token in tokens if s.verbless else ():
        majrur = s.head(token)
        jar = s.head(majrur) if majrur else None
        if (token["rel"] == "SBJ" and majrur["rel"] == "OBJ" and jar and is_preposition(jar)
                and noun_tagged(majrur) and not works_as_verb(majrur)):
            token["head"] = jar["id"]


def zarf_is_no_subject(tokens: list[dict]) -> None:
    """عِنْدَنَا ضَيْفٌ: a place or time word is built or in nasb, never the raf' a subject wears, so one the
    parser hung as the subject of the indefinite noun after it is that noun's شبه جملة, its khabar said
    first, hung on it as in عِنْدِي كِتَابٌ."""
    s = Sentence(tokens)
    for token in tokens if s.verbless else ():
        head = s.head(token)
        if (token["rel"] == "SBJ" and is_zarf(token, s) and typed_case_of(token) != "u" and head
                and head["head"] == 0 and head["id"] > token["id"] and noun_tagged(head) and _indefinite(head, tokens)):
            token["rel"] = "MOD"


def khabar_said_first(tokens: list[dict]) -> None:
    """إِنَّ عِنْدَنَا ضَيْفًا: a particle that governs a pair (إنّ، لا) has one khabar and one name, so where
    the parser hung two khabars on it, the first a place or time word, the second an indefinite noun after
    it, the first is the khabar said first and the noun is the name, as in إِنَّ لَدَيْنَا أَنْكَالًا."""
    s = Sentence(tokens)
    for particle in tokens if s.verbless else ():
        khabars = [k for k in s.kids(particle) if k["rel"] == "PRD"]
        if particle["pos"] == "PRT" and particle["head"] == 0 and len(khabars) == 2:
            first, second = khabars
            if (is_zarf(first, s) and first["id"] < second["id"] and noun_tagged(second)
                    and _indefinite(second, tokens)):
                second["rel"] = "SBJ"


def _in_shibh_jumla(token: dict, s: Sentence) -> bool:
    """A ظرف or a preposition: the head of a شبه جملة, which tells of nothing by a subject of its own."""
    return is_zarf(token, s) or is_preposition(token)


def _indefinite(token: dict, tokens: list[dict]) -> bool:
    """Without ال: read so, or read as a مضاف with nothing added to it (الملاحون أقوياء), which it then is not, or
    a مضاف to an indefinite word, which it narrows but leaves indefinite (Ibn Aqil V3 p43: وتفيد الاسم الأول تخصيصا
    إن كان المضاف إليه نكرة نحو هذا غلام امرأة وتعريفا إن كان المضاف إليه معرفة): زَيْدٌ صَاحِبُ مَالٍ."""
    if token.get("stt") != "c":
        return token.get("stt") == "i"
    added = next((t for t in tokens if t["head"] == token["id"] and t["rel"] == "IDF"), None)
    return added is None or (not is_name(added) and _indefinite(added, tokens))


def object_of_noun(tokens: list[dict]) -> None:
    """زَيْدٌ أَكْثَرُ مِنْكَ مَالًا: only a verb or a word working as one takes an object (notes,
    المفعول به: a فعل or a شبه الفعل governs it), so a word the parser hung as the object of a
    plain noun opening the sentence, both typed in raf', is that noun's khabar. A noun in nasb
    hung there after an elative khabar is the elative's تمييز (Tasheel 3.10: أفعل التفضيل
    ينصب التمييز), as the parser already hangs it when the opener is not between them."""
    s = Sentence(tokens)
    for token in tokens:
        opener = s.head(token)
        if not (opener and token["rel"] == "OBJ" and opener["rel"] == "---" and opener["id"] < token["id"]
                and not is_verb(opener) and not works_as_verb(opener)
                and typed_case_of(opener) == typed_case_of(token) == "u"):
            continue
        token["rel"] = "PRD"
        if is_elative(token):
            for kid in s.kids(opener):
                if kid["rel"] == "OBJ" and kid["id"] > token["id"] and typed_case_of(kid) == "a" and kid.get("stt") == "i":
                    kid["head"], kid["rel"] = token["id"], "TMZ"
        s = Sentence(tokens)


def elative_specified(tokens: list[dict]) -> None:
    """أَنْتُمْ أَشَدُّ رَهْبَةً: a مضاف إليه is in jarr, so an indefinite noun typed in nasb that the parser
    hung on an elative as one is its تمييز (Tasheel 3.10: أفعل التفضيل ينصب التمييز; Ibn Aqil V3 p174:
    هو أشد حمرة من زيد ... وههنا ينتصب تمييزا). A diptote's fatha is its jarr (أَفْضَلُ مَسَاجِدَ)."""
    s = Sentence(tokens)
    for token in tokens:
        head = s.head(token)
        if head and token["rel"] == "IDF" and is_elative(head) and typed_case_of(token) == "a" \
                and token.get("stt") == "i" and not shows_jarr(token):
            token["rel"] = "TMZ"
