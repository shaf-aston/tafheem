"""Where a condition opens in a typed sentence, by the book's test, not the parser's links.

A conditional word has the front of its sentence (له الصدارة): it opens a condition when it
leads its clause and a verb comes straight after, its فعل الشرط. A conditional noun (مَنْ،
ما) shares its letters with a relative or a question word, so it opens one only when an
answer follows too: a verb tied to it by its letter (فَلْيَصُمْهُ), else one in jazm, else
a past verb, never one joined on by a conjunction (closed_words.json, conditional_nouns).

The parser can hang مَنْ شاء under the answer as a relative and its clause, or the second
of two conditions under the first through وَ; naming, the picture and the cards all read
the conditions from here instead, so they agree.
"""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics
from backend.services.nahw_book import condition_of, is_one, named_roles

NAMED = named_roles()


def find(bases: list[dict], named: list[str | None], cases: list[str | None],
         before: list[list[str]]) -> list[dict]:
    """Each condition, in typed order: {opener, verb, answer, tie, frame}, the first three
    typed-word indexes (`answer` None for a particle whose answer is not found, as لو
    with its answer left unsaid). `before` is the letters written onto each word ahead of
    it (وَ، فَ), bare."""
    def joined(i: int) -> bool:
        return any(is_one(piece, "atf") for piece in before[i]) or (
            i > 0 and named[i - 1] in (NAMED.harf, None) and is_one(strip_diacritics(bases[i - 1]["form"]), "atf"))

    def opens(i: int) -> dict | None:
        frame = condition_of(strip_diacritics(bases[i]["form"]))
        if not frame or i + 1 >= len(bases) or named[i + 1] != NAMED.fil or (i and not joined(i)):
            return None
        return None if frame["noun"] and bases[i]["pos"] == "PRT" else frame  # ما النافية is a particle

    found = []
    for i in range(len(bases)):
        if not (frame := opens(i)):
            continue
        stretch = []
        for k in range(i + 2, len(bases)):
            if opens(k):
                break
            if named[k] == NAMED.fil:
                stretch.append(k)
        tie_of = {k: tie for k in stretch for tie in frame["ties"] if tie in before[k]}
        answer = next(iter(tie_of), None) or next(
            (k for k in stretch if not joined(k) and (cases[k] == "jazm" or bases[k].get("asp") == "p")), None)
        if answer is None and frame["noun"]:
            continue  # مَنْ جاءَ؟ : no answer, so the relative or the question word
        found.append({"opener": i, "verb": i + 1, "answer": answer, "tie": tie_of.get(answer), "frame": frame})
    return found
