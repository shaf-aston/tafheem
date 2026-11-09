"""The khabar, صفة or حال that no one writes: a word of its own, drawn hidden."""
from __future__ import annotations

from backend.services.nahw.book import clause_of, condition_of, says
from backend.services.nahw.syntax.facts import (
    Sentence,
    asked_verb,
    excepted_after_la,
    is_describing,
    is_masdar,
    is_preposition,
    is_verb,
    is_zarf,
    listed,
    noun_tagged,
    shown_cases,
    typed_or_parsed_case,
)
from backend.services.nahw.syntax.followers import FOLLOWERS
from backend.services.nahw.syntax.naming import NAMED
from backend.services.nahw.syntax.picture.hang import definite, hangs_under
from backend.services.nahw.syntax.picture.names import FRAMES
from backend.services.text.arabic_text import strip_diacritics
from backend.services.text.harakat import has_tanween
from backend.services.nahw.syntax.picture.state import Picture


def add_unwritten_khabars(c: Picture) -> None:
    """The khabar, صفة or حال that no one writes: a word of its own, drawn hidden."""
    bases, by_id, columns, drawn, named, role_of = c.bases, c.by_id, c.columns, c.drawn, c.named, c.role_of
    tokens, why_of, written = c.tokens, c.why_of, c.written
    # الحمدُ لله، زيدٌ في الدار: a jar-majroor or ظرف in the khabar slot hangs on a word no one
    # writes (ثابت), which is the khabar. It takes the column before the unit; `written` -1,
    # -2.. is the column of no typed word, a number of its own so it joins no word's run.
    # A relative pronoun is no مبتدأ (ما في القبور is a صلة).
    kept = FRAMES["understood"]
    sentence = Sentence(tokens)
    # لا رجلَ: its governor names the pair (اسم لا), `pair` in naming; a word nobody wrote takes its subject's
    pair_of = {token["id"]: found["pair"] for token, found in zip(bases, named) if "pair" in found}
    understood_pair: dict[int, dict] = {}
    understood: set[int] = set()
    hung: set[int] = set()
    fronted: dict[int, str] = {}  # في البيت رجلٌ: the khabar said before its مبتدأ, by id
    khabars = {*kept["khabar_of"].values(), NAMED.khabar_kaada}
    def understand(text: str, role: str, place: int, **word) -> dict:
        """A word no one writes: its own column before `place`, a role, drawn hidden."""
        word = {"id": max(by_id) + 1, "form": text, **word}
        by_id[word["id"]] = word
        role_of[word["id"]] = role
        why_of[word["id"]] = None
        drawn.insert(place, word)
        columns.insert(place, text)
        written.insert(place, -1 - len(understood))
        understood.add(word["id"])
        return word
    for held in [t for t in drawn if role_of[t["id"]] in kept["slot"]]:
        subject = next((s for s in drawn if role_of[s["id"]] in kept["khabar_of"] and s is not held
                        and "rel" not in s.get("pos_camel", "") and (held["head"] == s["id"] or s["head"] == held["id"] or (
                            held["head"] == s["head"] and s["head"] in by_id))), None)
        if not subject or any(role_of[k["id"]] in khabars and (k["id"] == subject["head"] or k["head"] in (
                subject["id"], subject["head"])) for k in drawn):
            continue
        # كوبٌ كبيرٌ من القهوة: مِن on an indefinite measure brings the tamyeez (roles.json
        # understood.measured), a word that describes the measure, not its khabar
        if strip_diacritics(held["form"]) in kept["measured"]["particles"] and not definite(subject) \
                and listed(subject, "tamyeez_head", "measures"):
            continue
        # the books write مبتدأ، خبر (ثابت)، ق (ثابت) side by side, so the khabar sits beside
        # the unit; a subject the unit headed (the لِ of الحمدُ لله) comes out beside them too
        # قال الضيفُ سلامٌ عليكم: a subject a verb hangs as its object heads the sentence it says,
        # so the unit and the khabar stay inside it, not beside it among the verb's own words
        inside = subject["rel"] == "OBJ" and subject["head"] in by_id and is_verb(by_id[subject["head"]])
        # قال لي زيد هو يكتب: a jar or ظرف hangs on a verb when there is one, an unwritten word only when there
        # is none (Mughni V1 p566: لا بد من تعلقهما بالفعل أو ما يشبهه ... فإن لم يكن شيء من هذه الأربعة موجودا قدر),
        # so one hung on the very verb whose said sentence the subject heads is that verb's, outside the sentence
        if inside and held["head"] == subject["head"]:
            continue
        if inside:
            held = {**held, "head": subject["id"]}
            drawn[[t["id"] for t in drawn].index(held["id"])], by_id[held["id"]] = held, held
        elif subject["head"] == held["id"]:
            new = {**subject, "head": held["head"]}
            drawn[drawn.index(subject)], by_id[subject["id"]] = new, new
        elif held["head"] == subject["id"]:  # إنما الأعمالُ بالنيات: the unit hung on its subject, not inside it
            held = {**held, "head": subject["head"]}
            drawn[[t["id"] for t in drawn].index(held["id"])], by_id[held["id"]] = held, held
        place = next(i for i, t in enumerate(drawn) if t["id"] == held["id"])
        khabar = kept["khabar_of"][role_of[subject["id"]]]
        # voweled for its place: the case its subject's khabar stands in (ثَابِتٌ، ثَابِتًا)
        case = (clause_of(role_of[subject["id"]]) or {}).get("case", "u")
        said_word = understand(kept["voweled"] + kept["tanween"][case], khabar, place,
                               head=subject["id"] if inside else held["head"], rel="PRD", pos="NOM", pos_camel="")
        understood_pair[said_word["id"]] = pair_of.get(subject["id"], {})
        at = [t["id"] for t in drawn]
        if at.index(said_word["id"]) < at.index(subject["id"]) and role_of[subject["id"]] in kept["fronted"]:
            fronted |= {said_word["id"]: kept["fronted"][khabar], subject["id"]: kept["fronted"][role_of[subject["id"]]]}
        hung.add(held["id"])
    # لا إله إلا الله: the khabar left out because it is known, between the noun and إلا
    # (roles.json exception_after_la), the name after إلا standing for its hidden pronoun
    after_la = FRAMES["exception_after_la"]
    mubdal_minhu: dict[int, dict] = {}  # the hidden khabar's own hidden pronoun, which the بدل stands for
    for token in list(drawn):
        if role_of.get(token["id"]) == NAMED.badal and (hit := excepted_after_la(token, sentence)):
            noun, illa, entry = hit
            said = understand(entry["khabar"], after_la["khabar_named"], [t["id"] for t in drawn].index(illa["id"]),
                              head=noun["head"], rel="PRD", pos="NOM", pos_camel="")
            if "mubdal_minhu" in entry:
                mubdal_minhu[said["id"]] = entry["mubdal_minhu"]
    # رجلٌ من الأنصار، غلامًا له: a noun for a thing works on nothing, so what hangs on it hangs on the
    # word it is described by, which no one writes (roles.json understood): its صفة or, after a known noun, its حال
    after_noun = FRAMES["clause_after_noun"]
    for held in [t for t in drawn if role_of[t["id"]] in kept["slot"] and t["id"] not in hung]:
        noun = by_id.get(held["head"])
        if (not noun or noun["id"] > held["id"] or noun["id"] in understood or not noun_tagged(noun) or not role_of[noun["id"]]
                or is_describing(noun) or is_masdar(noun) or is_zarf(noun, sentence)):
            continue
        known, case = definite(noun), typed_or_parsed_case(noun)
        if strip_diacritics(held["form"]) in kept["measured"]["particles"] and listed(noun, "tamyeez_head", "measures"):
            continue  # كوبٌ من القهوة: the tamyeez, not a description
        if not case and not known:
            continue
        job = after_noun["definite" if known else "indefinite"]
        said_word = understand(kept["voweled"] + kept["tanween"][after_noun["definite_case"] if known else case], job,
                               drawn.index(held), head=noun["id"], rel="MOD", pos="NOM", pos_camel="", lemma=kept["word"])
        hung.add(held["id"])
    c.fronted, c.hung, c.kept, c.khabars, c.mubdal_minhu = fronted, hung, kept, khabars, mubdal_minhu
    c.pair_of, c.sentence, c.understand, c.understood = pair_of, sentence, understand, understood
    c.understood_pair = understood_pair


