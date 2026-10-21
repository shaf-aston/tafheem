"""Repair 5: khabars the parser hung elsewhere: a second adjective khabar, and a لا clause after its mubtada."""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics
from backend.services.syntax.facts import Sentence, has_added, is_elative, is_participle, is_verb, typed_case_of, typed_or_parsed_case, subject_link, works_as_verb


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


def after_pointer(tokens: list[dict]) -> None:
    """هَاتَانِ قِلَادَتَانِ، زَيْدٌ ضَارِبٌ: a نعت matches its noun in being definite (هذا الكتابُ،
    زيدٌ الكريمُ), so an indefinite noun or adjective the parser hung as the صفة of a definite
    word that opens the sentence (a pointer, a name, a word with ال) is the khabar, that word its mubtada."""
    s = Sentence(tokens)
    for token in tokens:
        head = s.head(token)
        if (head and head["head"] == 0 and head["pos"] in ("NOM", "PROP") and not is_verb(head) and token["rel"] == "MOD"
                and (head.get("pos_camel") in ("pron_dem", "noun_prop") or head.get("stt") == "d")
                and token["id"] > head["id"] and token.get("pos_camel") in ("noun", "adj")
                and _indefinite(token, tokens)
                and not any(t["head"] == head["id"] and t["rel"] in ("PRD", "SBJ") for t in tokens)):
            token["head"], token["rel"] = 0, "---"
            head["head"], head["rel"] = token["id"], "SBJ"


def _indefinite(token: dict, tokens: list[dict]) -> bool:
    """Without ال: read so, or read as a مضاف with nothing added to it (الملاحون أقوياء), which it then is not."""
    return token.get("stt") == "i" or (token.get("stt") == "c" and not has_added(token, tokens))


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
