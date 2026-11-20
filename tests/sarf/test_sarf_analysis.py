"""A word's whole Sarf answer, called without the web layer."""
from backend.services.sarf import answer as sarf_word
from tests.nahw_helpers import needs_camel


@needs_camel
def test_istaqbala_conjugates_as_form_x_not_as_qabala():
    got = sarf_word.analyze("اِسْتَقْبَلَ", None)
    assert got.root and got.table and got.table.rows
    assert got.form == "X" and got.wazn
    assert got.source and got.meaning_source


def test_unknown_form_for_root_gives_reason_not_table():
    got = sarf_word.table_for("كتب", "IQ")
    assert got.table is None and got.table_note and got.form is None


@needs_camel
def test_the_babs_offered_for_a_hollow_root_leave_out_those_it_never_takes():
    offered = sarf_word.analyze("قَالَ", None).form_options
    assert "I-nasara" in offered and "I-fataha" not in offered   # no hollow root is on فَتَحَ
    assert sarf_word.analyze("زاخ", None).form_options             # an alif is no weak letter to rule out by


@needs_camel
def test_a_guessed_weak_letter_is_the_one_the_bab_allows(monkeypatch):
    monkeypatch.setattr(sarf_word.roots, "weak_letter_named", lambda root, word="": False)
    got = sarf_word.table_for("بوع", "I-daraba")   # يَبِيعُ, CAMeL's ب.#.ع read بوع
    assert got.table.rows[0].cells["mudari"] == "يَبِيْعُ"
    assert sarf_word.table_for("خوف", "I-fataha").table is None
    assert "I-daraba" in sarf_word.analyze("بَاعَ", None).form_options
    got = sarf_word.analyze("بَاعَ", "I-daraba")    # the root kept as read, so a later switch still guesses its letter
    assert (got.root, got.table.rows[0].cells["mudari"]) == ("بوع", "يَبِيْعُ")


@needs_camel
def test_a_bab_the_dictionary_names_is_judged_on_the_letter_it_tells(monkeypatch):
    monkeypatch.setattr(sarf_word.roots, "weak_letter_named", lambda root, word="": False)
    read = sarf_word.verb_forms.babs_of
    monkeypatch.setattr(sarf_word.verb_forms, "babs_of", lambda word: read(word) | {"form_key": "I-daraba"})
    got = sarf_word.analyze("بَاعَ", None)          # Lane's بَاعَ يَبِيعُ, CAMeL's بوع
    assert (got.form, got.table.rows[0].cells["mudari"]) == ("I-daraba", "يَبِيْعُ")


@needs_camel
def test_a_command_is_rooted_by_its_jussive(monkeypatch):
    assert sarf_word.analyze("قِفْ", None).root == "وقف"     # يَقِفْ less its ي, never قفف
    assert sarf_word.analyze("قُلْ", None).root == "قول"
    monkeypatch.setattr(sarf_word.roots, "root_of", lambda word: "سنو")
    assert sarf_word.analyze("سَنَةٍ", None).root == "سنو"   # any other word: the corpus's root before the tagger's سني


@needs_camel
def test_a_known_weak_letter_is_judged_with_the_word(monkeypatch):
    monkeypatch.setattr(sarf_word.roots, "weak_letter_named", lambda root, word="": bool(word))
    got = sarf_word.analyze("خَافَ", "I-daraba")   # the corpus names خَافَ's و: no يَخِيفُ
    assert got.table is None and "never takes" in got.table_note



@needs_camel
def test_a_weak_letter_the_corpus_names_is_kept(monkeypatch):
    monkeypatch.setattr(sarf_word.roots, "weak_letter_named", lambda root, word="": True)
    got = sarf_word.table_for("خوف", "I-daraba")   # خَافَ يَخَافُ: no يَخِيفُ to make
    assert got.table is None and "never takes" in got.table_note
    assert "I-daraba" not in sarf_word.analyze("خَافَ", None).form_options


def test_a_weak_letter_is_named_by_the_corpus_tag_or_a_root_with_no_twin(monkeypatch):
    roots = sarf_word.roots
    monkeypatch.setattr(roots, "_corpus_roots", lambda: {"خوف": "خوف", "سور": "سور", "سير": "سير", "اكل": "أكل"})
    monkeypatch.setattr(roots.quran_corpus, "root_of", lambda word: {"سَارَ": "سير"}.get(word))
    assert roots.weak_letter_named("خوف") and roots.weak_letter_named("ءكل")   # no خيف filed; no weak letter
    assert not roots.weak_letter_named("سور") and not roots.weak_letter_named("بوع")   # سير filed too; not filed
    assert roots.weak_letter_named("سير", "سَارَ") and not roots.weak_letter_named("سور", "سَارَ")
