"""What each unit does for the word above it, and which words open a clause."""
from __future__ import annotations

from backend.services.nahw.book import book_spelling, case_of, condition_of, is_one, kaffa_chart, teacher_rules
from backend.services.nahw.syntax.doer import written_on
from backend.services.nahw.syntax import ma
from backend.services.nahw.syntax.facts import is_participle, is_passive, is_preposition, is_verb, listed
from backend.services.nahw.roles import NAMED
from backend.services.nahw.syntax.picture.names import FRAMES, SISTERS, command_name, finer_name
from backend.services.nahw.syntax.picture.state import Picture


def give_jobs(c: Picture) -> None:
    """What each unit does for the word above it, and which words open a clause."""
    by_id, drawn, named, role_of, sentence = c.by_id, c.drawn, c.named, c.role_of, c.sentence
    typed_at = c.typed_at
    # what each unit does for the word above it: هذا البيتُ is drawn with the noun over its
    # pointer, but the pair is the مبتدأ, not a صفة of the khabar
    job_of = {token["id"]: NAMED.mubtada if role_of[token["id"]] == NAMED.sifah and any(
        t["head"] == token["id"] and t["id"] < token["id"] and role_of.get(t["id"]) == NAMED.mubtada for t in drawn)
        else role_of[token["id"]] for token in drawn}
    # a clause inside the sentence is headed by its verb, or by a khabar with its own مبتدأ
    # before it under it (زيدٌ أبوه عالمٌ): verbal or nominal, it is drawn as a sentence
    # (hung on a word other than that مبتدأ: the parser can draw the two pointing at each other)
    nominal = {token["id"] for token in drawn if role_of[token["id"]] == NAMED.khabar and any(
        t["head"] == token["id"] and t["id"] < token["id"]
        and role_of[t["id"]] == NAMED.mubtada and token["head"] != t["id"] for t in drawn)}
    opens = {token["id"] for token in drawn if role_of[token["id"]] == NAMED.fil} | nominal
    # أكلتُ ما طبختَ: a ما whose صلة has room for its عائد is the relative, whatever the tagger
    # guessed; سرّني ما قمتَ: one with none is ما المصدرية (ma.kind)
    masdar = FRAMES["masdar"]
    def job_by_place(token: dict) -> tuple[str, str] | None:
        """The job a ما or masdar unit does: a حرف جر's مجرور (its object: لكم الخيار ما دمتم, hung on ل, is no second one),
        else by the relation it hangs by."""
        governor = by_id.get(token["head"])
        if governor and is_preposition(governor) and token["rel"] == "OBJ":
            return masdar["after_preposition"]["job"], masdar["after_preposition"]["case"]
        # أُرِيدُ أَنْ أَقْرَأَ وَأَنْ أَكْتُبَ: a masdar a حرف عطف brings is معطوف, in the case of the one it is joined on to
        # (one whose case is not known, as after إِمَّا, keeps the job its relation gives)
        if governor and token["rel"] == "OBJ" and is_one(governor["form"], "atf") and (joined := by_id.get(governor["head"])) \
                and (place := job_by_place(joined)):
            return NAMED.matoof, place[1]
        # لَوْلَا أَنَّنَا أَسْرَعْنَا: after لولا the masdar is its مبتدأ (roles.json condition by_word subject)
        if governor and governor["pos"] == "PRT" and (frame := condition_of(governor["form"])) and frame.get("subject"):
            return frame["subject"], case_of(frame["subject"])
        rel = token["rel"]
        # وَأَنْ تَصُومُوا خَيْرٌ لَكُمْ، لَكَ مَا تُرِيدُ: a doer is a verb's or a participle's (Tasheel 2.4.1), so a unit
        # hung as the subject of a noun or a jar is its مبتدأ, and that word its khabar; إِنَّمَا الْعَدْلُ أَنْ يُسْمَعَ:
        # unless that noun is the مبتدأ said before it (of two known words the first is the مبتدأ), when it is the خبر
        # فَأَمَّا مَا يَنْفَعُ النَّاسَ فَيَمْكُثُ: a doer never comes before its verb (الفاعل لا يتقدم; page unchecked), so one
        # hung before it opens the sentence, its مبتدأ, as facts.slot reads a fronted subject
        fronted = governor and is_verb(governor) and governor["id"] > token["id"]
        if rel == "SBJ" and (fronted or not (governor and (is_verb(governor) or is_participle(governor)))):
            said_first = governor and governor["id"] < token["id"] and role_of.get(governor["id"]) == NAMED.mubtada
            job = NAMED.khabar if said_first else NAMED.mubtada
            return job, case_of(job)
        if (governor and rel in ("SBJ", "OBJ") and is_passive(governor)
                and not any(t["head"] == governor["id"] and t["rel"] in ("SBJ", "OBJ") and t is not token and t["pos"] != "PRT" for t in drawn)
                # أُمِرْتُ أَنْ أَكُونَ: the تُ written onto the verb is its deputy, so the masdar is no نائب فاعل
                and not written_on(governor)):
            return masdar["after_passive"]["job"], masdar["after_passive"]["case"]
        return (masdar["job_by_rel"][rel], masdar["case_by_rel"][rel]) if rel in masdar["job_by_rel"] else None
    kind_of_ma = {token["id"]: kind for token in drawn if (kind := ma.kind(token, sentence))}
    ma_card: dict[int, tuple[str | None, str | None]] = {}  # what the ما's card says: its job and case, or none
    for token in drawn:
        kind = kind_of_ma.get(token["id"])
        if kind == "masdar":
            token["pos"], token["pos_camel"] = "PRT", "part"
            for verb in sentence.kids(token):
                if is_verb(verb) and verb["id"] > token["id"]:
                    role_of[verb["id"]] = NAMED.fil  # بما تُرِكَ العملُ: the verb is no صفة of ما
        elif kind == "relative":
            token["pos"], token["pos_camel"] = "NOM", "pron_rel"
    # جاء الذي نجح: the clause after a relative is its صلة, with no place of its own; كَمْ مِنْ كِتَابٍ قَرَأْتُهُ:
    # a word the tagger calls relative but no book lists as one (closed_words mawsul) has none. A relative has one
    # صلة: a later clause hung on it is one too only when joined to it by و، أو، ثم (وَهُوَ الَّذِي سَخَّرَ ... وَتَرَى
    # الْفُلْكَ); else it tells of the relative (الَّذِي يَقْرَأُ كَثِيرًا يَزْدَادُ عِلْمُهُ، فَأَمَّا الَّذِينَ كَفَرُوا فَأُعَذِّبُهُمْ: its khabar)
    def joined(clause: dict, relative: dict) -> bool:
        return any(t["head"] == clause["id"] and relative["id"] < t["id"] < clause["id"] and is_one(t["form"], "atf", "joins_mood")
                   for t in drawn)
    with_silah: set[int] = set()
    for token in sorted(drawn, key=lambda t: t["id"]):
        up = next((t for t in drawn if t["id"] == token["head"]), None)
        if up and "rel" in up.get("pos_camel", "") and listed(up, "mawsul") and not up.get("reading") and up["id"] < token["id"] \
                and token["id"] in opens and "condition" not in named[typed_at.get(up["id"], 0)] \
                and (up["id"] not in with_silah or joined(token, up)):
            job_of[token["id"]] = NAMED.silah
            with_silah.add(up["id"])
    c.job_by_place, c.job_of, c.kind_of_ma, c.ma_card = job_by_place, job_of, kind_of_ma, ma_card
    c.masdar, c.nominal, c.opens = masdar, nominal, opens


