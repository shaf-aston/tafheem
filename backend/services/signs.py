"""The sign every card prints, decided once, after the roles are settled.

A sign comes from three things: the word as typed (its last letters, the vowels the
reader wrote), CAMeL's reading of it (the card's `camel`) and the case the card ended
on. The rule engine's cards and the parser's names both end
here (`settle`), so a case the parser moved never keeps a sign worked out for the old
one. The words printed are the book's, in data/nahw_rules/teacher.json.
"""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics
from backend.services.harakat import SHADDA, SUKUN, TANWEEN, drops_weak, five_verb_nun, has_tanween, letters
from backend.services.nahw_book import book_words, reason, six_noun_case, teacher_rules

# The noun tables a present verb ending in a weak letter borrows (يَهْدِي، يَدْعُو، يَسْعَى)
_WEAK_END = {"ي": "manqus", "و": "on_waw", "ا": "on_alef", "ى": "on_alef"}


def sign(case: str | None, kind: str = "vowel") -> str | None:
    """The sign a card prints for a case; `kind` names the letter or the assumed vowel
    that shows it (dual, sound_plural, five_verbs, ...), the plain vowel otherwise."""
    tables = teacher_rules()["signs"]
    return tables[kind].get(case) or tables["vowel"].get(case)


def kind_of(tag: dict) -> str:
    """Which sign table a noun's case is read from. CAMeL's number names a dual or a
    plural, unless the reader typed a tanween, which neither ever carries (غَافِلًا)."""
    word = tag.get("word", "")
    bare = strip_diacritics(word)
    marked = letters(word)
    if not has_tanween(word):
        if tag.get("number") == "p" and tag.get("gender") == "m" and bare.endswith(("ون", "ين")):
            return "sound_plural"
        if tag.get("number") == "d":
            return "dual"
        if tag.get("enclitic") != "1s_poss" and six_noun_case(tag["base"], strip_diacritics(tag.get("lemma") or "")):
            return "six_nouns"  # أَخًا has a tanween: not a مضاف, so the vowels show
    if tag.get("enclitic") == "1s_poss":
        return "before_ya"  # كِتَابِي: the kasra belongs to the ya, the case cannot show
    # no root read (key absent): the old test, a final ى is مقصور
    weak = tag.get("weak_last", bare.endswith("ى"))
    if bare.endswith(("ا", "ى")) and weak and not _has_pronoun(tag) and not (len(marked) > 1 and marked[-2][1] & TANWEEN):
        # الفَتَى، العَصَا: an alef cannot carry a vowel (شَيْئًا's alef is the tanween's, أَخَوَاتِهَا's the pronoun's)
        return "on_alef"
    if "weak_last" in tag and weak and len(marked) > 1 and bare.endswith("ي") and not (
            SHADDA in marked[-1][1] or marked[-2][1] & {"َ", "ُ", SHADDA, SUKUN}):
        return "manqus"  # القَاضِي: a damma or kasra is too heavy for the ya, the fatha shows
    return "vowel"


def _has_pronoun(reading: dict) -> bool:
    """CAMeL saw an attached pronoun at the end."""
    return bool(reading.get("enclitic"))


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
    return cards


def _noun_sign(card: dict, before: dict | None, after: dict | None) -> str | None:
    case = card.get("case")
    if case is None:
        return None
    if card.get("type") in ("harf", "damir"):
        return sign("mabni")  # a particle or a pronoun never shows a case of its own
    kind = kind_of(card["camel"])
    if case != "mabni" and _after_la_jins(card, before, after):
        # لا ضَرَرَ، لا قَلَمَيْنِ: built on what its nasb would show
        on = teacher_rules()["case_said"]["la_jins_on"]
        return _built(on.get(kind, on["vowel"]))
    return sign(case, "vowel" if case == "mabni" else kind)


def _after_la_jins(card: dict, before: dict | None, after: dict | None) -> bool:
    """The single indefinite noun straight after لا of the genus (ولا ضرار too): not a
    مضاف, no tanween (that لا works like ليس and its noun takes the vowels)."""
    if card.get("role") != "اسم إن" or not before:
        return False
    return before["camel"]["base"] in book_words("la_jins") and not has_tanween(card["word"]) and not (
        after and after.get("role") == "مضاف إليه")


def _built(ending: str) -> str:
    return teacher_rules()["case_said"]["built_on"].format(ending=ending)


def _verb(card: dict) -> dict:
    """A verb's case, sign and reason by its tense, so the three always agree."""
    said = teacher_rules()["case_said"]
    aspect = card.get("aspect")
    tense = said["tense"].get(aspect)
    if not tense:
        return {"case": "mabni", "sign": sign("mabni"), "reason": reason("فعل")}
    built_on = _built_on(card, aspect)
    if built_on:
        built = _built(built_on)
        return {"case": "mabni", "sign": built, "reason": f"{tense} {built}. {reason(tense)}"}
    case = card["case"]  # rule_engine.verb_card settled the mood
    return {"case": case, "sign": _present_sign(card, case),
            "reason": f"{tense} {said['word'][case]}. {reason(tense)}"}


def _built_on(card: dict, aspect: str) -> str | None:
    """What a past verb, a command or a present verb with a nun on it is built on."""
    said = teacher_rules()["case_said"]
    word = card["word"]
    if aspect == "p":
        return _past_ending(word)
    nun = _nun(word)
    if aspect == "c":
        # a command is built on what its jazm would show
        if not _has_pronoun(card["camel"]) and strip_diacritics(word).endswith(("وا", "ا", "ي")):
            return sign("jazm", "five_verbs")  # اُكْتُبُوا، اُكْتُبَا، اُكْتُبِي: the five verbs' nun is gone
        if _dropped_weak(card):
            return sign("jazm", "dropped_weak")  # اِسْقِ
        return said["nun_on"]["emphasis"] if nun == "emphasis" else said["command_on"]
    return said["nun_on"].get(nun)


def _present_sign(card: dict, case: str) -> str | None:
    word = card["word"]
    nun = None if _has_pronoun(card["camel"]) else five_verb_nun(word)  # لن يَكْتُبَهَا: the ا is the pronoun's
    if nun and (case == "raf'") == (nun == "kept"):
        return sign(case, "five_verbs")
    if card["camel"].get("weak_last"):
        if case == "jazm" and _dropped_weak(card):
            return sign(case, "dropped_weak")  # لم يَبْكِ: the weak letter went
        weak_end = _WEAK_END.get(strip_diacritics(word)[-1:])
        if weak_end and case != "jazm":
            return sign(case, weak_end)  # يَهْدِي: the damma is too heavy for the ya
    return sign(case)


def _dropped_weak(card: dict) -> bool:
    return drops_weak(card["camel"]["base"], card["camel"].get("weak_last"))


def _nun(word: str) -> str | None:
    """The nun of emphasis (لَيَنْصُرَنَّ: doubled, a fatha on it and on the letter before)
    or of women (يَرْسُمْنَ: a sukun on the consonant before it), as typed; a bare nun,
    a root's doubled nun (يَظُنُّ) or a long vowel's sukun (يَكُوْنَ) says neither."""
    marked = letters(word)
    if len(marked) < 3 or marked[-1][0] != "ن" or "َ" not in marked[-1][1]:
        return None
    if SHADDA in marked[-1][1]:
        return "emphasis" if "َ" in marked[-2][1] else None
    return "women" if SUKUN in marked[-2][1] and marked[-2][0] not in "اوي" else None


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
