"""The one reading of a small word with several (لا، إلا، ألا، إذا), decided once per sentence.

A word on more than one list (لا is a joining word, the لا of genus, a negation and a
prohibition) used to be read by whichever list a caller asked first, so the card, the
picture and the case rules could each read it apart. Here the book's tests decide it
once (data/nahw_rules/particle_tree.json, walked like the naming tree) and the answer is
stamped on the token as `reading`; facts, naming, the picture and the card all read that.
`stamp` works in place: it writes the readings on the tokens and corrects the few word classes and links they settle.
"""
from __future__ import annotations

from functools import lru_cache
from itertools import takewhile
from typing import Callable, Iterator

from backend.services.text.arabic_text import has_al, strip_diacritics
from backend.services.text.harakat import (
    DAMMA, FATHA, KASRA, PRESENT_PREFIX, SHADDA, SUKUN, doubled_last, fits_shape, five_verb_nun, letters, own_letters, stilled, typed_case)
from backend.services.sarf.morphology import has_comparative
from backend.services.nahw.book import (
    book_file, book_map, book_spelling, book_words, condition_of, family_cards, in_family, is_mabni, is_one, is_subject_pronoun, says)
from backend.services.nahw.syntax import facts, walker
from backend.services.nahw.syntax.facts import above


def _lemma(token: dict) -> str:
    """The word's lemma, spelled as the reader typed it: إِذًا (a tanween) is the spelling of
    إذن, which the time word إذا never takes (data: nasb_mudari `tanween_spells`)."""
    lemma, written = book_spelling(token["lemma"]), book_spelling(token["form"])
    if written != lemma and written.endswith(lemma) and written in _words():
        lemma = written  # فَلَمّا: the dictionary files the negation لَمّا under ما; the word written is لما
    spelled = book_map("nasb_mudari", "tanween_spells").get(lemma)
    return spelled if spelled and facts.typed_tanween(token) else lemma


def _word(token: dict, s: facts.Sentence) -> str:
    lemma = _lemma(token)
    return lemma if lemma in _words() and not _jarred_noun(token, s) else "other"


def _jarred_noun(token: dict, s: facts.Sentence) -> bool:
    """بِإِذْنِ اللَّهِ: a preposition written onto it and a kasra typed on its end is a noun in
    jarr, never the particle it is spelled like (إِذَنْ); بِأَنَّ، لِكَيْ end on no kasra. So is one the
    dictionary read as a noun (بِغَيْرِ إِذْنِ وَلِيِّهَا, an مضاف إليه): أَنِ اعْبُدُوا's moved kasra is a particle's."""
    if facts.typed_case_of(token) != "i":
        return False
    before = s.by_id.get(token["id"] - 1)
    return bool(before and facts.is_prefix(before) and before.get("pos_camel") == "prep" or token.get("pos_camel") == "noun")


def _what_follows(token: dict, s: facts.Sentence) -> str:
    """A verb in jazm (its last letter stilled or the nun of the five verbs gone), any other
    verb, an indefinite noun (no ال, no name, no pronoun on it: رجلَ، عدوى), a definite one,
    a tool (a particle, or a word only a condition opens with: إذا is a ظرف, a noun), or nothing."""
    # أَنَّنَا اجْتَهَدْنَا، إنه ذهب: a pronoun written onto the particle is the noun after it (its اسم), never past it
    if (own := s.by_id.get(token["id"] + 1)) and facts.is_suffix(own):
        return "noun"
    after = facts.next_word(token, s)
    if after is None:
        return "none"
    typed = after.get("typed") or ""
    if facts.is_verb(after) and not _is_present(after):
        return "verb"  # نَقَصَتْ: a past verb is never in jazm; its تْ is the still ت of the feminine
    if facts.is_verb(after):
        stuck_on, weak = after.get("stuck_on", 0), after.get("weak_last")
        # أَنْ لَا تَطُوفِي: after a nasb particle the nun is gone for its nasb, so it shows no jazm
        before = s.by_id.get(token["id"] - 1)
        bases = [t for t in s.tokens if "typed" in t]  # the words the reader typed (repair.correct)
        nasbed = bool(before and is_one(_lemma(before), "nasb_mudari", "before_a_present_verb")) \
            or (after in bases and facts.stressed_nasb(bases, bases.index(after)) is not None)  # لَنْ يَرُدَّ وَلَا يَمُدَّ
        # لِيَلِيَنِّي: a verb the nun of emphasis builds shows no jazm, the لام says it (facts.lam_mood)
        # لَا تَمُدَّ يَدَكَ: a doubled verb's jussive wears a fatha too (harakat.doubled_last), so with no nasb particle before it
        # (أَنْ لَا تَمُدَّ) the لا forbids: no negation puts a verb in nasb
        shows_jazm = five_verb_nun(typed, stuck_on, weak) == "dropped" or doubled_last(typed, stuck_on, fatha=True)
        jazm = stilled(typed, stuck_on, weak) or _moved_still(after, s) or _lam_on(after, s) == "jazm" \
            or (shows_jazm and not nasbed and _lam_on(after, s) != "nasb")
        return "verb_jazm" if jazm else "verb"
    if after["pos"] == "PRT" or ((cond := condition_of(_lemma(after))) and not cond["shared"]):
        return "tool"
    return "noun" if facts.is_known(after, s) else "indefinite_noun"


def _lam_on(verb: dict, s: facts.Sentence) -> str | None:
    """The mood the لام written onto the verb gives it (facts.lam_mood): وَلِتَبْتَغُوا lost its nun to the
    nasb of لام التعليل, not to the jazm of لام الأمر. Its pieces are those written straight before it. Read as
    not opening the sentence: a لِ that opens it is still named by the jazm its verb's card gives (naming)."""
    front: list[dict] = []
    while (piece := s.by_id.get(verb["id"] - len(front) - 1)) and facts.is_prefix(piece):
        front.insert(0, piece)
    return facts.lam_mood(verb, [t["form"].strip("+") for t in front], opens=False)


def _moved_still(verb: dict, s: facts.Sentence) -> bool:
    """لا تَأْكُلِ السَّمَكَ: a present verb's sukun of jazm turns kasra before the joining
    hamza of ال (التقاء الساكنين); a kasra is never the present verb's own case."""
    own = letters(verb.get("typed") or "")[:len(letters(verb.get("typed") or "")) - verb.get("stuck_on", 0)]
    after = facts.next_word(verb, s)
    return bool(own) and not verb.get("stuck_on") and "\u0650" in own[-1][1] and SHADDA not in own[-1][1] \
        and bool(after) and has_al(after.get("typed") or after["form"])


def _negated(token: dict, s: facts.Sentence) -> str:
    return "yes" if s.negated_before(token) else "no"


def _joins(token: dict, s: facts.Sentence) -> str:
    """The noun after it wears the case of the noun before it: جاء زيدٌ لا عمرٌو, ما جاء
    الطلابُ إلا زيدٌ; before إلا, the noun excepted from, out of any جار ومجرور or إضافة that adds
    to it (ما جاء أحدٌ من الضيوف إلا زيدٌ). Nothing to share a case with (ما جاء إلا زيدٌ) or a case apart
    (لا إلهَ إلا اللهُ) says no."""
    before, after = facts.excepted_from(token, s), facts.next_word(token, s)
    if not (before and after and facts.noun_tagged(after)):
        return "no"
    behind = s.by_id.get(before["id"] - 1)
    if behind and behind["pos"] == "PRT" and is_one(behind["lemma"], "negation") and not facts.read_as(behind, "la_jins"):
        return "no"  # ما أنت إلا بشر: the noun after the negation is the مبتدأ, what follows إلا its khabar
    mine = facts.case_shown(after)
    if not mine:
        # لا اله الا الله typed bare, لا إله إلا هو: the اسم لا named before إلا is the
        # excepted-from, so it is an exception, not a حصر (Tasheel 3.8.7). Elsewhere a case
        # that cannot show (ما أنقذ الغريقَ إلا فتًى) tells nothing: the verb may still want its فاعل.
        # ما جاء أحد إلا زيد typed bare: the noun excepted from is the doer of the very verb the إلا hangs on, a verb the book
        # lists as taking no object (intransitive_verbs), so the word after is its بدل (ما أكرم المعلم إلا فتى may be its object)
        verb = s.head(before) or {}
        doer_given = before["rel"] == "SBJ" and facts.is_verb(verb) and verb is s.head(token) and is_one(verb["lemma"], "intransitive_verbs")
        return "yes" if doer_given or (behind and facts.read_as(behind, "la_jins")) else "no"
    return "yes" if mine == facts.place_case(before, s) else "no"