def give_names(c: Picture) -> None:
    """The finer name each word is drawn with, and the name the sister of a family lends to what it governs."""
    bases, drawn, fronted, job_of, named, pair_of = c.bases, c.drawn, c.fronted, c.job_of, c.named, c.pair_of
    replies, role_of, said_verb, sentence, split = c.replies, c.role_of, c.said_verb, c.sentence, c.split
    understood, understood_pair = c.understood, c.understood_pair
    # الولدُ يكتبُ: the clause hung on a مبتدأ (or اسم كان) is its khabar, standing in a case;
    # كان الولدُ يكتبُ: so is the one beside it, the khabar (PRD) under their governor
    said = teacher_rules()["case_said"]
    family_of = {token["id"]: found.get("family") for token, found in zip(bases, named)} | {
        key: piece["family"] for key, piece in split.items()} | dict.fromkeys(understood)
    printed_of = {token["id"]: found["printed"] for token, found in zip(bases, named) if found.get("printed")}
    name_of = {token["id"]: finer_name(token, role_of[token["id"]], family_of[token["id"]]) for token in drawn}
    for token in drawn:
        if name_of[token["id"]] == NAMED.fil:
            name_of[token["id"]] = command_name(token, drawn, family_of) or printed_of.get(token["id"]) or NAMED.fil
    for key, pair in {**pair_of, **understood_pair}.items():
        name_of[key] = pair.get(role_of[key], name_of[key])
        if job_of.get(key) == role_of[key]:
            job_of[key] = name_of[key]  # لا طالبَ علمٍ: the unit the اسم heads is called اسم لا too
    # إِنَّمَا، كَأَنَّمَا: the sister a ما is written onto works on nothing, and that ما is always ما الكافة, not a bare حرف
    sister_name, ma_name = kaffa_chart()
    for token, found in zip(bases, named):
        if found.get("kaffa") and token["id"] in name_of:
            name_of[token["id"]] = sister_name
            if (after := c.by_id.get(token["id"] + 1)) and after["id"] in name_of and ma.is_ma(after):
                name_of[after["id"]] = ma_name
    name_of.update(dict.fromkeys(replies, said_verb["word"]))
    name_of.update(fronted)  # the question's verb, said no more than it is: unwritten
    # في البيت رجلٌ كريمٌ: a مبتدأ مؤخر heading its own unit is one as a whole, as on its own
    job_of.update({key: name for key, name in fronted.items() if job_of.get(key) == role_of[key]})
    # ظننتُ المعلمَ حاضرًا، أعطيتُ زيدًا كتابًا: the verb's two objects are its first and second
    two = FRAMES["two_objects"]
    def of_two(verb: dict) -> bool:
        return sentence.family(verb) in two["families"] or any(is_one(verb["lemma"], f) for f in two["families"])
    # وَجَدُوهُ طَوِيلًا: an object pronoun written onto the verb is nearer it than any written word, so the first
    objects_of: dict[int, list[int]] = {token["id"]: [piece["id"] for piece in found.get("attached", [])
                                                      if not piece["before"] and piece["role"] == two["role"]]
                                        for token, found in zip(bases, named) if of_two(token)}
    for token, found in zip(bases, named):
        if role_of[token["id"]] == two["role"] and (at_gov := found.get("governor")) is not None and of_two(verb := bases[at_gov]):
            objects_of.setdefault(verb["id"], []).append(token["id"])
    for pair in objects_of.values():
        if len(pair) == len(two["names"]):
            name_of.update(zip(pair, two["names"]))
    place_of: dict[int, str] = {}
    label_of: dict[int, str] = {}
    framed: set[int] = set()  # units whose job a governor gave, drawn even under a particle
    c.family_of, c.framed, c.label_of, c.name_of, c.place_of = family_of, framed, label_of, name_of, place_of
    c.said = said


