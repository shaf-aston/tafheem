"""Links the book rules out, as masks over the parser's scores, and the few links it
settles outright, written over the parser's tree.

Pure: takes the words' tags and returns which (dependent, head, relation) labels
are impossible, so the decoder picks the best reading the book allows instead of
the best reading full stop; `book_links` then fixes a structure the book states
whatever the scores say. Which rules are on lives in
data/nahw_rules/closed_words.json ("vetoes"). Index 0 is the root, word i is
index i, as in the score matrices.
"""
from __future__ import annotations

import numpy as np

from backend.services.arabic_text import strip_diacritics
from backend.services.nahw_book import is_one, is_plain_noun, vetoes
from backend.services.harakat import CAMEL_CASE


def _verb_subject_follows(toks, add_rel) -> None:
    """A فاعل never comes before its verb: a noun to the left of a verb is a
    mubtada (the parser's topic), so SBJ is ruled out. A noun typed with fatha
    or tanween-fath stays open: it is a fronted object. OBJ and MOD go
    with it, since an untyped noun before its verb is no object either, so
    what is left is the topic (الطعامَ أكل الولدُ)."""
    for d, dep in enumerate(toks, 1):
        if not is_plain_noun(dep) or dep.get("case") == "a":
            continue
        for h in range(d + 1, len(toks) + 1):
            if toks[h - 1]["pos"].startswith("VRB"):
                for label in ("SBJ", "OBJ", "MOD"):
                    add_rel(d, h, label)


_VETOES = {"verb_subject_follows": _verb_subject_follows}


def book_mask(toks: list[dict], labels: list[str]) -> np.ndarray:
    """rel_ok[L, L, R] for L = words + root; True = the label is allowed."""
    rel_ok = np.ones((len(toks) + 1, len(toks) + 1, len(labels)), dtype=bool)

    def add_rel(d, h, label):
        rel_ok[d, h, labels.index(label)] = False

    for rule in _switched_on(_VETOES):
        rule(toks, add_rel)
    return rel_ok


def _switched_on(rules: dict) -> list:
    """The rules closed_words.json "vetoes" turns on, in the order of the table passed."""
    return [rule for name, rule in rules.items() if vetoes().get(name)]


def _above(heads: list[int], word: int, target: int) -> bool:
    """`target` is `word` or one of the words it hangs under: a link from target down to
    word would close a loop."""
    while word:
        if word == target:
            return True
        word = heads[word - 1]
    return False


def _pointer_heads_its_noun(toks, heads, rels) -> None:
    """هذا الكتابُ: a pointer and the noun with ال after it are one unit, the pointer its
    head: it takes the job the pair has and the noun (the مشار إليه) hangs on it (Tasheel
    1.4.3 p10). The parser often draws it the other way round."""
    for d, dep in enumerate(toks[:-1], 1):
        n = d + 1  # the noun
        noun = toks[n - 1]
        if "dem" not in dep.get("pos_camel", "") or noun.get("stt") != "d" or not is_plain_noun(noun):
            continue
        if heads[n - 1] == d or _above(heads, heads[n - 1], d):
            continue  # already under the pointer, or the swap would make a loop
        # the pointer takes the noun's place in the sentence; the noun hangs on it
        heads[d - 1], rels[d - 1] = heads[n - 1], rels[n - 1]
        heads[n - 1], rels[n - 1] = d, "MOD"


def _listed_preposition_takes_majrur(toks, heads, rels) -> None:
    """رُبَّ رجلٍ، منذُ يومين: a word on the book's list of حروف الجر, with a noun in jarr
    straight after it, is that preposition and the noun its majrur (Tasheel 1.7 p18), though
    the parser may tag it a noun. Its word class is written over too. The noun is the next
    word: a pronoun stuck to the same word (رَبَّكَ) is the word's own. It is indefinite (the
    list's own note on رب): before a noun with ال or a name the word is a مضاف (رَبِّ الْعَالَمِينَ)."""
    for d, dep in enumerate(toks[:-1], 1):
        form = strip_diacritics(dep.get("form", "")).strip("+")
        after = toks[d]
        majrur = (after["pos"] == "NOM" and after.get("stt") == "i" and not after.get("form", "").startswith("+")
                  and "i" in (after.get("case"), CAMEL_CASE.get(after.get("cas"))))
        if dep["pos"] == "PRT" or len(form) < 2 or not is_one(form, "jarr") or not majrur or _above(heads, d, d + 1):
            continue
        dep.update(pos="PRT", pos_camel="prep")
        heads[d], rels[d] = d, "OBJ"


def _topic_carries_its_verb(toks, heads, rels) -> None:
    """الوَلَدُ يَكْتُبُ: a noun before its verb is the mubtada and the verb's clause its
    khabar (Tasheel 1.4.4 p11), so the verb hangs on the noun. The parser, barred from
    making the noun the verb's subject, hangs it under the verb as a bare topic instead.
    A noun in nasb is left: it is a fronted object."""
    for d, dep in enumerate(toks, 1):
        h = heads[d - 1]
        if not (h > d and toks[h - 1]["pos"].startswith("VRB") and rels[d - 1] in ("---", "TPC")
                and is_plain_noun(dep) and _case(dep) not in ("a", "i")):
            continue
        heads[d - 1], rels[d - 1] = heads[h - 1], rels[h - 1]
        heads[h - 1], rels[h - 1] = d, "---"


