"""Names each word's i'raab role from the links the parser drew and the vowels the reader typed
(the only evidence for case and for a passive verb), in the words a nahw book uses.

Reads the tokens `correct` has already corrected; reaches no network or model, so the same
tokens always give the same roles. Scored by `backend/scripts/score_iraab.py`; the numbers are
quoted once, in this package's `__init__.py`.
"""
from __future__ import annotations

from typing import NamedTuple, TypedDict

from backend.services.arabic_text import strip_diacritics
from backend.services.nahw_book import (
    extra_ba_named, extra_ba_on, is_extra_ba, kaffa_sister,
    book_map, book_merges, frames, book_path, case_of, teacher_rules, family_cards, in_family, is_mabni, is_one, needs_praised, doer_written_in, named_roles, role_table, unseen_case)
from backend.services.syntax import condition, facts, walker
from backend.services.syntax.facts import base_tokens  # re-exported: teacher and tree read it from here
from backend.services.harakat import (
    CASE_NAME, SUKUN, build_nun, five_verb_nun, letters, paused, stilled,
    typed_case)

# Every role this module can name, with its card colour key and bracket tone
# (data/nahw_rules/roles.json); a role missing there is left uncoloured.
ROLES = role_table()
NAMED = named_roles()


def _entry(role: str | None) -> tuple:
    # a recorded role is fully vowelled (نَائِبُ فَاعِلٍ); it is the same role
    return ROLES.get(strip_diacritics(role or ""), (None, None))


def role_key(role: str | None) -> str | None:
    """The stable name the word grid colours a card by."""
    return _entry(role)[0]


def roles_keyed(*keys: str) -> tuple[str, ...]:
    """Every role the card colours by one of these keys (`fail` is فاعل and نائب فاعل)."""
    return tuple(role for role in ROLES if role_key(role) in keys)


FOLLOWERS = roles_keyed("tabi", "sifah")
# the governor kinds (facts.AXES) whose families frame a clause as their khabar or object
VERB_FRAMERS = ("inna", "kana", "kaada", "zanna")


def tone(role: str | None) -> str | None:
    """The colour the bracket diagram draws this role in."""
    return _entry(role)[1]


class Piece(TypedDict, total=False):
    """A clitic written onto a typed word (بِـ، ـها), named by the same tree."""
    id: int
    role: str | None
    before: bool  # written before the word (بِـ، وَ) or after it (ـها)
    form: str
    family: str | None
    reading: dict | None
    named: str  # حرف جر زائد: a name a finishing step gave it


class Condition(TypedDict, total=False):
    """A word's part in a شرط (syntax.condition): the opener, its verb, the answer, or لولا's subject."""
    part: str  # opener / verb / answer / subject
    opener: int
    verb: int
    answer: int | None
    tie_at: int
    tie: str | None  # the letter written onto the answer that ties it (ف، ل)
    kind: str | None  # اسم شرط جازم: what a conditional noun is, said before its place
    family: str
    named: str | None  # جواب لولا: the part's own name where the family gives one


class Gap(TypedDict):
    """Why the teacher took a name back, in Arabic and English."""
    ar: str
    en: str


class Doer(TypedDict):
    """The doer drawn inside a verb (syntax.doer): hidden (هو) or written onto it (the تاء)."""
    role: str
    tone: str | None
    detail: str
    pronoun: str
    hidden: bool


class FoundEntry(TypedDict, total=False):
    """One typed word as naming found it; every later step (teacher, tree, cards) reads it.
    `role` and `case` are always there; the rest only when it applies."""
    role: str | None
    case: str | None
    aspect: str | None  # a فعل's tense, from the parser
    printed: str | None  # فعل مجهول: the name a passive verb's card prints
    family: str | None  # كان، إنّ: the family a governing word or particle belongs to
    named: str | None  # a particle reading's own name (ألا الاستفتاحية)
    book: str | None  # the proof line: the tree's branches that named it
    also: str | None  # a second thing the book says (عطف بيان)
    attached: list[Piece]  # pieces written onto it
    governor: int  # index of the word that works its case on it
    follows: int  # index of the word a تابع follows
    condition: Condition  # its part in a شرط
    pair: dict[str, str]  # لا رجلَ: role → the name its governor gives the pair
    extra_ba: str  # u / a: the place's case under a زائدة باء
    by_place: bool  # the case is its place's, not the one its letters show (the teacher skips the typed check)
    kaffa: str  # إنما: the إن sister the كافة ما is on
    gap: Gap  # set by the teacher: the rule a dashed role broke
    name: str  # set from the picture: its finer name (اسم ليس)
    doer: Doer  # set from the picture: the doer drawn inside a verb, said on its card too