def _tool_next(token: dict, s: facts.Sentence) -> str:
    """The word after it is خلا, عدا or حاشا (ما عدا زيدًا): the ما that turns them into a masdar."""
    after = facts.next_word(token, s)
    return "yes" if after and is_one(after["form"], "istithna_verbs") else "no"


def _timed(token: dict, s: facts.Sentence) -> str:
    """The word after it is لم or دام (data: istithna_verbs `timed_ma_before`) and it does not
    open the sentence (دام aside): ما المصدرية الظرفية, "as long as" (البيعان بالخيار ما لم يتفرقا). Added to a noun
    before it, or after a preposition, it is in jarr: the ما of a noun, the relative, not a time word
    (سَأُنَبِّئُكَ بِتَأْوِيلِ مَا لَمْ تَسْتَطِعْ عَلَيْهِ صَبْرًا; Mughni, ما الاسمية)."""
    after, before = facts.next_word(token, s), s.by_id.get(token["id"] - 1)
    in_jarr = token["rel"] == "IDF" or bool(before and facts.is_preposition(before))
    # أَنَا عَلَى عَهْدِكَ وَوَعْدِكَ مَا اسْتَطَعْتُ: the relative ما describes no noun (closed_words mawsul `mubham`), so one the
    # parser hung on a noun before it, a past verb after it, is the span of that verb; hung on a verb as neither its doer
    # nor its object, it fills no noun's place there either (فَاتَّقُوا اللَّهَ مَا اسْتَطَعْتُمْ). A حرف has no pronoun returning to
    # it, so a ـه on the verb is the عائد of the relative: سَرَّنِي الْخَبَرُ مَا سَمِعْتُهُ
    on_word = (token["rel"] == "MOD" and (word := s.head(token)) and word["id"] < token["id"]
               and (facts.noun_tagged(word) or facts.is_verb(word)) and after and facts.is_verb(after) and not _is_present(after)
               and not any(facts.attached_pronoun(k) and strip_diacritics(k["form"]).strip("+") == "ه" for k in s.kids(after)))
    # ما دمت هنا فاجلس: دام governs only after this ما, so before it ما is never the negation, opening the sentence too
    opens_dama = after and not before and is_one(after["lemma"], "kana", "needs_ma")
    return "yes" if opens_dama or before and after and not in_jarr and (on_word or is_one(
        after["lemma"] or after["form"], "istithna_verbs", "timed_ma_before")) else "no"


def _answered(token: dict, s: facts.Sentence) -> str:
    """A tying letter of its condition (ف) is written later onto a word that could not stand as a
    condition itself, anything but a past verb (data: roles.json condition `_evidence_comment`):
    ما أصابك من حسنة فمن الله is the ما of a condition, never the negation."""
    ties = (condition_of(_word(token, s)) or {}).get("ties") or {}
    for piece in s.tokens:
        if piece["id"] > token["id"] and facts.is_prefix(piece) and piece["form"].strip("+") in ties:
            after = s.by_id.get(piece["id"] + 1)
            if after and not (facts.is_verb(after) and not _is_present(after)):
                return "yes"
    return "no"


def _raf(token: dict, s: facts.Sentence) -> str:
    """The noun after it is typed in raf' (damma or tanween with damma): the noun of لا of the
    genus is never raf', so this لا is a plain negation and the noun is a مبتدأ."""
    after = facts.next_word(token, s)
    return "yes" if after and facts.typed_case_of(after) == "u" else "no"


def _told(token: dict, s: facts.Sentence) -> str:
    """What stands straight after the noun that follows: a noun (its khabar) or anything else."""
    noun = facts.next_word(token, s)
    told = facts.next_word(noun, s) if noun else None
    return "noun" if told and facts.noun_tagged(told) and not facts.is_verb(told) else "other"


def _fronted(token: dict, s: facts.Sentence) -> str:
    """ما في الدار أحدٌ، ما لك عليّ سلطانٌ: one or more جار ومجرور or ظرف straight after it, then a noun
    in raf': the khabar came first, so the noun is its مبتدأ مؤخر and the ما only negates; a ما with
    its khabar first does not work as ليس (Tasheel 1.9 n6 p23). A describing word there (وما عند الله
    خيرٌ، باقٍ) is told of the ما, the relative, and is its khabar, unless a صفة of its own makes it a thing named (ما له عاملٌ آخرُ). Its majrur, and what is added to
    it (في بيتِ زيدٍ), are in jarr; a joined one (فيه، عندي) is no word of its own. A مضاف إليه
    of a word inside it, in whatever case it shows (مَا بَيْنَ خَلْقِ آدَمَ ... خَلْقٌ: آدَمَ's fatha is its jarr) is inside it too."""
    words = [t for t in s.tokens if t["id"] > token["id"] and not facts.is_suffix(t)]
    at = 0
    inside = set()  # the words of the fronted phrase: what is added to them or governed by them is no noun to ask for
    while at < len(words) and (facts.is_preposition(words[at]) or facts.is_zarf(words[at], s)
                               or facts.typed_case_of(words[at]) == "i" or words[at]["rel"] == "IDF" and words[at]["head"] in inside):
        inside.add(words[at]["id"])
        at += 1
    noun = words[at] if 0 < at < len(words) else None
    # ما في الدار من رجلٍ، ما لي من صديقٍ في المدينة: a مِن after the first of them, before an indefinite noun, is
    # زائدة and its noun the مبتدأ, whatever jar-majrur comes after it
    drawn = not noun and any(t is not words[0] and facts.is_preposition(t) and is_one(t["lemma"], "extra_min") and any(
        k["rel"] == "OBJ" and facts.noun_tagged(k) and not facts.is_known(k, s) for k in s.kids(t)) for t in words[:at])
    # ما له عاملٌ آخرُ: a participle with a صفة of its own names a thing, the مبتدأ, not a khabar told of ما; an
    # elative compares what ما is to something, so is told of it still (ما عند الله خيرٌ كثيرٌ)
    described = noun and not facts.is_elative(noun) and any(k["rel"] == "MOD" and k["id"] > noun["id"] and facts.noun_tagged(k) and facts.agrees(k, noun)
                             for k in s.kids(noun))
    return "yes" if drawn or noun and facts.noun_tagged(noun) and facts.typed_case_of(noun) == "u" \
        and (described or not facts.is_describing(noun)) else "no"


def _opens(token: dict, s: facts.Sentence) -> str:
    """The noun after it opens a sentence of its own: a known noun in raf' with an unknown
    one in raf' after it, its khabar (واللهُ أكبرُ); a known one after it (والطلابُ جميعُهم)
    stresses or describes it, so the و joins."""
    noun = facts.next_word(token, s)
    told = facts.next_word(noun, s) if noun else None
    if not (noun and told and facts.noun_tagged(noun) and facts.noun_tagged(told)) or facts.is_verb(told):
        return "no"
    return "yes" if facts.is_known(noun, s) and facts.typed_or_parsed_case(noun) == "u" \
        and facts.typed_or_parsed_case(told) == "u" and not facts.is_known(told, s) else "no"


def _pronoun_of(verb: dict, s: facts.Sentence) -> dict | None:
    """The pronoun written onto the verb (أدراك، أجملها)."""
    return next((t for t in s.tokens if t["id"] == verb["id"] + 1 and facts.is_suffix(t)), None)


def _asked_after(token: dict, s: facts.Sentence) -> bool:
    """A question word stands straight after it (data: istifham `words`); a preposition does not
    count (مِنْ لَيْلَةٍ)."""
    after = facts.next_word(token, s)
    return bool(after) and not facts.is_preposition(after) and is_one(after["form"], "istifham")


def _after_object(noun: dict, s: facts.Sentence) -> dict | None:
    """The indefinite noun in nasb straight after an object."""
    more = facts.next_word(noun, s)
    return more if more and facts.noun_tagged(more) and more.get("stt") == "i" and not facts.is_verb(more) \
        and facts.typed_or_parsed_case(more) == "a" else None


