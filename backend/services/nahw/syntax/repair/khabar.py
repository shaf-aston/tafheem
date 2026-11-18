"""Repair 5: khabars the parser hung elsewhere: a second adjective khabar, and a لا clause after its mubtada."""
from __future__ import annotations

from backend.services.text.arabic_text import strip_diacritics
from backend.services.nahw.book import frames, is_one, kaffa_sister, is_subject_pronoun
from backend.services.nahw.syntax.facts import Sentence, attached_pronoun, is_built, is_called_alone, is_known, is_name, is_suffix, listed, noun_tagged, reaches_pronoun, read_as, is_describing, is_elative, is_participle, is_prefix, is_preposition, is_verb, is_zarf, is_masdar, zarf_in_nasb, shows_jarr, typed_case_of, typed_or_parsed_case, subject_link, works_as_verb


def second_khabar(s: Sentence) -> None:
    """إِنَّ اللَّهَ كَانَ عَلِيمًا حَكِيمًا، زيدٌ ذكيٌّ مجتهدٌ: a describing word describes a noun, not
    another describing word, so the second, in the first's case, is a khabar of its own
    (تعدد الخبر). A noun khabar keeps its صفة (زيدٌ طالبٌ مجتهدٌ)."""
    tokens = s.tokens
    for token in tokens:
        head = s.head(token)
        if (head and token["rel"] == "MOD" and head["rel"] == "PRD" and head["id"] == token["id"] - 1
                and is_participle(head) and is_participle(token) and token.get("stt") == head.get("stt") == "i"
                and typed_or_parsed_case(token) == typed_or_parsed_case(head)):
            s.relink(token, head["head"], "PRD")


def naat_after_its_noun(s: Sentence) -> None:
    """الخياطون حاذقون: a صفة stands after its موصوف, never before it, so in a verbless sentence a word
    with ال the parser hung on the indefinite word after it, which heads the sentence, is no na't of it:
    the known word is the mubtada and the indefinite word its khabar (the khabar is the new
    information, so it is the less known: Ajrumiyya, the mubtada is a known noun). A مضاف to a known noun is
    known too (يَوْمُ الْجُمُعَةِ يَوْمٌ مُبَارَكٌ)."""
    tokens = s.tokens
    if not s.verbless:
        return
    for token in tokens:
        head = s.head(token)
        if (head and token["rel"] == "MOD" and head["id"] > token["id"] and head["head"] == 0
                and noun_tagged(token) and noun_tagged(head) and head.get("stt") != "c"
                and not is_known(head, s) and is_known(token, s)):
            s.relink(token, 0, "---")
            s.relink(head, token["id"], "PRD")


def known_pair_in_order(s: Sentence) -> None:
    """إِنَّمَا زَيْدٌ الْقَائِمُ، إِنَّمَا وَلِيُّكُمُ اللَّهُ: a known noun said first is the مبتدأ; where the second is known
    too, nothing but their order tells them apart (Ibn Aqil, تقديم المبتدأ وجوبًا إذا تساويا تعريفًا: page unchecked), and
    where it is not, the less known is the khabar. So a known khabar the parser put before a subject of its own is
    the مبتدأ, and that subject its khabar. A word that works as a verb keeps its doer (إِنَّمَا الْقَائِمُ أَبُوهُ); one said
    after its subject is in order already (الْمُسْلِمُ مَنْ سَلِمَ); ما that may be نافية is no noun to weigh (مَا جَزَاؤُهُ إِلَّا سَجْنُهُ).
    A khabar tells of one مبتدأ, so one with another subject is no pair (أَنَا سَيِّدُ وَلَدِ آدَمَ وَأَوَّلُ مَنْ يَنْشَقُّ)."""
    for told in s.tokens:
        first = s.head(told)
        # the first hung as the khabar, or as the subject of an إنّ stopped by ما that has no khabar (إِنَّمَا أَخُوكَ زَيْدٌ)
        particle = s.head(first) if first and first["rel"] == "SBJ" else None
        no_khabar = particle and particle["pos"] == "PRT" and kaffa_sister(particle["lemma"]) and not any(k["rel"] == "PRD" for k in s.kids(particle))
        if (first and told["rel"] == "SBJ" and first["id"] < told["id"] and (first["rel"] in ("PRD", "---") or no_khabar)
                and not is_one(first["lemma"], "negation") and works_as_verb(first) is None and not is_zarf(first, s)
                and is_known(first, s) and not any(k["rel"] == "SBJ" and k is not told for k in s.kids(first))):
            s.relink(told, first["head"], "PRD" if no_khabar else first["rel"])
            s.relink(first, told["id"], "SBJ")