def roles(words: list[str], tokens: list[dict]) -> list[FoundEntry]:
    """One {role, case, aspect, book} per typed word, in the order they were typed;
    `book` is the proof line, the tree's branches that named it.

    The parser splits بِ and ـه off as their own tokens; the words a reader types
    are the base words, so only those are named and the vowels are carried over.
    The case is decided here, once: the vowel the reader typed, else the case the
    role itself takes (رأيتُ أخي shows none, yet a مفعول به is منصوب).
    """
    bases = base_tokens(words, tokens)
    if len(bases) != len(words):
        return [{"role": None, "case": None} for _ in words]  # the split does not line up
    s = facts.Sentence(tokens)
    found_answers, governed_by = facts.of_sentence(tokens)
    answers = {t["id"]: a for t, a in zip(tokens, found_answers)}
    # the book's tree has no leaf for some answers: that word stays unnamed
    walked = [walker.walk(answers[token["id"]]) for token in bases]
    named = [found.role if found else None for found in walked]
    # بِـ، ـها: an attached piece is named by the same tree as a typed word
    base_ids = {token["id"] for token in bases}
    attached = {t["id"]: found.role if (found := walker.walk(answers[t["id"]])) else None
                for t in tokens if t["id"] not in base_ids}
    role_by_id = {token["id"]: role for token, role in zip(bases, named)} | attached
    # a particle with a مجرور under it is a حرف جر: the one name, for card and picture
    for t in tokens:
        if t["pos"] == "PRT" and any(role_by_id.get(kid["id"]) == NAMED.majroor
                                     for kid in tokens if kid["head"] == t["id"]):
            role_by_id[t["id"]] = NAMED.harf_jarr
    named = [role_by_id[token["id"]] for token in bases]
    word_of = _typed_word_of(bases, tokens)
    before = [[t["form"].strip("+") for t in tokens if facts.is_prefix(t) and word_of.get(t["id"]) == i]
              for i in range(len(bases))]
    cases = [_ending(role, token, _governor(bases, i), words[i + 1] if i + 1 < len(words) else "",
                     facts.puts_in_jarr(token, s), _lam_mood(token, before[i], i == 0))
             for i, (role, token) in enumerate(zip(named, bases))]
    _followers_take_their_ending(named, cases, bases, tokens)
    # what each word shows: the governor and follower the tree gave it, and its case
    shown = [{answers[token["id"]]["governor"], answers[token["id"]]["follows"], case}
             for token, case in zip(bases, cases)]
    # a piece written onto a تابع joins it, it does not govern it: وَإِيمَانٌ shows عطف first
    joined = [{answers[token["id"]]["follows"]} if answers[token["id"]]["follows"] not in (None, "none") else said
              for token, said in zip(bases, shown)]
    # the parser's tense goes with a فعل, so a card CAMeL took for a noun (ضُرِبَ) still says ماضٍ
    found = [{"role": role, "case": case,
             "aspect": token.get("asp") if role == NAMED.fil else None,
             "printed": frames()["passive"]["verb"] if role == NAMED.fil and facts.is_passive(token) else None,
             "family": _family(token, bases, shown, s=s) if role in (NAMED.fil, NAMED.harf, NAMED.harf_jarr) else None,
             "named": (token.get("reading") or {}).get("named"),
             "book": book_path(found.path, found.book) if found else None,
             # محمدُ بنُ عبدِ اللهِ: the books also read the ابن as عطف بيان or بدل
             "also": book_map("nasab", "also") if role == NAMED.sifah and facts.is_nasab(token)
             else _kind_said(role, token, s, governed_by),
             # إيّاك: the pronoun on إيّا is a letter of the one detached pronoun, not a piece of its own
             "attached": [] if facts.is_object_pronoun(token) else [{"id": t["id"], "role": role_by_id[t["id"]], "before": facts.is_prefix(t), "form": t["form"].strip("+"),
                           "family": _family(t, bases, joined, onto=joined[i]) if role_by_id[t["id"]] in (NAMED.harf, NAMED.harf_jarr) else None,
                           "reading": t.get("reading")}
                          for t in tokens if t["id"] in attached and word_of.get(t["id"]) == i],
             **_governed(i, role, token, bases, tokens, governed_by, word_of, answers[token["id"]])}
            for i, (role, case, token, found) in enumerate(zip(named, cases, bases, walked))]
    for found_condition in condition.find(bases, named, cases, before):
        _conditioned(found, found_condition, bases)
    for step in FINISHES:
        step(Named(found, bases, tokens, s, words))
    return found


