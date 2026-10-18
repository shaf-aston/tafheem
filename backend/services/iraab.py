"""A typed sentence's i'raab, by the book's rules alone (no AI, no network).

1. CAMeL reads each word (morphology).
2. An ayah the Quranic Treebank recorded is read from that record (tarkeeb_store);
   anything else goes to the parser and the book's tree (syntax), which alone name
   each word's job and its case. A word the tree leaves unnamed stays a gap.
3. Each card is built once (cards): what the word is (rule_engine), the tree's name
   on it, then its sign. The summary is the picture's top label, so the cards, the
   line above them and the picture all come from one reading.

The Analyse page and the practice questions both read sentences through here.
"""
from __future__ import annotations

from backend.services.arabic_text import strip_diacritics, words
from backend.services import morphology, provenance, quran_corpus, rule_engine, signs, syntax, tarkeeb_store, tree_columns
from backend.services.harakat import CASE_NAME, typed_case
from backend.services.nahw_book import book_map, book_words, case_of, family_cards, is_object_stem, reason, teacher_rules
from backend.services.syntax import teacher
from backend.services.syntax.tree import names_a_sentence as names_a_sentence
from backend.services.syntax.naming import NAMED, role_key


def analyze(sentence: str, recorded: bool = True) -> dict:
    """{words, summary, source, tree} for one sentence; `tree` is None when nothing joins.
    `recorded=False` skips the treebank and always works the sentence out. The summary is the picture's own top label, so the line above the cards and the
    picture can never name the sentence apart; with no picture, or a phrase (محمد بن عبد الله), there is none."""
    picks = morphology.pick(words(sentence), syntax.disambiguator())  # the one reading, cards and parser alike
    tags = morphology.analyze_sentence(sentence, picks)
    record = tarkeeb_store.for_sentence(sentence) if recorded else None
    parsed = record or syntax.read(sentence, picks)
    tree = _drawn(record) if record else parsed["tree"]
    return {
        "words": cards(tags, parsed["roles"]),
        "summary": label if tree and names_a_sentence(label := tree["tree"].get("label")) else None,
        "source": provenance.of("treebank" if record else "nahw"),
        "tree": tree,
        "parse": parsed.get("parse"),
        "read_failed": bool(parsed.get("failed")),
    }


def ayah_tree(surah: int, ayah: int) -> dict:
    """An ayah the treebank has no record of, read as a typed sentence is: one engine,
    one set of rules, so an ayah and the same words typed are named alike."""
    text = dict(quran_corpus.ayah_texts(surah)).get(ayah)
    if not text:
        return {"words": [], "tree": None, "coverage": 0.0}
    drawn = syntax.read(text, morphology.pick(words(text), syntax.disambiguator()))["tree"]
    return drawn or {"words": words(text), "tree": None, "coverage": 0.0}


def _drawn(recorded: dict) -> dict:
    """The recorded tree, in the shape the page draws a typed sentence's in."""
    keep = ("surah", "ayah", "words", "tree", "coverage", "unwritten")
    return {**tree_columns.cut({key: recorded[key] for key in keep}), "source": provenance.of("treebank")}