def naat_not_subject(s: Sentence) -> None:
    """إِنَّمَا زَيْدٌ الْكَرِيمُ قَائِمٌ: a word with ال straight after a known noun that is itself a subject, in its
    case, is its صفة (a نعت follows its noun in التعريف and in case, Tasheel 3.10.1): a subject's word is told of, it
    tells nothing, and a name or plain noun works on no doer of its own (القائمُ أبوه زيدٌ: a participle does)."""
    for token in s.tokens:
        noun = s.head(token)
        if (noun and token["rel"] == "SBJ" and noun["rel"] == "SBJ" and noun["id"] == token["id"] - 1
                and token.get("stt") == "d" and noun_tagged(token) and not is_verb(token)
                and noun_tagged(noun) and is_known(noun, s) and not is_describing(noun) and works_as_verb(noun) is None
                and typed_or_parsed_case(token) == typed_or_parsed_case(noun)):
            token["rel"] = "MOD"


def hasr_khabar(s: Sentence) -> None:
    """مَا جَزَاؤُهُ إِلَّا سَجْنُهُ، مَا مُحَمَّدٌ إِلَّا رَسُولٌ: after a negation, إلا excepts nothing; the
    word after it takes the place the sentence leaves for it (closed_words hasr, Tasheel 3.8.7 p85).
    A verbless clause with its mubtada said leaves the khabar, so a noun the parser hung on an إلا
    that hangs on that mubtada is its khabar, and the negation and إلا hang on it. Not when the mubtada is typed in
    nasb: that إن is إنّ, and إلا then excepts from its اسم."""
    tokens = s.tokens
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
        # إِنَّ لِلَّهِ تِسْعَةً ... إِلَّا وَاحِدًا: a noun the reader put in nasb after إن is إنّ's اسم, so that إن denies nothing (Tasheel 1.8 p21)
        if subject and subject is not negation and noun_tagged(subject) and typed_case_of(subject) != "a":
            # the khabar takes the clause's place (قالوا إن هذا إلا سحر: the said clause)
            s.relink(told, negation["head"], negation["rel"])
            for word in (subject, illa, negation):
                s.relink(word, told["id"], "SBJ" if word is subject else "MOD")
            return


def described_doer(s: Sentence) -> None:
    """ما ذاهبٌ المسلمون، أذاهبٌ زيدٌ: the مبتدأ وصف (facts.Sentence.described_doer) heads its
    clause and the raf' noun after it is its doer, not its صفة: a نعت follows a noun, and the
    وصف here is no noun said of anything before it. The particle before it hangs on it."""
    if said := s.described_doer:
        lead, wasf, doer = said
        s.relink(doer, wasf["id"], "SBJ")
        s.relink(lead, wasf["id"], "MOD")
        if wasf["head"] in (lead["id"], doer["id"]):
            s.relink(wasf, 0, "---")


def before_la(s: Sentence) -> None:
    """ذَلِكَ الْكِتَابُ لَا رَيْبَ فِيهِ: the noun of لا النافية للجنس stands after it, so a noun
    the parser hung on لا from before it is the mubtada, and the لا clause its khabar."""
    tokens = s.tokens
    for token in tokens:
        la = s.head(token)
        if (la and la["pos"] == "PRT" and strip_diacritics(la["form"]) == "لا" and token["id"] < la["id"]
                and subject_link(token) and la["head"] == 0):
            s.relink(token, 0, "---")
            s.relink(la, token["id"], "PRD")
        # هُوَ الْحَيُّ لَا إِلَهَ إِلَّا هُوَ: nor does its khabar stand before it, so a word hung on it as one from before it,
        # where لا is told of the noun before that word, is that noun's khabar, the لا sentence a second
        elif (la and la["pos"] == "PRT" and strip_diacritics(la["form"]) == "لا" and token["id"] < la["id"] and token["rel"] == "PRD"
                and (told := s.head(la)) and told["id"] < token["id"] and la["rel"] == "PRD" and noun_tagged(told)):
            s.relink(token, told["id"], "PRD")
            # its اسم stands straight after it: left with no subject, the noun there is that اسم
            noun = s.by_id.get(la["id"] + 1)
            if noun and noun["head"] == la["id"] and noun["rel"] == "PRD" and noun_tagged(noun) \
                    and not any(subject_link(k) for k in s.kids(la)):
                noun["rel"] = "SBJ"
        # اللَّهُمَّ أَنْتَ رَبِّي لَا إِلَهَ إِلَّا أَنْتَ: a raf' pronoun hung on لا from before it is no part of its sentence
        # either; it is a mubtada, and the noun straight after it, hung on it, its khabar (a pronoun takes no صفة)
        elif (la and la["pos"] == "PRT" and strip_diacritics(la["form"]) == "لا" and token["id"] < la["id"]
                and subject_link(token) and is_subject_pronoun(token)
                and (khabar := s.by_id.get(token["id"] + 1)) and khabar["head"] == token["id"] and noun_tagged(khabar)):
            s.relink(khabar, la["head"], la["rel"])
            s.relink(token, khabar["id"], "SBJ")
            s.relink(la, khabar["id"], "MOD")


