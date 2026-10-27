"""Repair 1 after the book's links: what the reader typed overrides the parser's kind and tense."""
from __future__ import annotations

from itertools import pairwise

from backend.services.sarf import verb_reader
from backend.services.text.harakat import has_tanween, letters, merged_prefix, own_letters, paused, plural_alef, stuck_letters, typed_case, vowel_agreement
from backend.services.nahw.book import book_words, is_built_word, is_one, only_adverb
from backend.services.nahw.syntax.mask import above
from backend.services.nahw.syntax.facts import Sentence, has_added, is_elative, is_emphasis_lam, is_name, noun_tagged, puts_in_jarr, typed_case_of, typed_or_parsed_case, typed_tanween, verb_tagged


def typed_words(words: list[str], bases: list[dict], tokens: list[dict]) -> None:
    """Reads what was typed into each base word: its vowels, and its kind and tense where they or the book say otherwise."""
    for i, (word, token) in enumerate(zip(words, bases)):
        token["typed"] = word
        # a tenseless "verb" CAMeL reads as a noun or adjective is that noun (اللهُ أكبرُ); a word the book lists only as a ظرف is a noun
        if ((verb_tagged(token) and token.get("asp") == "na" and token.get("pos_camel") in ("adj", "noun"))
                or (token["pos"] == "PRT" and only_adverb(token["lemma"]))):
            token["pos"] = "NOM"
        # مُنْذُ أَمْسِ: the letters of a time word built on one ending are that word, never the command they spell
        built = is_built_word(token["base"])
        if built and verb_tagged(token):
            token.update(pos="NOM", pos_camel="noun", lemma=token["base"], asp="na")
        # مَعَ النَّاسِ: the noun the parser hung on a ظرف as a preposition's is its مضاف إليه
        if token["pos"] == "NOM" and token.get("pos_camel") == "prep" and only_adverb(token["lemma"]):
            for kid in tokens:
                if kid["head"] == token["id"] and kid["rel"] == "OBJ":
                    kid["rel"] = "IDF"
        # مُلَبِّينَ: no verb opens with مُ and ends in the plural ـونَ/ـينَ, so it is a participle, its case by
        # its place; so is one sarf read off its shape, whose ـينَ is nasb or jarr alike (noun_reader)
        elif (verb_tagged(token) or token.get("cas") == "u") and _participle_plural(word):
            token.update(pos="NOM", pos_camel="adj", asp="na", cas=_plural_case(word, token, tokens))
        # letters at the end that belong to an attached pronoun, then at the front that are joined words (وَ، فَ، لِـ)
        token["stuck_on"] = stuck_letters(t for t in tokens if t["head"] == token["id"])
        token["front"] = max(0, len(letters(word)) - token["stuck_on"] - len(token["base"]))
        # نِعْمَ الْوَكِيلُ: a verb of praise or blame typed with its fatha is that past verb, whatever the reading
        if is_one(token["lemma"], "praise_blame") and typed_case(word, token["stuck_on"]) == "a" and not has_tanween(word):
            token.update(pos="VRB", asp="p")
        # اُكْتُبْ، أَكْرِمْ: the typed command is the tense, whatever the reading. A verb is also tried on its own
        # letters (فَاقْبَلْهَا); a noun never, or the يَدِ of وَيَدِهِ would be a command, except a name the list only
        # guessed (فَادْفَعُوا). A noun read with the vowels typed stays that noun unless the command is typed in full (سَمِّ),
        # and so does a past verb (جَاءُوا is the dictionary's past, never a command spelled جَاِئُوا it left a mark off)
        after = words[i + 1] if i + 1 < len(words) else ""
        verb = verb_tagged(token)
        agrees = vowel_agreement(word, token.get("diac", "")) is not None
        read_noun = token.get("pos_camel") == "noun" and agrees
        read_past = verb and token.get("asp") == "p" and agrees
        # a noun read with a sign of the noun on it is that noun, never a command (Ibn Aqil V1 p15: بالجر والتنوين
        # والندا وأل): its own pronoun stuck on, not hung as an object (عَمِّي، جَدِّي), called (يَا رَبِّ), or with its يا left off,
        # opening the sentence before the command said to it (رَبِّ اغْفِرْ لِي; V3 p256), in jarr as a مضاف إليه or as the
        # صفة of a noun in jarr (لِلَّهِ رَبِّ الْعَالَمِينَ), as no sentence of asking describes (V3 p198: وامنع هنا إيقاع ذات الطلب)
        head = next((t for t in tokens if t["id"] == token["head"]), None)
        noun = read_noun and (any(t["head"] == token["id"] and t.get("token_type") == "enc0" and t["rel"] != "OBJ" for t in tokens)
                              or i > 0 and is_one(bases[i - 1]["base"], "nida") or i == 0 and verb_reader.command(after) is not None
                              or token["rel"] == "IDF" or token["rel"] == "MOD" and head is not None and typed_or_parsed_case(head) == "i")
        if (verb or token.get("pos_camel") in ("noun", "noun_prop")) and not built and not noun:
            governed = i > 0 and any(is_one(bases[i - 1]["base"], family, "before_a_present_verb")
                                     for family in ("jazm", "nasb_mudari"))
            # with no vowel typed, the sentence vouches for a verb: the dictionary has no reading at all
            # (اكتبي: it lists no command to a woman), or the parser hung an object on what it read as an
            # elative, which takes none (Ashmuni V2 p312: لا ينصب المفعول به): ارفعي صوتك
            vouched = token.get("guessed") or (is_elative(token) and any(
                t["head"] == token["id"] and t["rel"] == "OBJ" for t in tokens))
            own = own_letters(word, token["front"], token["stuck_on"]) if verb or token.get("pos_camel") == "noun_prop" else word
            if token["stuck_on"]:
                own = plural_alef(own)  # اُكْتُبُوهُ is اُكْتُبُوا with its object
            cell = next((found for form in dict.fromkeys((word, paused(word, after), own))
                         if (found := verb_reader.command(form, governed, token.get("root", ""), vouched))
                         and (not (read_noun or read_past) or vouched or verb_reader.typed_fully(form, found))), None)
            if cell:  # the person is sarf's: the reading may have taken اقبل for "I accept"
                token.update(asp="c", per=cell.person, gen=cell.gender, num=cell.number)
                if not verb:  # آتِ ذَا الْقُرْبَى: the noun read (آتٍ, one coming) gives way to the verb, آتَى of two objects
                    token["lemma"] = verb_reader.past(cell)
                # قُومِي: the ي a noun reading split off as "my" is the command's doer, a pronoun only ever
                # in raf' (Awdah V1 p85: ما يختص بمحل الرفع ... وياء المخاطبة كقومي)
                for kid in tokens:
                    if kid["head"] == token["id"] and kid.get("token_type") == "enc0" and kid["form"] == "+ي":
                        kid["rel"] = "SBJ"
            elif verb and merged_prefix(own, book_words("ta_merges")):
                token["asp"] = "i"  # تَطَّوَّعَ: the shadda is the second ta' merged in, so it is present
        token["mudaf"] = has_added(token, tokens)



