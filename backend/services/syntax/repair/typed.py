"""Repair 1 after the book's links: what the reader typed overrides the parser's kind and tense."""
from __future__ import annotations

from backend.services import verb_reader
from backend.services.harakat import has_tanween, letters, merged_prefix, own_letters, paused, stuck_letters, typed_case, vowel_agreement
from backend.services.nahw_book import book_words, is_one, only_adverb


def typed_words(words: list[str], bases: list[dict], tokens: list[dict]) -> None:
    """Reads what was typed into each base word: its vowels, and its kind and tense where they or the book say otherwise."""
    for i, (word, token) in enumerate(zip(words, bases)):
        token["typed"] = word
        # a tenseless "verb" CAMeL reads as a noun or adjective is that noun (اللهُ أكبرُ); a word the book lists only as a ظرف is a noun
        if ((token["pos"].startswith("VRB") and token.get("asp") == "na" and token.get("pos_camel") in ("adj", "noun"))
                or (token["pos"] == "PRT" and only_adverb(token["lemma"]))):
            token["pos"] = "NOM"
        # مُلَبِّينَ: no verb opens with مُ and ends in the plural ـونَ/ـينَ, so it is a participle
        elif token["pos"].startswith("VRB") and _participle_plural(word):
            token.update(pos="NOM", asp="na", cas=_plural_case(word, token, tokens))
        # letters at the end that belong to an attached pronoun, then at the front that are joined words (وَ، فَ، لِـ)
        token["stuck_on"] = stuck_letters(t for t in tokens if t["head"] == token["id"])
        token["front"] = max(0, len(letters(word)) - token["stuck_on"] - len(token["base"]))
        # نِعْمَ الْوَكِيلُ: a verb of praise or blame typed with its fatha is that past verb, whatever the reading
        if is_one(token["lemma"], "praise_blame") and typed_case(word, token["stuck_on"]) == "a" and not has_tanween(word):
            token.update(pos="VRB", asp="p")
        # اُكْتُبْ، أَكْرِمْ: the typed command is the tense, whatever the reading. A verb is also tried on its own
        # letters (فَاقْبَلْهَا); a noun never, or the يَدِ of وَيَدِهِ would be a command, except a name the list only
        # guessed (فَادْفَعُوا). A noun read with the vowels typed stays that noun unless the command is typed in full (سَمِّ)
        after = words[i + 1] if i + 1 < len(words) else ""
        verb = token["pos"].startswith("VRB")
        read_noun = token.get("pos_camel") == "noun" and vowel_agreement(word, token.get("diac", "")) is not None
        if verb or token.get("pos_camel") in ("noun", "noun_prop"):
            governed = i > 0 and any(is_one(bases[i - 1]["base"], family, "before_a_present_verb")
                                     for family in ("jazm", "nasb_mudari"))
            own = own_letters(word, token["front"], token["stuck_on"]) if verb or token.get("pos_camel") == "noun_prop" else word
            cell = next((found for form in dict.fromkeys((word, paused(word, after), own))
                         if (found := verb_reader.command(form, governed, token.get("root", "")))
                         and (not read_noun or verb_reader.typed_fully(form, found))), None)
            if cell:  # the person is sarf's: the reading may have taken اقبل for "I accept"
                token.update(asp="c", per=cell.person, gen=cell.gender, num=cell.number)
            elif verb and merged_prefix(own, book_words("ta_merges")):
                token["asp"] = "i"  # تَطَّوَّعَ: the shadda is the second ta' merged in, so it is present
        token["mudaf"] = any(t["head"] == token["id"] and t["rel"] == "IDF" for t in tokens)



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
    if head and head["pos"].startswith("VRB"):
        return "a"
    return head.get("cas", "na") if head else "na"
