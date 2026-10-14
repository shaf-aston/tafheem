"""What one word shows on its own: its kind, its typed case, its agreement, its listed families.
No sentence is needed for any of these; every other module here builds on them."""
from __future__ import annotations

from backend.services.arabic_text import bare_letters, strip_diacritics
from backend.services.harakat import CAMEL_CASE, PRESENT_PREFIX, SHADDA, SUKUN, has_tanween, own_letters, past_passive_shape, typed_case, typed_passive
from backend.services.nahw_book import book_words, is_diptote, is_fem_plural, is_object_stem, is_one, six_noun_case


# a root letter is what is left once the letters that come and go are removed
WEAK = set("اويىءأإآئؤة")


def read_as(token: dict, family: str) -> bool:
    """The word works as one of this family: by the one reading particles.stamp gave it
    (لا before a bare noun in nasb is the لا of genus, never a joining word), else by the
    family's list, for a word with one reading only."""
    reading = token.get("reading")
    if reading:
        return reading["family"] == family
    return family not in token.get("judged", ()) and is_one(token["lemma"], family)


def is_verb(token: dict) -> bool:
    if token.get("reading"):
        return token["reading"]["kind"] == "fil"  # أَلَا is a particle, whatever the parser tagged it
    if has_tanween(token.get("typed")):
        return False  # a verb never carries tanween, whatever the parser tagged it
    if token["pos"].startswith("VRB"):  # VRB-PASS is a verb too
        return True
    # the word is unknown to the morphology, but the reader typed a passive verb or a
    # hollow command (بِعْ, which CAMeL takes for a name)
    typed = token.get("typed") or ""
    # naming marks a typed command shape (asp c): بِعِ البيتَ، اعْبُدُوا. Not Form IV's أَفْعِلْ,
    # which a name shares (أَحْمَدْ); CAMeL's own reading settles that one
    if token.get("asp") == "c" and strip_diacritics(typed)[:1] != "أ":
        return token.get("pos_camel") in ("noun", "noun_prop")  # نَمْ is not the noun نَمّ
    return token.get("pos_camel") == "noun_prop" and (
        (token["base"][:1] in PRESENT_PREFIX and typed_passive(typed, True, token.get("stuck_on", 0)))
        or past_passive_shape(typed))


def is_light(token: dict) -> bool:
    """The light لكنْ (or إنْ، أنْ) the reader typed: a sukun on the end and no shadda. It
    only joins (or is the light particle); the inna sister wears the shadda (Tasheel 1.8 p20)."""
    typed = token.get("typed") or ""
    return typed.endswith(SUKUN) and SHADDA not in typed


def is_passive(token: dict) -> bool:
    if token.get("asp") == "c":
        return False  # a command is never passive; اُكْتُبُوا opens with a damma all the same
    if token.get("vox") == "p":
        return True
    typed = own_letters(token.get("typed") or "", token.get("front", 0), 0)  # وَيُغْسَلُ opens with the و's fatha
    present = token.get("asp") == "i" or not (token["pos"].startswith("VRB") or past_passive_shape(typed))
    return typed_passive(typed, present, token.get("stuck_on", 0))


def typed_case_of(token: dict) -> str | None:
    """The case the reader typed on the word: its last vowel, or for one of the six nouns
    as a مضاف the long letter standing for it (أَخُوْ، أَخَا، أَخِيْ زَيْدٍ; أَبَاهُ)."""
    shown = typed_case(token.get("typed") or "", token.get("stuck_on", 0))
    return shown or six_noun_case(token["base"], token["lemma"])


def shows_nasb_by_kasra(token: dict) -> bool:
    """A sound feminine plural (ـات) whose typed kasra is also its nasb (رأيت المعلماتِ، آتَيْنَاهُمْ آيَاتِنَا)."""
    return typed_case_of(token) == "i" and is_fem_plural(token["base"], token.get("num", "na"))


def shows_jarr(token: dict) -> bool:
    """The typed ending can be jarr: a kasra, or a diptote's fatha (طَرِيقَ جَهَنَّمَ، بَنِي إِسْرَائِيلَ)."""
    shown = typed_case_of(token)
    return shown == "i" or shown == "a" and is_diptote(token.get("typed") or "", token.get("pos_camel", ""), token["lemma"],
                                         attached=bool(token.get("stuck_on")), annexed=bool(token.get("mudaf")))


def shown_cases(token: dict) -> set[str]:
    """Every case the word's ending can mean: the one typed or parsed, and nasb too for a
    ـات word typed with a kasra."""
    shown = typed_or_parsed_case(token)
    return {shown, "a"} if shows_nasb_by_kasra(token) else {shown} - {None}


def is_preposition(token: dict) -> bool:
    """A particle of the book's list of حروف الجر, or one the parser tags a preposition; a word
    particles.stamp read one way (حتى before إذا is no جر) is what that reading says."""
    reading = token.get("reading")
    return token["pos"] == "PRT" and (reading["family"] == "jarr" if reading else token.get("pos_camel") == "prep" or read_as(token, "jarr"))


def typed_or_parsed_case(token: dict) -> str | None:
    """What the reader typed first, the parser's guess second."""
    return typed_case_of(token) or CAMEL_CASE.get(token.get("cas"))