def la_over_its_khabar(s: Sentence) -> None:
    """لَا مُتْقِنًا صَنْعَتَهُ مَذْمُومٌ: لا النافية للجنس governs the pair after it (تنصب الاسم وترفع الخبر), so
    where the parser hung it under the word that is the khabar, or the noun straight after it as its
    khabar, لا heads the sentence, the noun after it is its اسم and the word it hung on its khabar."""
    tokens = s.tokens
    if not s.verbless:
        return
    for la in tokens:
        khabar, noun = s.head(la), s.by_id.get(la["id"] + 1)
        if (la["pos"] == "PRT" and strip_diacritics(la["form"]) == "لا" and la["rel"] == "MOD"
                and khabar and khabar["head"] == 0 and khabar["id"] > la["id"] + 1 and noun_tagged(khabar)
                and noun and noun_tagged(noun) and noun["head"] == la["id"] and noun["rel"] in ("SBJ", "PRD")):
            s.relink(la, 0, "---")
            noun["rel"] = "SBJ"
            s.relink(khabar, la["id"], "PRD")


def after_pointer(s: Sentence) -> None:
    """هَاتَانِ قِلَادَتَانِ، زَيْدٌ ضَارِبٌ، وَمَا عِنْدَ اللَّهِ خَيْرٌ: the مبتدأ is as a rule the definite
    word (Ibn Aqil V1 p216: الأصل في المبتدأ أن يكون معرفة), and a نعت matches its noun in being definite
    (هذا الكتابُ، زيدٌ الكريمُ), so an indefinite noun or adjective the parser hung as the صفة of a
    definite word that opens the sentence (a pointer, a relative, a name, a word with ال), or a
    describing word it hung as its subject, is the khabar, that word its mubtada. A plain noun stays
    its subject: after ما it is the مبتدأ مؤخر of the negation (ما في الدار أحدٌ, particles `fronted`).
    A ظرف or جار ومجرور takes no subject, so one hung as the subject of the ظرف or majrur that is the
    opener's صلة (وَمَا عِنْدَ اللَّهِ خَيْرٌ وَأَبْقَى) is told of the opener. A pointer the parser hung on the
    indefinite noun after it is that noun's mubtada the same."""
    tokens = s.tokens
    for token in tokens:
        head = s.head(token)
        while token["rel"] == "SBJ" and head and head["head"] and _in_shibh_jumla(head, s):
            head = s.head(head)
        if (head and head["head"] == 0 and head["pos"] in ("NOM", "PROP") and not is_verb(head) and (token["rel"] == "MOD" or token["rel"] == "SBJ" and is_describing(token))
                and is_known(head, s)
                and token["id"] > head["id"] and token.get("pos_camel") in ("noun", "adj")
                and not is_known(token, s) and typed_case_of(token) != "a"
                and not any(t is not token and t["head"] == head["id"] and t["rel"] in ("PRD", "SBJ") for t in tokens)):
            s.relink(token, 0, "---")
            s.relink(head, token["id"], "SBJ")
        # هَذِهِ حِجَارَةٌ: the parser may hang the pointer as the صفة of the indefinite noun after it, but a نعت
        # follows its noun, so the pointer is that noun's mubtada, as it hangs in هَذَا رَجُلٌ
        elif (token.get("pos_camel") == "pron_dem" and token["rel"] == "MOD" and head and head["head"] == 0
                and head["id"] > token["id"] and head.get("pos_camel") in ("noun", "adj")
                and not is_known(head, s) and typed_case_of(head) != "a"):
            token["rel"] = "SBJ"


