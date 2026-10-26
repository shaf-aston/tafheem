"""The bracket picture (tarkeeb) for a typed sentence, from the same links.

The cards say what each word is; this says which words join into a unit and what
that unit does. Both come from one reading, so the page can never show a word as
a فاعل in the cards and as something else in the picture.

Shape and wording follow the book examples in `data/tarkeeb/examples`, so a typed
sentence and a book example draw the same way: a unit carries what it **is**
(`label`) and what it **does** (`role`), a leaf carries its role and the index of
its word, and a word no rule could name is left as a gap rather than guessed.
"""
from __future__ import annotations

from backend.services.nahw.book import (book_spelling, card_keys, clause_of, condition_of, family_cards, family_mother, frames, is_one, role_units,
                                       tarkeeb_rules, teacher_rules, term_ar, counted_name)
from backend.services.nahw.syntax.facts import (Sentence, ma_kind, is_preposition, is_participle, asked_verb, is_prefix, completes_kaada, is_masdar, previous_noun,
                                          is_nasab, is_verb, read_as, reading, excepted_after_la, shown_cases, noun_tagged,
                                          NOUN_LINKS, typed_or_parsed_case)
from backend.services.nahw.syntax.naming import FOLLOWERS, NAMED, base_tokens, opens_with_verb, tone
from backend.services.nahw.syntax.doer import DOER, doer as _doer, person_key as _person, persons as _persons
from backend.services.text.arabic_text import bare_letters, strip_diacritics
from backend.services.text.harakat import SHADDA, has_tanween, letters, own_letters

# What a unit is called, by the join that makes it. Spelled once, in
# data/nahw_rules/tarkeeb.json, so a typed sentence, a book example and an ayah
# name the same unit the same way; which role heads which unit is in roles.json.
VERBAL = term_ar("jumlah_filiyyah")
NOMINAL = term_ar("jumlah_ismiyyah")
QUESTION = term_ar("jumlah_istifhamiyyah")
CONDITION = term_ar("jumlah_shartiyyah")
FRAMES = frames()
CARDS = dict(family_cards())
JAR_MAJROOR = term_ar("jar_majroor")
FOLLOWED = NAMED.matboo  # the word any تابع follows


def names_a_sentence(label: str | None) -> bool:
    """The label is a kind of sentence (جملة فعلية، جملة تعجب...), not a phrase's name: a
    مركب توصيفي shows itself in the picture and needs no line above it."""
    return label in {VERBAL, NOMINAL, QUESTION, CONDITION, term_ar("jumlah_nidaiyyah"), *map(term_ar, FRAMES["sentence_by_family"].values())}


def _leaf(index: int, role: str | None, why: dict | None = None, name: str | None = None) -> dict:
    """One word on its own. No role means the rules could not name it; `why` is the
    teacher's reason when a rule took the name away, shown on hover. `name` is the
    finer name the picture prints (حرف نصب for a حرف), coloured as its role."""
    leaf = {"word": index, "role": name or role, "tone": tone(role or name), "gap": not (role or name)}
    if role is None and why:
        leaf["detail"] = f"{why['ar']} · {why['en']}"
    return leaf


def _label(head: dict, child_roles: list[str], kids: list[dict] = ()) -> str | None:
    """What the unit this word heads is called. None: it has no name of its own, as a name
    with its ابن (محمدُ بنُ عبدِ اللهِ), whose ابن the books read as صفة, عطف بيان or بدل."""
    if any(is_nasab(kid) for kid in kids):
        return None
    for unit in role_units():
        if unit["child"] in child_roles and (head["pos"] == "PRT" or not unit.get("on_particle")):
            return term_ar(unit["label"])
    return ""


def _unit_role(role: str | None, child_roles: list[str]) -> str | None:
    """What the head word is called inside its own unit.

    On its own it is a مبتدأ; inside كِتَابُ الطَّالِبِ it is the مضاف and the
    unit as a whole is the مبتدأ, which is how the books draw it.
    """
    for unit in role_units():  # غَيْرَ زيدٍ keeps its مستثنى, as its card says
        if unit["child"] in child_roles and "head_as" in unit:
            return role if role in unit.get("head_keeps", ()) else unit["head_as"]
    return role


# the family whose sisters lend their own name to what they govern, by its mother's word
SISTERS = {family: family_mother(family) for family in ("inna", "kana", "kaada")}
# the roles that stay inside the unit their head names (a صفة of the مضاف إليه, a عطف on it)
def _quieted(node: dict) -> dict:
    """مفعول به, not مفعول به / مركب إضافي: a unit wearing a job leaves off the name of what it
    is made of (roles.json units `quiet_under_job`); one with no job keeps it."""
    label = "" if node.get("role") and node.get("label") in QUIET_UNDER_JOB else node.get("label")
    return {**node, **({"label": label} if "label" in node else {}),
            **({"children": [_quieted(kid) for kid in node["children"]]} if node.get("children") else {})}


