"""What a unit is called: the vocabulary and naming helpers of the bracket picture."""
from __future__ import annotations

from backend.services.nahw.book import (
    book_spelling,
    card_keys,
    family_cards,
    family_mother,
    frames,
    is_one,
    role_units,
    term_ar,
)
from backend.services.nahw.syntax.facts import is_nasab, is_particle, is_prefix, reading
from backend.services.nahw.syntax.followers import FOLLOWERS
from backend.services.nahw.syntax.naming import NAMED, opens_with_verb, tone
from backend.services.text.arabic_text import strip_diacritics

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


def word_leaf(index: int, role: str | None, why: dict | None = None, name: str | None = None) -> dict:
    """One word on its own. No role means the rules could not name it; `why` is the
    teacher's reason when a rule took the name away, shown on hover. `name` is the
    finer name the picture prints (حرف نصب for a حرف), coloured as its role."""
    leaf = {"word": index, "role": name or role, "tone": tone(role or name), "gap": not (role or name)}
    if role is None and why:
        leaf["detail"] = f"{why['ar']} · {why['en']}"
    return leaf


def unit_label(head: dict, child_roles: list[str], kids: list[dict] = ()) -> str | None:
    """What the unit this word heads is called. None: it has no name of its own, as a name
    with its ابن (محمدُ بنُ عبدِ اللهِ), whose ابن the books read as صفة, عطف بيان or بدل."""
    if any(is_nasab(kid) for kid in kids):
        return None
    for unit in role_units():
        if unit["child"] in child_roles and (head["pos"] == "PRT" or not unit.get("on_particle")):
            return term_ar(unit["label"])
    return ""


def unit_role(head: dict, role: str | None, child_roles: list[str]) -> str | None:
    """What the head word is called inside its own unit.

    On its own it is a مبتدأ; inside كِتَابُ الطَّالِبِ it is the مضاف and the
    unit as a whole is the مبتدأ, which is how the books draw it.
    """
    for unit in role_units():  # غَيْرَ زيدٍ keeps its مستثنى, as its card says; a particle (إلا) is no noun to be renamed
        if unit["child"] in child_roles and "head_as" in unit and not is_particle(head):
            return role if role in unit.get("head_keeps", ()) else unit["head_as"]
    return role

# the family whose sisters lend their own name to what they govern, by its mother's word
SISTERS = {family: family_mother(family) for family in ("inna", "kana", "kaada")}

QUIET_UNDER_JOB = {term_ar(unit["label"]) for unit in role_units() if unit.get("quiet_under_job")}

ATF = card_keys().atf

UNIT_CHILDREN = {unit["child"] for unit in role_units()} | set(FOLLOWERS) | {ATF}


def finer_name(token: dict, role: str | None, family: str | None) -> str | None:
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


def command_name(token: dict, drawn: list[dict], family_of: dict) -> str | None:
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


def sentence_label(roles: dict[int, str | None], tokens: list[dict], named: list[dict]) -> str:
    # مَنْ شاء فليصمه، لو كنتُ ... لأمرتُ: a condition opens it (syntax.condition)
    if named and named[0].get("condition", {}).get("part") == "opener":
        return CONDITION
    if wonder := next((FRAMES["sentence_by_family"][reading(t)] for t in tokens if reading(t) in FRAMES["sentence_by_family"]), None):
        return term_ar(wonder)  # ما أحسن زيدًا
    if any("interrog" in t.get("pos_camel", "") for t in tokens):
        return QUESTION
    return VERBAL if opens_with_verb([roles[t["id"]] for t in tokens]) else NOMINAL