def name_not_told_by_ma(s: Sentence) -> None:
    """زَيْدٌ مَا رَأَيْتُهُ: ما is for what has no mind (Ibn Aqil, al-mawsul al-mushtarak; page unchecked), so a person's
    name opening the clause is told of by no relative ما: ما straight after it, a verb straight after ما holding the ه
    that goes back to the name, negates that verb, and the verb's clause is the name's khabar, hung as the parser hangs
    زَيْدٌ لَمْ أَرَهُ (the verb on the name, the negation on the verb)."""
    for ma in s.tokens:
        name, verb = s.by_id.get(ma["id"] - 1), s.by_id.get(ma["id"] + 1)
        if not (name and verb and strip_diacritics(ma["form"]) == "ما" and ma["pos"] != "PRT" and is_name(name) and is_verb(verb)
                and (ma["head"] == name["id"] or name["head"] == ma["id"]) and verb["head"] == ma["id"]
                and any(attached_pronoun(k) and strip_diacritics(k["form"]).strip("+") == "ه" for k in s.kids(verb))):
            continue
        if name["head"] == ma["id"]:
            s.relink(name, ma["head"], ma["rel"])
        s.relink(verb, name["id"], "---")
        s.relink(ma, verb["id"], "MOD")
        ma["pos"], ma["pos_camel"] = "PRT", "part_neg"


def relative_khabar(s: Sentence) -> None:
    """الْكَيِّسُ مَنْ دَانَ نَفْسَهُ، إِنَّمَا الشَّدِيدُ الَّذِي يَمْلِكُ نَفْسَهُ: a known word opening the clause, then a
    relative with its صلة, and nothing else said of that word, is told by the relative: both are definite, so the
    first is the mubtada and the relative its khabar (Ibn Aqil V1 p216: المبتدأ معرفة، and the موصول
    with its صلة is one word, the khabar of the clause). مَنْ and ما are never a صفة (they are
    mubham, no noun takes them as one); the الذي family only after a particle that cannot be a noun's governor (إنما),
    since الرجل الذي نجح alone is a phrase. The relative heads the clause, the known word hangs on it as its
    subject, as the parser draws المؤمن من أمنه الناس."""
    tokens = s.tokens
    for relative in tokens:
        noun = s.head(relative)
        if not (noun and relative["rel"] == "MOD" and "pron_rel" in relative.get("pos_camel", "")
                and noun["id"] == relative["id"] - 1 and noun_tagged(noun) and not is_verb(noun)
                and is_known(noun, s) and typed_case_of(noun) in (None, "u")):
            continue
        above = s.head(noun)
        if noun["head"] != 0 and not (above and above["pos"] == "PRT" and above.get("pos_camel") != "prep"):
            continue
        if not (is_one(relative["lemma"], "mawsul", "mubham") or above):
            continue
        inside = s.below(relative)
        # nothing else is said of the known word, and no word after the relative's clause says it
        if any(k is not relative and k["rel"] in ("PRD", "SBJ", "OBJ") for k in s.kids(noun)):
            continue
        if any(t["id"] > relative["id"] and t["id"] not in inside and t["pos"] != "PRT" and t["head"] in (noun["id"], noun["head"], 0)
               for t in tokens):
            continue
        s.relink(relative, noun["head"], noun["rel"])
        s.relink(noun, relative["id"], "SBJ")