QUIET_UNDER_JOB = {term_ar(unit["label"]) for unit in role_units() if unit.get("quiet_under_job")}
UNIT_CHILDREN = {unit["child"] for unit in role_units()} | set(FOLLOWERS) | {card_keys().atf}


def _finer(token: dict, role: str | None, family: str | None) -> str | None:
    """A governor's name in the picture: كان is a فعل ناقص, أنْ a حرف نصب, as its card says;
    a particle read one way of several (particles.stamp) by that reading's name."""
    if family in FRAMES["leaf_by_family"] and role != NAMED.harf:
        card = CARDS.get(family, {})
        named = card.get("named_as", {}).get(book_spelling(token["form"]), card.get("named"))
        return FRAMES["leaf_by_family"][family].format(named=named)
    if role == NAMED.harf and (reading := token.get("reading")):
        card = CARDS.get(reading["family"], {})
        word = strip_diacritics(token["form"]).strip("+")
        return reading["named"] or card.get("chart") or card.get("chart_as", {}).get(word) or card.get("named_as", {}).get(
            word, card.get("named", role))
    if family is None and role == NAMED.harf and is_prefix(token) and is_one(token["form"], "atf"):
        family = "atf"  # وَمَنْ شاء: a وَ written onto a new sentence is named by its letters, as its card is
    card = CARDS.get(family) or {}
    word = strip_diacritics(token["form"]).strip("+")
    if word in card.get("chart_as", {}):
        return card["chart_as"][word]  # لْـ: the chart's لام الأمر, the card's حرف جزم، لام الأمر
    named = card and card.get("named_as", {}).get(word, card["named"])
    # only a finer name for the same role (حرف نصب for حرف), so card and picture still agree
    return named if role in (NAMED.harf, NAMED.harf_jarr) and named and named.startswith(role) else role


def _command_name(token: dict, drawn: list[dict], family_of: dict) -> str | None:
    """A verb that gives an order says so: اكتبْ is a فعل أمر, and a present verb the jazm
    particle before it makes a command or a prohibition (لِيَكتبْ، لا تأكلْ) is named for it."""
    if token.get("asp") == "c":
        return FRAMES["command"]["verb"]
    for before in drawn:
        # the particle on the verb, or (أَوْ لِيَصْمُتْ) the one the parser hung the verb on
        on_it = before["head"] == token["id"] and before["id"] < token["id"]
        if (on_it or token["head"] == before["id"] == token["id"] - 1) and family_of[before["id"]] == "jazm":
            return CARDS["jazm"].get("verb_as", {}).get(strip_diacritics(before["form"]).strip("+"))
    return None


def _sentence_label(roles: dict[int, str | None], tokens: list[dict], named: list[dict]) -> str:
    # مَنْ شاء فليصمه، لو كنتُ ... لأمرتُ: a condition opens it (syntax.condition)
    if named and named[0].get("condition", {}).get("part") == "opener":
        return CONDITION
    if wonder := next((FRAMES["sentence_by_family"][reading(t)] for t in tokens if reading(t) in FRAMES["sentence_by_family"]), None):
        return term_ar(wonder)  # ما أحسن زيدًا
    if any("interrog" in t.get("pos_camel", "") for t in tokens):
        return QUESTION
    return VERBAL if opens_with_verb([roles[t["id"]] for t in tokens]) else NOMINAL


