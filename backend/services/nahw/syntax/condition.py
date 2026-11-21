"""Where a condition opens in a typed sentence, by the book's test, not the parser's links.

A conditional word has the front of its sentence (له الصدارة): it opens a condition when it
leads its clause and a verb comes straight after, its فعل الشرط. A conditional noun (مَنْ،
ما) shares its letters with a relative or a question word, so it opens one only when an
answer follows too: a verb tied to it by its letter (فَلْيَصُمْهُ), else one in jazm, else
a past verb, never one joined on by a conjunction (closed_words.json, conditional_nouns). A
conditional noun nothing else shares its letters with (مَهْمَا) needs no clause to lead: it
opens after one, its answer having come first (لَنْ نَتَرَاجَعَ مَهْمَا طَالَ الزَّمَنُ). The
letter that ties an answer (فَ) may stand on a noun clause or a particle in front of it (فَلَهُ،
فَإِنَّ، فَلَا): the book ties an answer exactly when it could not stand as a condition itself, so
that is an answer too, and a plain past verb after فَ is not enough to prove one (roles.json).

The parser can hang مَنْ شاء under the answer as a relative and its clause, or the second
of two conditions under the first through وَ; naming, the picture and the cards all read
the conditions from here instead, so they agree.
"""
from __future__ import annotations

from backend.services.text.arabic_text import strip_diacritics
from backend.services.text.harakat import has_tanween
from backend.services.nahw.book import book_map, condition_of, frames, is_one, kaffa_sister, named_roles, says
from backend.services.nahw.syntax.facts import reading, spelled

NAMED = named_roles()


def subject_id(i: int, found: dict, bases: list[dict]) -> int:
    """The token لولا opened at word i opens on: the noun after it, or the pronoun written on it (لَوْلَاكَ)."""
    at = found["condition"]["verb"]
    return bases[at]["id"] if at != i else next(piece["id"] for piece in found["attached"] if not piece["before"])