class Named(NamedTuple):
    """What a finishing step reads: the entries so far, and the sentence they name."""
    found: list[FoundEntry]
    bases: list[dict]
    tokens: list[dict]
    s: facts.Sentence
    words: list[str]


def _pair(n: Named) -> None:
    """لا رجلَ: the role keeps its id; only the printed name follows the governor."""
    for entry in n.found:
        if (pair := _pair_named(n.bases, entry.get("governor"))) and entry["role"] in pair:
            entry["pair"] = pair


def _kaffa(n: Named) -> None:
    """إنما، كأنما: a particle that is an إن sister with ما written onto it (data: closed_words
    inna `kaffa`) leaves the sister on its entry; card_wording names the pair."""
    for entry, typed in zip(n.found, n.words):
        if entry["role"] == NAMED.harf and (sister := kaffa_sister(strip_diacritics(typed))):
            entry["kaffa"] = sister


def _extra_ba(n: Named) -> None:
    """كفى بالله شهيدًا، ليس الشديد بالصرعة: the باء is زائدة and its word holds the place of the
    verb's doer or khabar (data: closed_words extra_ba). The word keeps its jarr, the case it shows;
    its role is its place, and the reason says both."""
    found, bases, tokens, s = n.found, n.bases, n.tokens, n.s
    index = {token["id"]: i for i, token in enumerate(bases)}
    for i, token in enumerate(bases):
        ba, entry = s.head(token), found[i]
        verb = s.head(ba) if ba else None
        rule = extra_ba_on(strip_diacritics(verb["lemma"])) if verb and verb["id"] in index else None
        if not (rule and entry["role"] == NAMED.majroor and is_extra_ba(ba["form"].strip("+"))
                and ba["rel"] == rule["rel"]):
            continue
        # كفى بالمرء كذبًا أن يحدّث: another doer (a subject, or the masdar أن makes) leaves the باء a plain one
        if rule.get("alone") and any(t["id"] != ba["id"] and t["head"] == verb["id"] and t["rel"] == "SBJ" for t in tokens) \
                or rule.get("alone") and any(t["id"] > token["id"] and strip_diacritics(t["lemma"]) in frames()["masdar"]["words"]
                                             for t in tokens):
            continue
        # by_place: the teacher reads the place's case, not the jarr the letters show
        entry.update(role=rule["role"], governor=index[verb["id"]], extra_ba=rule["place_case"], by_place=True)
        for piece in entry["attached"]:
            if piece["id"] == ba["id"]:
                piece["named"] = extra_ba_named()  # حرف جر زائد