def cards(tags: list[dict], roles: list[dict]) -> list[dict]:
    """One card per word, built once: what the word is (rule_engine), the job the book's
    tree names on it, then its sign from the final case (signs.settle). A word the tree
    left unnamed keeps the no-role dash; a name the teacher took back shows why."""
    entries = rule_engine.cards(tags)
    if len(roles) == len(entries):
        for entry, found, after in zip(entries, roles, roles[1:] + [{}]):
            if _my_ya(entry, found, after):
                entry["camel"] = {**entry["camel"], "enclitic": "1s_poss"}
            if found.get("gap"):
                entry.update(role=rule_engine.UNNAMED, role_key=None, case=found["case"], sign=None, gap=True,
                             reason=found["gap"]["ar"], notes=found["gap"]["en"])
            elif found["role"]:
                _named(entry, found, after.get("role") == NAMED.mudaf_ilayh)
            elif found["case"] and entry["type"] not in ("fi'l", "harf", "damir", "punc"):
                entry["case"] = found["case"]  # no name yet: the vowel the reader typed, not CAMeL's guess
    words = signs.settle(entries)
    if len(roles) != len(words):
        return words
    for word, found in zip(words, roles):
        if word.get("role") in found.get("pair", {}):  # لا رجلَ: its governor names the pair, after the sign is settled
            word["role"] = found["pair"][word["role"]]
            word["reason"] = reason(word["role"])
    for word, found in zip(words, roles):
        if found.get("printed") and word.get("role") == NAMED.fil:
            word["role"] = found["printed"]  # أُمِرْتُ: فعل مجهول; its reason already says مبني للمجهول
    for word, found in zip(words, roles):
        # اسم ليس: the reason names the sister the picture names, not the family's mother (لأنه اسم كان)
        if (name := found.get("name")) and word.get("role") and name.split()[0] == word["role"].split()[0]:
            word["reason"] = (word.get("reason") or "").replace(f"لأنه {word['role']}", f"لأنه {name}", 1)
    for word in words:  # غير، سوى: the excepted noun is the tool itself, and says so, not إلا's rule
        if teacher.tool_reason(word):
            word["reason"] = teacher.tool_reason(word)
    for word, found in zip(words, roles):
        if found.get("also") and word.get("reason"):
            word["reason"] = f"{word['reason']}، {found['also']}"
    _pieces_said(words, roles)
    _extra_ba_said(words, roles)
    _kaffa_said(words)
    _counted(words)
    _followed(words)
    return rule_engine.mark_condition(words, roles)


def _counted(cards: list[dict]) -> None:
    """Objects or khabars side by side, with no و between: the books count them
    (ظننتُ الامتحانَ سهلًا: مفعول به أول، مفعول به ثانٍ؛ إن الله غفور رحيم: خبر ثانٍ؛ a third is ثالث)."""
    ordinals = teacher_rules()["case_said"]["ordinals"]
    run = 0  # how many of this role came straight before
    for before, card in zip(cards, cards[1:]):
        role = card.get("role")
        if not role or role != before.get("role") or not (role == "مفعول به" or role.startswith("خبر")):
            run = 0
            continue
        run += 1
        said = f"لأنه {role}"

        def count(nth: str) -> str:  # خبر إن → خبر ثانٍ لإن، مفعول به → مفعول به ثانٍ
            return f"لأنه خبر {nth} ل{role[4:]}" if role.startswith("خبر ") else f"{said} {nth}"
        def bare(reason: str) -> bool:  # said, and not already counted (ظنّ names its own أول and ثانٍ)
            return said in reason and not any(f"{said} {nth}" in reason for nth in ordinals)
        if run == 1 and bare(before.get("reason", "")):
            before["reason"] = before["reason"].replace(said, count(ordinals[0]), 1)
        if bare(card.get("reason", "")):
            card["reason"] = card["reason"].replace(said, count(ordinals[min(run, len(ordinals) - 1)]), 1)


