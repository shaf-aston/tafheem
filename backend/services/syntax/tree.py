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

from backend.services.nahw_book import (clause_of, condition_of, family_cards, frames, is_one, named_roles, role_units,
                                       tarkeeb_rules, teacher_rules, term_ar)
from backend.services.syntax.facts import (Sentence, completes_kaada, is_masdar, is_passive, previous_noun, read_as,
                                          shown_cases)
from backend.services.syntax.naming import base_tokens, opens_with_verb, tone
from backend.services.arabic_text import bare_letters, strip_diacritics
from backend.services.harakat import SHADDA, has_tanween, letters, own_letters

# What a unit is called, by the join that makes it. Spelled once, in
# data/nahw_rules/tarkeeb.json, so a typed sentence, a book example and an ayah
# name the same unit the same way; which role heads which unit is in roles.json.
VERBAL = term_ar("jumlah_filiyyah")
NOMINAL = term_ar("jumlah_ismiyyah")
QUESTION = term_ar("jumlah_istifhamiyyah")
CONDITION = term_ar("jumlah_shartiyyah")
NAMED = named_roles()
FRAMES = frames()
CARDS = dict(family_cards())
JAR_MAJROOR = term_ar("jar_majroor")


def _leaf(index: int, role: str | None, why: dict | None = None, name: str | None = None) -> dict:
    """One word on its own. No role means the rules could not name it; `why` is the
    teacher's reason when a rule took the name away, shown on hover. `name` is the
    finer name the picture prints (حرف نصب for a حرف), coloured as its role."""
    leaf = {"word": index, "role": name or role, "tone": tone(role), "gap": role is None}
    if role is None and why:
        leaf["detail"] = f"{why['ar']} · {why['en']}"
    return leaf


def _label(head: dict, child_roles: list[str]) -> str:
    """What the unit this word heads is called."""
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


DOER = FRAMES["doer"]


def _person(token: dict) -> str:
    """CAMeL's person, gender and number as one key of DOER["pronoun"] (2ms, 1s)."""
    per = token.get("per", "na")
    return per + ("" if per == "1" else token.get("gen", "na")) + token.get("num", "na")


def _persons(token: dict, owner: list[str] | None) -> list[str]:
    """Who a verb's doer may be: one person, or the two its letters allow (تكتبُ is you
    or she) narrowed by the subject its pronoun goes back to (`owner`)."""
    if token.get("asp") == "c" and token.get("per") != "2":
        return [DOER["command"]]  # a command speaks to the listener, whatever the reading said
    letter = strip_diacritics(token["base"])[:1]
    if token.get("asp") == "i" and letter in DOER["prefix_says"]:
        return [DOER["prefix_says"][letter]]
    if token.get("asp") == "i" and token.get("per", "na") not in DOER["prefix_person"].get(letter, token.get("per", "na")):
        return []  # the reading's person is not one its letter allows
    if token.get("asp") == "i" and token.get("num") == "s" and letter == "ت":
        both = DOER["ta_prefix"]
        # the subject's person settles it: a ت said of a third person is هي (هِنْدٌ تَكْتُبُ)
        return [key for key in both if key[0] in {o[0] for o in owner or []}] or both
    return [_person(token)]


def _doer(token: dict, family: str | None, persons: list[str]) -> dict | None:
    """The doer inside a verb no typed word stands as (اقبلْ: أنت, كنتَ: the تاء);
    None when the person is not known."""
    pronouns = [DOER["pronoun"].get(key) for key in persons]
    if token.get("asp") not in DOER["hidden"] or not pronouns or not all(pronouns):
        return None
    name = DOER["by_family"].get(family) or DOER["passive" if is_passive(token) else "active"]
    said = DOER["hidden_said" if persons[0] in DOER["hidden"][token["asp"]] else "attached_said"]
    pronoun = pronouns[0] if len(pronouns) == 1 else DOER["either"].format(one=pronouns[0], other=pronouns[1])
    return {"role": name, "tone": tone(name), "detail": said.format(pronoun=pronoun)}


