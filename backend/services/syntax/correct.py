"""One step that corrects the parser: every change to a word's kind, tense, head and link.

The parser's tokens are rewritten here, in one fixed order, and nowhere after: the typed
vowels are read into them (`typed`, `stuck_on`, `front`), the book's links are written over
the parser's, then the words' kinds and tenses, the clashing modifiers and the listed
particles. `naming` and everything after only read. Each change is kept as
{id, field, was, now, rule}.
"""
from __future__ import annotations

from backend.services import verb_reader
from backend.services.arabic_text import bare_letters
from backend.services.harakat import (
    has_tanween, letters, merged_prefix, own_letters, paused, typed_case, vowel_agreement)
from backend.services.nahw_book import book_words, is_one, only_adverb
from backend.services.syntax import facts, particles
from backend.services.syntax.mask import book_links
from backend.services.syntax.naming import base_tokens

FIELDS = ("pos", "asp", "head", "rel")


def _typed_words(words: list[str], bases: list[dict], tokens: list[dict]) -> None:
    """What the reader typed, read into each base word: its vowels, and its kind and tense where
    the vowels or the book's lists say otherwise."""
    for i, (word, token) in enumerate(zip(words, bases)):
        token["typed"] = word
        # a "verb" with no tense that CAMeL reads as a noun or an adjective is that noun
        # (اللهُ أكبرُ: the elative, never the verb أَكْبَرَ)
        if token["pos"].startswith("VRB") and token.get("asp") == "na" and token.get("pos_camel") in ("adj", "noun"):
            token["pos"] = "NOM"
        # وَإِذْ قَالَ، مَعَ الصَّابِرِينَ: a word the book lists only as a ظرف is a noun, whatever the tag
        if token["pos"] == "PRT" and only_adverb(token["lemma"]):
            token["pos"] = "NOM"
        # letters at the end that belong to an attached pronoun, not to the word
        token["stuck_on"] = sum(len(bare_letters(t["form"].strip("+"))) for t in tokens
                                if t["head"] == token["id"] and t["form"].startswith("+"))
        # and letters at the front that are joined words (وَ، فَ، لِـ), not the word's own
        token["front"] = max(0, len(letters(word)) - token["stuck_on"] - len(token["base"]))
        # نِعْمَ الْوَكِيلُ، وَلَبِئْسَ الْمِهَادُ: a verb of praise or blame typed as the past verb it is
        # (its fatha), whatever the reading (the noun نِعْمَة، the "yes" نَعَمْ)
        if is_one(token["lemma"], "praise_blame") and typed_case(word, token["stuck_on"]) == "a" and not has_tanween(word):
            token.update(pos="VRB", asp="p")
        # اُكْتُبْ، أَكْرِمْ: the typed command is the tense, whatever reading the parser had;
        # a verb's reading (فَاقْبَلْهَا) is also tried on its own letters, the ف and ها aside;
        # a noun's never is, or the يَدِ of وَيَدِهِ would be a command; a name the list could
        # only guess (فَادْفَعُوا) is no noun the reader knew, so its own letters are tried too.
        # A noun the dictionary read with the vowels typed stays that noun unless the command
        # is typed in full too (سَمِّ): ابْنُ is no اُبْنُ, nor بَنِي a بَنِّي, with a mark left off
        after = words[i + 1] if i + 1 < len(words) else ""
        verb = token["pos"].startswith("VRB")
        read_noun = token.get("pos_camel") == "noun" and vowel_agreement(word, token.get("diac", "")) is not None
        if verb or token.get("pos_camel") in ("noun", "noun_prop"):
            governed = i > 0 and any(is_one(bases[i - 1]["base"], family, "before_a_present_verb")
                                     for family in ("jazm", "nasb_mudari"))
            root = token.get("root", "")
            own = own_letters(word, token["front"], token["stuck_on"]) if verb or token.get("pos_camel") == "noun_prop" else word
            cell = next((found for form in dict.fromkeys((word, paused(word, after), own))
                         if (found := verb_reader.command(form, governed, root))
                         and (not read_noun or verb_reader.typed_fully(form, found))), None)
            if cell:
                # the person is sarf's: the reading may have taken اقبل for "I accept"
                token.update(asp="c", per=cell.person, gen=cell.gender, num=cell.number)
            elif verb and merged_prefix(own, book_words("ta_merges")):
                # تَطَّوَّعَ: the shadda is the second ta' merged in, so it is present whatever the reading said
                token["asp"] = "i"
        token["mudaf"] = any(t["head"] == token["id"] and t["rel"] == "IDF" for t in tokens)


def correct(words: list[str], tokens: list[dict]) -> tuple[list[dict], list[dict]]:
    """The parser's tokens with every correction made, and each change as {id, field, was, now, rule}.
    A split that does not line up with the typed words is left as the parser drew it."""
    bases = base_tokens(words, tokens)
    changes: list[dict] = []
    for rule, run in (("book_links", lambda: book_links(tokens)),
                      ("typed_words", lambda: _typed_words(words, bases, tokens)),
                      ("free_clashing_modifiers", lambda: facts.free_clashing_modifiers(tokens)),
                      ("particles", lambda: particles.stamp(tokens))):
        if len(bases) != len(words) and rule != "book_links":
            continue
        was = [{field: t.get(field) for field in FIELDS} for t in tokens]
        run()
        changes += [{"id": t["id"], "field": f, "was": w[f], "now": t.get(f), "rule": rule}
                    for t, w in zip(tokens, was) for f in FIELDS if t.get(f) != w[f]]
    return tokens, changes