def _followed(cards: list[dict]) -> None:
    """A follower names the word it follows (تابع لـ«زيدٌ»). Every معطوف of a chain is joined on
    its first word, the معطوف عليه, which says it is one; several on one word are counted
    (جاء زيدٌ وعمرٌو وبكرٌ: وعمرٌو معطوف أول على زيد، وبكرٌ معطوف ثانٍ)."""
    said = teacher_rules()["case_said"]
    atf = NAMED.matoof

    def root(i: int) -> int:
        seen = {i}
        while cards[i].get("role") == atf and isinstance(at := cards[i].get("follows"), int) \
                and 0 <= at < len(cards) and at not in seen:
            seen.add(i := at)
        return i

    joined: dict[int, list[int]] = {}
    for i, card in enumerate(cards):
        if card.get("role") == atf and isinstance(card.get("follows"), int):
            joined.setdefault(root(i), []).append(i)
    for i, card in enumerate(cards):
        at = card.get("follows")
        if not isinstance(at, int) or not 0 <= at < len(cards) or not card.get("reason"):
            continue
        on = root(i) if card.get("role") == atf else at
        card["reason"] = card["reason"].replace(said["before"], said["followed"].format(word=cards[on]["word"]), 1)
        if card.get("role") == atf and len(joined.get(on, [])) > 1:
            nth = said["ordinals"][min(joined[on].index(i), len(said["ordinals"]) - 1)]
            card["reason"] = card["reason"].replace(f"لأنه {atf}", f"لأنه {atf} {nth}", 1)
    for on in joined:
        if cards[on].get("reason") and said["joined_on"] not in cards[on]["reason"]:
            first, dot, rule = cards[on]["reason"].partition(". ")
            cards[on]["reason"] = f"{first}، {said['joined_on']}{dot}{rule}"


def _pieces_said(cards: list[dict], roles: list[dict]) -> None:
    """A piece written onto the word that its family card says on the word's own card first
    (وَاللهُ: الواو حرف عطف، ويجوز أن تكون استئنافية), where the picture names it short."""
    said = dict(family_cards())
    for card, found in zip(cards, roles):
        for piece in found.get("attached", []):
            line = said.get((piece.get("reading") or {}).get("family"), {}).get("said")
            if line:
                card["reason"] = f"{line}، {card['reason']}"


def _kaffa_said(cards: list[dict]) -> None:
    """إنما الأعمال بالنيات: an إن-family word with ما written onto it works on nothing, and the
    card names the pair (data: closed_words inna `kaffa`)."""
    kaffa = book_map("inna", "kaffa")
    for card in cards:
        bare = strip_diacritics(card.get("word") or "")
        if card.get("role") == NAMED.harf and bare.endswith(kaffa["ma"]) and bare[:-len(kaffa["ma"])] in book_words("inna"):
            card["name"] = kaffa["named"]
            card["reason"] = kaffa["said"].format(word=card["word"], bare=bare[:-len(kaffa["ma"])])


def _extra_ba_said(cards: list[dict], roles: list[dict]) -> None:
    """كفى بالله شهيدًا: the card says the باء is زائدة, and the word is مجرور in its letters and
    in its place's case (data: closed_words extra_ba), before the rule its place follows."""
    for card, found in zip(cards, roles):
        if not (place := found.get("extra_ba")):
            continue
        said = book_map("extra_ba", "said").format(place=book_map("extra_ba", "place_said")[place])
        rule = card.get("reason", "").partition(". ")[2]
        card.update(case="jarr", reason=f"الباء {book_map('extra_ba', 'named')}، {said} لأنه {card.get('name') or card['role']}"
                    + (f". {rule}" if rule else ""))


def _my_ya(entry: dict, found: dict, after: dict) -> bool:
    """لِأَبِي: the parser split off "my" that CAMeL left on the word, so the kasra
    belongs to the ya and the six nouns' letter is no sign here. Not in أَبِي الطَّبِيبِ,
    where a noun in jarr after it can be its مضاف إليه and the ي the six nouns' sign."""
    idafa_next = after.get("role") == NAMED.mudaf_ilayh or (after.get("case") == "jarr" and not after.get("role"))
    return (any(not piece["before"] and piece["form"] == "ي" for piece in found.get("attached", []))
            and entry.get("camel", {}).get("enclitic") in (None, "", "0") and not idafa_next)


