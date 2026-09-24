"""What a typed question turns into before anything is searched for.

Daleel's whole claim is that it finds the right passage without any model
guessing at meaning. That claim rests entirely on this file's subject: four
lookups in mappings that already exist. So these tests use a made-up lexicon
of five words rather than the real dictionary, because what is being checked
is the rule, not whether the dictionary happens to hold a particular word.
"""
from backend.services.daleel.expand import expand

# A stand-in dictionary. Small enough to read, which is the point: every
# expectation below can be traced by eye.
_ROOTS = {"كتاب": "كتب", "كاتب": "كتب", "اب": "ابو", "والد": "ابو"}
_SYNONYMS = {"اب": ("والد",)}
_ENGLISH = {"father": ("أب",), "book": ("كِتَاب",)}


class FakeLexicon:
    def root_of(self, word):
        return _ROOTS.get(word, "")

    def synonyms_of(self, word):
        return _SYNONYMS.get(word, ())

    def arabic_for(self, english_word):
        return _ENGLISH.get(english_word, ())


def run(query, *, max_expand=6, max_translations=3, min_trigram_len=3, lexicon=None):
    return expand(query, lexicon or FakeLexicon(), max_expand=max_expand,
                  max_translations=max_translations, min_trigram_len=min_trigram_len)


def test_an_arabic_word_reaches_its_root():
    """كتاب must find كاتب, and the thing that connects them is the root."""
    assert "كتب" in run("كتاب").roots


def test_two_words_of_one_root_expand_to_the_same_root():
    """The root is the mapping, so both directions land in the same place."""
    assert run("كتاب").roots == run("كاتب").roots


def test_an_english_word_reaches_the_arabic_it_defines():
    """Asking in English has to cross to Arabic, or the tab is Arabic-only."""
    result = run("father")
    assert "اب" in result.related
    assert "ابو" in result.roots


def test_a_synonym_is_searched_for_too():
    """Different word, same meaning: the dictionary already lists which."""
    assert "والد" in run("اب").related


def test_a_long_word_is_also_matched_loosely_for_typos():
    """A misspelling shares its three-letter runs with the word meant."""
    assert "كتاب" in run("كتاب").loose


def test_a_short_word_is_never_matched_loosely():
    """Two letters are shared by too much to mean anything as a loose match."""
    assert run("في").loose == ()


def test_diacritics_and_spelling_variants_fold_to_one_term():
    """ٱلْكِتَاب typed any of its several ways has to become one query."""
    assert run("كِتَاب").typed == run("كتاب").typed


def test_expansion_is_capped():
    """One common word must not become a hundred-term search."""
    many = {"x": tuple(f"w{i}" for i in range(50))}

    class Wide(FakeLexicon):
        def synonyms_of(self, word):
            return many.get(word, ())

    result = run("x", max_expand=3, lexicon=Wide())
    # The word itself, plus no more than three of its synonyms.
    assert len(result.typed) + len(result.related) <= 4


class Idioms(FakeLexicon):
    """An English word whose dictionary entries include phrases built on it."""

    def arabic_for(self, english_word):
        return ("لا سمح الله", "الله", "إله", "رب")

    def root_of(self, word):
        return {"الله": "اله", "اله": "اله", "رب": "ربب"}.get(word, "")


def test_single_word_translations_come_before_phrases():
    """The cap keeps real translations, not idioms that merely contain the word."""
    assert run("god", max_translations=3, lexicon=Idioms()).related == ("الله", "اله", "رب")


def test_a_phrase_never_becomes_a_root():
    """A phrase with its spaces squeezed out was searched for as a root."""
    result = run("god", max_translations=4, lexicon=Idioms())
    assert "لا سمح الله" in result.related
    assert all(" " not in r and "لاسمح" not in r for r in result.roots)


def test_an_empty_query_asks_for_nothing():
    """A blank box must not turn into a search that matches every passage."""
    assert run("   ").is_empty()


def test_expansion_touches_no_file_and_no_database():
    """The rules are pure; the lookups arrive from outside.

    Guards the layering: the moment this file reads the dictionary itself, it
    stops being testable without the whole app and starts being slow per query.
    """
    import backend.services.daleel.expand as module

    source = open(module.__file__, encoding="utf-8").read()
    for forbidden in ("sqlite3", "open(", "requests", "dictionary_service", "Path("):
        assert forbidden not in source, f"expand.py must not reference {forbidden}"


def test_a_typed_word_is_never_filed_as_a_synonym():
    """What somebody typed stays first class, even if it is also a synonym.

    Guards the split that fixed a real result: while synonyms counted as
    equal to the typed word, searching كتب put Ibn Faris's entry on رسم at the
    top of the page, because رسم is listed as a synonym and his entry uses it.
    """
    result = run("اب")
    assert "اب" in result.typed
    assert "اب" not in result.related


def test_wildcards_are_not_treated_as_search_syntax():
    """A typed % must be a character, not "match anything".

    It has now been this twice, in two different query languages. Through LIKE
    it was a wildcard and one % returned twelve passages picked at random from
    every book, each labelled a clean match. Through the word index it is not a
    wildcard but it is not a word either, so the tokenizer drops it and the
    filter that is left, the source on its own, matches every passage there is.
    Same twelve quotations, same lie, different mechanism, so the test outlives
    the escaping it was written for.
    """
    from backend.services.daleel.search import _escape, _is_a_word, search

    assert not _is_a_word("%") and not _is_a_word("_")
    assert _is_a_word("في")
    assert search("%") == []
    assert search("_") == []
    # A quote is the one character that is syntax here, and it is doubled
    # rather than passed through, so a term cannot close its own phrase.
    assert _escape('a"b') == 'a""b'