def _finer(token: dict, role: str | None, family: str | None) -> str | None:
    """A governor's name in the picture: كان is a فعل ناقص, أنْ a حرف نصب, as its card says;
    a particle read one way of several (particles.stamp) by that reading's name."""
    if family in FRAMES["leaf_by_family"]:
        return FRAMES["leaf_by_family"][family]
    if role == NAMED.harf and (reading := token.get("reading")):
        card = CARDS.get(reading["family"], {})
        return reading["named"] or card.get("chart") or card.get("named_as", {}).get(
            strip_diacritics(token["form"]).strip("+"), card.get("named", role))
    if family is None and role == NAMED.harf and token["form"].endswith("+") and is_one(strip_diacritics(token["form"]), "atf"):
        family = "atf"  # وَمَنْ شاء: a وَ written onto a new sentence is named by its letters, as its card is
    card = CARDS.get(family) or {}
    word = strip_diacritics(token["form"]).strip("+")
    if word in card.get("chart_as", {}):
        return card["chart_as"][word]  # لْـ: the chart's لام الأمر, the card's حرف جزم، لام الأمر
    named = card and card.get("named_as", {}).get(word, card["named"])
    # only a finer name for the same role (حرف نصب for حرف), so card and picture still agree
    return named if role in (NAMED.harf, NAMED.harf_jarr) and named and named.startswith(role) else role


def _read(token: dict) -> str | None:
    """The family particles.stamp read the word as, if it read it."""
    return (token.get("reading") or {}).get("family")


