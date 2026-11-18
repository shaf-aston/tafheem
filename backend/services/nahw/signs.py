"""The sign every card prints, decided once, after the roles are settled.

A sign comes from three things: the word as typed (its last letters, the vowels the
reader wrote), CAMeL's reading of it (the card's `camel`) and the case the card ended
on. iraab.cards calls `settle` once, after the parser's
names, so a case the parser moved never keeps a sign worked out for the old
one. The words printed are the book's, in data/nahw_rules/teacher.json.
"""
from __future__ import annotations

from backend.services.text.arabic_text import bare_letters, strip_diacritics
from backend.services.text.harakat import CASE_LETTER, SHADDA, SUKUN, TANWEEN, build_nun, drops_weak, drops_ya, five_verb_nun, has_tanween, letters, own_letters, paused, plural_alef, typed_case, typed_passive
from backend.services.nahw.book import attention_off, book_words, case_of, family_cards, is_diptote, is_one, is_fem_plural, named_roles, reason, six_noun_case, teacher_rules

NAMED = named_roles()
# The noun tables a present verb ending in a weak letter borrows (يَهْدِي، يَدْعُو، يَسْعَى)
_WEAK_END = {"ي": "manqus", "و": "on_waw", "ا": "on_alef", "ى": "on_alef"}


def sign(case: str | None, kind: str = "vowel") -> str | None:
    """The sign a card prints for a case; `kind` names the letter or the assumed vowel
    that shows it (dual, sound_plural, five_verbs, ...), the plain vowel otherwise."""
    tables = teacher_rules()["signs"]
    return tables[kind].get(case) or tables["vowel"].get(case)


def kind_of(tag: dict, annexed: bool) -> str:
    """Which sign table a noun's case is read from. CAMeL's number names a dual or a
    plural, unless the reader typed a tanween, which neither ever carries (غَافِلًا); a sound
    feminine plural's alone is its own, standing for the plural's نون (Awdah V1 p14: تنوين
    المقابلة، وهو اللاحق لنحو مسلمات), so its kasra is its nasb with one or without (لَآيَاتٍ)."""
    word = tag.get("word", "")
    bare = strip_diacritics(word)
    marked = letters(word)
    if tag.get("gender") == "f" and is_fem_plural(tag["base"], tag.get("number") or "na"):  # a masculine plural keeps its fatha (أَصْوَاتَهُمْ)
        return "fem_plural"  # المعلماتِ: nasb shows by the kasra
    if not has_tanween(word):
        if bare.endswith(("ون", "ين")) and _attached_plural(bare):
            return "attached_plural"  # عِشْرِينَ، أُولُو: they take its letters without being one
        if tag.get("number") == "p" and tag.get("gender") == "m" and (bare.endswith(("ون", "ين")) or _dropped_nun(tag, annexed)):
            return "sound_plural"
        if is_one(tag.get("lemma") or "", "kila"):
            # كِلَاهُمَا، كِلَيْهِمَا: ملحق بالمثنى joined to a pronoun; كِلَا الرَّجُلَيْنِ like the مقصور (closed_words kila)
            return "attached_dual" if _has_pronoun(tag) else "on_alef"
        if is_one(strip_diacritics(tag["base"]), "compound_number", "dual"):
            return "attached_dual"  # اثْنَا، اثْنَيْ عَشَرَ: ملحق بالمثنى, its letters show the case (Tasheel 1.4.3 p10)
        if tag.get("number") == "d":
            return "dual"
        # بِمَسَاجِدَ: a diptote, unless a مضاف إليه follows (CAMeL's construct state is no guide: a صفة after it reads as a مضاف إليه)
        if tag.get("case") in ("jarr", "nasb") and is_diptote(word, tag.get("pos", ""), tag.get("lemma") or "", attached=_has_pronoun(tag), annexed=annexed):
            return "diptote"
        if not _my(tag) and six_noun_case(tag["base"], tag.get("lemma") or ""):
            return "six_nouns"  # أَخًا has a tanween: not a مضاف, so the vowels show
    if drops_ya(word, tag.get("lemma") or ""):
        return "manqus_dropped"  # بِصَوْتٍ عَالٍ، قَاضٍ: the tanween took the ya's place, so the vowel is on the ya that went
    if _my(tag):
        return "before_ya"  # كِتَابِي، عِنْدِي: the kasra belongs to the ya, the case cannot show
    # ى is always an alef maqsura; a plain alef is one only on a weak root (العَصَا)
    weak = tag.get("weak_last")
    if (bare.endswith("ى") or (bare.endswith("ا") and weak)) and not _has_pronoun(tag) and not (len(marked) > 1 and marked[-2][1] & TANWEEN):
        # الفَتَى، العَصَا: an alef cannot carry a vowel (شَيْئًا's alef is the tanween's, أَخَوَاتِهَا's the pronoun's)
        return "on_alef"
    if weak and len(marked) > 1 and bare.endswith("ي") and not (
            SHADDA in marked[-1][1] or marked[-2][1] & {"َ", "ُ", SHADDA, SUKUN}):
        return "manqus"  # القَاضِي: a damma or kasra is too heavy for the ya, the fatha shows
    return "vowel"