def name_sisters(c: Picture) -> None:
    """كَأَنَّ رَأْسَهُ زَبِيبَةٌ، أَصْبَحَ الْجَوُّ بَارِدًا: the two a sister governs are called after that sister
    (اسم كأنّ، خبر أصبح), the family's mother (إنّ، كان) only naming the family: a word it governs, a pronoun
    written onto it (كَأَنَّهُ) and a clause that is its khabar (لَيْتَ الْمَطَرَ يَنْزِلُ), each named after the
    nearest of that family above it. Run once every job is given, the clauses' too."""
    by_id, family_of, job_of, name_of, role_of = c.by_id, c.family_of, c.job_of, c.name_of, c.role_of
    # the governor naming found comes first: ما اللهُ بغافلٍ hangs ما on the khabar, not the khabar on ما
    governor = {token["id"]: c.bases[found["governor"]] for token, found in zip(c.bases, c.named) if found.get("governor") is not None}
    def sister_above(token: dict, mother: str) -> dict | None:
        if (gov := governor.get(token["id"])) and SISTERS.get(family_of.get(gov["id"])) == mother:
            return gov
        up, seen = by_id.get(token["head"]), set()
        while up and up["id"] not in seen:
            if SISTERS.get(family_of.get(up["id"])) == mother:
                return up
            seen.add(up["id"])
            up = by_id.get(up["head"])
        return None
    def renamed(said: str | None, token: dict) -> str | None:
        mother = next((m for m in SISTERS.values() if (said or "").endswith(f" {m}")), None)
        sister = mother and sister_above(token, mother)
        spelled = sister and book_spelling(sister["lemma"])
        return f"{said.removesuffix(mother)}{spelled}" if spelled and spelled != mother else None
    for token in c.drawn:
        if name := renamed(role_of.get(token["id"]), token):
            name_of[token["id"]] = name
        if job := renamed(job_of.get(token["id"]), token):
            job_of[token["id"]] = job
