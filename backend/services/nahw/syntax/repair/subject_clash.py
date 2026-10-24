"""Repair 2: a word hung on a verb's subject that the typed vowels forbid there is the verb's object."""
from __future__ import annotations

from backend.services.nahw.book import is_mabni, is_one
from backend.services.nahw.syntax.facts import (
    Sentence, attached_pronoun, has_added, indefinite_nasb, typed_tanween, is_state_word, is_verb, is_zarf, same_root, shows_jarr, typed_case_of, noun_tagged, subject_link, works_as_verb)


def subject_clash(tokens: list[dict]) -> None:
    """A word the parser hung on a verb's subject that the typed vowels forbid there is the verb's object.
    أَعْطَى الرَّجُلُ الْفَقِيرَ دِرْهَمًا، ضَرَبَ زَيْدٌ عَمْرًا: a نعت wears its noun's case (Tasheel 3.10.1),
    so a word in nasb after the subject's damma is no نعت; a hal (جَاءَ زَيْدٌ رَاكِبًا) or the verb's own
    masdar (فَرِحَ الْوَلَدُ فَرَحًا) is left to its own rule.
    ضَرَبَ زَيْدٌ مَرْيَمَ: a noun with tanween is complete, so nothing after it is its مضاف إليه.
    ضرب زيد عمرا typed bare: the subject is raf' by its place, unless typed otherwise, and a word
    whose nasb is written (its alif of tanween) is neither its نعت nor its مضاف إليه, which is jarr."""
    s = Sentence(tokens)
    for token in tokens:
        head = s.head(token)
        verb = s.head(head) if head else None
        if not (verb and is_verb(verb) and noun_tagged(token) and token["id"] > head["id"]
                and subject_link(head) and not is_verb(token) and typed_case_of(head) in ("u", None)
                and not is_mabni(token.get("pos_camel", "")) and not is_zarf(token, s)):
            continue
        # جَاءَ خَلِيفَةُ عُمَرَ: a diptote's fatha is its jarr, so the مضاف إليه stays
        clash = (token["rel"] in ("MOD", "---") or (token["rel"] == "IDF" and not shows_jarr(token))) \
            and typed_case_of(token) == "a" and not (indefinite_nasb(token) and (is_state_word(token) or same_root(token, verb)))
        # the parser may hang it there unlabelled (---) rather than as IDF; either way an إضافة is meant
        added = (token["rel"] in ("IDF", "---") and typed_tanween(head)
                 and typed_case_of(token) in ("a", None) and not any(k["rel"] == "OBJ" for k in s.kids(verb)))
        if clash or added:
            token["head"], token["rel"] = verb["id"], "OBJ"
            head["mudaf"] = has_added(head, tokens)
            s = Sentence(tokens)


def doer_after_object(tokens: list[dict]) -> None:
    """أَدْهَشَ الْجُمْهُورَ السَّاحِرُ: the object may come before the doer. A word hung on a verb
    as its subject that the reader typed in nasb, with a raf' word hung on it straight after,
    is the object and that raf' word the doer: a نعت wears its noun's case, and a مضاف إليه is
    in jarr."""
    s = Sentence(tokens)
    for token in tokens:
        verb = s.head(token)
        if not (verb and is_verb(verb) and token["rel"] == "SBJ" and typed_case_of(token) == "a"
                and not is_mabni(token.get("pos_camel", ""))):
            continue
        doer = next((k for k in s.kids(token) if k["id"] == token["id"] + 1 and k["rel"] in ("MOD", "IDF")
                     and noun_tagged(k) and typed_case_of(k) == "u"), None)
        if doer:
            token["rel"] = "OBJ"
            doer["head"], doer["rel"] = verb["id"], "SBJ"
            s = Sentence(tokens)


def verb_under_fronted_object(tokens: list[dict]) -> None:
    """عِلْمًا طَلَبَ زَيْدٌ: the مفعول به may come before its verb (Jumla Filiyya p4). A verb with
    its own doer that the parser hung as the صفة of a nasb noun before it describes nothing: a
    describing sentence needs a pronoun back to its noun (عِلْمًا طَلَبَهُ زَيْدٌ), so with none the
    verb heads the sentence and the noun is its fronted object."""
    s = Sentence(tokens)
    for verb in tokens:
        noun = s.head(verb)
        if not (noun and is_verb(verb) and verb["rel"] == "MOD" and noun["head"] == 0 and noun["id"] < verb["id"]
                and noun_tagged(noun) and not is_verb(noun) and typed_case_of(noun) == "a"
                and not is_mabni(noun.get("pos_camel", ""))):
            continue
        kids = s.kids(verb)
        if any(subject_link(k) and k["id"] > verb["id"] for k in kids) and not any(attached_pronoun(k) for k in kids):
            verb["head"], verb["rel"] = 0, "---"
            noun["head"], noun["rel"] = verb["id"], "OBJ"
            s = Sentence(tokens)