def _dropped_nun(tag: dict, annexed: bool) -> bool:
    """مُعَلِّمُو الْمَدْرَسَةِ، مُعَلِّمِيهِمْ: a sound masculine plural drops its ن as a مضاف, to a noun or a pronoun
    (Ibn Aqil V1 p62), and its و or ي still shows the case: the singular with only that letter after it. A broken
    plural ending in a ي (مَبَانِيهَا) is no singular and a letter."""
    base = strip_diacritics(tag.get("base") or "")
    return (annexed or _has_pronoun(tag)) and base[-1:] in ("و", "ي") \
        and bare_letters(base[:-1]) == bare_letters(strip_diacritics(tag.get("lemma") or ""))


def _my(tag: dict) -> bool:
    """كِتَابِي، عِنْدِي: ياء المتكلم on a noun. CAMeL names it 1s_poss on most, 1s_pron on a ظرف (عِنْدِي، لَدَيَّ)."""
    return tag.get("enclitic") in ("1s_poss", "1s_pron")


def _attached_plural(bare: str) -> bool:
    """عشرون..تسعون، أولو، أهلون، سنون، أرضون، عالمون (teacher.json attached_plural)."""
    return bare.removeprefix("ال")[:-2] in teacher_rules()["case_said"]["attached_plural"]


def _has_pronoun(reading: dict) -> bool:
    """CAMeL saw an attached pronoun at the end."""
    return bool(reading.get("enclitic"))


def _has_object(reading: dict) -> bool:
    """CAMeL saw an object pronoun on the verb: a verb takes no "my" (Awdah V1 p85: ياء المتكلم
    on a verb is أكرمني), so a possessive one is a noun reading's left on a command (ارْفَعِي)."""
    return str(reading.get("enclitic", "")).endswith("_dobj")


def settle(cards: list[dict]) -> list[dict]:
    """Write every card's sign (and a verb's case and reason, which say the sign too)
    from its final case. A gap keeps no sign: its name was taken back."""
    for i, card in enumerate(cards):
        if card.get("gap") or card.get("type") == "punc":
            continue
        before = cards[i - 1] if i else None
        after = cards[i + 1] if i + 1 < len(cards) else None
        if card.get("type") == "fi'l":
            card.update(_verb(card))
        else:
            card["sign"] = _noun_sign(card, before, after)
            if card.get("type") == "harf" and (said := _family_said(card)):
                # a family that only names (حرف نفي) has nothing to add after its name
                card["reason"] = teacher_rules()["case_said"]["harf_by_family"].format(**said).rstrip("، ")
    return cards