def _kind_said(role: str | None, token: dict, s: facts.Sentence, governed_by: dict[int, int]) -> str | None:
    """Which kind of idafa, badal or فاعل the word is, as the books name it (teacher.json kinds)."""
    kinds = teacher_rules()["kinds"]
    if role == NAMED.mudaf_ilayh and (mudaf := s.by_id.get(governed_by.get(token["id"], -1))):
        if (facts.is_participle(mudaf) or mudaf.get("ud") == "ADJ") and not facts.is_elative(mudaf):
            return kinds["idafa"]["lafziyya"]  # حسنُ الوجهِ: the mudaf stays indefinite; أعلى صوتِه is not, it works on nothing
        bare = strip_diacritics(token["form"]).strip("+").removeprefix("ال")
        if any(is_one(bare, family) or is_one(bare + "ا", family) or facts.listed(token, family) for family in ("zarf_zaman", "zarf_makan")) \
                or bare in kinds["time"]:
            return kinds["idafa"]["fi"]  # مكرُ الليلِ
        bare = strip_diacritics(token["lemma"]).strip("+")
        return kinds["idafa"]["min" if bare in kinds["material"] else "lam"]
    if role == NAMED.fail and s.described_doer and token is s.described_doer[2]:
        return kinds["fail"]["sadda"]  # ما ذاهبٌ المسلمون
    if role == NAMED.badal:
        if said := facts.excepted_after_la(token, s):
            return said[2]["badal"]  # لا إله إلا الله: no بدل كل من كل of the منصوب noun
        pronoun = any(facts.attached_pronoun(k) for k in s.kids(token))
        if not pronoun:
            return kinds["badal"]["kul"]
        bare = strip_diacritics(token["lemma"]).strip("+")
        return kinds["badal"]["baad" if bare in kinds["part"] else "ishtimal"]
    return None


def _pair_named(bases: list[dict], governor: int | None) -> dict[str, str] | None:
    """What a governor of the inna family calls its pair, by its own name (لا: اسم لا، خبر لا),
    from the `pair_named` of its family card (closed_words.json); None for إنّ itself."""
    if governor is None:
        return None
    return next((card["pair_named"] for family, card in family_cards()
                 if "pair_named" in card and facts.read_as(bases[governor], family)), None)


def _conditioned(found: list[dict], c: dict, bases: list[dict]) -> None:
    """A condition the book's test found (syntax.condition): a conditional noun keeps the place
    it was named for (مَنْ يصبرْ: مبتدأ); with none, it takes the book's (_noun_place), never
    the relative the picture would call it; a جازم opener governs both its verbs, rather
    than whatever verb the parser hung them on."""
    frame = c["frame"]
    opener = found[c["opener"]]
    # a time or place word (متى، إذا) is always the ظرف, whatever place it was named for
    if frame["noun"] and (not opener["role"] or opener["role"] == NAMED.harf or frame["adverb"]):
        opener.update(role=_noun_place(frame, c["verb"], found, bases[c["verb"]]), book=None)
    if frame["built"]:
        opener["case"] = "mabni"  # أينما: built, whatever vowel it ends on
    opener["condition"] = {"part": "opener", "verb": c["verb"], "answer": c["answer"], "tie_at": c["tie_at"],
                           "kind": frame["opener"] if frame["noun"] else None}
    if subject := frame.get("subject"):
        # لولا زيدٌ: the noun after it is the مبتدأ, its khabar left out; the answer still answers
        found[c["verb"]].update(role=subject, book=None)
        found[c["verb"]]["condition"] = {"part": "subject", "opener": c["opener"], "family": frame["family"]}
    for part in ("answer",) if subject else ("verb", "answer"):
        if c[part] is None:
            continue
        word = found[c[part]]
        if word["role"] == NAMED.fil:  # a noun sentence or a particle keeps the links it has
            word.pop("follows", None)
            word.pop("governor", None)
            if frame["case"]:
                word["governor"] = c["opener"]
        word["condition"] = {"part": part, "opener": c["opener"], "family": frame["family"],
                             "tie": c["tie"] if part == "answer" else None, "named": frame.get(f"{part}_named")}