def _named(entry: dict, found: dict, annexed: bool) -> None:
    """One card takes the tree's name; the case is naming's (syntax.naming._ending)."""
    renamed = found["role"] != entry.get("role")
    # a recorded ayah names its words vowelled (فِعْلٌ، بَدَلٌ): the rules read the bare name
    plain = strip_diacritics(found["role"])
    if plain != found["role"]:
        if not found["case"] and plain != NAMED.fil and entry.get("type") in ("harf", "fi'l") \
                and not is_object_stem(entry["word"].lstrip("وَفَ")) \
                and (typed := typed_case(entry["word"])):
            found = {**found, "case": CASE_NAME[typed]}  # رَبِّ read by CAMeL as a particle: the kasra typed is its case
    entry.update(role=found["role"], book=found.get("book"), role_key=role_key(plain),
                 family=found.get("family"),  # كان، إنّ: named by what they govern (signs.settle)
                 named=found.get("named"),  # أَلَا: a reading's own name, where the family card's does not fit
                 name=found.get("name"),  # the picture's finer name (حرف ناسخ، فعل أمر), said on the card too
                 governor=found.get("governor"), follows=found.get("follows"))
    if plain != NAMED.fil and entry.get("type") == "fi'l":  # نَعْبُدُ keeps CAMeL's tense and mood
        # لَسِحْرًا: CAMeL's verb is the parser's noun, so the verb's case goes with it
        entry.update(type="harf" if plain in (NAMED.harf, NAMED.harf_jarr) else "ism", case=None, aspect=None)
    elif entry.get("type") == "harf" and found["role"] and plain not in (NAMED.harf, NAMED.harf_jarr):
        entry["type"] = "ism"  # أينما: a particle's card named for a place is a built noun
    elif entry.get("type") in ("ism", "zarf") and found["role"] == NAMED.harf and (found.get("named") or found.get("name")):
        # ما عدا، ما النافية: CAMeL's relative is the particle the reading or its family names
        entry["type"] = "harf"
    if not found["case"] and entry.get("case") != "mabni" and (own := case_of(found["role"])):
        found = {**found, "case": CASE_NAME[own]}  # a recorded ayah's name brings its own case
    moved = found["case"] and found["case"] != entry.get("case")
    if found["role"] == NAMED.fil:
        # أَقِمْ: the root made it a command; the parser, seeing only a sukun, says jazm
        if entry.get("case") == "mabni" and found["case"] == "jazm":
            moved = False
        # a word CAMeL took for a noun (ضُرِبَ، كان) or a mood the particle before settled
        # (لن يذهب), or a command CAMeL read as past (فَاتَّبِعْنِي): the card is the verb's own, by naming's tense
        if entry.get("type") != "fi'l" or moved or found.get("aspect") not in (None, entry.get("aspect")):
            aspect = found.get("aspect") or ("i" if found["case"] != "mabni" else None)
            entry.update(type="fi'l", **rule_engine.verb_card(entry["camel"]["base"], aspect, found["case"]))
        return
    if renamed:
        entry["reason"] = reason(found["role"])  # the reason must explain the new name
    if not _stands_for_own(entry, found, annexed) and moved:
        entry["case"] = found["case"]  # signs.settle writes the sign for it
    if entry["case"] == "mabni" and entry.get("type") != "harf":
        entry["reason"] = reason(found["role"], mabni=True)  # الذي، هذا: in the place of a case


def _stands_for_own(entry: dict, found: dict, annexed: bool) -> bool:
    """The typed vowel is the sign of the role's own case for this kind of word (a sound plural's kasra in nasb, a diptote's fatha in jarr): mirrors
    facts.shows_jarr / shows_nasb_by_kasra on the card's reading, so the role's case stands."""
    own = case_of(found["role"])
    typed = next((letter for letter, name in CASE_NAME.items() if name == found["case"]), None)
    stands = teacher_rules()["signs"]["stands_for"].get(signs.kind_of(entry["camel"], annexed), {})
    if own and stands.get(typed) == own:
        entry["case"] = CASE_NAME[own]
        return True
    return False