def _participle_plural(word: str) -> bool:
    marked = letters(word)
    return (len(marked) > 4 and marked[0] == ("م", {"ُ"})
            and [l for l, _ in marked[-2:]] in (["ي", "ن"], ["و", "ن"]) and "َ" in marked[-1][1])


def _plural_case(word: str, token: dict, tokens: list[dict]) -> str:
    """ـونَ is raf'; ـينَ is jarr under a preposition or مضاف, nasb under a verb, and under a
    noun that noun's صفة, in its case (بِرِجَالٍ مُسَافِرِينَ)."""
    if letters(word)[-2][0] == "و":
        return "n"
    head = next((t for t in tokens if t["id"] == token["head"]), None)
    if token["rel"] == "IDF" or (head and head["pos"] == "PRT" and head.get("pos_camel") == "prep"):
        return "g"
    if head and verb_tagged(head):
        return "a"
    return head.get("cas", "na") if head else "na"


def since_jarr(tokens: list[dict]) -> None:
    """مُنْذُ أَمْسِ: a built time word that is also on the book's list of prepositions (منذ، مذ) is a
    preposition before a noun, the noun its majrur; the parser can read it as a conjunction.
    Before a verb it stays what it read."""
    for since, noun in zip(tokens, tokens[1:]):
        if is_built_word(since["lemma"]) and is_one(since["lemma"], "jarr") and noun["pos"] == "NOM":
            since.update(pos="PRT", pos_camel="prep")
            noun["head"], noun["rel"] = since["id"], "OBJ"