def _wonder_parts(token: dict, s: facts.Sentence) -> tuple[dict, dict] | None:
    """ما أجمل السماء: (the verb, its object) when ما is followed by a verb of the wonder shape
    (data: wonder `shapes`, read from the letters) and a noun that is not raf', or a pronoun on the
    verb (ما أجملها), its one object that closes the clause (Tasheel 1.4.2 p8). A typed case is held to
    nasb; plain text only has the analyser's, so a noun it reads raf' (ما أكرم زيدٌ) makes the verb an
    ordinary one. A second indefinite nasb noun (ما أعطى الرجل كتابًا) is no wonder, nor is a question
    word after the pronoun (ما أدراك ما يوم الدين: that clause is its second object), nor a verb whose
    root gives no comparative أفعل (ما أنزل الله: a negation), the wonder being built only where the
    comparative is."""
    verb = facts.next_word(token, s)
    pronoun = _pronoun_of(verb, s) if verb else None
    noun = pronoun or (facts.next_word(verb, s) if verb else None)
    if not (verb and noun and verb["pos"] != "PRT" and facts.noun_tagged(noun) and not facts.is_verb(noun)):
        return None
    if pronoun:
        if _asked_after(pronoun, s):
            return None
    else:
        typed = facts.typed_case_of(noun)
        case = facts.typed_or_parsed_case(noun)
        if case == "u" or (typed == "i" and not facts.shows_nasb_by_kasra(noun)):
            return None
    own = own_letters(verb.get("typed") or "", 0, verb.get("stuck_on", 0))  # the pronoun's letters are not the shape's
    if not any(fits_shape(own, shape, verb.get("root") or "") for shape in book_words("wonder", "shapes")) \
            or not has_comparative(verb["form"]):
        return None
    # after a noun object a second indefinite nasb noun is no wonder (ما أعطى الرجل كتابًا); after a
    # pronoun it is a second object only of a verb that takes two (ما أعطاها كتابًا), else the
    # tamyeez (ما أجملها ليلةً)
    lemma = verb["lemma"]
    second = _after_object(noun, s) and (not pronoun or is_one(lemma, "two_objects_give") or is_one(lemma, "zanna"))
    return None if second else (verb, noun)


def _wonder(token: dict, s: facts.Sentence) -> str:
    return "yes" if _wonder_parts(token, s) else "no"


def _informing(token: dict, s: facts.Sentence) -> dict | None:
    """وما أدراك ما يوم الدين: the verb after it when it is a verb of informing with its first
    object written on it and a question word after that, the clause which is its second object."""
    verb = facts.next_word(token, s)
    pronoun = _pronoun_of(verb, s) if verb else None
    lemma = verb["lemma"] if verb else ""
    return verb if pronoun and (is_one(lemma, "two_objects_give") or is_one(lemma, "zanna")) \
        and _asked_after(pronoun, s) else None


def _asks_nominal(token: dict, s: facts.Sentence) -> bool:
    """ما اسمك، من أنت: a noun, pronoun or pointer in raf' (its مبتدأ; a ظرف is one only if typed so:
    ما يومُ الدين) and nothing else of a clause: no verb after it, no preposition or restricting إلا
    (ما أنت بعالمٍ, ما أنت إلا بشر), no khabar of its own for the noun (ما زيدٌ قائمٌ), not ما الحجازية,
    not a وصف with its own doer (ما ذاهبٌ المسلمون: ما negates the مبتدأ وصف)."""
    after = facts.next_word(token, s)
    if token["pos"] == "PRT" or s.hijazi or (s.described_doer and token is s.described_doer[0]) or not after or not facts.noun_tagged(after) or facts.is_verb(after) \
            or (facts.is_zarf(after, s) and facts.typed_case_of(after) != "u") \
            or not (is_mabni(after.get("pos_camel", "")) or facts.typed_case_of(after) in (None, "u")):
        return False
    later = [t for t in s.tokens if t["id"] > token["id"] and not facts.is_suffix(t)]
    # مَنِ الَّذِي يَضْمَنُ: a relative's صلة is no clause of its own. Only ما can be the negation that a preposition
    # or an إلا after the noun would show (ما أنت بعالمٍ); مَنْ أَحَقُّ النَّاسِ بِحُسْنِ صَحَابَتِي asks all the same
    clause = s.below(after) if is_one(after["lemma"], "mawsul") else set()
    # a verb that is no saying straight before takes it as its object, so what follows is its nominal صلة (فَلْيُبَلِّغِ ... مَنْ
    # هُوَ أَوْعَى لَهُ مِنْهُ), and a preposition after it then ends the asking too (rule from the Tasheel chapter on الموصول, page unchecked)
    shut = is_one(token["lemma"], "negation") or not _opens_clause(token, s)
    return not any((facts.is_verb(t) and t["id"] not in clause)
                   or (shut and (facts.is_preposition(t) or (t["pos"] == "PRT" and is_one(t["lemma"], "hasr"))))
                   for t in later) and _opens(token, s) == "no"


def _asks(token: dict, s: facts.Sentence) -> str:
    return "yes" if _informing(token, s) or _asks_nominal(token, s) else "no"


def _opens_clause(token: dict, s: facts.Sentence) -> bool:
    """Nothing before it asks for it: a verb straight before takes it as its object (قرأتُ ما كتبَ),
    and so does a preposition (لا يعلمُ ما في الغيبِ), unless the verb is one of saying, whose quoted
    speech it opens (قالوا ما أنتم إلا بشرٌ; data: roles.json said_clause)."""
    before = next((t for t in reversed(s.tokens) if t["id"] < token["id"] and not facts.is_suffix(t)), None)
    return not (before and (facts.is_preposition(before)
                            or (facts.is_verb(before) and not says(before["lemma"]))))


def _restricted(token: dict, s: facts.Sentence) -> str:
    """The ما opens its clause and an إلا of restriction comes later in it: the ما is the negation."""
    return "yes" if _opens_clause(token, s) and any(
        t["id"] > token["id"] and not facts.is_suffix(t) and is_one(t["lemma"], "hasr") for t in s.tokens) else "no"


def _negates_a_verb(token: dict, s: facts.Sentence) -> str:
    """A particle comes after it and a present verb after that: a conditional إنْ takes its negation (لم، لا) between it
    and its verb (فَإِنْ لَمْ تَفْعَلُوا، إِنْ لَا تَفْعَلُوهُ: Mughni, إنْ الشرطية; page unchecked), so the condition opens on
    the negated verb. Without a verb there is no condition (إِنْ لَا رَيْبَ فِيهِ)."""
    after = facts.next_word(token, s)
    verb = facts.next_word(after, s) if after else None
    return "yes" if after and after["pos"] == "PRT" and verb and facts.is_verb(verb) and _is_present(verb) else "no"


def _differing_lam(token: dict, s: facts.Sentence) -> str:
    """A ناسخ verb comes after it (كان، كاد، ظن and their sisters) and a لام of emphasis on that verb's own خبر: the
    إنْ is the lightened إنّ, idle, and the لام tells it from the negating إنْ (Alfiyya, إنّ وأخواتها: وتلزم اللام إذا ما
    تهمل ... والفعل إن لم يك ناسخا فلا تلفيه غالبا بإن ذي موصلا; Mughni V1 p37, إن المكسورة الخفيفة):
    وَإِنْ وَجَدْنَا أَكْثَرَهُمْ لَفَاسِقِينَ، وَإِنْ كَادُوا لَيَفْتِنُونَكَ. The لام sits on that خبر itself, never after a و
    (وَلَقَدْ وَعَدْتُكَ opens another sentence). The clause ends at a ف, at إنّ or a sister of it, or at a خبر the verb
    already holds (`_holds_khabar`): a لام after that opens another clause, as the answer of an oath left unsaid does (وَاللَّهِ إِنْ
    كَانَ زَيْدٌ صَادِقًا لَقَدْ ظَلَمْنَاهُ), so the condition stands; so does one on قد or a frozen verb after a جار or
    ظرف that may be that خبر, when an oath opens the sentence (`_answers_oath`). A لام with no fatha typed on it is told
    only on a جار (`is_emphasis_lam`), so unvowelled text may read the condition."""
    verb = facts.next_word(token, s)
    if not (verb and any(in_family(verb["lemma"], kin) for kin in ("kana", "kaada", "zanna"))):
        return "no"
    if _what_follows(token, s) == "verb_jazm":
        return "no"  # إِنْ تَكُنْ لَصَادِقًا، إِنْ تَكُونُوا لَصَادِقِينَ: the lightened إنّ governs nothing, so a present verb after it is in raf' (وَإِنْ يَكَادُ)
    tokens = s.tokens
    for i in _clause(tokens.index(verb) + 1, s):
        if _holds_khabar(verb, tokens[i], s):
            return "no"
        if facts.is_emphasis_lam(tokens, i):
            return "yes" if _lam_tells(i, s, khabar_in_nasb=True) and not _answers_oath(verb, i, s) else "no"
    return "no"


