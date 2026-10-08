"""Where a condition opens in a typed sentence, by the book's test, not the parser's links.

A conditional word has the front of its sentence (له الصدارة): it opens a condition when it
leads its clause and a verb comes straight after, its فعل الشرط. A conditional noun (مَنْ،
ما) shares its letters with a relative or a question word, so it opens one only when an
answer follows too: a verb tied to it by its letter (فَلْيَصُمْهُ), else one in jazm, else
a past verb, never one joined on by a conjunction (closed_words.json, conditional_nouns). The
letter that ties an answer (فَ) may stand on a noun clause or a particle in front of it (فَلَهُ،
فَإِنَّ، فَلَا): the book ties an answer exactly when it could not stand as a condition itself, so
that is an answer too, and a plain past verb after فَ is not enough to prove one (roles.json).

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
    """Each condition, in typed order: {opener, verb, answer, tie, tie_at, frame}, the first
    three typed-word indexes (`answer` None for a particle whose answer is not found, as لو
    with its answer left unsaid; `tie_at` the word the tying letter is written on, which is
    not the answer's own when a particle stands in front of it: فَلَا تُكْرِمْهُ). `before` is
    the letters written onto each word ahead of it (وَ، فَ), bare."""
    index = {base["id"]: k for k, base in enumerate(bases)}

    def joined(i: int) -> bool:
        return any(is_one(piece, "atf") for piece in before[i]) or (
            i > 0 and named[i - 1] in (NAMED.harf, None) and is_one(strip_diacritics(bases[i - 1]["form"]), "atf"))

    def opens(i: int) -> dict | None:
        frame = condition_of(strip_diacritics(bases[i]["form"]))
        if not frame or i + 1 >= len(bases) or named[i + 1] != NAMED.fil or (i and not joined(i)):
            return None
        # ما النافية is a particle; إذا before a verb is a ظرف, whatever the parser tagged it
        kind = (bases[i].get("reading") or {}).get("kind") or ("harf" if bases[i]["pos"] == "PRT" else "ism")
        return None if frame["noun"] and kind == "harf" else frame

    def needs_the_tie(frame: dict, k: int) -> bool:
        """The فاء on a verb shows an answer when the verb could not stand as a condition
        itself (roles.json, condition._evidence_comment): not a plain past verb."""
        fixed, form = frame["fixed_verbs"], strip_diacritics(bases[k]["form"])
        return bases[k].get("asp") != "p" or form in fixed["words"] or any(is_one(form, f) for f in fixed["families"])

    def clause_head(k: int) -> int:
        """The word an answer begun at k is the sentence of: a particle in front of its
        clause (فَلَا تُكْرِمْهُ، فَقَدْ فَازَ) answers through the word it hangs on."""
        up = index.get(bases[k]["head"])
        return up if bases[k]["pos"] == "PRT" and up is not None and up > k else k

    found = []
    for i in range(len(bases)):
        if not (frame := opens(i)):
            continue
        span = []
        for k in range(i + 2, len(bases)):
            if opens(k):
                break
            span.append(k)
        verbs = [k for k in span if named[k] == NAMED.fil]
        tied = [(k, letter) for k in span if (letter := next((t for t in frame["ties"] if t in before[k]), None))]
        # a tied verb first; else any other word the tying letter is written on (فَلَهُ، فَإِنَّ، فَهُوَ، فَلَا):
        # a noun sentence or a particle is an answer whatever follows, a plain past verb only
        # where nothing shares its letters with a relative or a question word
        pick = next(((k, t) for k, t in tied if k in verbs and (not frame["shared"] or needs_the_tie(frame, k))), None) or next(
            ((k, t) for k, t in tied if k not in verbs), None)
        if pick:
            answer, (tie_at, tie) = clause_head(pick[0]), pick
        else:
            answer = next((k for k in verbs if not joined(k) and (cases[k] == "jazm" or bases[k].get("asp") == "p")), None)
            tie, tie_at = None, answer
        # a present verb in jazm right after مَنْ is never a relative's: it opens a condition
        if answer is None and frame["shared"] and not (cases[i + 1] == "jazm" and span):
            continue  # مَنْ جاءَ؟ : no answer, so the relative or the question word
        found.append({"opener": i, "verb": i + 1, "answer": answer, "tie": tie, "tie_at": tie_at, "frame": frame})
    return found
