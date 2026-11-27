"""A clause's job and place (في محل رفع."""
from __future__ import annotations

from backend.services.nahw.book import book_map, clause_of, counted_name, is_one, says, term_ar
from backend.services.nahw.syntax.facts import (
    NOUN_LINKS,
    is_participle,
    is_prefix,
    is_suffix,
    is_verb,
    noun_tagged,
    previous_noun,
    read_as,
    reading,
    typed_or_parsed_case,
)
from backend.services.nahw.roles import NAMED
from backend.services.nahw.syntax.picture.hang import definite
from backend.services.nahw.syntax.picture.names import CARDS, FRAMES
from backend.services.text.arabic_text import strip_diacritics
from backend.services.text.harakat import CASE_LETTER, SHADDA
from backend.services.nahw.syntax.picture.state import Picture


def place_clauses(c: Picture) -> None:
    """A clause's job and place (في محل رفع...): khabar, masdar, relative ما, after و, after a noun, a صلة, a مقول القول."""
    by_id, drawn, family_of, framed, job_by_place = c.by_id, c.drawn, c.family_of, c.framed, c.job_by_place
    job_of, kind_of_ma, label_of, ma_card, masdar = c.job_of, c.kind_of_ma, c.label_of, c.ma_card, c.masdar
    name_of, named, nominal, opens, place_of = c.name_of, c.named, c.nominal, c.opens, c.place_of
    replies, role_of, said, sentence, typed_at = c.replies, c.role_of, c.said, c.sentence, c.typed_at
    headed = set(nominal)  # the nominal sentences a khabar heads, its مبتدأ under it (picture.jobs)
    def in_place(case: str) -> str:
        return said["in_place"].format(place=said["place"][case])
    khabar_clause: dict[int, dict] = {}  # a khabar's job and case, by its subject's role or its governor's family
    def by_family(token: dict, governor: dict) -> dict | None:
        """كنتَ تحبُّ: the clause on كان's PRD is its khabar, with no اسم كان word to hang it on; كاد زيدٌ يموتُ: a كاد-type
        verb's, a present verb bare or behind أنْ, whichever relation the parser hung it by (roles clause_by_family)."""
        by = FRAMES["clause_by_family"].get(family_of[governor["id"]])
        return by if by and token["rel"] in by["rels"] else None
    for token in drawn:
        owners = [t for t in drawn if t["id"] == token["head"] or (
            token["rel"] == "PRD" and t["head"] == token["head"] and t["id"] != token["id"])]
        clause = next((found for t in owners if (found := clause_of(role_of.get(t["id"])) or by_family(token, t))), None)
        if clause and (token["rel"] == "PRD" or clause.get("rels")):
            khabar_clause[token["id"]] = clause
        # لهم ما يشاءون: the clause after a relative is its صلة, with no place, though the relative be a مبتدأ
        if clause and token["id"] in opens and job_of[token["id"]] != NAMED.silah:
            job_of[token["id"]] = clause["job"]
            place_of[token["id"]] = in_place(clause["case"])
    # تحب أن تطوّق: أنْ and the verb hung on it are one masdar, doing the job أنْ hangs by
    # (the parser's أنّ takes a noun, so a verb on it is the nasb أنْ whatever the card guessed, unless the
    # reader typed its shadda: أَنَّنَا أَسْرَعْنَا is أنّ, its اسم written on it and the verb its khabar)
    for token in drawn:
        # أكلتُ ما طبختَ: the relative ما does the job of the place it stands in
        if (kind_of_ma.get(token["id"]) == "relative" and (placed := job_by_place(token))
                and role_of[token["id"]] not in masdar["job_by_rel"].values()):
            job_of[token["id"]], place_of[token["id"]] = placed[0], in_place(placed[1])
            ma_card[token["id"]] = placed
    for token in drawn:
        word = strip_diacritics(token["form"])
        # أَنَّ with its pair is one masdar too (عَلِمْتُ أَنَّكَ نَاجِحٌ: علمتُ نجاحَك), the اسم hung on it; it keeps its own name
        doubled = SHADDA in (token.get("typed") or token["form"])
        # كَانَ الْخَيْرُ أَنْ تَصْدُقَ، عَسَى زَيْدٌ أَنْ يَقُومَ: a masdar khabar is named and placed as any khabar of its governor
        khabar = khabar_clause.get(token["id"])
        if (word in masdar["words"] and (placed := (khabar["job"], khabar["case"]) if khabar else job_by_place(token))
                and kind_of_ma.get(token["id"], "masdar") == "masdar"
                and any(t["head"] == token["id"] and (t["rel"] == "SBJ" if doubled else role_of[t["id"]] == NAMED.fil) for t in drawn)):
            if not doubled:
                name_of[token["id"]] = (masdar["named_by_word"].get(word) or reading(token, "named")
                                        or CARDS[masdar["family"]]["named"])
            label_of[token["id"]] = masdar["label"]
            job_of[token["id"]], place_of[token["id"]] = placed[0], in_place(placed[1])
            if token["id"] in kind_of_ma:
                ma_card[token["id"]] = (None, None)  # the unit has the job; ما itself is a حرف
            # إلا أنْ تتطوعَ after a noun: an action is not of the group the noun names, so a منقطع;
            # غَيْرَ أنْ is غير's مضاف إليه, the excepting noun being the مستثنى itself
            excepting = by_id.get(token["head"])
            for family, after in masdar["after_family"].items():
                if excepting and excepting["pos"] == "PRT" and read_as(excepting, family) and previous_noun(excepting, sentence):
                    job_of[token["id"]] = after["job"]
                    place_of[token["id"]] = in_place(after["case"])
            framed.add(token["id"])
    # اللهُ أكبرُ inside a longer sentence: a مبتدأ with its خبر hung on it is a sentence too,
    # and so is لا النافية للجنس with its noun, and هو with the verb's sentence its khabar (وهو يبكي)
    nominal |= {token["id"] for token in drawn if token["head"] in by_id and (
        reading(token) == "la_jins" or (role_of[token["id"]] == NAMED.mubtada and any(
            t["head"] == token["id"] and job_of[t["id"]] == NAMED.khabar for t in drawn)))}
    # جَاءَ زَيْدٌ وَقَدْ تَعِبَ، لِمَ تُؤْذُونَنِي وَقَدْ تَعْلَمُونَ: so is a verb's sentence with قد before it, a past verb
    # being a حال only with قد, said or understood (Ibn Aqil, باب الحال: الجملة الحالية; page unchecked); but after a
    # sentence begun with قد too (قَدْ أَفْلَحَ مَنْ زَكَّاهَا وَقَدْ خَابَ مَنْ دَسَّاهَا) it is a second one joined to it
    after_waw, sure = FRAMES["clause_after_waw"], book_map("ghair_amila_other", "before_past")
    def with_qad(verb: dict) -> bool:
        return any(t["head"] == verb["id"] and t["id"] < verb["id"] and strip_diacritics(t["form"]) in sure for t in drawn)
    # وَأَمَّا الْعَمَلُ فَقَدْ نَجَحَ: a sentence أمّا brings is one part of a detailing (حرف شرط وتفصيل), no حال
    def states(token: dict, waw: dict) -> bool:
        return (token["id"] in nominal or is_verb(token) and with_qad(token) and not with_qad(by_id.get(waw["head"], waw))) \
            and not any(waw["id"] < t["id"] < token["id"] and is_one(t["form"], "ghair_amila_other", "detail") for t in drawn)
    for token in drawn:
        waw = by_id.get(token["head"])
        if waw and states(token, waw) and token["id"] not in place_of and waw["pos"] == "PRT" and is_prefix(waw) \
                and strip_diacritics(waw["form"]).strip("+") == "و" and (verb := by_id.get(waw["head"])) and is_verb(verb):
            job_of[token["id"]], place_of[token["id"]] = after_waw["job"], in_place(after_waw["case"])
            name_of[waw["id"]] = after_waw["waw"]
            framed.add(token["id"])
    # جَاءَ زَيْدٌ أَخُوهُ يَرْكُضُ: a nominal sentence after the verb's known doer, with no و (repair.hal), hangs its
    # مبتدأ, with its own pronoun as repair.hal asks, on the verb beside that doer; it tells the doer's state,
    # a حال as the sentence after و is (قَالَ زَيْدٌ إِنْ أَحَدٌ جَاءَنِي: no pronoun, it is what he said)
    for token in drawn:
        verb = by_id.get(token["head"])
        if token["id"] in nominal and token["id"] not in place_of and token["rel"] == "SBJ" and verb and is_verb(verb) \
                and (doer := next((t for t in drawn if t["head"] == verb["id"] and t["rel"] == "SBJ" and t["id"] < token["id"]), None)) \
                and definite(doer) \
                and any(is_suffix(t) and t["head"] == token["id"] and t["rel"] == "IDF" for t in drawn):
            job_of[token["id"]], place_of[token["id"]] = after_waw["job"], in_place(after_waw["case"])
            framed.add(token["id"])
    # فَلْيَتَّقِ after الدِّينِ: a conjunction written onto the verb joins its sentence to the one before
    # (عطف جملة), it does not describe the noun beside it
    # (فَمِنَ النَّاسِ مَنْ يَقُولُ: on the sentence's first written word, when the khabar heading it is one no one writes)
    def joins_sentence(token: dict) -> bool:
        first = min((t for t in drawn if t["head"] == token["id"]), key=lambda t: t["id"], default=None) \
            if token["id"] in c.understood else token
        return bool(first) and first["id"] in typed_at and any(
            piece["before"] and is_one(piece["form"], "atf") for piece in named[typed_at[first["id"]]].get("attached", []))
    # يَحْمِلُ حَقِيبَةً after رَجُلًا, كَأَنَّ رَأْسَهُ زَبِيبَةٌ after حَبَشِيٌّ, يَرْكُضُ after جَاءَ الطَّالِبُ
    after_noun = FRAMES["clause_after_noun"]
    described: dict[int, dict] = {}  # the noun each such sentence describes, by the sentence's id
    for token in drawn:
        head = by_id.get(token["head"])
        if (token["rel"] != "MOD" or not head or token["id"] in place_of or token["id"] < head["id"]
                # جاء رجلٌ أبوه كريمٌ: a nominal sentence after a noun describes it as a verbal one does
                or job_of[token["id"]] not in (None, NAMED.fil, NAMED.harf) and token["id"] not in headed
                or not (is_verb(token) or family_of[token["id"]] == "inna" or token["id"] in headed)
                or joins_sentence(token)):
            continue
        if not noun_tagged(head):  # on the verb: the noun it describes is the verb's, just before it
            if not is_verb(head):  # وَمِنكُم مَّن يُرَدُّ ... إِنَّ اللَّهَ عَلِيمٌ: on a حرف جر it describes nothing
                continue
            head = next((t for t in reversed(drawn) if t["head"] == head["id"] and t["id"] < token["id"]
                         and noun_tagged(t) and t["rel"] in NOUN_LINKS), None)
            if not head or not definite(head):
                continue
        # إِلَى دُنْيَا يُصِيبُهَا: a noun showing no case (a diptote's ألف) stands in the one its job gives it
        known, case = definite(head), typed_or_parsed_case(head) or (
            head["id"] in typed_at and CASE_LETTER.get(named[typed_at[head["id"]]].get("case") or ""))
        if not known and (head.get("stt") != "i" or not case):  # مَا، مَتَى: no case shown, nothing to describe
            continue
        job_of[token["id"]], described[token["id"]] = after_noun["definite" if known else "indefinite"], head
        if not known and role_of.get(head["id"]) in after_noun["on_khabar"] and is_participle(head):
            # جميلٌ يحب الجمال: a second khabar, no صفة
            name_of[head["id"]], job_of[token["id"]] = counted_name(role_of[head["id"]], 0), counted_name(role_of[head["id"]], 1)
        place_of[token["id"]] = in_place(after_noun["definite_case"] if known else case)
        framed.add(token["id"])  # drawn even when a particle heads it
        if not is_verb(token):
            nominal.add(token["id"])
    # جاء الذي نجح: a صلة stands in no case of its own; the الذي it follows takes the job
    place_of |= {token["id"]: said["no_place"] for token in drawn
                 if job_of[token["id"]] == NAMED.silah and token["id"] not in place_of}
    clauses = {token["id"] for token in drawn if job_of[token["id"]] == NAMED.silah} | set(place_of) | nominal | replies
    for token in drawn:
        if reading(token) in FRAMES["unit_by_family"]:
            label_of[token["id"]] = term_ar(FRAMES["unit_by_family"][reading(token)])
    # قال: لا إله إلا الله: the sentence a verb of saying hangs as its object is its مقول القول
    saying = FRAMES["said_clause"]
    for token in drawn:
        verb = by_id.get(token["head"])
        if verb and token["rel"] == "OBJ" and token["id"] in clauses and role_of.get(verb["id"]) == NAMED.fil \
                and says(verb["lemma"]):
            job_of[token["id"]] = saying["job"]
            place_of[token["id"]] = in_place(saying["case"])
            framed.add(token["id"])
    c.after_noun, c.clauses, c.described, c.in_place = after_noun, clauses, described, in_place
    c.nominal, c.place_of = nominal, place_of