def _noun_place(frame: dict, verb: int, found: list[dict], verb_token: dict) -> str:
    """The place of a conditional noun the parser gave none (Tasheel): a time or place word
    (متى، أينما) is a ظرف; مَنْ or ما whose verb already has its object (مَنْ صامَ رمضانَ) is
    the مبتدأ; one before a verb of the first or second person with no object (مَا تَزْرَعْ)
    is that object, the doer being the hidden أنت. Else it is called only what it is: its verb
    may need no object (مبتدأ) or lack the one it stands for (مفعول به), and the parser has not said which."""
    places = frame["places"]
    if frame["adverb"]:
        return places["adverb"]
    if any(word["role"] == places["object"] and word.get("governor") == verb for word in found):
        return places["filled"]
    if verb_token.get("per") in ("1", "2"):
        return places["object"]
    return frame["opener"]


def _typed_word_of(bases: list[dict], tokens: list[dict]) -> dict[int, int]:
    """Token id -> the typed word it sits in: a clitic (بِـ، ـه) belongs to the base word
    it is written onto, a proclitic to the one after it, an enclitic to the one before."""
    base_ids = {t["id"]: i for i, t in enumerate(bases)}
    at, word, pending = {}, 0, []
    for t in tokens:
        if t["id"] in base_ids:
            word = base_ids[t["id"]]
            at.update(dict.fromkeys(pending, word))
            pending = []
        elif facts.is_prefix(t):
            pending.append(t["id"])
            continue
        at[t["id"]] = word
    at.update(dict.fromkeys(pending, word))
    return at


def _governed(i: int, role: str | None, token: dict, bases: list[dict], tokens: list[dict],
              governed_by: dict[int, int], word_of: dict[int, int], answer: dict) -> dict:
    """The typed word this one takes its case from: `follows` for a تابع (the word it copies),
    else `governor` (its عامل); each only when it is another typed word. A verb joined on by
    وَ (قامَ وقَعَدَ) follows the verb before it: the link through وَ is a join, never a governor."""
    joined_verb = role == NAMED.fil and answer["follows"] == "atf"
    if (role in FOLLOWERS or joined_verb) and (head := _followed(token, bases, tokens)) is not None:
        return {"follows": head} if head != i else {}
    # a verb clause stands in a place only by a family that frames it (كنتَ تحبُّ: خبر كان);
    # the verb a parser hangs it on otherwise (جاء مَنْ نجح، قام وقعد) does not govern it
    if role == NAMED.fil and answer["governor"] not in VERB_FRAMERS:
        return {}
    governor = word_of.get(governed_by.get(token["id"]))
    return {"governor": governor} if governor is not None and governor != i else {}


def _followed(token: dict, bases: list[dict], tokens: list[dict]) -> int | None:
    """The typed word a follower follows, reached through the و of a معطوف. A particle is
    climbed past, but not the called أيها, which the parser tags one: يا أيها الناسُ, the
    صفة follows it, not the verb after (facts._follows names it by the same test)."""
    at = {t["id"]: i for i, t in enumerate(bases)}
    by_id = {t["id"]: t for t in tokens}
    head = by_id.get(token["head"])
    while head and (head["id"] not in at or (head["pos"] == "PRT" and not facts.is_called_noun(head))):
        head = by_id.get(head["head"])
    return at[head["id"]] if head else None


def _followers_take_their_ending(named: list, cases: list, bases: list[dict], tokens: list[dict]) -> None:
    """In order, so a chain follows too. A follower with no vowel typed wears the case of the word it follows
    (اليدُ العليا); its kasra on ـات is also nasb, a diptote's fatha also jarr. A present verb showing nothing,
    joined (atf `joins_mood`) to a verb in nasb or jazm, is in that mood too (أَنْ تَبَرُّوا وَتَتَّقُوا); any other is raf'."""
    for i, (role, token) in enumerate(zip(named, bases)):
        head = _followed(token, bases, tokens) if role in FOLLOWERS else None
        if head is not None and cases[head] != "mabni" and (cases[i] is None or (cases[head] == "nasb" and facts.shows_nasb_by_kasra(token))
                                                             or (cases[head] == "jarr" and facts.shows_jarr(token))):
            cases[i] = cases[head]
    by_id = {t["id"]: t for t in tokens}
    for i, (role, token) in enumerate(zip(named, bases)):  # the verbs after every noun, as they were two passes
        if role == NAMED.fil and cases[i] is None:
            joiner = by_id.get(token["head"])
            head = _followed(token, bases, tokens) if joiner and joiner["pos"] == "PRT" and is_one(joiner["lemma"], "atf", "joins_mood") else None
            cases[i] = cases[head] if head is not None and named[head] == NAMED.fil and cases[head] in ("nasb", "jazm") else "raf'"