def build(words: list[str], tokens: list[dict], named: list[dict]) -> dict:
    """The tree for one typed sentence, ready for the diagram.

    `named` is what `naming.roles` returned, one entry per typed word.
    """
    bases = base_tokens(words, tokens)
    if not words or len(bases) != len(words) or len(named) != len(words):
        return {"words": words, "tree": {"gap": True}, "coverage": 0.0}

    # بِـ، وَ، ـهُ: written onto a word, yet each a word of its own in the books, so each is
    # drawn in its own column and joins the way a word typed apart does (لِمَنْ is a
    # جار ومجرور); only a verb keeps what is written after it, its doer and object, inside it
    split = {piece["id"]: piece for found in named for piece in found.get("attached", [])
             if piece["before"] or found["role"] != NAMED.fil}
    by_id = {t["id"]: t for t in tokens}
    drawn, columns, written = [], [], []  # written: the typed word each column was cut from
    for i, (word, token, found) in enumerate(zip(words, bases, named)):
        before = [by_id[p["id"]] for p in found.get("attached", []) if p["id"] in split and p["before"]]
        after = [by_id[p["id"]] for p in found.get("attached", []) if p["id"] in split and not p["before"]]
        sizes = [len(bare_letters(t["form"].strip("+"))) for t in before + after]
        spans = sizes[:len(before)] + [len(letters(word)) - sum(sizes)] + sizes[len(before):]
        drawn += before + [token] + after
        columns += [own_letters(word, sum(spans[:k]), sum(spans[k + 1:])) for k in range(len(spans))]
        written += [i] * len(spans)
    typed_at = {token["id"]: index for index, token in enumerate(bases)}
    role_of = {token["id"]: found["role"] for token, found in zip(bases, named)} | {
        key: piece["role"] for key, piece in split.items()}
    why_of = {token["id"]: found.get("gap") for token, found in zip(bases, named)}
    # جاء الأميرُ والجيشَ: the مفعول معه and its و hang on the verb, not inside the فاعل
    for token, found in zip(bases, named):
        if role_of[token["id"]] in FRAMES["on_the_verb"] and (at_gov := found.get("governor")) is not None:
            waw = by_id.get(token["head"])
            moved = waw if waw and is_prefix(waw) else token
            moved = {**moved, "head": bases[at_gov]["id"]}
            drawn[[t["id"] for t in drawn].index(moved["id"])], by_id[moved["id"]] = moved, moved
    # جاء الولدُ وهو يبكي: the parser can hang the مبتدأ under the verb after it; the verb's sentence
    # is the مبتدأ's khabar, so the verb hangs on the مبتدأ and the مبتدأ where the verb hung
    for verb in [t for t in drawn if is_verb(t)]:
        subject = next((t for t in drawn if t["head"] == verb["id"] and t["id"] < verb["id"]
                        and role_of.get(t["id"]) == NAMED.mubtada), None)
        for moved in ({**subject, "head": verb["head"]}, {**verb, "head": subject["id"]}) if subject else ():
            drawn[[t["id"] for t in drawn].index(moved["id"])], by_id[moved["id"]] = moved, moved
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
        # the books write مبتدأ، خبر (ثابت)، ق (ثابت) side by side, so the khabar sits beside
        # the unit; a subject the unit headed (the لِ of الحمدُ لله) comes out beside them too
        # قال الضيفُ سلامٌ عليكم: a subject a verb hangs as its object heads the sentence it says,
        # so the unit and the khabar stay inside it, not beside it among the verb's own words
        inside = subject["rel"] == "OBJ" and subject["head"] in by_id and is_verb(by_id[subject["head"]])
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
    for token in list(drawn):
        if role_of.get(token["id"]) == NAMED.badal and (hit := excepted_after_la(token, sentence)):
            noun, illa, entry = hit
            understand(entry["khabar"], after_la["khabar_named"], [t["id"] for t in drawn].index(illa["id"]),
                       head=noun["head"], rel="PRD", pos="NOM", pos_camel="")
    said_verb = kept["verb"]
    saying = FRAMES["said_clause"]
    unsaid_objects: set[int] = set()  # nouns that are the object of a verb no one writes
    replies: set[int] = set()  # the unwritten verbs that answer a question
    detail_of: dict[int, str] = {}

    def hang_on_unsaid_verb(noun: dict, text: str, **place) -> dict:
        """The noun (with the words that follow it) is the object of a verb no one writes."""
        verb = understand(text, NAMED.fil, drawn.index(noun), pos="VRB", pos_camel="", base=text, asp="na", **place)
        # شكرًا: the unwritten verb's own masdar; الصِّدْقَ الصِّدْقَ: one with ال urged on the
        # hearer is the object of an unwritten الزم (الإغراء, Tasheel 3.8.1)
        masdar = is_masdar(noun) and not strip_diacritics(noun["form"]).startswith("ال")
        role_of[noun["id"]] = said_verb["noun"]["masdar" if masdar else "other"]
        why_of[noun["id"]] = None  # the dash was for a case no job fitted; now one does
        under = {**noun, "head": verb["id"]}
        drawn[drawn.index(noun)], by_id[noun["id"]] = under, under
        unsaid_objects.add(noun["id"])
        return verb

    # أهلًا وسهلًا، شكرًا لك: a منصوب noun that heads its own sentence, named by no word, is the
    # object of a verb no one writes, beside the noun it governs. Alone, its nasb shows as
    # tanween, or as the case of the words that follow it (الصلواتِ الخمسَ): a fatha with none
    # (نِعْمَ، أَجْمَلَ) is a verb's
    for noun in [t for t in drawn if t["id"] in typed_at and role_of[t["id"]] is None
                 and t["head"] not in by_id and t["pos"] == "NOM" and "a" in shown_cases(t)
                 and (has_tanween(t.get("typed")) or any(role_of[k["id"]] in FOLLOWERS for k in drawn if k["head"] == t["id"]))]:
        hang_on_unsaid_verb(noun, said_verb["word"], head=0, rel="---")
    # ماذا فرض الله ... فقال الصلواتِ: after a question for an object, the noun a verb of saying
    # hangs is the answer, the object of the question's verb, which is drawn as an unwritten word
    asked = asked_verb(sentence)
    for noun in [t for t in drawn if asked and t["id"] > asked["id"] and t["id"] not in unsaid_objects and role_of[t["id"]] == said_verb["noun"]["other"]
                 and t["id"] in typed_at and noun_tagged(t) and "a" in shown_cases(t)
                 and role_of.get(t["head"]) == NAMED.fil
                 and strip_diacritics(by_id[t["head"]]["lemma"]) in saying["verbs"]]:
        text = columns[next(i for i, t in enumerate(drawn) if t["id"] == asked["id"])]
        verb = hang_on_unsaid_verb(noun, text, head=noun["head"], rel="OBJ")
        replies.add(verb["id"])
        detail_of[noun["id"]] = said_verb["reply"]["detail"].format(verb=text)
    at = {token["id"]: index for index, token in enumerate(drawn)}
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
    # الولدُ يكتبُ: the clause hung on a مبتدأ (or اسم كان) is its khabar, standing in a case;
    # كان الولدُ يكتبُ: so is the one beside it, the khabar (PRD) under their governor
    said = teacher_rules()["case_said"]
    family_of = {token["id"]: found.get("family") for token, found in zip(bases, named)} | {
        key: piece["family"] for key, piece in split.items()} | dict.fromkeys(understood)
    printed_of = {token["id"]: found["printed"] for token, found in zip(bases, named) if found.get("printed")}
    name_of = {token["id"]: _finer(token, role_of[token["id"]], family_of[token["id"]]) for token in drawn}
    for token in drawn:
        if name_of[token["id"]] == NAMED.fil:
            name_of[token["id"]] = _command_name(token, drawn, family_of) or printed_of.get(token["id"]) or NAMED.fil
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

    def in_place(case: str) -> str:
        return said["in_place"].format(place=said["place"][case])

    for token in drawn:
        owners = [t for t in drawn if t["id"] == token["head"] or (
            token["rel"] == "PRD" and t["head"] == token["head"] and t["id"] != token["id"])]
        # كنتَ تحبُّ: the clause on كان's PRD is its khabar, with no اسم كان word to hang it on
        clause = next((found for t in owners if (found := clause_of(role_of.get(t["id"])) or (
            (by := FRAMES["clause_by_family"].get(family_of[t["id"]])) and token["rel"] == by["rel"] and by))), None)
        if clause and token["id"] in opens:
            job_of[token["id"]] = clause["job"]
            place_of[token["id"]] = in_place(clause["case"])
    # تحب أن تطوّق: أنْ and the verb hung on it are one masdar, doing the job أنْ hangs by
    # (the parser's أنّ takes a noun, so a verb on it is the nasb أنْ whatever the card guessed)
    for token in drawn:
        # أكلتُ ما طبختَ: the relative ما does the job of the place it stands in
        if (kind_of_ma.get(token["id"]) == "relative" and (placed := job_by_place(token))
                and role_of[token["id"]] not in masdar["job_by_rel"].values()):
            job_of[token["id"]], place_of[token["id"]] = placed[0], in_place(placed[1])
            ma_card[token["id"]] = placed
    for token in drawn:
        word = strip_diacritics(token["form"])
        if (word in masdar["words"] and SHADDA not in token["form"] and (placed := job_by_place(token))
                and kind_of_ma.get(token["id"], "masdar") == "masdar"
                and any(t["head"] == token["id"] and role_of[t["id"]] == NAMED.fil for t in drawn)):
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
    after_waw = FRAMES["clause_after_waw"]
    for token in drawn:
        waw = by_id.get(token["head"])
        if token["id"] in nominal and token["id"] not in place_of and waw and waw["pos"] == "PRT" and is_prefix(waw) \
                and strip_diacritics(waw["form"]).strip("+") == "و" and (verb := by_id.get(waw["head"])) and is_verb(verb):
            job_of[token["id"]], place_of[token["id"]] = after_waw["job"], in_place(after_waw["case"])
            name_of[waw["id"]] = after_waw["waw"]
            framed.add(token["id"])
    # يَحْمِلُ حَقِيبَةً after رَجُلًا, كَأَنَّ رَأْسَهُ زَبِيبَةٌ after حَبَشِيٌّ, يَرْكُضُ after جَاءَ الطَّالِبُ
    after_noun = FRAMES["clause_after_noun"]
    for token in drawn:
        head = by_id.get(token["head"])
        if (token["rel"] != "MOD" or not head or token["id"] in place_of or token["id"] < head["id"]
                or job_of[token["id"]] not in (None, NAMED.fil, NAMED.harf)
                or not (is_verb(token) or family_of[token["id"]] == "inna")):
            continue
        if not noun_tagged(head):  # on the verb: the noun it describes is the verb's, just before it
            head = next((t for t in reversed(drawn) if t["head"] == head["id"] and t["id"] < token["id"]
                         and noun_tagged(t) and t["rel"] in NOUN_LINKS), None)
            if not head or not definite(head):
                continue
        known, case = definite(head), typed_or_parsed_case(head)
        if not known and (head.get("stt") != "i" or not case):  # مَا، مَتَى: no case shown, nothing to describe
            continue
        job_of[token["id"]] = after_noun["definite" if known else "indefinite"]
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
                and strip_diacritics(verb["lemma"]) in saying["verbs"]:
            job_of[token["id"]] = saying["job"]
            place_of[token["id"]] = in_place(saying["case"])
            framed.add(token["id"])
    children_of: dict[int, list[dict]] = {token["id"]: [] for token in drawn}

    def depth(token: dict) -> int:
        steps, head = 0, token["head"]
        while head in by_id and steps < len(tokens):
            steps, head = steps + 1, by_id[head]["head"]
        return steps

    def parent(token: dict) -> int:
        # an attached و or بِ is not a word the reader typed apart, so a word hung
        # on one hangs on whatever that particle hung on
        head = token["head"]
        for _ in tokens:
            if head in children_of or head not in by_id:
                break
            head = by_id[head]["head"]
        return head

    unit_less = {t["id"] for t in drawn if reading(t) in FRAMES["unit_less"]}
    roots = []
    for token in drawn:
        up = parent(token)
        while up in unit_less:  # واللهُ أكبرُ: the و stands beside its sentence, heading nothing
            up = parent(by_id[up])
        # رِزْقُ اللَّهِ عَزَّ وَجَلَّ: a حال tells the state of its صاحب, it is no part of that noun, so it
        # stands beside it in the unit the noun stands in, not inside the noun's own box; nor inside
        # the jar-majroor of a مجرور صاحب (مَرَرْتُ بِزَيْدٍ رَاكِبًا: beside it, on the verb)
        if job_of[token["id"]] == NAMED.haal and up in by_id and noun_tagged(by_id[up]) and not is_verb(by_id[up]):
            detail_of[token["id"]] = after_noun["owner"].format(word=columns[at[up]])
            up = parent(by_id[up])
            while up in by_id and is_preposition(by_id[up]):
                up = parent(by_id[up])
        if up in children_of and up != token["id"]:
            children_of[up].append(token)
        else:
            roots.append(token)
    roots = roots or [drawn[0]]
    # هذا بيتٌ كبيرٌ: the مبتدأ is said of the whole khabar unit, not of its head word,
    # so it is drawn beside that unit under the sentence rather than inside it; so it is
    # beside the khabar a حال of it stands beside (هذا زيدٌ قائمًا: مبتدأ، خبر، حال)
    top = roots[0]
    subjects = [kid for kid in children_of[top["id"]] if role_of[kid["id"]] == NAMED.mubtada]
    beside_hal = len(roots) > 1 and all(job_of[t["id"]] == NAMED.haal for t in roots[1:])
    if (len(roots) == 1 or beside_hal) and role_of[top["id"]] == NAMED.khabar and 0 < len(subjects) < len(children_of[top["id"]]) + beside_hal:
        children_of[top["id"]] = [kid for kid in children_of[top["id"]] if kid not in subjects]
        roots = subjects + roots
    # هل أنتَ تكتبُ، ما أنتَ إلا بشر، مَنْ أنتَ في المدينة: a unit typed wholly before or after the unit it
    # hangs in, with a word of another unit between them, cannot sit inside that unit and keep the
    # order typed, so it goes up to the unit above until no such word stands between
    for unit_head in drawn:
        span = [at[t["id"]] for t in drawn if t is unit_head or _inside(t, unit_head, children_of)]
        while home := next((t for t in drawn if unit_head in children_of[t["id"]]), None):
            near = at[home["id"]]
            low, high = (max(span), near) if near > max(span) else (near, min(span))
            if low >= high or not any(low < at[other["id"]] < high and not _inside(other, home, children_of)
                                      for other in drawn):
                break
            children_of[home["id"]].remove(unit_head)
            above = next((t for t in drawn if home in children_of[t["id"]]), None)
            (children_of[above["id"]] if above else roots).append(unit_head)
    # مَنْ شاء فليصمه: the opener, the condition's clause and the answer's side by side in
    # one unit, as the books draw it, wherever the parser hung them (syntax.condition)
    holder = {kid["id"]: kids for kids in (roots, *children_of.values()) for kid in kids}
    opened: dict[int, tuple[dict, ...]] = {}  # answer id -> (opener, condition verb, tie letters)
    for i, found in enumerate(named):
        if found.get("condition", {}).get("part") != "opener" or found["condition"]["answer"] is None:
            continue
        condition = condition_of(bases[i]["form"])
        opener, verb, answer = (bases[i], bases[found["condition"]["verb"]], bases[found["condition"]["answer"]])
        if not condition["noun"]:
            name_of[opener["id"]] = condition["opener"]  # إن: حرف شرط جازم; a noun keeps its place
        # فَلْيَصُمْهُ، لأمرتُ: the letter written onto the answer ties it to the condition, so it
        # stands beside the answer's sentence in the condition's unit, not inside that sentence
        ties = []
        for piece in named[found["condition"]["tie_at"]].get("attached", []):
            if piece["id"] in split and piece["before"] and piece["form"] in condition["ties"]:
                name_of[piece["id"]] = condition["ties"][piece["form"]]
                tied = by_id[piece["id"]]
                for under in list(children_of[tied["id"]]):  # a فَ the parser made the head of its clause: the clause takes its place
                    _move(holder, under, holder[tied["id"]])
                ties.append(_take(holder, tied))
        verb_case, answer_case = condition.get("verb_case"), condition["case"] if ties else None
        # لولا زيدٌ: the noun is a مبتدأ, no فعل الشرط; the answer is جواب لولا
        verb_job = None if condition.get("subject") else condition["verb"]
        for unit, job, case in ((verb, verb_job, verb_case), (answer, condition.get("answer_named") or condition["answer"], answer_case)):
            job_of[unit["id"]] = job
            place_of[unit["id"]] = in_place(case) if case else said["no_place"]
            clauses.add(unit["id"])
            framed.add(unit["id"])
        # أينما تكونوا يدرككم: an answer hung nowhere, or under the opener or its verb (which
        # leave their places just below), stands beside them at the top
        if answer["id"] not in holder or any(_inside(answer, unit, children_of) for unit in (opener, verb)):
            holder.setdefault(answer["id"], [answer])
            _move(holder, answer, roots)
        for unit in (opener, verb):
            _take(holder, unit)
            del holder[unit["id"]]
        opened[answer["id"]] = (opener, verb, *ties)
    # مَنْ شاء فليصمه ومَن شاء أفطر: a condition has the front of its sentence, so the وَ
    # bringing a second one joins it beside the first, not inside the first one's answer
    for answer_id in opened:
        up = next((t for t in drawn if any(kid["id"] == answer_id for kid in children_of[t["id"]])
                   and t["pos"] == "PRT"), None)
        outer = next((a for a in opened if up and _inside(up, by_id[a], children_of)), None)
        if up and outer is not None and up["id"] in holder:
            _move(holder, up, holder[outer])
    # وَمَنْ يُشْرِكْ: a particle typed before the opener, which the parser hung on the answer, comes
    # before the whole condition, so it stands at the front of the condition's unit, not in the answer
    for answer_id, (opener, *_) in opened.items():
        for kid in [k for k in children_of[answer_id] if k["pos"] == "PRT" and at[k["id"]] < at[opener["id"]]]:
            opened[answer_id] += (_take(holder, kid),)
    root = roots[0]

    seen: set[int] = set()

    # every verb no typed word is the doer of, outermost first, so a khabar's pronoun can
    # go back to its subject: the اسم كان inside كنتَ, or the مبتدأ above يكتبُ
    persons_of: dict[int, list[str]] = {}
    subjects = {NAMED.mubtada, NAMED.ism_inna, *DOER["explicit"]}
    for token in sorted(drawn, key=lambda t: depth(t)):
        if role_of[token["id"]] != NAMED.fil or any(
                role_of[kid["id"]] in DOER["explicit"] for kid in drawn if kid["head"] == token["id"]):
            continue
        up = by_id.get(token["head"])
        nouns = [t for t in drawn if role_of[t["id"]] in subjects and t["id"] != token["id"] and (
            t["id"] == token["head"] or (token["rel"] == "PRD" and t["head"] == token["head"]))]
        owner = [_person({"per": "3", **{k: v for k, v in nouns[0].items() if v not in (None, "na")}})] if nouns else (
            persons_of.get(up["id"]) if up and token["rel"] == "PRD" else None)
        if owner is None and any(_inside(token, by_id[reply], children_of) for reply in replies):
            owner = [DOER["reply_to"]]  # the answer is said to the one who asked
        persons_of[token["id"]] = _persons(token, owner)

    doer_of: dict[int, dict] = {}  # the doer drawn inside each typed verb, said on its card too

    def said_of(token: dict) -> str | None:
        """What the books say of a unit beyond its job: its place (في محل نصب), then whose it is (حال من «الله»)."""
        return " ".join(filter(None, (place_of.get(token["id"]), detail_of.get(token["id"])))) or None

    def pieces(token: dict, leaf: dict) -> dict:
        """The leaf with what is written after a verb (ـها) and its doer, in the order
        the books say them: the verb, its doer, then the pronoun on it."""
        found = named[typed_at[token["id"]]] if token["id"] in typed_at else {}
        leaf = {**leaf, "hidden": True} if token["id"] in understood else leaf
        attached = [{"role": _finer(piece, piece["role"], piece["family"]), "tone": tone(piece["role"]),
                     "gap": piece["role"] is None}
                    for piece in found.get("attached", []) if piece["id"] not in split]
        doer = _doer(token, family_of[token["id"]], persons_of[token["id"]]) if token["id"] in persons_of else None
        if doer and token["id"] in typed_at:
            doer_of[token["id"]] = doer
        if not attached and not doer:
            return leaf
        own = {key: leaf[key] for key in ("role", "tone", "gap", "detail") if key in leaf}
        return {**leaf, "parts": [own] + ([doer] if doer else []) + attached}

    def kind_of(token: dict) -> str:
        """A unit with no name of its own is still a sentence when its head opens one,
        wherever it hangs (وَأَطِيعُوا، وَإِنَّ كَيْدَ الشَّيْطَانِ كَانَ ضَعِيفًا، وَإِنِ اسْتُعْمِلَ):
        a verb a verbal one, a particle of إنّ's family a nominal one, a condition's
        opener a condition."""
        found = named[typed_at[token["id"]]] if token["id"] in typed_at else {}
        if found.get("condition", {}).get("part") == "opener":
            return CONDITION
        if is_verb(token):
            return VERBAL
        if family_of[token["id"]] == "inna":
            return NOMINAL
        # وَأَطِيعُوا hung on its وَ: the joined sentence is what the وَ brings; a condition's answer is
        # drawn in the condition's own unit (وَمَنْ شَاءَ أَفْطَرَ), so the وَ beside it names nothing
        if token["pos"] == "PRT":
            return next((kind for kid in children_of[token["id"]] if kid["id"] not in opened and (kind := kind_of(kid))), "")
        return ""

    def node(token: dict) -> dict:
        # the parser can hand back two words pointing at each other; a word already
        # drawn is left as a leaf rather than followed round the circle again
        seen.add(token["id"])
        kids = [kid for kid in children_of[token["id"]] if kid["id"] not in seen]
        index = at[token["id"]]
        if not kids:
            leaf = pieces(token, _leaf(index, role_of[token["id"]], why_of.get(token["id"]), name_of[token["id"]]))
            # a صلة of one verb is still a clause, its doer the pronoun hidden in it; a khabar
            # whose مبتدأ is drawn beside it is a word (هذا زيدٌ قائمًا)
            if token["id"] in clauses - nominal:
                return {"role": job_of[token["id"]], "label": VERBAL, "tone": tone(job_of[token["id"]]) or leaf["tone"],
                        "detail": said_of(token), "children": [leaf]}
            return {"detail": detail_of[token["id"]], **leaf} if token["id"] in detail_of else leaf
        kid_roles = [job_of[kid["id"]] for kid in kids if job_of[kid["id"]]]
        if token is root and role_of[token["id"]] and token["id"] not in opened and (own := _label(token, kid_roles, kids)) and not names_a_sentence(own):
            # كِتَابُ الطَّالِبِ جَدِيدٌ: the مضاف heads its unit, but the خبر hangs outside it;
            # the sentence holds both, the unit as a whole is the مبتدأ
            if beside := [kid for kid in kids if job_of[kid["id"]] not in UNIT_CHILDREN]:
                children_of[token["id"]] = [kid for kid in kids if kid not in beside]
                seen.discard(token["id"])
                whole = {**node(token), "role": role_of[token["id"]], "tone": tone(role_of[token["id"]])}
                seen.update(kid["id"] for kid in beside)
                inside = [(index, whole), *((at[kid["id"]], unit(kid)) for kid in beside)]
                return {"role": None, "label": top_label, "tone": None, "detail": None,
                        "children": [drawn for _, drawn in sorted(inside, key=lambda pair: pair[0])]}
        seen.update(kid["id"] for kid in kids)
        inside = [(at[kid["id"]], unit(kid)) for kid in kids]
        role = role_of[token["id"]]
        why = why_of.get(token["id"])
        # a word the teacher dashed stays a dash at the head of its unit: مضاف would name it
        own = _label(token, kid_roles, kids)
        # a name with its ابن is the متبوع: موصوف or مبدل منه would pick one of the three readings
        head_name = FOLLOWED if own is None else _unit_role(name_of[token["id"]], kid_roles)
        inside.append((index, pieces(token, _leaf(index, role, why, None if why else head_name))))
        # الطالبُ مجتهدٌ في المدرسة: a خبر whose مبتدأ is drawn beside it is a word with its
        # jar-majroor, not a sentence
        lone_khabar = role == NAMED.khabar and token["id"] in nominal and not any(
            role_of[kid["id"]] == NAMED.mubtada for kid in kids)
        label = label_of.get(token["id"]) or ("" if own is None or lone_khabar else own or (
            top_label if token is root and token["id"] not in opened
            else NOMINAL if token["id"] in clauses & nominal
            else VERBAL if token["id"] in clauses or role == NAMED.fil else kind_of(token)))
        # A particle's name is what it is, not a job for the unit it heads: the
        # parser gives no job for a jar-majroor or a clause under إِذَا, so none
        # is written rather than calling the whole unit a حرف. The clause a كاد-type
        # verb is finished by is that verb's khabar as a whole.
        job = NAMED.khabar_kaada if completes_kaada(token, sentence) else (
            job_of[token["id"]] if token["id"] in framed
            else None if token is root or token["pos"] == "PRT" or job_of[token["id"]] == NAMED.fil
            else job_of[token["id"]])
        # مِن نارٍ: a jar-majroor with a word to hang on is named by it, متعلق بـX
        if token["id"] in hung:
            label = FRAMES["attached"].format(word=kept["word"])
        elif label == JAR_MAJROOR and (up := parent(token)) in at:
            # فِي سَنَةٍ أَوْ فِي ثَلَاثِ سِنِينَ: hung on a حرف عطف, it is معطوف on the jar-majroor that
            # حرف follows, and hangs where that one hangs (the معطوف follows its معطوف عليه)
            while is_one(by_id[up]["form"], "atf") and is_preposition(followed := by_id.get(parent(by_id[up]), {})) \
                    and parent(followed) in at:
                job, up = NAMED.matoof, parent(followed)
            label = FRAMES["attached"].format(word=columns[at[up]])
        return {"role": job,
                "label": label,
                "tone": tone(job) or tone(role),
                "detail": said_of(token),
                # right to left, so the picture reads in the order they were typed
                "children": [drawn for _, drawn in sorted(inside, key=lambda pair: pair[0])]}

    # the parser can leave a sentence as two loose halves; they are still one
    # sentence, so they are drawn side by side under it rather than one dropped
    def unit(token: dict) -> dict:
        """A word's node, or for a condition's answer the whole condition around it."""
        if token["id"] not in opened:
            return node(token)
        beside = opened[token["id"]]
        seen.update(t["id"] for t in beside)
        inside = [(at[t["id"]], node(t)) for t in (*beside, token)]
        return {"role": None, "label": CONDITION, "tone": None, "detail": None,
                "children": [drawn for _, drawn in sorted(inside, key=lambda pair: pair[0])]}

    top_label = _sentence_label(role_of, drawn, named)
    drawn = sorted(((at[part["id"]], unit(part)) for part in roots), key=lambda pair: pair[0])
    tree = drawn[0][1] if len(drawn) == 1 else None
    # a phrase alone (محمد بن عبد الله): its head has no job, nothing makes it a sentence
    phrase = tree is not None and tree.get("word") is None and not role_of[roots[0]["id"]]
    if not phrase and (tree is None or tree.get("word") is not None or not tree.get("label")):
        tree = {"label": top_label,
                "children": [part for _, part in drawn] if tree is None else [tree]}
    tree = _quieted(_unbracket(tree))
    covered = sum(1 for found in named if found["role"])
    return {"words": columns, "written": written, "tree": tree, "coverage": round(covered / len(words), 2),
            "unsaid": [role_of[token["id"]] if token["id"] in unsaid_objects else None for token in bases],  # the job on the card too
            # the picture's finer name (حرف ناسخ, فعل أمر, فعل مجهول) where it says more than the role
            "finer": [name_of.get(token["id"]) if name_of.get(token["id"]) != role_of[token["id"]] else None for token in bases],
            # the doer no typed word is (هو hidden in يكتبُ, the تاء of كتبتُ): the card says it as the picture draws it
            "doer": [doer_of.get(token["id"]) for token in bases],
            # ما read by its عائد (facts.ma_kind): the relative's job and case, or (None, None) for ما المصدرية
            "ma": [ma_card.get(token["id"]) for token in bases],
            **({"unwritten": {"mark": columns[written.index(-1)], "note": tarkeeb_rules()["treebank"]["unwritten_note"]}} if understood else {})}