def _family_said(card: dict) -> dict | None:
    """{named, does} of the family the word governs as (iraab.cards sets it),
    by the member's own name where the book gives one (لم حرف نفي وجزم وقلب)."""
    family = dict(family_cards()).get(card.get("family"))
    if not family:
        return None
    named = card.get("named") or family.get("named_as", {}).get(card["camel"]["base"], family["named"])
    return {"named": named, "does": family["does"]}




def _noun_sign(card: dict, before: dict | None, after: dict | None) -> str | None:
    case = card.get("case")
    if case is None:
        return None
    if card.get("type") in ("harf", "damir"):
        # a particle or a pronoun never shows a case of its own, only what it is built on (إِنَّ، لَمْ، فِي);
        # إِنَّهُ is built on إِنَّ's fatha, not the ضمة of the pronoun on it
        own = _without_object(card["word"]) if _has_pronoun(card["camel"]) else _unmoved(card, after)
        return _built(ending) + _moved(card, after) if (ending := _typed_ending(own)) else sign("mabni")
    if (part := card.get("compound")) in ("built", "ordinal", "second"):
        # ثلاثةَ عشرَ: مبني على فتح الجزأين في محل رفع; the عشر after اثنا is built on its own fatha
        said = teacher_rules()["case_said"]
        both = part != "second" or (before or {}).get("compound") in ("built", "ordinal")
        on = _built(said["compound_on"]["both" if both else "one"])
        place = CASE_LETTER.get(case) or case_of(card.get("role") or "")
        return f"{on} {said['in_place'].format(place=said['place'][place])}" if place else on
    kind = kind_of(card["camel"], bool(after and after.get("role") == NAMED.mudaf_ilayh))
    if case != "mabni" and _after_la_jins(card, before, after):
        # لا ضَرَرَ، لا قَلَمَيْنِ: built on what its nasb would show; لا طالبَ علمٍ, a مضاف, stays معرب منصوب
        card["in_place"] = True  # its reason says so too (card_wording.names.pair)
        said = teacher_rules()["case_said"]
        on = said["la_jins_on"]
        # built, yet it stands where nasb would be: مبني على الفتح في محل نصب
        place = said["in_place"].format(place=said["place"][CASE_LETTER[case]])
        return f"{_built(on.get(kind, on['vowel']))} {place}"
    # أَمْسِ، حَيْثُ، مَنْ: built on the vowel typed on the last letter; أَيُّهَا on أَيُّ's, the ها written on it
    built = attention_off(card["word"], (card.get("camel") or {}).get("lemma") or "")
    if case == "mabni" and (ending := _typed_ending(built or _unmoved(card, after))):
        return _built(ending) + _moved(card, after)
    return sign(case, "vowel" if case == "mabni" else kind)


def _unmoved(card: dict, after: dict | None) -> str:
    """The word as built: مَنِ ائْتَمَنَكَ is مَنْ, its kasra only meets the sakin after it
    (التقاء الساكنين). A kasra the word is built on stays (هَؤُلَاءِ الرِّجَالُ): its own
    pattern, as the morphology reads it, ends on a sukun only in the first case. A particle's
    pattern leaves a sakin end bare (عَنْ is 1َ2), as no case ever moves it."""
    word = card["word"]
    own = (card.get("camel") or {}).get("pattern") or ""
    sakin = own.endswith(SUKUN) or (card.get("type") == "harf" and own[-1:].isdigit())
    return paused(word, (after or {}).get("word", "")) if sakin else word


def _moved(card: dict, after: dict | None) -> str:
    """مَنِ ائْتَمَنَكَ، عَنِ ابْنِ: the sukun it is built on shows as a kasra, said so."""
    return teacher_rules()["case_said"]["moved_to_meet"] if _unmoved(card, after) != card["word"] else ""