def object_after_tanween(tokens: list[dict]) -> None:
    """يَا سَائِقًا الشَّاحِنَةَ: a word with tanween is complete, so nothing after it is its
    مضاف إليه; a participle typed so takes the word the parser hung on it that way, in nasb,
    as its object."""
    s = Sentence(tokens)
    for token in tokens:
        head = s.head(token)
        if (head and token["rel"] == "IDF" and works_as_verb(head) and typed_tanween(head)
                and typed_case_of(token) == "a"):
            token["rel"] = "OBJ"


def kana_subject(tokens: list[dict]) -> None:
    """لَيْسَ الشَّدِيدُ بِالصُّرَعَةِ: كان and its sisters put their خبر in nasb (Tasheel 1.9), so
    a word the parser made the خبر that the reader typed in raf', with no اسم beside it, is the
    اسم; what the parser hung on it after it (here بِالصُّرَعَةِ) is the خبر. So too when the
    parser had the اسم right but hung the خبر on it (لَيْسَ الطَّالِبُ بِكَسُولٍ), leaving كان none."""
    s = Sentence(tokens)
    for token in tokens:
        verb = s.head(token)
        if not (verb and s.family(verb) == "kana" and verb["id"] < token["id"] and noun_tagged(token)):
            continue
        if token["rel"] == "PRD" and typed_case_of(token) == "u" and not any(subject_link(k) for k in s.kids(verb)):
            token["rel"] = "SBJ"
        elif not (subject_link(token) and not any(k["rel"] == "PRD" for k in s.kids(verb))):
            continue
        told = next((k for k in s.kids(token) if k["id"] > token["id"] and k["rel"] == "MOD"
                     and (k["pos"] == "PRT" or typed_case_of(k) == "a")), None)
        if told:
            told["head"], told["rel"] = verb["id"], "PRD"
        s = Sentence(tokens)


def zanna_pair(tokens: list[dict]) -> None:
    """حَسِبَ الرَّجُلُ الطَّرِيقَ قَصِيرًا: ظنّ and its sisters enter a مبتدأ and its خبر and put both
    in nasb as their two objects (Alfiyya: انصب بفعل القلب جزأي ابتدا). The parser may keep the pair
    as it was, the first word the subject of the second, and hang the second anywhere (on the verb,
    or on its doer); with the reader's fatha on both, after the nearest verb before them being one of
    ظنّ's (by the book's list: the family test wants the two objects already on the verb), the first is that verb's first object and the second its second. A doer the parser took for
    the object, typed in raf', is the verb's doer."""
    s = Sentence(tokens)
    for first in tokens:
        second = s.head(first)
        verb = second and next((t for t in reversed(tokens[:tokens.index(first)]) if is_verb(t)), None)
        if not (verb and first["rel"] in ("SBJ", "TPC") and is_one(verb["lemma"], "zanna") and first["id"] < second["id"]
                and noun_tagged(first) and typed_case_of(first) == typed_case_of(second) == "a"):
            continue
        for doer in tokens:
            if doer["head"] in (verb["id"], second["id"]) and doer["rel"] in ("OBJ", "MOD") \
                    and verb["id"] < doer["id"] < first["id"] and typed_case_of(doer) == "u":
                doer["head"], doer["rel"] = verb["id"], "SBJ"
        first["head"], first["rel"] = verb["id"], "OBJ"
        second["head"], second["rel"] = verb["id"], "OBJ"
        s = Sentence(tokens)


def praise_specified(tokens: list[dict]) -> None:
    """نِعْمَ رَجُلًا زَيْدٌ: the فاعل of a verb of praise or blame may be a pronoun hidden in it, which
    an indefinite noun in nasb straight after explains as its تمييز; the raf' noun after that is
    the one praised (Ibn Aqil, باب نعم وبئس). The parser takes the تمييز for an object and hangs the
    praised noun on it; both go on the verb, as the pattern reads."""
    s = Sentence(tokens)
    for verb in tokens:
        specifier = s.by_id.get(verb["id"] + 1)
        if not (is_verb(verb) and is_one(verb["lemma"], "praise_blame") and specifier
                and noun_tagged(specifier) and indefinite_nasb(specifier)):
            continue
        specifier["head"], specifier["rel"] = verb["id"], "TMZ"
        praised = s.by_id.get(specifier["id"] + 1)
        if praised and noun_tagged(praised):
            praised["head"], praised["rel"] = verb["id"], "SBJ"