def add_unwritten_verbs(c: Picture) -> None:
    """A noun that heads its own sentence, or answers a question: the object of a verb no one writes; a title: the khabar of a مبتدأ no one writes."""
    bases, by_id, columns, drawn, kept, khabars = c.bases, c.by_id, c.columns, c.drawn, c.kept, c.khabars
    named, role_of, sentence, typed_at, understand = c.named, c.role_of, c.sentence, c.typed_at, c.understand
    why_of = c.why_of
    said_verb = kept["verb"]
    named_by_unsaid: set[int] = set()  # nouns whose job a word no one writes gives: its object, its khabar
    replies: set[int] = set()  # the unwritten verbs that answer a question
    detail_of: dict[int, str] = {}
    def hang_on_unsaid_verb(noun: dict, text: str, **place) -> dict:
        """The noun (with the words that follow it) is the object of a verb no one writes."""
        verb = understand(text, NAMED.fil, drawn.index(noun), pos="VRB", pos_camel="", base=text, asp="na", **place)
        # شكرًا: the unwritten verb's own masdar; الصِّدْقَ الصِّدْقَ: one with ال urged on the
        # hearer is the object of an unwritten الزم (الإغراء, Tasheel 3.8.1)
        masdar = (is_masdar(noun) or listed(noun, "verbless_masdars")) and not strip_diacritics(noun["form"]).startswith("ال")
        role_of[noun["id"]] = said_verb["noun"]["masdar" if masdar else "other"]
        why_of[noun["id"]] = None  # the dash was for a case no job fitted; now one does
        under = {**noun, "head": verb["id"]}
        drawn[drawn.index(noun)], by_id[noun["id"]] = under, under
        named_by_unsaid.add(noun["id"])
        return verb
    # أهلًا وسهلًا، شكرًا لك: a منصوب noun that heads its own sentence, named by no word, is the
    # object of a verb no one writes, beside the noun it governs. Alone, its nasb shows as
    # tanween, or as the case of the words that follow it (الصلواتِ الخمسَ), or by a مضاف إليه, which no
    # verb takes (سُبْحَانَ اللَّهِ، مَعَاذَ اللَّهِ: Ibn Jinni, al-Munsif): a fatha with none (نِعْمَ، أَجْمَلَ) is a verb's
    for noun in [t for t in drawn if t["id"] in typed_at and role_of[t["id"]] is None
                 and t["head"] not in by_id and t["pos"] == "NOM" and "a" in shown_cases(t)
                 and (has_tanween(t.get("typed")) or any(role_of[k["id"]] in (*FOLLOWERS, NAMED.mudaf_ilayh) for k in drawn if k["head"] == t["id"]))]:
        hang_on_unsaid_verb(noun, said_verb["word"], head=0, rel="---")
    # ماذا فرض الله ... فقال الصلواتِ: after a question for an object, the noun a verb of saying
    # hangs is the answer, the object of the question's verb, which is drawn as an unwritten word
    asked = asked_verb(sentence)
    for noun in [t for t in drawn if asked and t["id"] > asked["id"] and t["id"] not in named_by_unsaid and role_of[t["id"]] == said_verb["noun"]["other"]
                 and t["id"] in typed_at and noun_tagged(t) and "a" in shown_cases(t)
                 and role_of.get(t["head"]) == NAMED.fil
                 and says(by_id[t["head"]]["lemma"])]:
        text = columns[next(i for i, t in enumerate(drawn) if t["id"] == asked["id"])]
        verb = hang_on_unsaid_verb(noun, text, head=noun["head"], rel="OBJ")
        replies.add(verb["id"])
        detail_of[noun["id"]] = said_verb["reply"]["detail"].format(verb=text)
    # لولا زيدٌ لهلك عمرٌو: the noun after لولا is a مبتدأ whose khabar, a general being, is always
    # left out (roles.json condition by_word `khabar`); it is drawn hidden after the noun, before the answer
    for i, found in enumerate(named):
        opens = found.get("condition", {})
        frame = condition_of(bases[i]["form"]) if opens.get("part") == "opener" else None
        if not frame or not frame.get("khabar") or opens.get("answer") is None or opens.get("verb") is None:
            continue
        noun = by_id[bases[opens["verb"]]["id"]]
        if any(role_of.get(t["id"]) in khabars and t["head"] == noun["id"] for t in drawn):
            continue
        # after the noun and the words hung under it (لولا رحمةُ اللهِ)
        start = drawn.index(noun)
        place = next((k for k in range(start, len(drawn)) if not hangs_under(drawn[k], noun, by_id)), len(drawn))
        said_khabar = understand(frame["khabar"], NAMED.khabar, place, head=noun["id"], rel="PRD", pos="NOM", pos_camel="")
        detail_of[said_khabar["id"]] = frame["khabar_detail"]
    # بابُ الفاعلِ، كوبٌ كبيرٌ من القهوة: a noun phrase alone, its head in raf' or in no case shown,
    # with no verb, no khabar, no فاعل (أذاهبٌ زيدٌ: the doer stands for the khabar) and no question
    # word (أيوسفُ الفائزُ أم طارقٌ asks: أم is on the istifham list) in it, is a title or an
    # answer: the khabar of a مبتدأ no one writes, هذا (roles.json understood.subject). A nasb head was taken above (شكرًا).
    alone = kept["subject"]
    def a_title(noun: dict) -> bool:
        """The one head of several typed words, a noun that is no pronoun and has no job but مبتدأ,
        not shown out of raf', in words with no verb, khabar, فاعل or question word."""
        if noun["id"] not in typed_at:  # a hidden word has no reading to ask
            return False
        cases = shown_cases(noun)
        return noun_tagged(noun) and not noun.get("pos_camel", "").startswith("pron") \
            and role_of[noun["id"]] in (None, NAMED.mubtada) and not (cases & {"a", "i"} and "u" not in cases) \
            and not any(is_verb(t) or role_of.get(t["id"]) in (*khabars, NAMED.fail) or t["head"] == noun["id"] and t["rel"] == "PRD" for t in drawn) \
            and not any(t["id"] in typed_at and listed(t, "istifham") and not is_preposition(t) for t in drawn)
    heads = [t for t in drawn if t["head"] not in by_id]
    if len(heads) == 1 and len(bases) > 1 and a_title(noun := heads[0]):
        said_subject = understand(alone["voweled"], NAMED.mubtada, drawn.index(noun), head=0, rel="SBJ", pos="NOM", pos_camel="")
        role_of[noun["id"]] = alone["noun"]
        why_of[noun["id"]] = None
        under = {**noun, "head": said_subject["id"], "rel": "PRD"}
        drawn[drawn.index(noun)], by_id[noun["id"]] = under, under
        named_by_unsaid.add(noun["id"])
        detail_of[noun["id"]] = alone["detail"]
    at = {token["id"]: index for index, token in enumerate(drawn)}
    c.at, c.detail_of, c.named_by_unsaid, c.replies = at, detail_of, named_by_unsaid, replies
    c.said_verb = said_verb