def _sentence_label(roles: dict[int, str | None], tokens: list[dict], named: list[dict]) -> str:
    # مَنْ شاء فليصمه، لو كنتُ ... لأمرتُ: a condition opens it (syntax.condition)
    if named and named[0].get("condition", {}).get("part") == "opener":
        return CONDITION
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
    # الحمدُ لله، زيدٌ في الدار: a jar-majroor or ظرف in the khabar slot hangs on a word no one
    # writes (ثابت), which is the khabar. It takes the column before the unit; `written` -1,
    # -2.. is the column of no typed word, a number of its own so it joins no word's run.
    # A relative pronoun is no مبتدأ (ما في القبور is a صلة).
    kept = FRAMES["understood"]
    understood: set[int] = set()
    hung: set[int] = set()
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
        if subject["head"] == held["id"]:
            new = {**subject, "head": held["head"]}
            drawn[drawn.index(subject)], by_id[subject["id"]] = new, new
        place = next(i for i, t in enumerate(drawn) if t["id"] == held["id"])
        understand(kept["word"], kept["khabar_of"][role_of[subject["id"]]], place, head=held["head"],
                   rel="PRD", pos="NOM", pos_camel="")
        hung.add(held["id"])
    # أهلًا وسهلًا، شكرًا لك: a منصوب noun that heads its own sentence, named by no word, is the
    # object of a verb no one writes, beside the noun it governs. Alone, its nasb shows as
    # tanween: a fatha with none (نِعْمَ، أَجْمَلَ) is a verb's
    said_verb = kept["verb"]
    for noun in [t for t in drawn if t["id"] in typed_at and role_of[t["id"]] is None
                 and t["head"] not in by_id and t["pos"] == "NOM" and shown_cases(t) == {"a"}
                 and has_tanween(t.get("typed"))]:
        verb = understand(said_verb["word"], NAMED.fil, drawn.index(noun), head=0, rel="---", pos="VRB",
                          pos_camel="", base=said_verb["word"], asp="na")
        role_of[noun["id"]] = said_verb["noun"]["masdar" if is_masdar(noun) else "other"]
        why_of[noun["id"]] = None  # the dash was for a case no job fitted; now one does
        under = {**noun, "head": verb["id"]}
        drawn[drawn.index(noun)], by_id[noun["id"]] = under, under
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
    # جاء الذي نجح: the clause after a relative is its صلة, with no place of its own
    for token in drawn:
        up = next((t for t in drawn if t["id"] == token["head"]), None)
        if up and "rel" in up.get("pos_camel", "") and up["id"] < token["id"] and token["id"] in opens                 and "condition" not in named[typed_at.get(up["id"], 0)]:
            job_of[token["id"]] = NAMED.silah
    # الولدُ يكتبُ: the clause hung on a مبتدأ (or اسم كان) is its khabar, standing in a case;
    # كان الولدُ يكتبُ: so is the one beside it, the khabar (PRD) under their governor
    said = teacher_rules()["case_said"]
    family_of = {token["id"]: found.get("family") for token, found in zip(bases, named)} | {
        key: piece["family"] for key, piece in split.items()} | dict.fromkeys(understood)
    name_of = {token["id"]: _finer(token, role_of[token["id"]], family_of[token["id"]]) for token in drawn}
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
    masdar = FRAMES["masdar"]
    sentence = Sentence(tokens)
    for token in drawn:
        if (strip_diacritics(token["form"]) in masdar["words"] and SHADDA not in token["form"]
                and token["rel"] in masdar["job_by_rel"]
                and any(t["head"] == token["id"] and role_of[t["id"]] == NAMED.fil for t in drawn)):
            name_of[token["id"]] = CARDS[masdar["family"]]["named"]
            label_of[token["id"]] = masdar["label"]
            job_of[token["id"]] = masdar["job_by_rel"][token["rel"]]
            place_of[token["id"]] = in_place(masdar["case_by_rel"][token["rel"]])
            # إلا أنْ تتطوعَ after a noun: an action is not of the group the noun names, so a منقطع
            excepting = by_id.get(token["head"])
            for family, after in masdar["after_family"].items():
                if excepting and read_as(excepting, family) and previous_noun(excepting, sentence):
                    job_of[token["id"]] = after["job"]
                    place_of[token["id"]] = in_place(after["case"])
            framed.add(token["id"])
    # اللهُ أكبرُ inside a longer sentence: a مبتدأ with its خبر hung on it is a sentence too,
    # and so is لا النافية للجنس with its noun
    nominal |= {token["id"] for token in drawn if token["head"] in by_id and (
        _read(token) == "la_jins" or (role_of[token["id"]] == NAMED.mubtada and any(
            t["head"] == token["id"] and role_of[t["id"]] == NAMED.khabar for t in drawn)))}
    clauses = {token["id"] for token in drawn if job_of[token["id"]] == NAMED.silah} | set(place_of) | nominal
    for token in drawn:
        if _read(token) in FRAMES["unit_by_family"]:
            label_of[token["id"]] = term_ar(FRAMES["unit_by_family"][_read(token)])
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

    unit_less = {t["id"] for t in drawn if _read(t) in FRAMES["unit_less"]}
    roots = []
    for token in drawn:
        up = parent(token)
        while up in unit_less:  # واللهُ أكبرُ: the و stands beside its sentence, heading nothing
            up = parent(by_id[up])
        if up in children_of and up != token["id"]:
            children_of[up].append(token)
        else:
            roots.append(token)
    roots = roots or [drawn[0]]
    # هذا بيتٌ كبيرٌ: the مبتدأ is said of the whole khabar unit, not of its head word,
    # so it is drawn beside that unit under the sentence rather than inside it
    top = roots[0]
    subjects = [kid for kid in children_of[top["id"]] if role_of[kid["id"]] == NAMED.mubtada]
    if len(roots) == 1 and role_of[top["id"]] == NAMED.khabar and 0 < len(subjects) < len(children_of[top["id"]]):
        children_of[top["id"]] = [kid for kid in children_of[top["id"]] if kid not in subjects]
        roots = subjects + roots
    # مَنْ شاء فليصمه: the opener, the condition's clause and the answer's side by side in
    # one unit, as the books draw it, wherever the parser hung them (syntax.condition)
    holder = {kid["id"]: kids for kids in (roots, *children_of.values()) for kid in kids}
    opened: dict[int, tuple[dict, ...]] = {}  # answer id -> (opener, condition verb, tie letters)
    for i, found in enumerate(named):
        if found.get("condition", {}).get("part") != "opener" or found["condition"]["answer"] is None:
            continue
        condition = condition_of(strip_diacritics(bases[i]["form"]))
        opener, verb, answer = (bases[i], bases[found["condition"]["verb"]], bases[found["condition"]["answer"]])
        if not condition["noun"]:
            name_of[opener["id"]] = condition["opener"]  # إن: حرف شرط جازم; a noun keeps its place
        # فَلْيَصُمْهُ، لأمرتُ: the letter written onto the answer ties it to the condition, so it
        # stands beside the answer's sentence in the condition's unit, not inside that sentence
        ties = []
        for piece in named[typed_at[answer["id"]]].get("attached", []):
            if piece["id"] in split and piece["before"] and piece["form"] in condition["ties"]:
                name_of[piece["id"]] = condition["ties"][piece["form"]]
                holder[piece["id"]].remove(by_id[piece["id"]])
                ties.append(by_id[piece["id"]])
        for unit, job in ((verb, condition["verb"]), (answer, condition["answer"])):
            job_of[unit["id"]] = job
            place_of[unit["id"]] = in_place(condition["case"]) if condition["case"] else said["no_place"]
            clauses.add(unit["id"])
            framed.add(unit["id"])
        # أينما تكونوا يدرككم: an answer hung nowhere, or under the opener or its verb (which
        # leave their places just below), stands beside them at the top
        if answer["id"] not in holder or any(_inside(answer, unit, children_of) for unit in (opener, verb)):
            holder.setdefault(answer["id"], [answer])
            _move(holder, answer, roots)
        for unit in (opener, verb):
            holder[unit["id"]].remove(unit)
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
        persons_of[token["id"]] = _persons(token, owner)

    def pieces(token: dict, leaf: dict) -> dict:
        """The leaf with what is written after a verb (ـها) and its doer, in the order
        the books say them: the verb, its doer, then the pronoun on it."""
        found = named[typed_at[token["id"]]] if token["id"] in typed_at else {}
        leaf = {**leaf, "hidden": True} if token["id"] in understood else leaf
        attached = [{"role": _finer(piece, piece["role"], piece["family"]), "tone": tone(piece["role"]),
                     "gap": piece["role"] is None}
                    for piece in found.get("attached", []) if piece["id"] not in split]
        doer = _doer(token, family_of[token["id"]], persons_of[token["id"]]) if token["id"] in persons_of else None
        if not attached and not doer:
            return leaf
        own = {key: leaf[key] for key in ("role", "tone", "gap", "detail") if key in leaf}
        return {**leaf, "parts": [own] + ([doer] if doer else []) + attached}

    printed: dict[int, str | None] = {}  # what each word's own leaf is called

    def node(token: dict) -> dict:
        # the parser can hand back two words pointing at each other; a word already
        # drawn is left as a leaf rather than followed round the circle again
        seen.add(token["id"])
        kids = [kid for kid in children_of[token["id"]] if kid["id"] not in seen]
        index = at[token["id"]]
        if not kids:
            leaf = pieces(token, _leaf(index, role_of[token["id"]], why_of.get(token["id"]), name_of[token["id"]]))
            printed[token["id"]] = leaf["role"]
            # a صلة of one verb is still a clause, its doer the pronoun hidden in it
            return {"role": job_of[token["id"]], "label": VERBAL, "tone": tone(job_of[token["id"]]) or leaf["tone"],
                    "detail": place_of.get(token["id"]), "children": [leaf]} if token["id"] in clauses else leaf
        kid_roles = [job_of[kid["id"]] for kid in kids if job_of[kid["id"]]]
        seen.update(kid["id"] for kid in kids)
        inside = [(at[kid["id"]], unit(kid)) for kid in kids]
        role = role_of[token["id"]]
        why = why_of.get(token["id"])
        # a word the teacher dashed stays a dash at the head of its unit: مضاف would name it
        inside.append((index, pieces(token, _leaf(index, role, why, None if why else _unit_role(name_of[token["id"]], kid_roles)))))
        printed[token["id"]] = inside[-1][1]["role"]
        label = label_of.get(token["id"]) or _label(token, kid_roles) or (top_label if token is root and token["id"] not in opened
                                             else NOMINAL if token["id"] in clauses & nominal
                                             else VERBAL if token["id"] in clauses or role == NAMED.fil else "")
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
            label = FRAMES["attached"].format(word=columns[at[up]])
        return {"role": job,
                "label": label,
                "tone": tone(job) or tone(role),
                "detail": place_of.get(token["id"]),
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
    if tree is None or tree.get("word") is not None or not tree.get("label"):
        tree = {"label": top_label,
                "children": [part for _, part in drawn] if tree is None else [tree]}
    covered = sum(1 for found in named if found["role"])
    return {"words": columns, "written": written, "tree": tree, "coverage": round(covered / len(words), 2),
            "printed": [printed.get(token["id"]) for token in bases],
            **({"unwritten": {"mark": columns[written.index(-1)], "note": tarkeeb_rules()["treebank"]["unwritten_note"]}} if understood else {})}


def _move(holder: dict[int, list[dict]], token: dict, to: list[dict]) -> None:
    """Hang a word in another unit: off the list that holds it, onto `to`."""
    holder[token["id"]].remove(token)
    to.append(token)
    holder[token["id"]] = to


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