def _before_noun(token: dict, s: facts.Sentence) -> str:
    """What an إنْ the reader typed light (a sukun or a kasra on its nun) is before a noun, no ناسخ verb and no إلا after
    it. A conditional word opens only on a verb, so a noun after it belongs to one left out: a past verb after the noun
    that explains it (_explained_at), or كان with only its خبر kept before the answer's ف (_kana_dropped), makes it the
    إنْ of a condition. Else it is the lightened إنّ (Alfiyya, إنّ وأخواتها: وخففت إنّ فقل العمل وتلزم اللام إذا ما تهمل):
    idle, the noun a مبتدأ, where a لام of emphasis comes on the خبر (إِنْ هَذَانِ لَسَاحِرَانِ), and working where the
    reader typed its noun in nasb, which tells it from the negation with no لام needed (إِنْ زَيْدًا قَائِمٌ). A خبر put
    first, a جار or a ظرف, leaves that noun after it (إِنْ فِي ذَلِكَ لَعِبْرَةً). A لام after the explaining verb is the خبر's
    only where that verb is a صفة on the noun, which still wants its خبر (إِنْ رَجُلٌ صَدَقَ لَنَاجٍ), and no oath opens the
    sentence, whose answer it then is (وَاللَّهِ إِنْ أَحَدٌ زَارَكَ لَزَيْدٌ خَيْرٌ مِنْهُ); else it is inside that verb's
    words (إِنْ أَحَدٌ قَالَ لَزَيْدٌ أَفْضَلُ مِنْكَ فَكَذِّبْهُ). With none of these it negates (إِنْ عِنْدَكُمْ مِنْ سُلْطَانٍ بِهَذَا). An إن typed
    with no such mark may be إنّ written without its shadda, so it reads as that ("other")."""
    if not facts.is_light(token):
        return "other"
    tokens = s.tokens
    clause = list(_clause(tokens.index(token) + 1, s))
    first = next((tokens[i] for i in clause if not facts.is_suffix(tokens[i])), None)
    if first is None:
        return "negation"
    fronted = _jar_or_zarf(first, s)
    noun = _put_after(first, clause, s) if fronted else first
    explained = None if fronted else _explained_at(first, clause, s)
    nasb = noun is not None and _shows_nasb(noun)
    if any(facts.is_emphasis_lam(tokens, i) and _lam_tells(i, s, khabar_in_nasb=False)
           and (explained is None or i < explained or _khabar_past_sifa(i, explained, first, clause, s)) for i in clause):
        return "working" if nasb else "idle"
    if explained is not None and _has_answer(explained, token, s) or _kana_dropped(first, clause, s):
        return "condition"
    return "working" if nasb else "negation"


def _jar_or_zarf(token: dict, s: facts.Sentence) -> bool:
    return facts.is_preposition(token) or facts.is_zarf(token, s)


def _khabar_past_sifa(i: int, explained: int, noun: dict, clause: list[int], s: facts.Sentence) -> bool:
    """The لام at `i`, after the verb at `explained`, is on the خبر: that verb is a صفة on the noun, which still wants
    its خبر (إِنْ رَجُلٌ صَدَقَ لَنَاجٍ). Where an oath opens the sentence the لام answers it, the condition before it
    whole (وَاللَّهِ إِنْ أَحَدٌ زَارَكَ لَزَيْدٌ خَيْرٌ مِنْهُ), unless the لام's word stands alone, all after it its own
    words: an oath's answer is a whole sentence, never one noun (وَاللَّهِ إِنْ رَجُلٌ صَدَقَ لَنَاجٍ)."""
    tokens = s.tokens
    word = tokens[i + 1]
    return tokens[explained]["head"] == noun["id"] and (facts.sworn_by(s) is None or all(
        s.under(tokens[j]["id"], word["id"]) for j in clause if j > i + 1))


def _has_answer(at: int, token: dict, s: facts.Sentence) -> bool:
    """A condition is never the whole sentence (Mughni, إنْ النافية, page unchecked). After its verb at `at` the answer is
    opened by what only an answer takes there: a فاء (Ibn Aqil V4 p37: إن جاء زيد فاضربه), the لام of an oath's answer
    (لَزَيْدٌ خَيْرٌ مِنْهُ), or a verb standing bare, not joined on or put under a particle, that is an answer and no حال or
    صفة (`_answers_bare`); the verb's own object or جار is none (إِنْ أَحَدٌ رَأَى زَيْدًا، إِنْ أَحَدٌ خَرَجَ مِنَ الدَّارِ: no
    one saw Zayd, came out of the house). The answer may also be put first, before the إنْ, where no oath opens the
    sentence, whose answer comes after it, and the last verb before it is no verb of saying, which opens it as its speech
    (أُكْرِمُكَ إِنْ أَحَدٌ زَارَنِي; not قُلْتُ لَكَ إِنْ أَحَدٌ جَاءَنِي، قَالَ زَيْدٌ إِنْ أَحَدٌ جَاءَنِي). With neither the إنْ negates
    (إِنْ أَحَدٌ جَاءَنِي)."""
    tokens = s.tokens
    if any(tokens[j]["form"] == "ف+" or facts.is_emphasis_lam(tokens, j)
           or _answers_bare(tokens[j]) and tokens[j - 1]["pos"] != "PRT" and not _inside(j, at, tokens)
           for j in range(at + 1, len(tokens))):
        return True
    before = [t for t in tokens[:tokens.index(token)] if not facts.is_prefix(t)]
    verbs = [t for t in before if facts.is_verb(t)]
    if verbs and says(verbs[-1]["lemma"]) or facts.sworn_by(s) is not None:
        return False
    return bool(verbs) or _nominal(before)


def _inside(j: int, at: int, tokens: list[dict]) -> bool:
    """The verb at `j` is inside the condition verb's own sentence, no answer: under it through another word, a صلة of its
    object or what it governs (إِنْ أَحَدٌ رَأَى الَّذِي سَرَقَ، إِنْ أَحَدٌ قَالَ إِنَّ زَيْدًا خَرَجَ: no one saw the one who stole),
    or straight under a verb of saying, its speech (إِنْ أَحَدٌ قَالَ اذْهَبْ). The parser hangs a bare answer straight on the
    condition verb (إِنْ أَحَدٌ زَارَنِي أَكْرَمْتُهُ)."""
    word = next(t for t in tokens[j:] if not facts.is_prefix(t))
    verb = tokens[at]
    return above([t["head"] for t in tokens], word["id"], verb["id"]) and (word["head"] != verb["id"] or says(verb["lemma"]))


def _nominal(words: list[dict]) -> bool:
    """Words before the إنْ that may be its answer put first, a whole sentence: two words beyond a particle, with no call
    among them (أَنْتَ ظَالِمٌ إِنْ أَحَدٌ ظَلَمْتَهُ); a called noun or a bare particle is none (يَا زَيْدُ إِنْ أَحَدٌ جَاءَنِي، بَلْ
    إِنْ أَحَدٌ جَاءَنِي)."""
    return sum(t["pos"] != "PRT" for t in words) > 1 and not any(is_one(t["lemma"], "nida") for t in words)


def _answers_bare(word: dict) -> bool:
    """A verb that is a condition's answer with no فاء: a past (إِنْ أَحَدٌ زَارَنِي أَكْرَمْتُهُ) or a present typed in jazm,
    stilled or its nun of the five dropped (إِنْ أَحَدٌ يَزُرْكَ تَجِدُوهُ). A present in raf' a past condition's answer may
    take, but a حال or صفة always does, and one typed bare may be either, so neither tells (إِنْ أَحَدٌ جَاءَنَا يَسْأَلُ عَنْكَ:
    no one came asking about you); and a command, which is never a حال or صفة (Ibn Aqil V3 p198: وامنع هنا إيقاع ذات
    الطلب), its فاء written onto it (فَأَجِرْهُ)."""
    if not facts.is_verb(word):
        return False
    typed, stuck_on = word.get("typed") or "", word.get("stuck_on", 0)
    return word.get("asp") in ("p", "c") or facts.typed_mood(typed, word) == "jazm" or facts.five_verbs(word) and five_verb_nun(
        typed, stuck_on, word.get("weak_last")) == "dropped"