def _case(tok: dict) -> str | None:
    return tok.get("case") or CAMEL_CASE.get(tok.get("cas"))


def _inner_sentence(toks, heads, rels) -> None:
    """زَيْدٌ أَبُوْهُ عَالِمٌ، جَاءَ الَّذِيْ أَبُوْهُ عَالِمٌ: a noun carrying a pronoun back, then
    an indefinite noun in raf', is a sentence of its own (mubtada and khabar), standing as
    the khabar of the noun before it or as the صلة of a relative (Tasheel 1.4.4 p11). The
    parser draws it three ways; it is written as the khabar hung on that noun (PRD) with
    its mubtada under it (SBJ), as a verb's clause is. Only after the first noun of a
    sentence with no verb, or straight after a relative, so a hal is never caught."""
    verbless = not any(t["pos"].startswith("VRB") for t in toks)
    for n2 in range(2, len(toks) - 1):  # 1-based: noun, its pronoun, the khabar
        noun, pronoun, khabar, before = toks[n2 - 1], toks[n2], toks[n2 + 1], toks[n2 - 2]
        n1, n3 = n2 - 1, n2 + 2
        # the noun's typed case is under its pronoun's vowel, so the reading's case is used
        if not (is_plain_noun(noun) and noun.get("stt") == "c" and CAMEL_CASE.get(noun.get("cas")) not in ("a", "i")
                and pronoun.get("pos_camel") == "pron" and pronoun.get("form", "").startswith("+")
                and khabar["pos"] in ("NOM", "PROP") and khabar.get("stt") == "i" and _case(khabar) == "u"):
            continue
        relative = "rel" in before.get("pos_camel", "")
        first = verbless and n1 == 1 and before["pos"] in ("NOM", "PROP") and not before.get("form", "").startswith("+")
        if relative and (_above(heads, n1, n2) or _above(heads, n1, n3)):
            continue  # the relative hangs inside the sentence: its own place is not known
        if first:
            if any(h == 0 for i, h in enumerate(heads, 1) if i not in (n1, n2, n3)):
                continue  # another word is the sentence's head
            heads[n1 - 1], rels[n1 - 1] = 0, "---"
        elif not relative:
            continue
        heads[n3 - 1], rels[n3 - 1] = n1, "PRD"
        heads[n2 - 1], rels[n2 - 1] = n3, "SBJ"


def _ma_cancels_inna(toks, heads, rels) -> None:
    """إنّما زيدٌ قائمٌ: the ما joined to إنّ or a sister is ما الكافة, a particle that stops
    it working (Tasheel 1.8 n4 p21); the noun after the pair is the mubtada and what is
    told of it the khabar. The parser takes the ما for a noun and makes it the subject, so
    the ما hangs on the particle as a plain modifier and the noun under it takes its place."""
    for m, tok in enumerate(toks, 1):
        particle = heads[m - 1]
        if strip_diacritics(tok.get("form", "")) != "+ما" or not particle or rels[m - 1] != "SBJ" \
                or not is_one(toks[particle - 1]["lemma"].removesuffix("ما"), "inna"):
            continue
        for n, h in enumerate(heads, 1):
            if h == m:
                heads[n - 1], rels[n - 1] = particle, "SBJ"
        rels[m - 1] = "MOD"


def _exception_word_by_case(toks, heads, rels) -> None:
    """جاء القومُ خلا زيدًا، خلا زيدٍ، خلا البيتُ: خلا، عدا، حاشا with a noun straight after read
    by that noun's typed vowel (Tasheel 3.8.7). Nasb: a past verb (its doer hidden) and the noun
    its object. Jarr: a preposition and the noun its majrur. Raf': the ordinary verb and the noun
    its doer. After ما only the verb stands (ما عدا زيدًا). The parser's tags are written over."""
    for d, dep in enumerate(toks[:-1], 1):
        after = toks[d]
        if (dep.get("token_type") != "baseword" or after["pos"] not in ("NOM", "PROP")
                or after.get("form", "").startswith("+") or not is_one(dep.get("form", ""), "istithna_verbs")
                or _above(heads, d, d + 1)):
            continue
        case, verb = _case(after), d > 1 and is_one(strip_diacritics(toks[d - 2].get("form", "")), "istithna_verbs", "masdar_ma")
        if case == "i" and not verb:
            dep.update(pos="PRT", pos_camel="prep")
            heads[d], rels[d] = d, "OBJ"
        elif case in ("a", "u"):
            dep.update(pos="VRB", pos_camel="verb", asp="p", vox="a", per="3", gen="m", num="s")
            heads[d], rels[d] = d, "OBJ" if case == "a" else "SBJ"


_LINKS = {"pointer_heads_its_noun": _pointer_heads_its_noun,
          "ma_cancels_inna": _ma_cancels_inna,
          "listed_preposition_takes_majrur": _listed_preposition_takes_majrur,
          "topic_carries_its_verb": _topic_carries_its_verb,
          "exception_word_by_case": _exception_word_by_case,
          "inner_sentence": _inner_sentence}


def book_links(toks: list[dict], heads: list[int], rels: list[str]) -> tuple[list[int], list[str]]:
    """The parser's heads and labels with every link the book settles written over them
    (a listed preposition's word class is corrected on its token too)."""
    heads, rels = list(heads), list(rels)
    for rule in _switched_on(_LINKS):
        rule(toks, heads, rels)
    return heads, rels