def same_case(token: dict, head: dict) -> bool:
    """The word and the noun it hangs on wear one case."""
    return bool(shown_cases(token) & shown_cases(head)) and not is_verb(head)


def agrees(token: dict, head: dict) -> bool:
    """A na't matches its noun in case, in "the" and in number (Tasheel 3.10.1): a word in
    idafa counts as definite, so an indefinite word after a definite or construct noun does
    not agree; a dual describes only a dual (مُحَمَّدٌ وَعَلِيٌّ مُجْتَهِدَانِ: the khabar of both).
    Only the dual is compared: a plural not of people takes a singular na't (الكتبُ الجديدةُ);
    and only a noun's: a verb reading's number is its doer's (ضَحِكًا read as ضَحِكَا)."""
    dual = [t.get("num") == "d" for t in (token, head) if t["pos"] in ("NOM", "PROP")]
    return same_case(token, head) and not (token.get("stt") == "i" and head.get("stt") in ("d", "c")) \
        and len(set(dual)) < 2


def unlike(token: dict, head: dict) -> bool:
    """In its noun's case yet not agreeing: no na't, so a khabar or a hal."""
    return same_case(token, head) and not agrees(token, head)


def told_of_subject(token: dict, head: dict) -> bool:
    """A modifier of a subject in raf' or jarr: the khabar (لا رجلَ حاضرٌ), not a follower."""
    mine, theirs = typed_or_parsed_case(token), typed_or_parsed_case(head)
    return bool(mine and theirs and head["rel"] in ("SBJ", "TPC") and mine != "a")


def indefinite_nasb(token: dict) -> bool:
    """An indefinite word in nasb: a hal or tamyeez, never a na't."""
    return typed_or_parsed_case(token) == "a" and token.get("stt") != "d"


def is_state_word(token: dict) -> bool:
    """What a hal is made of: a participle, or any word beginning مـ."""
    return is_participle(token) or bare_letters(token.get("typed") or "")[:1] == "م"


def state_or_specification(token: dict, head: dict) -> str:
    """An indefinite nasb word is a hal if it is a participle, else a tamyeez, which never
    comes before its head (Tasheel 3.2 p67)."""
    if is_state_word(token):
        return "state"
    return "specification" if token["id"] > head["id"] else "none"


def is_deputy(token: dict, doers: list[dict]) -> bool:
    """Under a passive verb the first of its nouns (a subject before an object, then by
    position) stands in for the doer; only a later one is an object."""
    first = min(doers, key=lambda t: (t["rel"] == "OBJ", t["id"]))
    return token is first


def is_object_pronoun(token: dict) -> bool:
    """إيّاك، إيّاه: the detached pronoun of nasb, only ever an object (Tasheel 2.4.1 p31),
    though the parser tags its إيا a particle."""
    return is_object_stem(token["form"]) and _listed(token, "damir_munfasil")


def is_called_alone(token: dict) -> bool:
    """اللهمّ: the called noun with the ميم in the place of يا, so no particle before it."""
    return _listed(token, "nida", "called_alone")


def is_called_noun(token: dict) -> bool:
    """أيها، أيتها: the noun يا calls, though the parser tags it a particle."""
    return _listed(token, "nida", "called_nouns")


def _skeleton(word: str) -> list[str]:
    return [letter for letter in bare_letters(word) if letter not in WEAK]


def same_root(token: dict, other: dict) -> bool:
    """فَرِحَ فَرَحًا، يُطَهِّرَكُمْ تَطْهِيرًا: one root, the analyser's where both have one,
    else the lemma's letters less the weak ones (the ت of تَفْعِيل is not a weak letter)."""
    if token.get("root") and other.get("root"):
        return token["root"] == other["root"]
    return _skeleton(token["lemma"]) == _skeleton(other["lemma"])


def is_participle(token: dict) -> bool:
    """An active or passive participle, or an adjective: what a hal is made of.
    A word the morphology does not know (مسرعا) is judged by its مـ and its ending ـا."""
    typed = bare_letters(token.get("typed") or "")
    return (token.get("ud") == "ADJ" or token.get("pos_camel") == "adj"
            or token.get("pattern", "").removeprefix("ال").startswith(tuple(book_words("participle_patterns")))
            or (token.get("pos_camel") == "noun_prop" and typed[:1] == "م" and typed[-1:] == "ا"))


def is_masdar(token: dict) -> bool:
    """A noun of a masdar measure (شُكْرًا), judged by the analyser's pattern."""
    return token.get("pos_camel") == "noun" and token.get("pattern", "").removeprefix("ال").startswith(
        tuple(book_words("masdar_patterns")))


def _listed(token: dict, family: str, part: str = "words") -> bool:
    """On a book list by its lemma, by the form as typed, or by that form without its
    tanween alef: the list holds صباحا and كوب, while the parser lemmatises the first
    to صباح and may misread the second (كُوبًا as كوان)."""
    form = strip_diacritics(token["form"])
    bare = form[:-1] if form.endswith("ا") and has_tanween(token.get("typed") or "") else form
    return any(is_one(spelling, family, part) for spelling in (token["lemma"], form, bare))