def khabar_after_silah(s: Sentence) -> None:
    """الرَّجُلُ الَّذِي أَبُوهُ عَالِمٌ كَرِيمٌ، زَيْدٌ الَّذِي أُمُّهُ كَرِيمَةٌ نَاجِحٌ: a known word opening the clause, a الذي
    hung on it as its صفة, and a صلة that is a whole sentence (a مبتدأ and its khabar): the raf' word
    closing the clause, agreeing with that known word, is told of it (its khabar), not more of the صلة, or the
    clause tells nothing (الكلام ما أفاد). The الذي already wears the noun's gender and number as the language
    treats it (الطُّلَّابُ الَّذِينَ: men; الْكُتُبُ الَّتِي: a plural not of people, feminine one), so the khabar must wear
    the same: كِرَامٌ is told of الطلاب, كَرِيمٌ only describes the word inside the صلة."""
    words = [t for t in s.tokens if not is_suffix(t)]
    last = words[-1] if words else None
    for relative in s.tokens:
        noun, said = s.head(relative), s.head(last) if last else None
        if not (noun and said and noun["head"] == 0 and relative["rel"] == "MOD" and "pron_rel" in relative.get("pos_camel", "")
                and noun_tagged(noun) and not is_verb(noun)):
            continue
        # the word it hangs on is a khabar inside the صلة (or a sentence joined to it), its own مبتدأ before it
        if not (any(k["rel"] == "SBJ" and k["id"] < said["id"] for k in s.kids(said))
                and noun_tagged(last) and not is_verb(last)
                and typed_or_parsed_case(last) in (None, "u") and (last.get("gen"), last.get("num")) == (relative.get("gen"), relative.get("num"))):
            continue
        s.relink(last, 0, "---")
        s.relink(noun, last["id"], "SBJ")


def majrur_of_jar(s: Sentence) -> None:
    """هَلْ مِنْ مُجِيبٍ، مَا لَنَا مِنْ شَافِعٍ: the noun written straight after a preposition word of its own (not a letter joined to the noun: لَآيَاتٍ) is its
    مجرور; where the parser hung it as a subject of the preposition (or of the word before it), it is the
    preposition's object, and told_of_jar then reads what is said of it."""
    tokens = s.tokens
    for jar in tokens:
        noun = next((t for t in tokens if t["id"] == jar["id"] + 1), None)
        if (noun and is_preposition(jar) and not is_prefix(jar) and noun_tagged(noun) and not is_verb(noun) and noun["rel"] == "SBJ"
                and noun["head"] in (jar["id"], jar["head"]) and not any(k["rel"] == "OBJ" for k in s.kids(jar))):
            s.relink(noun, jar["id"], "OBJ")


def hung_on_pronoun(s: Sentence) -> None:
    """إِنِّي مُكَاثِرٌ بِكُمُ الْأُمَمَ: a pronoun written onto a preposition governs nothing, so a word the
    parser hung on it hangs, as the same link, on what the جار ومجرور hangs on (here the participle)."""
    for token in s.tokens:
        pronoun = s.head(token)
        jar = s.head(pronoun) if pronoun else None
        if jar and s.head(jar) and attached_pronoun(pronoun) and is_preposition(jar) and token["id"] > pronoun["id"]:
            s.relink(token, jar["head"], token["rel"])


def told_of_jar(s: Sentence) -> None:
    """لِزَيْدٍ هَذَا الْكِتَابُ، لِمَنْ هَذَا: a noun in jarr has no مبتدأ of its own, so a noun the parser
    hung as the subject of a preposition's majrur is told of by the whole جار ومجرور, the khabar
    said first, and hangs on the preposition as in لِزَيْدٍ كِتَابٌ. A وصف keeps its doer (لِلْقَائِمِ أَبُوهُ)."""
    tokens = s.tokens
    for token in tokens if s.verbless else ():
        majrur = s.head(token)
        jar = s.head(majrur) if majrur else None
        if (jar and token["rel"] == "SBJ" and majrur["rel"] == "OBJ" and is_preposition(jar)
                and noun_tagged(majrur) and not works_as_verb(majrur)):
            s.relink(token, jar["id"], token["rel"])


def zarf_is_no_subject(s: Sentence) -> None:
    """عِنْدَنَا ضَيْفٌ: a place or time word is built or in nasb, never the raf' a subject wears, so one the
    parser hung as the subject of the indefinite noun after it is that noun's شبه جملة, its khabar said
    first, hung on it as in عِنْدِي كِتَابٌ."""
    tokens = s.tokens
    for token in tokens if s.verbless else ():
        head = s.head(token)
        if (token["rel"] == "SBJ" and is_zarf(token, s) and typed_case_of(token) != "u" and head
                and head["head"] == 0 and head["id"] > token["id"] and noun_tagged(head) and not is_known(head, s)):
            token["rel"] = "MOD"