def find(bases: list[dict], named: list[str | None], cases: list[str | None],
         before: list[list[str]], after: list[list[str]]) -> list[dict]:
    """Each condition, in typed order: {opener, verb, answer, tie, tie_at, frame, masdar, negations}, the first
    three typed-word indexes (`answer` None for a particle whose answer is not found, as لو
    with its answer left unsaid; `tie_at` the word the tying letter is written on, which is
    not the answer's own when a particle stands in front of it: فَلَا تُكْرِمْهُ; `negations` the لا that negates there,
    see negations; `masdar` whether the opener and its verb make a masdar). `before` is
    the letters written onto each word ahead of it (وَ، فَ), bare, and `after` those written after it (ـكَ)."""
    index = {base["id"]: k for k, base in enumerate(bases)}

    def joined(i: int) -> bool:
        """A joiner is written on the word, or on the particle before it (إِنْ تَدْرُسْ وَلَا تَكْسَلْ تَنْجَحْ), or is that
        particle. A word read as other than a joiner (particles.stamp) joins nothing: لا العاطفة joins a single word, never
        a verb (إِنْ تَدْرُسْ لَا تَرْسُبْ: the لا negates the answer)."""
        if any(is_one(piece, "atf") for piece in before[i]):
            return True
        return i > 0 and named[i - 1] in (NAMED.harf, None) and (any(is_one(piece, "atf") for piece in before[i - 1]) or (
            is_one(bases[i - 1]["form"], "atf") and reading(bases[i - 1]) in (None, "atf")))

    def verb_at(i: int) -> int:
        """The فعل الشرط's index: straight after the opener, or past a particle hung on it
        (إذا لم تستحِ، إن لا تفعلوه): the particle is in its clause, not between. لولا opens on
        a noun, and a pronoun written on it is that noun (لَوْلَاكَ): its index is the opener's own."""
        if after[i] and (condition_of(bases[i]["form"]) or {}).get("before") == "noun":
            return i
        k = i + 1
        if k + 1 < len(bases) and bases[k]["pos"] == "PRT" and bases[k]["head"] == bases[k + 1]["id"]:
            return k + 1
        return k

    def tells(i: int) -> bool:
        """Word i leads what a verb of saying before it tells, no other verb between (قُلْ إِنْ كُنْتُمْ تُحِبُّونَ اللَّهَ فَاتَّبِعُونِي،
        قَالَ الْمُعَلِّمُ إِنْ تَدْرُسْ لَا تَرْسُبْ): the مقول القول is a sentence of its own, so a word leading it leads a clause."""
        v = next((k for k in reversed(range(i)) if named[k] == NAMED.fil), None)
        return v is not None and says(bases[v]["lemma"])

    def opens(i: int) -> dict | None:
        frame = condition_of(spelled(bases[i]))
        v = verb_at(i)
        # a noun no relative or question word shares its letters with opens after a clause too, its answer
        # having come first (لَنْ نَتَرَاجَعَ مَهْمَا طَالَ الزَّمَنُ); so does لولا, which opens on a noun only, its
        # answer left out for the clause before it to tell (كَادَ الْقِطَارُ يَفُوتُنَا لَوْلَا أَنَّنَا أَسْرَعْنَا)
        # لَقِيَ لَوْمًا: a built opener takes no tanween, so a word with one is the noun its letters spell (أيّ,
        # the one conditional word declined, is no built opener and may take one)
        if frame and frame["built"] and has_tanween(bases[i].get("typed") or ""):
            return None
        # وَاللَّهِ لَئِنْ قَامَ زَيْدٌ لَأَقُومَنَّ: the لام that announces an oath comes onto a condition's إنْ only (`oath_lam`), so it
        # opens one after the oath too
        primed = primer_lam(i)
        if not frame or v >= len(bases) or (i and not joined(i) and not tells(i) and not primed and frame.get("before") != "noun"
                                             and (frame["shared"] or not frame["noun"])):
            return None
        # فَأَمَّا مَنْ أَعْطَى وَاتَّقَى فَسَنُيَسِّرُهُ: the one word after أمّا is the mubtada its فاء's answer tells of (closed_words
        # ghair_amila_other `detail`), so a word a relative shares its letters with is that relative, never a condition
        if frame["shared"] and i and is_one(bases[i - 1]["lemma"], "ghair_amila_other", "detail"):
            return None
        # إنما: the lemma is the pair, a ما الكافة cut off the إنّ sister it stops, so no إنْ of a condition
        if kaffa_sister(bases[i]["lemma"]):
            return None
        # لولا زيدٌ: a particle of امتناع لوجود opens on a noun; before a verb it urges and opens none
        # a masdar particle with its pair is a noun too (لَوْلَا أَنَّنَا أَسْرَعْنَا)
        if (named[v] == NAMED.fil) == (frame.get("before") == "noun") or (
                frame.get("before") == "noun" and v != i and bases[v]["pos"] not in ("NOM", "PROP") and not masdar(v)):
            return None
        # لَمَّا سَارُوا: لمّا opens on a past verb; لَمَّا يَذْهَبْ is the jazm particle, no condition
        if frame.get("before") == "past" and bases[v].get("asp") != "p":
            return None
        # ما النافية is a particle; إذا before a verb is a ظرف, whatever the parser tagged it
        read = reading(bases[i])
        if read == "wonder":
            return None  # مَا أَسْرَعَ مَا تَغَيَّرَتْ: the ما of wonder asks for no answer
        kind = reading(bases[i], "kind") or ("harf" if bases[i]["pos"] == "PRT" else "ism")
        if not frame["noun"] and read and read != frame["family"]:
            return None  # إِنَّا جَعَلْنَا: the particle's one reading is إنّ, no condition
        # مَا تَزْرَعْ تَحْصُدْ: ما النافية puts no verb in jazm, so a jussive verb after it shows the
        # conditional noun, whatever the parser tagged it
        return None if frame["noun"] and kind == "harf" and cases[v] != "jazm" else frame

    def primer_lam(i: int) -> bool:
        primer = book_map("ghair_amila_other", "oath_lam")
        return primer["lam"] in before[i] and spelled(bases[i]) in primer["onto"]

    def masdar(k: int) -> bool:
        return strip_diacritics(bases[k]["form"]) in frames()["masdar"]["words"]

    def under(k: int, v: int) -> bool:
        """Word k hangs, through typed words, on word v: in v's own clause."""
        seen = set()
        while k not in seen and (k := index.get(bases[k]["head"])) is not None:
            if k == v:
                return True
            seen.add(k)
        return False

    def needs_the_tie(frame: dict, k: int) -> bool:
        """The فاء on a verb shows an answer when the verb could not stand as a condition
        itself (roles.json, condition._evidence_comment): not a plain past verb."""
        fixed, form = frame["fixed_verbs"], strip_diacritics(bases[k]["form"])
        return bases[k].get("asp") != "p" or form in fixed["words"] or any(is_one(form, f) for f in fixed["families"])

    def said(k: int, opener: int) -> bool:
        """Word k is what a verb of saying inside the condition says, its مقول القول (وَإِذَا قِيلَ لَهُمْ لَا تُفْسِدُوا فِي الْأَرْضِ
        قَالُوا): a sentence of its own, never the condition's answer nor its clause. A verb of saying before the opener
        says the whole condition (قَالَ الْمُعَلِّمُ إِنْ تَدْرُسْ لَا تَرْسُبْ), so it hides nothing inside it. A verb joined on to
        a said one is said with it, the معطوف sharing its place (إِنْ قُلْتَ لَهُ لَا تَكْذِبْ وَلَا تَسْرِقْ غَضِبَ)."""
        if any(named[v] == NAMED.fil and says(bases[v]["lemma"]) and under(k, v) for v in range(opener + 1, k)):
            return True
        last = next((v for v in reversed(range(opener + 1, k)) if named[v] == NAMED.fil), None)
        return last is not None and joined(k) and said(last, opener)

    def negations(frame: dict, opener: int, verb: int, answer: int | None, end: int) -> list[int]:
        """The لا a prohibition would take before the condition's verb, a verb joined to it, or an answer no ف ties: what
        asks is never a condition's clause, nor its answer unless a ف ties it (Ibn Aqil V4, page unchecked: وأقرن بفا حتما جوابا لو جعل
        شرطا), so that لا negates. One before a said verb asks inside what is said (قِيلَ لَهُمْ لَا تُفْسِدُوا). Only a
        condition that puts its verbs in jazm leaves the jazm to it: after إذا or لو none but the لا gives it, so that one forbids
        (إِذَا جَاءَ زَيْدٌ لَا تُكَلِّمْهُ). A word read as putting in jazm there is that لا: an إن or إلّا would open a condition
        of its own, and لمّا never follows a conditional word (Mughni, لمّا, page unchecked)."""
        if frame["family"] != "jazm":
            return []
        return [k for k in range(opener + 1, end) if reading(bases[k]) == "jazm"
                and k + 1 < len(bases) and not said(k + 1, opener) and (k + 1 in (verb, answer) or joined(k + 1))]

    def clause_head(k: int) -> int:
        """The word an answer begun at k is the sentence of: a particle in front of its
        clause (فَلَا تُكْرِمْهُ، فَقَدْ فَازَ) answers through the word it hangs on."""
        up = index.get(bases[k]["head"])
        return up if bases[k]["pos"] == "PRT" and up is not None and up > k else k

    found = []
    for i in range(len(bases)):
        if not (frame := opens(i)):
            continue
        verb = verb_at(i)
        span = []
        for k in range(verb + 1, len(bases)):
            if opens(k):
                break
            if not (frame.get("before") == "noun" and under(k, verb)):  # أَنَّنَا أَسْرَعْنَا: the masdar's own verb answers nothing
                span.append(k)
        verbs = [k for k in span if named[k] == NAMED.fil and not said(k, i)]
        # إِنْ تَدْرُسُوا فَتَجْتَهِدُوا يُحِبَّكُمُ: a present verb after the ف showing jazm or nasb stands between the two clauses
        # (Ibn Aqil V4, page unchecked: وجزم أو نصب لفعل إثر فا ... بالجملتين اكتنفا); one the ف ties as the answer is a noun clause's
        # khabar, its مبتدأ unsaid, so in raf' (V4, page unchecked: وأقرن بفا حتما جوابا لو جعل شرطا ... لم ينجعل). A لام on it bids (فَلْيَصُمْهُ)
        between = {k for k in verbs if cases[k] in ("jazm", "nasb") and "ل" not in before[k]}
        tied = [(k, letter) for k in span if k not in between
                and (letter := next((t for t in frame["ties"] if t in before[k]), None))]
        # the first word the tying letter is written on is the answer (فَلَهُ، فَإِنَّ، فَهُوَ، فَلَا، فَقَدْ):
        # a noun sentence or a particle is one whatever follows, a plain past verb only where nothing
        # shares its letters with a relative or a question word. A later tied clause is joined on to
        # it (فَقَدِ اسْتَكْمَلَ ... فَلْيَتَّقِ), it does not replace it
        pick = next(((k, t) for k, t in tied if k not in verbs or not frame["shared"] or needs_the_tie(frame, k)), None)
        if pick:
            answer, (tie_at, tie) = clause_head(pick[0]), pick
        else:
            # a present verb showing no ending may be the answer a particle (إن) puts in jazm; a noun
            # sharing its letters with a relative needs the answer to show it (مَنْ يدرسُ ينجحُ)
            answer = next((k for k in verbs if not joined(k) and (cases[k] == "jazm" or bases[k].get("asp") == "p"
                                                                  or cases[k] is None and not frame["shared"])), None)
            tie, tie_at = None, answer
        # a present verb in jazm right after مَنْ is never a relative's: it opens a condition
        if answer is None and frame["shared"] and not (cases[verb] == "jazm" and span):
            continue  # مَنْ جاءَ؟ : no answer, so the relative or the question word
        # لَئِنْ شَكَرْتُمْ لَأَزِيدَنَّكُمْ: the لام on إنْ announces an oath left unsaid (closed_words ghair_amila_other `oath_lam`).
        # Of an oath and a condition the answer is the first one's, the other's left out (Alfiyya, فصل الشرط: واحذف لدى اجتماع
        # شرط وقسم جواب ما أخرت; page unchecked), so what follows answers the oath (`sworn`) and the condition has none
        # (the oath's answer, its verb built on the nun of emphasis, shows no jazm: the first verb its clause has)
        sworn = None
        if primer_lam(i):
            sworn = answer if answer is not None else next((k for k in verbs if not joined(k)), None)
            answer, tie, tie_at = None, None, None
        end = tie_at if tie else verb + 1 if answer is None else answer
        found.append({"opener": i, "verb": verb, "answer": answer, "tie": tie, "tie_at": tie_at, "frame": frame, "sworn": sworn,
                      "masdar": verb != i and masdar(verb), "negations": negations(frame, i, verb, answer, end)})
    return found