def _family(token: dict, bases: list[dict], shown: list[set], onto: set | None = None,
            s: facts.Sentence | None = None) -> str | None:
    """The family a particle or verb is named by (كان، إنّ): one whose list holds it and whose effect
    shows on a word linked to it. A listed word that governs nothing here (the لا of a plain negation)
    keeps its plain name, unless particles.stamp read it. A piece written onto a word (وَ، بِـ، لْـ)
    works only on that word (`onto`, what it shows) and the words hung below it."""
    if token.get("reading"):
        return token["reading"]["family"]
    linked = set().union(onto or set(), *(said for other, said in zip(bases, shown)
                         if other["head"] == token["id"] or (onto is None and other["id"] == token["head"])))
    family = next((family for family, card in family_cards()
                   if in_family(token["lemma"], family)
                   # حبذا governs the doer written inside it (ذا), so shows its work on no other word
                   and (card.get("governs") in linked or doer_written_in(token["lemma"], family))), None)
    # سَاءَ الخبرُ زيدًا is a plain verb: ساء blames only with the one blamed after its doer (Ibn Aqil)
    if family and s and needs_praised(token["lemma"], family) \
            and not any(facts.praised_noun(t, s) for t in bases):
        return None
    return family


def opens_with_verb(roles: list[str | None]) -> bool:
    """Verbal unless a مبتدأ (or the اسم of إنّ) comes before the first verb. A particle,
    a fronted adverb or a fronted object leaves it verbal (لم يكتب، متى سافر، القرآنَ قرأ):
    the book judges a sentence by the word it rests on, not the one put first."""
    for role in roles:
        if role == NAMED.fil:
            return True
        if role in (NAMED.mubtada, NAMED.ism_inna, NAMED.khabar):
            return False
    return False


def _governor(bases: list[dict], i: int) -> dict | None:
    """The word before word i that may govern it. A لا straight after a nasb particle is
    the plain negation, which governs nothing: أَنْ لَا تَطُوفِي، لِكَيْ لَا يَعْلَمَ are
    in nasb by the particle before it, not in jazm by a لا of prohibition."""
    before = bases[i - 1] if i else None
    if (before and i > 1 and is_one(before["base"], "negation")
            and is_one(bases[i - 2]["base"], "nasb_mudari", "before_a_present_verb")):
        return bases[i - 2]
    return before


def _lam_mood(token: dict, front: list[str], opens: bool) -> str | None:
    """The mood a لام written onto a present verb gives it: a sukun (فَلْيَصُمْهُ) or opening the sentence
    (لِيُنْفِقْ) is لام الأمر, jazm; a kasra after a clause is لام التعليل, nasb (لِيُضِلُّوا). A fatha or a bare لام settles nothing."""
    if "ل" not in front:
        return None
    marks = letters(token["typed"])[front.index("ل")][1]
    if SUKUN in marks or (opens and "ِ" in marks):
        return "jazm"
    return "nasb" if "ِ" in marks else None