def jarr_after_mudaf(tokens: list[dict]) -> None:
    """زَيْدٌ أَكْرَمُ رِجَالٍ: a noun typed in jarr with no جار is a مضاف إليه (Alfiyya: وَالثَّانِيَ اجْرُرْ),
    and the مضاف drops its tanween (نُونًا تَلِي الْإِعْرَابَ أَوْ تَنْوِينًا مِمَّا تُضِيفُ احْذِفْ), so a word the
    parser hung elsewhere, straight after a noun typed with its case but no tanween, is that noun's
    مضاف إليه. A word known already (ال or a name: بِسْمِ اللَّهِ الرَّحْمَنِ) is added to nothing, and a fatha
    on a word put in jarr is a diptote's, which never takes tanween (مَرَرْتُ بِمَسَاجِدَ كَثِيرَةٍ: its صفة).
    A مضاف the parser hung under that word takes the word's place first, so the link closes no loop."""
    s = Sentence(tokens)
    for before, word in pairwise(tokens):
        if (typed_case_of(word) == "i" and noun_tagged(word)
                and noun_tagged(before) and before.get("stt") != "d" and not is_name(before)
                and typed_case_of(before) is not None and not typed_tanween(before)
                and not (typed_case_of(before) == "a" and puts_in_jarr(before, s))):
            if above([t["head"] for t in tokens], before["id"], word["id"]):
                before["head"], before["rel"] = word["head"], word["rel"]
            word["head"], word["rel"] = before["id"], "IDF"
            before["mudaf"] = True


def emphasis_lam_opener(tokens: list[dict]) -> None:
    """لَزَيْدٌ قَائِمٌ، وَلَلْآخِرَةُ خَيْرٌ لَكَ: the لام of emphasis (facts.is_emphasis_lam) governs nothing,
    so a noun the parser hung on it as a جار's majrur is in that لام's place: it hangs where the لام hung,
    what hung on the لام hangs on it, and the لام on it (لام الابتداء). That لام has the head of the
    sentence, so its word's khabar never comes before it (Ibn Aqil V1 p236: لام الابتداء لها صدر الكلام،
    فلا تقول قائم لزيد), and it comes onto no فاعل: the word hung on a word after it, as its صفة or
    its doer (لَأَنْتُمْ أَشَدُّ رَهْبَةً، لَزَيْدٌ يَقُومُ، عَلِمْتُ لَزَيْدٌ قَائِمٌ), is its مبتدأ."""
    by_id = {t["id"]: t for t in tokens}
    for i, (lam, word) in enumerate(pairwise(tokens)):
        if not (word["head"] == lam["id"] and noun_tagged(word) and is_emphasis_lam(tokens, i)):
            continue
        for kid in tokens:
            if kid["head"] == lam["id"]:
                kid["head"] = word["id"]
        word["head"], word["rel"] = lam["head"], lam["rel"]
        lam["head"], lam["rel"] = word["id"], "MOD"
        told = by_id.get(word["head"])
        if told and told["id"] > word["id"]:
            word["rel"] = "SBJ"