def _put_after(fronted: dict, clause: list[int], s: facts.Sentence) -> dict | None:
    """The noun a خبر put first leaves after it: the first word of the clause that does not hang under that جار or ظرف
    (إِنْ فِي الدَّارِ رَجُلًا)."""
    return next((s.tokens[i] for i in clause
                 if not facts.is_prefix(s.tokens[i]) and not s.under(s.tokens[i]["id"], fronted["id"])), None)


def _explained_at(noun: dict, clause: list[int], s: facts.Sentence) -> int | None:
    """The place of the verb that explains the one an إنْ of a condition leaves out before `noun` (Ibn Aqil, الفاعل,
    page unchecked: وَإِنْ أَحَدٌ مِنَ الْمُشْرِكِينَ اسْتَجَارَكَ). It is the first verb after the noun that is not inside
    the noun's own words, a صلة (إِنِ الَّذِينَ كَفَرُوا فِي غُرُورٍ، إِنْ أَحَدٌ مِمَّنْ ظَلَمَكَ) or a صفة that is no
    condition's verb (إِنْ رَجُلٌ لَيْسَ لَهُ مَالٌ جَاءَكَ); a noun joined to it by و is still the noun's (إِنْ زَيْدٌ وَعَمْرٌو
    جَاءَا), a و hung on it, while any other و opens another sentence (إِنْ أَحَدٌ فِي الدَّارِ وَالنَّاسُ نَامُوا). See
    `_explains`."""
    tokens = s.tokens
    heads = [t["head"] for t in tokens]
    cut_at_waw = [0 if t["form"] == "و+" else t["head"] for t in tokens]
    sentence = takewhile(lambda i: tokens[i]["form"] != "و+" or above(heads, tokens[i]["id"], noun["id"]), clause)
    for i in sentence:
        verb = tokens[i]
        if not facts.is_verb(verb) or verb["head"] != noun["id"] and above(cut_at_waw, verb["head"], noun["id"]) \
                or verb["head"] == noun["id"] and facts.listed(noun, "mawsul"):
            continue
        if _explains(i, noun, s):
            return i
        if verb["head"] != noun["id"]:
            return None
    return None


def _explains(at: int, noun: dict, s: facts.Sentence) -> bool:
    """The verb can explain a condition's verb left out before `noun`. It is past, or present after لم or لمّا, which
    turn it past (closed_words jazm `before_a_present_verb`: إِنْ هُوَ لَمْ يَحْمِلْ عَلَى النَّفْسِ ضَيْمَهَا), a present one
    alone being a noun sentence's خبر (إِنْ أَحَدٌ يَعْلَمُ الْغَيْبَ); and one a condition may take (jazm `frozen_verbs`,
    `not_before_its_verb`: not إِنْ زَيْدٌ لَيْسَ بِقَائِمٍ، إِنْ زَيْدٌ قَدْ قَامَ). It holds the noun: as its hidden doer, of
    the noun's person, no doer of its own after it, in raf' or built (هذا), a doer never coming before its verb
    (إِنِ امْرُؤٌ هَلَكَ، إِنْ أَنْتَ قُمْتَ، إِنْ رَجُلٌ وَامْرَأَةٌ جَاءَا; not إِنْ زَيْدٌ ضَرَبْتُهُ، إِنْ زَيْدٌ ضَرَبَهُ الْمُعَلِّمُونَ)
    nor after a لام of emphasis, which opens a sentence of its own (إِنْ أَحَدٌ قَالَ لَزَيْدٌ أَفْضَلُ مِنْكَ فَكَذِّبْهُ), or, the
    noun typed in nasb, as the pronoun the verb is busied with (`facts.busied`, الاشتغال: إِنْ زَيْدًا لَقِيتَهُ، مَرَرْتَ بِهِ،
    أَكْرَمْتَ أَخَاهُ; not إِنْ زَيْدًا قَامَ أَبُوهُ، إِنْ زَيْدًا رَآنِي)."""
    tokens = s.tokens
    verb, before = tokens[at], tokens[at - 1]["lemma"]
    if not (verb.get("asp") == "p" or is_one(before, "jazm", "before_a_present_verb")) \
            or is_one(verb["lemma"], "jazm", "frozen_verbs") or is_one(before, "jazm", "not_before_its_verb"):
        return False
    if _shows_nasb(noun):
        return facts.busied(verb, s)
    person = noun["per"] if is_subject_pronoun(noun) else "3"
    return verb.get("per") == person and not any(
        kid["id"] > verb["id"] and facts.subject_link(kid)
        and (facts.typed_or_parsed_case(kid) == "u" or facts.is_built(kid))
        and not any(facts.is_emphasis_lam(tokens, j) for j in range(at + 1, tokens.index(kid))) for kid in s.kids(verb))


def _kana_dropped(kept: dict, clause: list[int], s: facts.Sentence) -> bool:
    """كان left out after إنْ, one part of its sentence kept alone before the answer's ف (Alfiyya, كان وأخواتها:
    ويحذفونها ويبقون الخبر وبعد إن ولو كثيرًا ذا اشتهر; Ibn Aqil, page unchecked: النَّاسُ مَجْزِيُّونَ بِأَعْمَالِهِمْ إِنْ خَيْرًا
    فَخَيْرٌ): `kept`, a noun or a جار or ظرف put first, with only its own words after it (إِنْ عَمَلًا صَالِحًا فَجَزَاءٌ
    حَسَنٌ). A جار or ظرف after a noun in raf' may be its خبر, which makes a noun sentence (إِنْ أَحَدٌ فِي الدَّارِ فَخَرَجَ);
    after one typed in nasb it is only that noun's (إِنْ خَيْرًا مِنْ ذَلِكَ فَخُذْهُ)."""
    tokens = s.tokens
    end = clause[-1] + 1
    return end < len(tokens) and tokens[end]["form"] == "ف+" and all(
        s.under(tokens[i]["id"], kept["id"]) and not (_jar_or_zarf(tokens[i], s) and not _shows_nasb(kept))
        for i in clause[1:])


def _shows_nasb(noun: dict) -> bool:
    """The reader typed the noun in nasb: a fatha, a feminine plural's kasra, or a word ending in ين with a vowel typed
    on its nun, which nothing after إنْ puts in jarr: a fatha is a plural's nun (إِنِ الْمُسْلِمِينَ صَادِقُونَ) or a broken
    plural's case, both nasb, and a kasra the nun of two (إِنِ الزَّيْدَيْنِ قَائِمَانِ). With no vowel there the letters
    do not tell a plural's ين from a broken plural's own (إِنِ السَّلَاطِين لَظَالِمُونَ) or a single noun's (إِنِ
    الْمِسْكِين). Not a built word's fatha (هُوَ), nor a broken plural's ين with its damma typed (إِنِ الشَّيَاطِينُ)."""
    if facts.is_built(noun):
        return False
    typed = noun.get("typed") or ""
    pair = strip_diacritics(typed).endswith("ين") and bool({FATHA, KASRA} & letters(typed)[-1][1])
    return facts.typed_case_of(noun) == "a" or facts.shows_nasb_by_kasra(noun) or pair


def _clause(start: int, s: facts.Sentence) -> Iterator[int]:
    """The places of the words from `start` to the end of their clause: a ف, or إنّ or a sister of it, opens another.
    A sister of إنّ never stands straight before a verb, so أنْ there is the مصدرية, inside the clause (إِنْ رَجُلٌ
    يُرِيدُ أَنْ يَذْهَبَ جَاءَكَ); one with a pronoun written on it is that sister (لَكِنَّهُ خَرَجَ)."""
    for i, token in enumerate(s.tokens[start:], start):
        after = s.tokens[i + 1:i + 2]
        if token["form"] == "ف+" or is_one(token["lemma"], "inna") and not (after and facts.is_verb(after[0])):
            return
        yield i