def _ending(role: str | None, token: dict, before: dict | None, after: str, jarred: bool,
            lam: str | None = None) -> str | None:
    """What to print under the word: a case for a noun or a present verb, else mabni.
    A noun's case is the vowel typed on it, else its role's own. A kasra on ـات is nasb when
    its role takes nasb, or it has no role and nothing puts it in jarr, shown by the kasra (رأيت المعلماتِ)."""
    if role == NAMED.fil:
        return "mabni" if is_mabni("verb", token.get("asp", "na"), token["base"]) or (not token.get("stuck_on") and build_nun(token["typed"])) else _mood(paused(token["typed"], after), token, before, lam)
    if role in (NAMED.harf, NAMED.harf_jarr):
        return "mabni"
    # يَا وَلَدُ، يا أيها: a single called noun is built on the damma (in the place of nasb), as is اللهمّ
    if role == NAMED.munada and (typed_case(token["typed"]) == "u" or facts.is_called_noun(token)
                                 or facts.is_called_alone(token)):
        return "mabni"
    # a question word, a demonstrative, a relative or a pronoun never changes its
    # ending, so the vowel on it is part of the word and not a case
    if facts.is_built(token) or facts.is_object_pronoun(token) or facts.is_built_zarf(token):
        return "mabni"
    # وَإِذْ قَالَ: a noun's case never ends on a sukun but at a pause, so one typed mid-sentence is built;
    # a name is never built, so a sukun on one is the reader pausing (أَحْمَدْ جَاءَ)
    marked = letters(token["typed"])
    if (after and not token.get("stuck_on") and marked and SUKUN in marked[-1][1]
            and token.get("pos_camel") != "noun_prop"):
        return "mabni"
    if facts.shows_nasb_by_kasra(token) and (case_of(role, token["mudaf"]) == "a" if role else not jarred):
        return "nasb"
    if facts.shows_jarr(token) and (case_of(role, token["mudaf"]) == "i" if role else jarred):
        return "jarr"  # إِلَى إِبْرَاهِيمَ: a diptote's fatha is its jarr
    return CASE_NAME.get(facts.typed_case_of(token) or case_of(role or "", token["mudaf"]) or unseen_case(role))


def _mood(typed: str, token: dict, before: dict | None, lam: str | None = None) -> str | None:
    """A present verb's case, the governor first (the book's عامل): a particle that
    settles it by itself (لم يكتب، لن يذهب), or one of the shapes only jazm or nasb
    leaves, a weak last letter gone (لم يَدْعُ، لا تَنْسَ) or the five verbs' nun gone
    with a jazm or nasb particle before (لا تَسُبُّوا). Then the ending the reader typed,
    on the verb's own last letter (يُفَقِّهْهُ), else the mood of a لام written onto it
    (_lam_mood), else None: nothing shows, and the verb it is joined to decides, else raf'.
    `typed` is the word as paused on (harakat.paused); `before` the base token before it."""
    particle = before["base"] if before else ""
    dropped_nun = five_verb_nun(typed, token.get("stuck_on", 0), token.get("weak_last")) == "dropped"
    read = (before or {}).get("reading") or {}  # أَلَّا: the nasb أنْ with a لا merged in
    for family, case in (("jazm", "jazm"), ("nasb_mudari", "nasb")):
        if is_one(particle, family, "before_a_present_verb") or (dropped_nun and is_one(particle, family)) \
                or (read.get("family") == family and read.get("named") in {m["named"] for m in book_merges(family).values()}):
            return case
    stuck_on = token.get("stuck_on", 0)
    if stilled(typed, token["base"], stuck_on, token.get("weak_last")):
        return "jazm"
    shown = typed_case(typed, stuck_on)
    return CASE_NAME[shown] if shown in ("u", "a") else lam  # None: nothing shows (_followers_take_their_ending)


# run in this order once every word is named; each adds keys to the entries, never a role to a
# word another step named (the condition's roles come first, above)
def _excepted_after_la(n: Named) -> None:
    """لا اله الا الله typed bare: the بدل follows the hidden pronoun of a khabar no one writes,
    so no typed word lends it its case; it stands in raf', that khabar's (roles.json exception_after_la)."""
    for entry, token in zip(n.found, n.bases):
        if entry["role"] == NAMED.badal and entry["case"] is None and facts.excepted_after_la(token, n.s):
            entry["case"] = CASE_NAME["u"]


FINISHES = (_pair, _extra_ba, _kaffa, _excepted_after_la)