def khabar_said_first(s: Sentence) -> None:
    """إِنَّ عِنْدَنَا ضَيْفًا: a particle that governs a pair (إنّ، لا) has one khabar and one name, so where
    the parser hung two khabars on it, the first a place or time word, the second an indefinite noun after
    it, the first is the khabar said first and the noun is the name, as in إِنَّ لَدَيْنَا أَنْكَالًا."""
    tokens = s.tokens
    for particle in tokens if s.verbless else ():
        khabars = [k for k in s.kids(particle) if k["rel"] == "PRD"]
        if particle["pos"] == "PRT" and particle["head"] == 0 and len(khabars) == 2:
            first, second = khabars
            if (is_zarf(first, s) and first["id"] < second["id"] and noun_tagged(second)
                    and not is_known(second, s)):
                second["rel"] = "SBJ"


def jar_off_particle(s: Sentence) -> None:
    """لَا طَالِبَ عِلْمٍ مُتَكَاسِلٌ فِي هَذَا الْفَصْلِ: a جار ومجرور hangs on a verb or on what carries a verb's
    sense (يتعلق بالفعل أو بما فيه معناه), never on إنّ or لا, which only govern their pair. One the parser
    hung on such a particle hangs on its khabar where that is a وصف; with no khabar yet, it is the khabar."""
    for particle in s.tokens:
        if particle["pos"] != "PRT" or s.family(particle) != "inna":
            continue
        khabar = next((k for k in s.kids(particle) if k["rel"] == "PRD"), None)
        for jar in s.kids(particle):
            # وَإِنَّ عَمْرًا قَاعِدٌ: a و over a second إنّ joins two sentences; a jar works on a noun
            if jar["rel"] != "MOD" or not is_preposition(jar) or not any(noun_tagged(k) for k in s.kids(jar)):
                continue
            if khabar and is_participle(khabar):
                s.relink(jar, khabar["id"], "MOD")
            elif not khabar:
                jar["rel"] = "PRD"
                khabar = jar


def masdar_khabar(s: Sentence) -> None:
    """فَإِنَّمَا الْعَدْلُ أَنْ يُسْمَعَ الطَّرَفَانِ، إِنَّ الْخَيْرَ أَنْ تَصْدُقَ: أنْ with its verb is one masdar (roles frames
    masdar), a noun in all but its letters: it describes no noun before it, and works on none. So one the parser hung on
    the noun إنّ (or إنما) is told of, where that particle has no khabar yet, is that khabar; and الْخَيْرُ أَنْ تَصْدُقَ:
    a noun the parser hung on أنْ as its subject from before it, the masdar heading the sentence, is the مبتدأ, the
    masdar its khabar."""
    words = frames()["masdar"]["words"]
    def is_masdar_unit(token: dict) -> bool:
        return token["pos"] == "PRT" and strip_diacritics(token["lemma"]) in words and any(is_verb(v) for v in s.kids(token))
    for masdar in [t for t in s.tokens if t["head"] == 0 and is_masdar_unit(t)]:
        if noun := next((k for k in s.kids(masdar) if k["rel"] == "SBJ" and k["id"] < masdar["id"] and noun_tagged(k)), None):
            s.relink(noun, 0, "---")
            s.relink(masdar, noun["id"], "PRD")
    for particle in s.tokens:
        if particle["pos"] != "PRT" or not is_one(particle["form"], "inna") or any(k["rel"] == "PRD" for k in s.kids(particle)):
            continue
        for subject in [k for k in s.kids(particle) if k["rel"] == "SBJ" and noun_tagged(k)]:
            if masdar := next((k for k in s.kids(subject) if k["rel"] == "MOD" and is_masdar_unit(k)), None):
                s.relink(masdar, particle["id"], "PRD")
                break


def jar_on_its_khabar(s: Sentence) -> None:
    """زَيْدٌ فِي الدَّارِ جَالِسٌ، أَصْبَحَ الْجَوُّ بَعْدَ الْمَطَرِ لَطِيفًا: a جار ومجرور or ظرف hangs on a verb or on what
    carries a verb's sense (Mughni: لا بد من تعلقهما بالفعل أو ما يشبهه), so one the parser hung on a known subject,
    with a وصف khabar of that subject after it, hangs on the khabar, not on a word no one writes said of the
    subject (its حال). An unknown subject keeps it as its صفة (كان رجلٌ من الأنصار صالحًا), and a subject that does a
    verb's work itself keeps it (السَّفَرُ إِلَى مَكَّةَ مُمْتِعٌ، الْجَالِسُ فِي الدَّارِ مَسْرُورٌ)."""
    for jar in s.tokens:
        subject = s.head(jar)
        # a ظرف is منصوب: تِلْكَ السَّاعَةُ ثَمِينَةٌ (raf'), الْيَدُ الْعُلْيَا (case unseen) are no ظرف
        if not (subject and jar["rel"] == "MOD" and (is_preposition(jar) or zarf_in_nasb(jar, s)) and subject["id"] < jar["id"]
                and noun_tagged(subject) and is_known(subject, s) and not (is_masdar(subject) or works_as_verb(subject))):
            continue
        # the khabar is the subject's own (a مبتدأ), its governor's (كان، إنّ and their sisters), or the noun the
        # parser hung the مبتدأ on as its subject (زيدٌ ... جالسٌ)
        holder = subject if subject["rel"] == "---" else s.head(subject) if subject_link(subject) else None
        khabar = holder if holder and noun_tagged(holder) and holder is not subject else next(
            (k for k in s.kids(holder) if k["rel"] == "PRD"), None) if holder else None
        if khabar and khabar["id"] > jar["id"] and is_participle(khabar):
            s.relink(jar, khabar["id"], "MOD")