def _holds_khabar(verb: dict, word: dict, s: facts.Sentence) -> bool:
    """The word fills the ناسخ's خبر: a noun or a verb the parser hangs on it as its خبر (a جار there may be only
    what comes before the خبر, إِنْ كُنَّا عَنْ عِبَادَتِكُمْ لَغَافِلِينَ), or where each family puts that خبر as
    a word of its own: كاد's present verb (Alfiyya, أفعال المقاربة: ككان كاد وعسى لكن ندر غير مضارع لهذين خبر) and
    ظنّ's second object, a noun neither a ظرف nor a مصدر of the verb's own root (وَإِنْ ظَنَنْتُهُ ظَنًّا لَصَادِقًا).
    Any other word hung on كان is a فضلة of its clause, a حال or a ظرف (وَإِنْ كَانُوا جَمِيعًا لَمُحْضَرِينَ)."""
    if word["head"] != verb["id"]:
        return False
    if word["rel"] == "PRD":
        return facts.noun_tagged(word) or facts.is_verb(word)
    if word["rel"] != "MOD":
        return False
    if in_family(verb["lemma"], "kaada"):
        return facts.is_verb(word)
    return in_family(verb["lemma"], "zanna") and facts.noun_tagged(word) and not (
        facts.is_zarf(word, s) or facts.same_root(word, verb))


def _lam_tells(i: int, s: facts.Sentence, *, khabar_in_nasb: bool) -> bool:
    """The لام at `i` is the differing one: it sits on the خبر itself, never after a و (وَلَقَدْ وَعَدْتُكَ opens another
    sentence): a noun, a جار, or a present verb (Mughni V1 p37), in the case that خبر takes. Where the ناسخ puts it in
    nasb (`khabar_in_nasb`), a noun typed in raf' is not it, nor a detached pronoun of raf' (لَأَنْتَ أَكْرَمُ النَّاسِ),
    since a pronoun in كان's خبر is كُنْتُهُ or كان إيّاه (Alfiyya, النكرة والمعرفة: في كنته الخلف انتمى); nor a جار
    with a مبتدأ of its own, which opens a new nominal clause (وَاللَّهِ إِنْ رَأَيْتَهُ لَفِي ذَلِكَ عِبْرَةٌ); nor a
    present verb whose last letter is still or doubled without a damma, so not in raf': the nun of emphasis, heavy or
    light (لَيَنْدَمَنَّ، لَيَفْعَلَانِّ، لَيَخْرُجَنْ), while a root's own doubled letter in raf' takes a damma (لَيَظُنُّ).
    On that nun it is the لام that answers an oath (وَإِنْ كَانَ ذَلِكَ لَأَضْرِبَنَّهُ: كان complete, no خبر). Of past
    verbs it takes only one that does not conjugate (jazm `frozen_verbs`, Ibn Aqil, page unchecked: إِنْ زَيْدٌ لَنِعْمَ
    الرَّجُلُ) or one behind قد (Alfiyya, إنّ وأخواتها: وقد يليها مع قد كإن ذا لقد سما على العدا مستحوذا), never another
    (ولا من الأفعال ما كرضيا)."""
    tokens = s.tokens
    lam, word = tokens[i], tokens[i + 1]
    if tokens[i - 1]["form"] == "و+":
        return False
    if _past_taking_lam(word):
        return True
    if facts.is_verb(word):
        last = letters(own_letters(word.get("typed") or "", 0, word.get("stuck_on", 0)))
        marks = last[-1][1] if last else set()
        return facts.present_verb_tagged(word) and not (SUKUN in marks or (SHADDA in marks and DAMMA not in marks))
    if facts.is_preposition(word):
        return not any(kid["rel"] == "SBJ" for kid in s.kids(lam))  # the parser hangs that مبتدأ on the لام
    return facts.noun_tagged(word) and not (khabar_in_nasb and (facts.typed_case_of(word) == "u" or is_subject_pronoun(word)))


def _past_taking_lam(word: dict) -> bool:
    """A past verb a لام of emphasis may sit on: one that does not conjugate (jazm `frozen_verbs`) other than ليس, a
    negation (Alfiyya, إنّ وأخواتها: ولا يلي ذي اللام ما قد نفيا), or قد before one (ghair_amila_other `before_past`)."""
    lemma = word["lemma"]
    return is_one(lemma, "jazm", "frozen_verbs") and not is_one(lemma, "negation") \
        or book_spelling(lemma) in book_map("ghair_amila_other", "before_past")


def _answers_oath(verb: dict, i: int, s: facts.Sentence) -> bool:
    """The لام at `i`, on قد or a frozen verb, answers the oath the sentence opens with, the condition before it whole
    (Alfiyya, الجوازم: واحذف لدى اجتماع شرط وقسم جواب ما أخرت): a جار or ظرف after the ناسخ `verb` may be its خبر
    (وَاللَّهِ إِنْ كَانَ زَيْدٌ فِي الدَّارِ لَقَدْ ظَلَمْنَاهُ). With nothing there the لام's word is that خبر, and the إنْ the
    lightened one (وَاللَّهِ إِنْ كُنْتَ لَنِعْمَ الصَّاحِبُ)."""
    tokens = s.tokens
    return facts.sworn_by(s) is not None and _past_taking_lam(tokens[i + 1]) and any(
        _jar_or_zarf(t, s) for t in tokens[tokens.index(verb) + 1:i])


def _merged_in_la(token: dict, s: facts.Sentence) -> str:
    """إلّا before a verb in jazm is إنْ merged into لا (إِلَّا تَنْصُرُوهُ), its hamza written below for the kasra of إنْ.
    Written without that hamza (الا تعبدوا) the word may as well be أَلَّا, أنْ merged into لا, whose verb loses its nun
    for nasb as the jussive does for jazm: only the reader's spelling tells the two apart."""
    return "yes" if _what_follows(token, s) == "verb_jazm" and "إ" in (token.get("typed") or token["form"]) else "no"


def _one_clause_restricted(token: dict, s: facts.Sentence) -> str:
    """An إلا of restriction comes after it with no second verb between (إِنْ أَرَدْنَا إِلَّا الْحُسْنَى، إِنْ نَحْنُ إِلَّا
    بَشَرٌ): one clause, negated and restricted, so the إنْ is the negation (Mughni, إنْ النافية; page unchecked). A
    condition needs a clause and its answer, so a second verb before the إلا is that answer (إِنْ جَاءَ زَيْدٌ لَمْ يَبْقَ
    إِلَّا عَمْرٌو)."""
    rest = [t for t in s.tokens if t["id"] > token["id"] and not facts.is_suffix(t)]
    until = next((at for at, t in enumerate(rest) if is_one(t["lemma"], "hasr")), None)
    return "yes" if until is not None and sum(map(facts.is_verb, rest[:until])) <= 1 else "no"


def _starts(token: dict, s: facts.Sentence) -> str:
    """It opens its clause: nothing before it, or a و or ف written onto it (data: nasb_mudari
    `idhan_after`), as in فَإِذًا after the sentence it answers; زيدٌ إذن يَنجحُ is not."""
    before = next((t for t in reversed(s.tokens) if t["id"] < token["id"]), None)
    return "yes" if before is None or (
        facts.is_prefix(before) and before["form"].strip("+") in book_words("nasb_mudari", "idhan_after")) else "no"


def _verb_after(token: dict, s: facts.Sentence) -> dict | None:
    """The verb that follows it directly, a negating لا or an oath (و and the noun sworn by)
    allowed between (data: nasb_mudari `idhan_between`, `idhan_oath`)."""
    rest = [t for t in s.tokens if t["id"] > token["id"] and not facts.is_suffix(t)]
    at = 0
    while at < len(rest):
        word = rest[at]
        if facts.is_verb(word):
            return word
        if is_one(word["lemma"], "nasb_mudari", "idhan_between") and word["pos"] == "PRT":
            at += 1
        elif is_one(word["lemma"], "nasb_mudari", "idhan_oath") and at + 1 < len(rest) \
                and facts.typed_case_of(rest[at + 1]) == "i":
            at += 2
        else:
            return None
    return None


def _is_present(verb: dict) -> bool:
    """A present verb by the parser, or by its shape when the parser took it for a past one
    (أُكْرِمَكَ): a present prefix with a damma, or followed by a letter at rest (أَذْهَبَ)."""
    if verb.get("asp") == "i":
        return True
    marked = letters(verb.get("typed") or "")
    return verb["base"][:1] in PRESENT_PREFIX and len(marked) > 2 and (
        "ُ" in marked[0][1] or SUKUN in marked[1][1])


def _shows(token: dict, s: facts.Sentence) -> str:
    """The mood the present verb after it shows: nasb (a fatha, or the nun of the five verbs
    dropped), raf' (a damma, or the nun kept), else other; none where no such verb follows."""
    verb = _verb_after(token, s)
    if verb is None or not _is_present(verb):
        return "none"
    nun = five_verb_nun(verb.get("typed") or "", verb.get("stuck_on", 0), verb.get("weak_last"))
    shown = typed_case(verb.get("typed") or "", verb.get("stuck_on", 0))
    return "nasb" if nun == "dropped" or shown == "a" else "raf" if nun == "kept" or shown == "u" else "other"