def _unbracket(node: dict) -> dict:
    """A brace with no name and no job says nothing (وَ with its معطوف, the books name
    neither the pair nor the unit), so its words are drawn under the brace above it."""
    if node.get("word") is not None or "children" not in node:
        return node
    children = []
    for kid in map(_unbracket, node["children"]):
        bare = kid.get("word") is None and "children" in kid and not kid.get("label") and not kid.get("role")
        children.extend(kid["children"] if bare else [kid])
    return {**node, "children": children}


def definite(token: dict) -> bool:
    """ال, a مضاف, a name or a pronoun stuck on it makes a noun known."""
    return token.get("stt") in ("d", "c") or token["pos"] == "PROP" or bool(token.get("stuck_on"))


def _move(holder: dict[int, list[dict]], token: dict, to: list[dict]) -> None:
    """Hang a word in another unit: off the list that holds it, onto `to`."""
    to.append(_take(holder, token))
    holder[token["id"]] = to


def _take(holder: dict[int, list[dict]], token: dict) -> dict:
    """Off the list that holds it, by its id: the picture's own token, which may carry more
    than the one asked with (6:139's answer هم did, and a list.remove of it failed)."""
    kids = holder[token["id"]]
    return kids.pop(next(i for i, kid in enumerate(kids) if kid["id"] == token["id"]))


def _inside(token: dict, top: dict, children_of: dict[int, list[dict]]) -> bool:
    """Whether a word hangs anywhere under `top`."""
    below = list(children_of[top["id"]])
    while below:
        kid = below.pop()
        if kid["id"] == token["id"]:
            return True
        below += children_of[kid["id"]]
    return False


def is_drawable(tree: dict) -> bool:
    """False when nothing could be joined, so the page shows the cards alone."""
    return bool(tree.get("tree", {}).get("children")) and tree.get("coverage", 0) > 0