def _in_shibh_jumla(token: dict, s: Sentence) -> bool:
    """A ظرف or a preposition: the head of a شبه جملة, which tells of nothing by a subject of its own."""
    return is_zarf(token, s) or is_preposition(token)


def object_of_noun(s: Sentence) -> None:
    """زَيْدٌ أَكْثَرُ مِنْكَ مَالًا: only a verb or a word working as one takes an object (notes,
    المفعول به: a فعل or a شبه الفعل governs it), so a word the parser hung as the object of a
    plain noun opening the sentence, both typed in raf', is that noun's khabar. A noun in nasb
    hung there after an elative khabar is the elative's تمييز (Tasheel 3.10: أفعل التفضيل
    ينصب التمييز), as the parser already hangs it when the opener is not between them. Opening the
    sentence behind its حرف جر (بِحَسْبِ ابْنِ آدَمَ لُقَيْمَاتٌ), the noun is told of no word: the raf' word
    is the mubtada, as the parser hangs it when it does not make it an object."""
    tokens = s.tokens
    for token in tokens:
        opener = s.head(token)
        jar = s.head(opener) if opener and opener["rel"] == "OBJ" and typed_case_of(opener) == "i" else None
        behind_jar = bool(jar and jar["rel"] == "---" and is_preposition(jar))
        # اللَّهُمَّ أَنْتَ رَبِّي: a called noun takes no object either; a word hung on it as one, with its subject before it, is
        # told of that subject, a sentence of its own after the call (hung on it as the parser hangs one after يا)
        if (opener and token["rel"] == "OBJ" and is_called_alone(opener) and opener["id"] < token["id"]
                and any(k["rel"] == "SBJ" and k["id"] < token["id"] for k in s.kids(token))):
            token["rel"] = "MOD"
            continue
        # زَيْدٌ مَا رَأَيْتُهُ: a built word shows no case to forbid it (is_built)
        if not (opener and token["rel"] == "OBJ" and opener["id"] < token["id"] and (typed_case_of(token) == "u" or is_built(token))
                and not is_verb(opener) and not works_as_verb(opener)
                and (behind_jar or opener["rel"] == "---" and typed_case_of(opener) == "u")):
            continue
        token["rel"] = "SBJ" if behind_jar else "PRD"
        if is_elative(token):
            for kid in s.kids(opener):
                if kid["rel"] == "OBJ" and kid["id"] > token["id"] and typed_case_of(kid) == "a" and not is_known(kid, s):
                    s.relink(kid, token["id"], "TMZ")
        s.refresh()


def elative_specified(s: Sentence) -> None:
    """أَنْتُمْ أَشَدُّ رَهْبَةً: a مضاف إليه is in jarr, so an indefinite noun typed in nasb that the parser
    hung on an elative as one is its تمييز (Tasheel 3.10: أفعل التفضيل ينصب التمييز; Ibn Aqil V3 p174:
    هو أشد حمرة من زيد ... وههنا ينتصب تمييزا). A diptote's fatha is its jarr (أَفْضَلُ مَسَاجِدَ)."""
    tokens = s.tokens
    for token in tokens:
        head = s.head(token)
        if head and token["rel"] == "IDF" and is_elative(head) and typed_case_of(token) == "a" \
                and not is_known(token, s) and not shows_jarr(token):
            token["rel"] = "TMZ"


