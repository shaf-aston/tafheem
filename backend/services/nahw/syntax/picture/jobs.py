"""What each unit does for the word above it, and which words open a clause."""
from __future__ import annotations

from backend.services.nahw.book import book_spelling, is_one, teacher_rules
from backend.services.nahw.syntax.facts import is_passive, is_preposition, is_verb, ma_kind
from backend.services.nahw.syntax.naming import NAMED
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
        t["head"] == token["id"] and t["id"] < token["id"] and role_of[t["id"]] == NAMED.mubtada
        and token["head"] != t["id"] for t in drawn)}
    opens = {token["id"] for token in drawn if role_of[token["id"]] == NAMED.fil} | nominal
    # أكلتُ ما طبختَ: a ما whose صلة has room for its عائد is the relative, whatever the tagger
    # guessed; سرّني ما قمتَ: one with none is ما المصدرية (facts.ma_kind)
    masdar = FRAMES["masdar"]
    def job_by_place(token: dict) -> tuple[str, str] | None:
        """The job a ما or masdar unit does: a حرف جر's مجرور, else by the relation it hangs by."""
        governor = by_id.get(token["head"])
        if governor and is_preposition(governor):
            return masdar["after_preposition"]["job"], masdar["after_preposition"]["case"]
        rel = token["rel"]
        if (governor and rel in ("SBJ", "OBJ") and is_passive(governor)
                and not any(t["head"] == governor["id"] and t["rel"] in ("SBJ", "OBJ") and t is not token and t["pos"] != "PRT" for t in drawn)):
            return masdar["after_passive"]["job"], masdar["after_passive"]["case"]
        return (masdar["job_by_rel"][rel], masdar["case_by_rel"][rel]) if rel in masdar["job_by_rel"] else None
    kind_of_ma = {token["id"]: kind for token in drawn if (kind := ma_kind(token, sentence))}
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
    # جاء الذي نجح: the clause after a relative is its صلة, with no place of its own
    for token in drawn:
        up = next((t for t in drawn if t["id"] == token["head"]), None)
        if up and "rel" in up.get("pos_camel", "") and not up.get("reading") and up["id"] < token["id"] and token["id"] in opens                 and "condition" not in named[typed_at.get(up["id"], 0)]:
            job_of[token["id"]] = NAMED.silah
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
    name_of.update(dict.fromkeys(replies, said_verb["word"]))
    name_of.update(fronted)  # the question's verb, said no more than it is: unwritten
    # في البيت رجلٌ كريمٌ: a مبتدأ مؤخر heading its own unit is one as a whole, as on its own
    job_of.update({key: name for key, name in fronted.items() if job_of.get(key) == role_of[key]})
    # كَأَنَّ رَأْسَهُ زَبِيبَةٌ، أَصْبَحَ الْجَوُّ بَارِدًا: the two a sister governs are called after
    # that sister (اسم كأنّ، خبر أصبح), the family's mother (إنّ، كان) only naming the family
    for token, found in zip(bases, named):
        role, at_gov = role_of.get(token["id"]), found.get("governor")
        if not role or at_gov is None or family_of.get(bases[at_gov]["id"]) not in SISTERS:
            continue
        mother, sister = SISTERS[family_of[bases[at_gov]["id"]]], book_spelling(bases[at_gov]["lemma"])
        if role.endswith(f" {mother}") and sister != mother:
            name_of[token["id"]] = f"{role.removesuffix(mother)}{sister}"
            if job_of.get(token["id"]) == role:
                job_of[token["id"]] = name_of[token["id"]]
    # ظننتُ المعلمَ حاضرًا، أعطيتُ زيدًا كتابًا: the verb's two objects are its first and second
    two = FRAMES["two_objects"]
    objects_of: dict[int, list[int]] = {}
    for token, found in zip(bases, named):
        if role_of[token["id"]] == two["role"] and (at_gov := found.get("governor")) is not None:
            verb = bases[at_gov]
            if sentence.family(verb) in two["families"] or any(is_one(verb["lemma"], f) for f in two["families"]):
                objects_of.setdefault(verb["id"], []).append(token["id"])
    for pair in objects_of.values():
        if len(pair) == len(two["names"]):
            name_of.update(zip(sorted(pair), two["names"]))
    place_of: dict[int, str] = {}
    label_of: dict[int, str] = {}
    framed: set[int] = set()  # units whose job a governor gave, drawn even under a particle
    c.family_of, c.framed, c.label_of, c.name_of, c.place_of = family_of, framed, label_of, name_of, place_of
    c.said = said