def _again(token: dict, s: facts.Sentence) -> str:
    """The same small word stood earlier in the sentence: a pair of tools splits its work
    between its two halves (إمّا أن تذهب وإمّا أن تبقى: the first إمّا only sets out the
    choice, the second joins, Tasheel 3.10.2 p91), so the second reads apart from the first."""
    word = _lemma(token)
    return "yes" if any(t["id"] < token["id"] and _lemma(t) == word for t in s.tokens) else "no"


def _paired(token: dict, s: facts.Sentence) -> str:
    """The same small word stands later in the sentence: إمّا with a second إمّا after it sets out a choice
    (إِمَّا يُعَذِّبُهُمْ وَإِمَّا يَتُوبُ عَلَيْهِمْ); alone before a verb it is إنْ with ما merged into it (فَإِمَّا يَأْتِيَنَّكُمْ)."""
    word = _lemma(token)
    return "yes" if any(t["id"] > token["id"] and _lemma(t) == word for t in s.tokens) else "no"


def _doubled(token: dict, s: facts.Sentence) -> str:
    """The reader typed a shadda on it: إِنَّا is إنّ, never the إنْ of a condition."""
    return "yes" if SHADDA in (token.get("typed") or "") else "no"


AXES: dict[str, tuple[tuple[str, ...], Callable[[dict, facts.Sentence], str]]] = {
    "doubled": (("yes", "no"), _doubled),
    "again": (("yes", "no"), _again),
    "paired": (("yes", "no"), _paired),
    "next": (("verb_jazm", "verb", "indefinite_noun", "noun", "tool", "none"), _what_follows),
    "negated": (("yes", "no"), _negated),
    "joins": (("yes", "no"), _joins),
    "opens": (("yes", "no"), _opens),
    "raf": (("yes", "no"), _raf),
    "tool_next": (("yes", "no"), _tool_next),
    "timed": (("yes", "no"), _timed),
    "answered": (("yes", "no"), _answered),
    "told": (("noun", "other"), _told),
    "fronted": (("yes", "no"), _fronted),
    "wonder": (("yes", "no"), _wonder),
    "asks": (("yes", "no"), _asks),
    "restricted": (("yes", "no"), _restricted),
    "one_clause_restricted": (("yes", "no"), _one_clause_restricted),
    "negates_a_verb": (("yes", "no"), _negates_a_verb),
    "differing_lam": (("yes", "no"), _differing_lam),
    "before_noun": (("idle", "working", "condition", "negation", "other"), _before_noun),
    "merged_in_la": (("yes", "no"), _merged_in_la),
    "starts": (("yes", "no"), _starts),
    "shows": (("nasb", "raf", "other", "none"), _shows),
}


@lru_cache(maxsize=1)
def _tree() -> dict:
    tree = book_file("particle_tree.json")["tree"]
    words = tuple(child["is"] for child in tree["children"]) + ("other",)
    walker.validate(tree, {"word": (words, _word), **AXES}, book_file("closed_words.json")["families"])
    return tree


@lru_cache(maxsize=1)
def _words() -> frozenset[str]:
    return frozenset(child["is"] for child in _tree()["children"])


@lru_cache(maxsize=None)
def _judged(word: str) -> frozenset[str]:
    """The families the tree decides for this word: every role at a leaf of its branch."""
    def roles(node: dict) -> set[str]:
        return {node["role"]} if "role" in node else set().union(*map(roles, node.get("children", [])))
    return frozenset(roles(next(c for c in _tree()["children"] if c["is"] == word)))


def _merged(tokens: list[dict], s: facts.Sentence) -> None:
    """أَلَّا (shadda on the lam) is أنْ with its nun merged into لا (data: nasb_mudari `merges`):
    the word is the nasb particle, and the لا the parser split off it a plain negation.
    Only before a present verb (أنّ + لا before a noun is not this)."""
    for word, merged in book_map("nasb_mudari", "merges").items():
        for token, tail in zip(tokens, tokens[1:]):
            if strip_diacritics(token["lemma"]) == word and SHADDA in (token.get("typed") or "") and facts.is_suffix(tail) \
                    and (after := facts.next_word(tail, s)) and facts.is_verb(after) and after.get("asp") == "i":
                token["reading"] = {"family": "nasb_mudari", "named": merged["named"], "kind": "harf", "book": None}
                tail["reading"] = {"family": merged["tail"], "named": None, "kind": "harf", "book": None}


def _emphasis_lam(tokens: list[dict], s: facts.Sentence) -> None:
    """لَيَقُولَنَّ، لَلْحُسْنَى، لَآيَاتٍ: the لام of emphasis (facts.is_emphasis_lam) is read so."""
    named = dict(family_cards())["ghair_amila_other"]["named_as"]
    for i, token in enumerate(tokens):
        if facts.is_emphasis_lam(tokens, i):
            token["reading"] = {"family": "ghair_amila_other", "named": named["ل"], "kind": "harf", "book": None}


def _qad_names_its_sense(tokens: list[dict], s: facts.Sentence) -> None:
    """فَقَدِ اسْتَكْمَلَ: قَدْ before a past verb is the particle of تحقيق (data: ghair_amila_other
    `before_past`). Before a present verb it is تقليل or توقع by the meaning, so it keeps its plain name."""
    named = book_map("ghair_amila_other", "before_past")
    for token in tokens:
        if (name := named.get(book_spelling(token["lemma"]))) and facts.reading(token) in (None, "ghair_amila_other")                 and (after := facts.next_word(token, s)) and facts.is_verb(after) and after.get("asp") == "p":
            token["reading"] = {"family": "ghair_amila_other", "named": name, "kind": "harf", "book": None}


def _amma_names_its_fa(tokens: list[dict], s: facts.Sentence) -> None:
    """فَأَمَّا الْيَتِيمَ فَلَا تَقْهَرْ: أمّا, its mim doubled, and the first فاء after the word it sets out, which ties its
    answer (data: ghair_amila_other `detail_named`). أَمَا with its mim light opens speech and asks no فاء."""
    named = book_map("ghair_amila_other", "detail_named")
    for amma in tokens:
        if not (is_one(amma["lemma"], "ghair_amila_other", "detail") and SHADDA in (amma.get("typed") or "")):
            continue
        if fa := next((t for t in tokens if t["id"] > amma["id"] and t["form"] == "ف+"), None):
            amma["reading"] = {"family": "ghair_amila_other", "named": named["أما"], "kind": "harf", "book": None}
            fa["reading"] = {"family": "ghair_amila_other", "named": named["ف"], "kind": "harf", "book": None}


def emphasis_lam_frees_its_word(s: facts.Sentence) -> None:
    """إِنَّ هَذَا لَسِحْرٌ، إِنَّ اللَّهَ لَغَفُورٌ: the لام of emphasis (_emphasis_lam) governs nothing, so
    a place the parser gave it (here خبر إنّ) is the place of the word it is written onto, and the لام
    hangs on that word, as in إِنَّ زَيْدًا لَجَالِسٌ."""
    tokens = s.tokens
    for lam, word in zip(tokens, tokens[1:]):
        if facts.reading(lam) != "ghair_amila_other" or lam["form"] != "ل+" \
                or lam["head"] in (0, word["id"]):
            continue  # لَزَيْدٌ قَائِمٌ: a لام the sentence rests on took no other word's place
        if word["head"] == lam["id"]:
            s.relink(word, lam["head"], lam["rel"])
        s.relink(lam, word["id"], "MOD")


def hasr_frees_its_words(s: facts.Sentence) -> None:
    """لا تعبدوا إلا الله: the إلا of restriction excepts nothing, so the word the parser hung on
    it belongs to the verb above it, as in ما ضربتُ إلا زيدًا (Tasheel 3.8.7 p85). It takes the place
    the verb leaves open, so one in raf' under a verb with no doer yet is that doer whatever the
    parser hung it as (ما أنقذ الغريقَ إلا فتًى جريءٌ: فتى shows its raf' on its نعت). A كان sister takes no object:
    its word is one of its own two, as _kana_place reads it."""
    tokens = s.tokens
    for particle in tokens:
        verb = s.head(particle)
        if facts.reading(particle) == "hasr" and verb and facts.is_verb(verb):
            open_doer = not facts.own_doer(verb) and not facts.holds_doer(verb, s.kids(verb))
            for kid in s.kids(particle):
                s.relink(kid, verb["id"], kid["rel"])
                if kid["rel"] != "OBJ":
                    continue
                if in_family(verb["lemma"], "kana"):
                    _kana_place(verb, kid, s)
                elif open_doer and _typed_raf(kid, s):
                    s.relabel(kid, "SBJ")