def _typed_ending(word: str) -> str | None:
    marked = letters(word)
    on = teacher_rules()["case_said"]["vowel_on"]
    if not marked:
        return None
    letter, marks = marked[-1]
    if letter in "اآوىي" and len(marked) > 1 and not any(m in on or m == SHADDA for m in marks):
        # فِي، إِلَى، هَذَا، وَمَآ: a long letter carries no vowel (a reciter's madda is none), it is built on the sukun
        return on["ْ"]
    return next((on[m] for m in marks if m in on), None)


def _after_la_jins(card: dict, before: dict | None, after: dict | None) -> bool:
    """The single indefinite noun straight after لا of the genus (ولا ضرار too): not a
    مضاف, no tanween (that لا works like ليس and its noun takes the vowels)."""
    if card.get("role") != NAMED.ism_inna or not before:
        return False
    return before["camel"]["base"] in book_words("la_jins") and not has_tanween(card["word"]) and not (
        after and after.get("role") == NAMED.mudaf_ilayh)


def _built(ending: str) -> str:
    return teacher_rules()["case_said"]["built_on"].format(ending=ending)


def _verb(card: dict) -> dict:
    """A verb's case, sign and reason by its tense, so the three always agree."""
    said = teacher_rules()["case_said"]
    aspect = card.get("aspect")
    tense = said["tense"].get(aspect)
    if not tense:
        return {"sign": sign("mabni"), "reason": reason(NAMED.fil)}
    built_on = _built_on(card, aspect)
    case = card["case"]  # rule_engine.verb_card settled the mood, a nun of women or emphasis builds it too
    shown = _built(built_on) if built_on else _present_sign(card, case)
    state = shown if built_on else said["word"][case]
    family = _family_said(card)
    # تُطَوَّقَ، كُتِبَ: the vowels show who is not named, so the card says so; the letters
    # after the base are an attached pronoun (أُكْرِمَكَ), not the verb's
    bare, base = strip_diacritics(card["word"]), card["camel"]["base"]
    stuck_on = len(bare) - bare.rfind(base) - len(base) if base and base in bare else 0
    voiced = f"{tense} {said['passive']}" if aspect != "c" and (
        card["camel"].get("vox") == "p" or typed_passive(card["word"], aspect == "i", stuck_on, card["camel"].get("weak_last"))) else tense
    told = said["verb_by_family"].format(tense=voiced, state=state, **family).rstrip("، ") if family else f"{voiced} {state}"
    return {"sign": shown, "reason": f"{told}. {reason(tense)}"}


def _built_on(card: dict, aspect: str) -> str | None:
    """What a past verb, a command or a present verb with a nun on it is built on."""
    said = teacher_rules()["case_said"]
    word = card["word"]
    if aspect == "p":
        # رَمَيْتُهُ، رَمَاهُ: the verb ends before its object pronoun, so read it without the pronoun
        verb = _without_object(word) if _has_pronoun(card["camel"]) else word
        bare = strip_diacritics(verb)
        # نَادَى، دَعَا: the fatha is there but an alef cannot carry it, so it is implied;
        # رَوَيْنَاهُ، رَمَيَاهُ: an alef after a doer's pronoun (نا، ا) is the pronoun's, not the verb's
        alone = card["camel"].get("person") == "3" and card["camel"].get("number") == "s"
        alef = alone and (bare.endswith("ى") or (bare.endswith("ا") and card["camel"].get("weak_last")))
        return said["past_on_alef"] if alef else _past_ending(verb)  # رَوَاهُ: one doer, so its وا is no plural's
    nun = build_nun(word)
    if aspect == "c":
        # a command is built on what its jazm would show
        verb = _without_object(word) if _has_object(card["camel"]) else word
        if strip_diacritics(verb).endswith(("وا", "ا", "ي")):
            return sign("jazm", "five_verbs")  # اُكْتُبُوا، اُكْتُبَا، اُكْتُبِي: the five verbs' nun is gone
        if _dropped_weak(verb, card):
            return sign("jazm", "dropped_weak")  # اِسْقِ، اِسْقِهِ
        return said["nun_on"]["emphasis"] if nun == "emphasis" else said["command_on"]
    return said["nun_on"].get(nun)