# the attached pronoun's letters, by the number and gender it stands for
_PRONOUN_KIND = {"ه": ("s", "m"), "ها": ("s", "f"), "هما": ("d", None), "هم": ("p", "m"), "هن": ("p", "f")}


def tawkeed_before_khabar(s: Sentence) -> None:
    """زَيْدٌ نَفْسُهُ حَاضِرٌ، الْقَوْمُ كُلُّهُمْ حَاضِرُونَ: نفس، عين، كل، جميع، كلا with a pronoun back to the noun just before
    it is that noun's توكيد معنوي (Ajrumiyya, at-tawkeed: النفس والعين وكل وأجمع; page unchecked), so the khabar after it
    is the noun's, not its own. Told of in the noun's number and gender, through the pronoun (حاضرون of هم, not of
    the single كل); else it is a مبتدأ with the noun as a sentence over it: زيدٌ نفسُه طيبةٌ (his soul is good),
    القومُ كلُّهم حاضرٌ (each of them)."""
    if not s.verbless:
        return
    for token in s.tokens:
        before, told = s.by_id.get(token["id"] - 1), s.head(token)
        pronoun = next((k for k in s.kids(token) if attached_pronoun(k) and k["rel"] == "IDF"), None)
        kind = pronoun and _PRONOUN_KIND.get(strip_diacritics(pronoun["form"]).lstrip("+"))
        if not (kind and before and told and listed(token, "tawkeed", "with_pronoun") and token["rel"] == "SBJ"
                and told["id"] > token["id"] and noun_tagged(before) and is_known(before, s) and not is_verb(before)):
            continue
        num, gen = kind
        if told.get("num") == num and gen in (None, told.get("gen")):
            s.relink(token, before["id"], "MOD")


def sentence_khabar(s: Sentence) -> None:
    """زَيْدٌ أَبُوهُ عَالِمٌ، زَيْدٌ عِنْدَهُ كِتَابٌ: a khabar can be a sentence of its own, tied to its مبتدأ by a pronoun that
    returns to it (the رابط). So after a مبتدأ opening a verbless sentence, a word holding such a pronoun heads a
    sentence that is its khabar: a noun told of by the word after it (أبوه عالمٌ، أبوه في الدار, both raf'), or a ظرف or جار
    ومجرور said before the noun it tells of (عنده كتابٌ، في بيته ضيفٌ، عنده الكتابُ). Known and known, the first is the مبتدأ
    (Ibn Aqil, al-ibtida: يجب تقديم المبتدأ إذا كانا معرفتين; page unchecked), so the noun after it never makes it a خبر
    said first. A توكيد (نفسُه، كلُّهم) is no مبتدأ, nor is a وصف told of (زيدٌ في بيته نائمٌ: the jar is نائم's)."""
    words = [t for t in s.tokens if not is_suffix(t)] if s.verbless else []
    # a noun in nasb or jarr is no مبتدأ (غَدًا عِنْدَهُ امْتِحَانٌ: a ظرف)
    if len(words) < 3 or not noun_tagged(first := words[0]) or typed_or_parsed_case(first) not in (None, "u"):
        return
    second = words[1]
    if not reaches_pronoun(second, s):
        return
    # the word told of comes after the second word's own phrase, its مجرور and مضاف إليه (له أخٌ: the parser can hang أخ on ل too)
    phrase, queue = {second["id"]}, [second]
    while queue:
        for kid in s.kids(queue.pop()):
            if kid["rel"] in ("OBJ", "IDF") and kid["id"] not in phrase:
                phrase.add(kid["id"])
                queue.append(kid)
    told = next((t for t in words if t["id"] > max(phrase)), None)
    if not told:
        return
    shibh = is_preposition(second) or is_zarf(second, s)
    if shibh and noun_tagged(told) and not (is_describing(told) or works_as_verb(told)) \
            and typed_or_parsed_case(told) in (None, "u"):
        s.relink(first, 0, "---")
        s.relink(second, first["id"], "PRD")
        s.relink(told, second["id"], "SBJ")
    elif not shibh and noun_tagged(second) and not is_describing(second) and typed_or_parsed_case(second) in (None, "u") \
            and not listed(second, "tawkeed", "with_pronoun") and (
                is_preposition(told) or is_zarf(told, s) or noun_tagged(told) and typed_or_parsed_case(told) in (None, "u")):
        s.relink(first, 0, "---")
        s.relink(told, first["id"], "PRD")
        s.relink(second, told["id"], "SBJ")