def _kana_place(verb: dict, word: dict, s: facts.Sentence) -> None:
    """كان raises its اسم and puts its خبر in nasb (Tasheel 1.9), so the word its restricting إلا hands it is its
    خبر (إِنْ كَانَتْ إِلَّا صَيْحَةً وَاحِدَةً), unless the reader typed it in raf': then it is the اسم, and a noun the
    parser made the اسم is the خبر put before it (وَمَا كَانَ جَوَابَهُمْ إِلَّا قَوْلُهُمْ). A verb that holds its خبر already
    has its two words (وَلَا يَزَالُونَ مُخْتَلِفِينَ إِلَّا مَنْ رَحِمَ رَبُّكَ): the word after إلا is no خبر of it."""
    if any(k["rel"] == "PRD" for k in s.kids(verb)):
        return
    ism = next((k for k in s.kids(verb) if k["rel"] == "SBJ"), None)
    if _typed_raf(word, s):
        if ism:
            s.relabel(ism, "PRD")
        s.relabel(word, "SBJ")
    else:
        s.relabel(word, "PRD")


def _typed_raf(word: dict, s: facts.Sentence) -> bool:
    """The reader typed the word in raf', or, its case unseen (فتى), typed its نعت so: a نعت wears its noun's case."""
    if facts.case_unseen(word):
        return any(k["rel"] == "MOD" and facts.describes(k, word) and facts.typed_case_of(k) == "u" for k in s.kids(word))
    return facts.typed_case_of(word) == "u"


def wonder_settles_its_words(s: facts.Sentence) -> None:
    """ما أجمل السماء: a ما read as the wonder ما is the مبتدأ, the verb after it a built past verb
    (its hidden doer goes back to ما) and its clause the khabar, the noun its object. The parser
    tags and hangs these differently from one sentence to the next, so they are written over."""
    tokens = s.tokens
    for ma in tokens:
        if facts.reading(ma) != "wonder" or not (parts := _wonder_parts(ma, s)):
            continue
        verb, noun = parts
        ma.update(pos="NOM", pos_camel="pron_rel")
        verb.update(pos="VRB", pos_camel="verb", asp="p", vox="a", per="3", gen="m", num="s",
                    reading={"family": "wonder", "named": None, "kind": "fil", "book": ma["reading"]["book"]})
        three = {ma["id"], verb["id"], noun["id"]}
        outer = next((t for t in (verb, ma, noun) if t["head"] not in three), None)
        s.relink(ma, *((outer["head"], outer["rel"]) if outer else (0, "---")))
        s.relink(verb, ma["id"], "---")
        s.relink(noun, verb["id"], "OBJ")
        if specified := _after_object(noun, s):
            s.relink(specified, verb["id"], "TMZ")  # ما أجملها ليلةً


def asks_settles_its_words(s: facts.Sentence) -> None:
    """ما اسمك، وما أدراك: a ما or من read as the question word is a built noun. With a clause
    of its own after it (the verb of informing) it is that verb's مبتدأ; otherwise it is the
    khabar brought to the front and the noun after it its مبتدأ, hung on it. Standing after a verb,
    its clause is that verb's (قال ما اسمك). Hung on a preposition (لِمَنْ هذا الكتابُ) it is that
    preposition's majrur, and the جار ومجرور is the fronted khabar the noun hangs on. The parser
    tags and hangs these differently from one sentence to the next, so they are written over."""
    tokens = s.tokens
    def before(token: dict) -> dict | None:
        return next((t for t in reversed(tokens) if t["id"] < token["id"] and not facts.is_suffix(t)), None)
    for ma in tokens:
        if facts.reading(ma) != "istifham":
            continue
        ma.update(pos="NOM", pos_camel="pron_interrog")
        jar = s.head(ma) if ma["rel"] == "OBJ" else None
        if not (jar and facts.is_preposition(jar)) and (verb := _informing(ma, s)):
            s.relink(ma, verb["id"], "SBJ")
            s.relink(verb, 0, "---")
            continue
        top = jar if jar and facts.is_preposition(jar) else ma
        if (noun := facts.next_word(ma, s)) and not facts.is_verb(noun):
            s.relink(noun, top["id"], "SBJ")
        verb = before(top)
        s.relink(top, *((verb["id"], "---") if verb and facts.is_verb(verb) else (0, "---")))


def idhan_settles_its_words(s: facts.Sentence) -> None:
    """إِذَنْ أُكْرِمَكَ: an إذن read as the particle stands over its verb, as لن does, and the verb
    is the present one it works on. The parser took it for a noun with a past verb under it,
    so both are written over."""
    tokens = s.tokens
    for idhan in tokens:
        if not idhan.get("reading") or _word(idhan, s) != "إذن" or not (verb := _verb_after(idhan, s)):
            continue
        if verb["head"] == idhan["id"]:
            s.relink(verb, idhan["head"], idhan["rel"])
        s.relink(idhan, verb["id"], "MOD")
        verb["asp"] = "i"


def negation_settles_its_words(s: facts.Sentence) -> None:
    """وَمَا قَلَىٰ: a negation is said of the verb after it and hangs on it as its modifier (مَا نَجَحَ زَيْدٌ). The
    parser may hang the verb under the particle, which then stands where the verb stands, as the object of the و
    before it (Tasheel 1.7 p18: only a noun is a حرف جر's majrur); the two are swapped."""
    tokens = s.tokens
    for ma in tokens:
        if facts.reading(ma) != "negation":
            continue
        verb = next((k for k in s.kids(ma) if k["id"] > ma["id"] and facts.is_verb(k)), None)  # by whatever relation it hangs
        if not verb or s.under(ma["head"], verb["id"]):
            continue
        for kid in s.kids(ma):
            s.relink(kid, verb["id"], kid["rel"])
        s.relink(verb, ma["head"], ma["rel"])  # the verb takes the place the negation stood in
        s.relink(ma, verb["id"], "MOD")


@lru_cache(maxsize=1)
def _retagged() -> frozenset[str]:
    """The words with a leaf that writes a new word class over the parser's (data: `retag`)."""
    def leaves(node: dict) -> list[dict]:
        return [node] if "role" in node else [leaf for child in node.get("children", []) for leaf in leaves(child)]
    return frozenset(child["is"] for child in _tree()["children"] if any("retag" in leaf for leaf in leaves(child)))


def _read(token: dict, found: walker.Walked) -> None:
    retag = found.leaf.get("retag", {})
    token["reading"] = {"family": found.role, "named": found.leaf.get("named"), "kind": found.leaf.get("kind", "harf"),
                        "book": found.book, "sense": found.leaf.get("sense", retag.get("pos_camel")),
                        "spells": found.leaf.get("spells")}
    token.update(retag)


def negates(token: dict) -> None:
    """Read a لا the tree took for the prohibition as the negation before a verb, whatever the verb after it
    shows: its leaf's reading, when what stands round it (syntax.condition) shows it asks for nothing."""
    _read(token, walker.walk({"word": "لا", "next": "verb"}, _tree()))


def stamp(s: facts.Sentence) -> None:
    """Stamp each listed word's reading on its token: {family, named, kind, book, sense}, and the
    families the tree judges for it as `judged`. A word no leaf took (a و that opens no
    sentence) is read by its other lists as before, never as one of those families."""
    tokens = s.tokens
    # a word class written over first (ما قبل إلا is a particle) is seen by the words read after it
    for token in sorted(tokens, key=lambda t: _word(t, s) not in _retagged()):
        token.pop("reading", None)
        token.pop("judged", None)
        if (word := _word(token, s)) == "other":
            continue
        token["judged"] = _judged(word)
        if word != book_spelling(token["lemma"]):
            token["lemma"] = word  # إِذًا is إذن, to every list
        values = {"word": word, **{axis: answer(token, s) for axis, (_, answer) in AXES.items()}}
        if found := walker.walk(values, _tree()):
            _read(token, found)
    _merged(tokens, s)
    _emphasis_lam(tokens, s)
    _qad_names_its_sense(tokens, s)
    _amma_names_its_fa(tokens, s)