def _present_sign(card: dict, case: str) -> str | None:
    """Read off the verb as typed less its attached pronoun's letters, as its case is:
    لن يَكْتُبَهَا ends in the pronoun's ا, يَكْتُبُونَهُ keeps its nun, يَعْنِيهِ its ي."""
    word, tag = card["word"], card["camel"]
    stuck_on, weak_last = _pronoun_letters(word) if _has_pronoun(tag) else 0, tag.get("weak_last")
    nun = five_verb_nun(word, stuck_on, weak_last)
    if nun and (case == "raf'") == (nun == "kept"):
        return sign(case, "five_verbs")
    if weak_last:
        verb = own_letters(word, 0, stuck_on)
        # لا تَنْسَوْهُ، لن يَرْمُوهُ: one doer's و goes in jazm (لم يَدْعُهُ) and takes a fatha in nasb (لن يَدْعُوَهُ),
        # so a و left bare before a pronoun there is the group's, its nun gone
        if case in ("jazm", "nasb") and stuck_on and strip_diacritics(verb).endswith("و") \
                and typed_case(word, stuck_on) != "a":
            return sign(case, "five_verbs")
        if case == "jazm" and _dropped_weak(verb, card):
            return sign(case, "dropped_weak")  # لم يَبْكِ: the weak letter went
        weak_end = _WEAK_END.get(strip_diacritics(verb)[-1:])
        if weak_end and case != "jazm":
            return sign(case, weak_end)  # يَهْدِي: the damma is too heavy for the ya
    return sign(case)


def _dropped_weak(verb: str, card: dict) -> bool:
    """Read off the verb as typed less its pronoun: CAMeL's base for يَأْتِنَا is no guide."""
    return drops_weak(verb, card["camel"].get("weak_last"))


def _without_object(word: str) -> str:
    """The verb or particle with its attached pronoun (and that pronoun's marks) cut off: رَمَيْتُهُ → رَمَيْتُ,
    ضَرَبُوهُ → ضَرَبُوا، إِنَّهُ → إِنَّ."""
    return plural_alef(own_letters(word, 0, _pronoun_letters(word)))


def _pronoun_letters(word: str) -> int:
    """How many letters at the word's end are an attached pronoun's: the longest one a verb can carry, so هما
    is not read as ه, with at least two letters left before it."""
    bare = strip_diacritics(word)
    return next((len(p) for p in sorted(book_words("damir_muttasil", "on_verbs"), key=len, reverse=True)
                 if bare.endswith(p) and len(bare) > len(p) + 1), 0)


def _past_ending(word: str) -> str:
    """What a past verb is built on, from its last letters and the mark before them
    (teacher.json past_ending)."""
    bare = strip_diacritics(word)
    marked = letters(word)
    for ending, rule in teacher_rules()["past_ending"].items():
        if ending.startswith("_"):
            continue
        tail = next((t for t in rule["tails"] if bare.endswith(t)), None)
        if not tail:
            continue
        letter, before = marked[-len(tail) - 1] if len(marked) > len(tail) else ("", set())
        before = {"َ"} if letter == "ا" else before  # أَتَانَا، مَاتَ: the alef is a fatha said long
        if before and rule.get("before"):
            # غَشَّنَا، كَتَبَتْ: a vowel before the letters makes them the object or تاء التأنيث
            if rule["before"] in before:
                return ending
        elif not (tail == "ت" and SUKUN in marked[-1][1]):
            return ending  # bare before: a sukun typed on a last ت is تاء التأنيث (كَتَبَتْ)
    return teacher_rules()["case_said"]["past_on"]
